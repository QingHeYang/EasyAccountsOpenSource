"""
Agent执行器 - 负责执行Agent协作调用
"""

import uuid
from typing import TYPE_CHECKING, Any, Dict

from ...config.agent_builder import AgentBuilder
from ...models.agent import Agent
from ..agents.agent_registry import AgentRegistry
from ...models import AgentCall
from ..websocket_handler import MessageType
from .base_executor import BaseExecutor, ExecutionResult

if TYPE_CHECKING:
    from ..agents.agent_executor import AgentExecutor


class SubAgentExecutor(BaseExecutor):
    """Agent执行器 - 处理Agent之间的协作调用"""
    
    def __init__(self, 
                 agent_excutor: 'AgentExecutor',
                 agent_builder: AgentBuilder,
                 agent_registry: AgentRegistry,
                 repository_adapter):
        """
        初始化Agent执行器
        
        Args:
            agent_excutor: 聊天管理器（用于内部调用）
            agent_builder: Agent构建器
            agent_registry: Agent注册表
            repository_adapter: 数据库适配器
        """
        super().__init__()
        self.agent_excutor = agent_excutor  # 这里的agent_excutor实际上应该是agent_executor
        self.agent_builder = agent_builder
        self.repository = repository_adapter
        self.agent_registry = agent_registry
        
        # 调用栈管理（防止循环调用）
        self._call_stacks = {}  # conversation_id -> [agent_ids]
        self.max_call_depth = 5
    
    async def execute(self, call: Any, context: Dict[str, Any]) -> ExecutionResult:
        """
        执行Agent调用
        
        Args:
            call: Agent调用对象（AgentCall）
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        # 验证上下文
        if not await self.validate_context(context):
            return self._create_error_result("执行上下文无效")
        
        # 只支持AgentCall
        if isinstance(call, AgentCall):
            return await self._execute_single_agent(call, context)
        else:
            return self._create_error_result(f"不支持的调用类型: {type(call)}")
    
    
    async def _execute_single_agent(self, call: AgentCall, context: Dict[str, Any]) -> ExecutionResult:
        """执行单个Agent调用"""
        conversation_id = context["conversation_id"]
        user_id = context["user_id"]
        parent_agent: Agent = context["agent"]
        
        # 检查调用深度
        if not self._check_call_depth(conversation_id, call.agent_id):
            return self._create_error_result(
                f"超过最大调用深度({self.max_call_depth})或检测到循环调用"
            )
        
        # 获取目标Agent配置
        target_app_config = self.agent_builder.get_agent(call.agent_id)
        if not target_app_config or not target_app_config.enable:
            return self._create_error_result(f"Agent '{call.agent_id}' 不可用或已禁用")
        
        try:
            # 创建子会话ID（用于隔离历史记录）
            sub_conversation_id = f"{conversation_id}_sub_{uuid.uuid4().hex[:8]}"
            
            # 记录调用栈
            self._push_call_stack(conversation_id, call.agent_id)
            
            # 构建Agent执行的消息
            agent_message = self._build_agent_message(call, context)
            
            self.logger.info(
                "执行Agent调用",
                {
                    "agent_id": call.agent_id,
                    "parent_conversation": conversation_id,
                    "sub_conversation": sub_conversation_id,
                    "task": call.task[:50] + "..." if len(call.task) > 50 else call.task
                }
            )
            
            # 创建子agent
            sub_agent = self.agent_registry.build_sub_agent(call.agent_id)
            sub_agent.websocket_mode = parent_agent.websocket_mode
            sub_agent.parent_agent_id = parent_agent.agent_id
            sub_agent.current_conversation_id = sub_conversation_id
            
            result = await self.agent_excutor.execute(
                agent=sub_agent, 
                message=agent_message, 
                conversation_id=sub_conversation_id, 
                user_id=user_id, 
                source="internal", 
                parent_conversation_id=conversation_id)
            
            # 提取结果
            agent_result = self._extract_agent_result(result)
            
            return self._create_success_result(
                result=agent_result,
                metadata={
                    "agent_id": call.agent_id,
                    "sub_conversation_id": sub_conversation_id
                }
            )
            
        except Exception as e:
            import traceback
            self.logger.error(
                "Agent执行失败",
                {
                    "agent_id": call.agent_id,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
            )
            
            return self._create_error_result(
                error=f"Agent执行失败: {str(e)}",
                metadata={"agent_id": call.agent_id}
            )
        finally:
            # 清理调用栈
            self._pop_call_stack(conversation_id)
    
    
    def _build_agent_message(self, call: AgentCall, context: Dict[str, Any]) -> str:
        """构建发送给Agent的消息"""
        message = call.task
        
        # 如果有上下文信息，添加到消息中
        if call.context:
            context_str = "\n[上下文信息]:\n"
            for key, value in call.context.items():
                context_str += f"- {key}: {value}\n"
            message = message + "\n" + context_str
        
        # 如果有父对话的相关信息
        if "parent_result" in context:
            message += f"\n\n[相关信息]:\n{context['parent_result']}"
        
        return message
    
    def _extract_agent_result(self, message_box: Dict[str, Any]) -> str:
        """从message_box中提取Agent的最终回复
        
        Args:
            message_box: 包含不同类型消息的字典，key是消息类型，value是WebSocketMessage
            
        Returns:
            Agent的响应内容
        """
        if not message_box:
            self.logger.warning("子Agent返回空的message_box")
            return "Agent未返回任何内容"
        
        # 记录收到的消息类型
        self.logger.info("子Agent返回消息类型", {
            "message_types": list(message_box.keys()),
            "total_count": len(message_box)
        })
        
        # 优先级查找顺序：segment > tool_response > error
        # 1. 查找 segment 类型的消息（Agent 的主要回复）
        if MessageType.SEGMENT.value in message_box:
            segment_msg = message_box[MessageType.SEGMENT.value]
            if segment_msg.text:
                self.logger.info("找到segment消息", {
                    "text_length": len(segment_msg.text),
                    "has_object": bool(segment_msg.object)
                })
                return segment_msg.text
        
        # 2. 查找最后一个 tool_response（如果有多个工具调用）
        if MessageType.TOOL_RESPONSE.value in message_box:
            tool_msg = message_box[MessageType.TOOL_RESPONSE.value]
            # tool_response 的内容可能在 text 或 object.tool_response 中
            response_text = tool_msg.text or (tool_msg.object or {}).get("tool_response", "")
            if response_text:
                self.logger.info("找到tool_response消息", {
                    "response_length": len(response_text)
                })
                return response_text
        
        # 3. 如果有错误消息，返回错误
        if MessageType.ERROR.value in message_box:
            error_msg = message_box[MessageType.ERROR.value]
            self.logger.warning("子Agent返回错误", {
                "error": error_msg.text
            })
            return f"Agent执行出错: {error_msg.text}"
        
        # 4. 收集所有可能包含内容的消息
        all_texts = []
        for msg_type, msg in message_box.items():
            if msg.text and msg_type not in [MessageType.START.value, MessageType.COMPLETE.value, MessageType.EXIT.value]:
                all_texts.append(msg.text)
        
        if all_texts:
            self.logger.info("通过遍历找到消息", {
                "message_count": len(all_texts),
                "total_length": sum(len(text) for text in all_texts)
            })
            return "\n".join(all_texts)
        
        self.logger.warning("未找到任何有效的Agent响应消息", {
            "message_types": list(message_box.keys())
        })
        
        return "Agent执行完成但无输出"
    
    # 调用栈管理
    def _check_call_depth(self, conversation_id: str, agent_id: str) -> bool:
        """检查调用深度和循环调用"""
        stack = self._call_stacks.get(conversation_id, [])
        
        # 检查深度
        if len(stack) >= self.max_call_depth:
            return False
        
        # 检查循环调用
        if agent_id in stack:
            return False
        
        return True
    
    def _push_call_stack(self, conversation_id: str, agent_id: str):
        """添加到调用栈"""
        if conversation_id not in self._call_stacks:
            self._call_stacks[conversation_id] = []
        self._call_stacks[conversation_id].append(agent_id)
    
    def _pop_call_stack(self, conversation_id: str):
        """从调用栈移除"""
        if conversation_id in self._call_stacks and self._call_stacks[conversation_id]:
            self._call_stacks[conversation_id].pop()
            # 清理空栈
            if not self._call_stacks[conversation_id]:
                del self._call_stacks[conversation_id]
    
