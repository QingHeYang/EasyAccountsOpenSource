"""
基础聊天处理器 - 包含公共业务逻辑
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ...config.settings import config
from ...models.agent import Agent
from ..executor import SubAgentExecutor, ToolExecutor
from ..history_manager import HistoryManager
from ..llm.enhanced_llm_client import LLMResponse, TokenUsage
from ..logging_utils import ManagerLogger
from ..parser.agent_parser import AgentCall
from ..summary_manager import SummaryManager
from ..tool.mcp.mcp_tool_manager import ToolManager
from ..websocket_handler import MessageBuilder, WebSocketMessage


class BaseChatProcessor(ABC):
    """聊天处理器基类 - 包含公共业务逻辑"""

    def __init__(self, history_manager: HistoryManager, tool_manager: ToolManager,  summary_manager: SummaryManager):
        """初始化基础聊天处理器

        Args:
            history_manager: 历史记录管理器
            tool_manager: 工具管理器
            llm_client: LLM客户端
            summary_manager: 总结管理器
        """
        self.history_manager = history_manager
        self.tool_manager = tool_manager
        self.summary_manager = summary_manager

        # 初始化日志记录器
        self.logger = ManagerLogger(f"{self.__class__.__name__}")
        
        # 初始化执行器（需要在子类中完成，因为需要额外的依赖）
        self.tool_executor:ToolExecutor = None
        self.agent_executor:SubAgentExecutor = None
        
        # 存储当前处理的Agent实例
        self.agent = None

    @abstractmethod
    async def call_llm(self, agent: Agent, messages: list, conversation_id: str):
        """调用LLM - 子类必须实现"""
        pass

    @abstractmethod
    async def send_message(self, conversation_id: str, message: WebSocketMessage):
        """发送消息 - 子类必须实现"""
        pass

    @abstractmethod
    def get_result(self):
        """获取处理结果 - 子类必须实现"""
        pass

    async def process_message(self, agent: Agent,
                              message: str, 
                              user_id: str, 
                              conversation_id: str, 
                              round_id: str = None,
                              recursion_depth: int = None, 
                              is_call_tool: bool = False, 
                              **kwargs) -> Any:  # fmt: skip
        """处理消息的公共逻辑

        Args:
            agent: Agent实例
            message: 用户消息
            user_id: 用户ID
            conversation_id: 会话ID
            round_id: 当前轮次ID（可选）
            recursion_depth: 当前递归深度（可选，默认用self.recursion_depth）
            is_call_tool: 是否为工具调用响应
            **kwargs: 其他参数

        Returns:
            处理结果（HTTP返回内容，WebSocket返回None）
        """
        # 保存agent引用
        self.agent = agent
        
        try:
            if recursion_depth is None:
                recursion_depth = agent.tool_round

            # 1. 加载历史记录,如果会话不存在，则创建会话
            self.history_manager.load_history(agent=agent,user_id=user_id, conversation_id=conversation_id)
            round_id = self.history_manager.load_round(
                agent=agent,
                user_id=user_id, 
                conversation_id=conversation_id, 
                round_id=round_id)

            # 2. 添加用户消息到历史
            if not is_call_tool: # 如果is_call_tool为True，说明已经把tool添加完了，直接调用即可
                self.history_manager.add_user_message(agent=agent, user_id=user_id, conversation_id=conversation_id, round_id=round_id, content=message)

            self.logger.info("对话索引",
                             {"conversation_id": conversation_id, 
                              "user_id": user_id, 
                              "history_length": len(self.history_manager.get_history(agent, user_id, conversation_id))})

            # 3. 获取历史记录并调用LLM
            history = self.history_manager.get_history(agent, user_id, conversation_id)
            llm_response: LLMResponse = await self.call_llm(agent, history, conversation_id)

            full_response = llm_response.content
            reasoning_content = llm_response.reasoning_content
            token_usage: TokenUsage = llm_response.token_usage
            #self.logger.info(f"full_response: {full_response}")
            self.logger.info("响应生成完毕",
                             {"response_length": len(full_response),
                              "总token": token_usage.total_tokens, 
                              "输入token": token_usage.prompt_tokens, 
                              "输出token": token_usage.completion_tokens, 
                              "推理token": token_usage.reasoning_tokens, 
                              "conversation_id": conversation_id})

            if llm_response.is_interrupted: # 中断直接保存
                # 短期修复：确保 content 不为空，避免 LLM API 错误
                if not full_response and reasoning_content:
                    full_response = "[思考被中断...]"
                    self.logger.info("中断时content为空，使用占位符", {
                        "conversation_id": conversation_id,
                        "has_reasoning": bool(reasoning_content)
                    })
                
                self.history_manager.add_assistant_message(
                    agent=agent,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    round_id=round_id,
                    content=full_response,
                    tool_calls=None,  # 中断时没有工具调用
                    token_usage=token_usage,
                    reasoning_content=reasoning_content)
                return self.get_result()

            # 4. 检查是否是错误响应
            if full_response.startswith("LLM服务出现错误:"):
                # 添加错误消息到历史记录
                self.history_manager.add_error_message(user_id, conversation_id, round_id, full_response)
                self.logger.error("LLM服务错误", {"response": full_response, "conversation_id": conversation_id})
                return self.get_result()
            
            # 只有当 full_response 不为空时才发送 segment 消息
            # 避免纯工具调用时发送空的 segment 消息
            if full_response and full_response.strip():
                message_obj = MessageBuilder.create_segment_message(conversation_id, full_response, reasoning_content)
                await self.send_message(conversation_id, message_obj)
            else:
                self.logger.info("跳过发送空的segment消息", {
                    "conversation_id": conversation_id,
                    "has_tool_calls": bool(llm_response.tool_calls),
                    "tool_calls_count": len(llm_response.tool_calls) if llm_response.tool_calls else 0
                })
            
            # 5. 处理工具调用和 Agent 调用
            has_executions = await self._handle_tool_and_agent_calls(
                agent=agent,
                llm_response=llm_response,
                user_id=user_id,
                conversation_id=conversation_id,
                round_id=round_id,
                recursion_depth=recursion_depth,
                **kwargs
            )
            
            if has_executions:
                return self.get_result()
            
            # 轮次结束处理
            self.logger.info("轮次结束 - 无调用", {"conversation_id": conversation_id, "round_id": round_id})
            # 发送退出消息
            message_obj = MessageBuilder.create_exit_message(conversation_id)
            await self.send_message(conversation_id, message_obj)
            # 记录助手响应
            self.history_manager.add_assistant_message(
                agent=agent,
                user_id=user_id,
                conversation_id=conversation_id,
                round_id=round_id,
                content=full_response,
                tool_calls=None,
                token_usage=token_usage,
                reasoning_content=reasoning_content
            )
            # 轮次结束，执行总结
            await self.history_manager.on_round_end(agent, conversation_id, round_id, self._get_websocket_handler())
            return self.get_result()

        except Exception as e:
            error_message = f"处理消息时出现错误: {str(e)}"
            self.logger.error("消息处理错误", {"error_message": error_message, "conversation_id": conversation_id})
            # 发送错误消息
            message_obj = MessageBuilder.create_error_message(conversation_id, error_message)
            await self.send_message(conversation_id, message_obj)

            # 添加错误消息到历史记录
            if round_id:
                self.history_manager.add_error_message(user_id, conversation_id, round_id, error_message)

            return self.get_result()
    
    async def _handle_tool_and_agent_calls(self, agent: Agent, llm_response: LLMResponse,
                                          user_id: str,
                                          conversation_id: str, round_id: str,
                                          recursion_depth: int, **kwargs) -> bool:
        """处理工具调用和 Agent 调用
        
        Returns:
            bool: 是否有执行（工具或 Agent）
        """
        full_response = llm_response.content
        reasoning_content = llm_response.reasoning_content
        token_usage = llm_response.token_usage
        
        # 检查 Function Calling 工具调用
        has_tool_calls = bool(llm_response.tool_calls)
        
        if not has_tool_calls:
            return False
        
        # 检查是否有 call_agent 调用
        has_agent_calls = False
        calling_agent_id = None
        if has_tool_calls:
            for tc in llm_response.tool_calls:
                if tc.function.get("name") == "call_agent":
                    has_agent_calls = True
                    # 尝试解析 agent_id
                    try:
                        import json
                        args = tc.function.get("arguments", "{}")
                        args = json.loads(args) if isinstance(args, str) else args
                        calling_agent_id = args.get("agent_id")
                    except:
                        pass
                    break
        
        # 存储 assistant 消息
        self.history_manager.add_assistant_message(
            agent=agent,
            user_id=user_id,
            conversation_id=conversation_id,
            round_id=round_id,
            content=full_response,
            tool_calls=[{
                "id": tc.id,
                "type": tc.type,
                "function": tc.function
            } for tc in llm_response.tool_calls] if has_tool_calls else None,
            token_usage=token_usage,
            reasoning_content=reasoning_content,
            is_agent=has_agent_calls,
            agent_id=calling_agent_id
        )
        
        # 执行工具调用
        tool_results = await self._execute_tool_calls(
            agent=agent,
            tool_calls=llm_response.tool_calls,
            user_id=user_id,
            conversation_id=conversation_id,
            round_id=round_id,
            recursion_depth=recursion_depth
        )
        
        # 递归处理
        if tool_results:
            # 如果有工具执行结果，需要继续处理
            if recursion_depth > 0:
                # 还有额度，继续递归
                result = await self.process_message(
                    agent=agent,
                    message="",  # 空消息，让 LLM 根据历史上下文继续
                    user_id=user_id,
                    conversation_id=conversation_id,
                    round_id=round_id,
                    recursion_depth=recursion_depth - 1,
                    is_call_tool=True,
                    **kwargs
                )
                return True
            else:
                # 额度已用完，但仍需要让 LLM 处理工具结果并生成最终回复
                self.logger.info("工具调用额度已用完，执行最后一次LLM调用", {
                    "conversation_id": conversation_id,
                    "tool_results_count": len(tool_results)
                })
                # 执行最后一次调用，但递归深度保持为0（防止LLM再次调用工具）
                result = await self.process_message(
                    agent=agent,
                    message="",  # 空消息，让 LLM 根据历史上下文继续
                    user_id=user_id,
                    conversation_id=conversation_id,
                    round_id=round_id,
                    recursion_depth=0,  # 保持为0，确保不会再执行工具
                    is_call_tool=True,
                    **kwargs
                )
                return True
        else:
            # 没有工具执行结果，直接结束
            self.logger.info("无需进一步处理", {"conversation_id": conversation_id})
            # 发送退出消息
            message_obj = MessageBuilder.create_exit_message(conversation_id)
            await self.send_message(conversation_id, message_obj)
            # 轮次结束，执行总结
            await self.history_manager.on_round_end(agent, conversation_id, round_id, self._get_websocket_handler())
            return True
    
    async def _execute_tool_calls(self, agent: Agent, tool_calls: List,
                                  user_id: str, conversation_id: str,
                                  round_id: str, recursion_depth: int) -> List[Dict[str, Any]]:
        """执行工具调用
        
        Args:
            agent: Agent实例
            tool_calls: LLM返回的工具调用列表
            user_id: 用户ID
            conversation_id: 会话ID
            round_id: 轮次ID
            recursion_depth: 递归深度
            
        Returns:
            工具执行结果列表
        """
        self.logger.info(f"Function Calling 模式 - 检测到 {len(tool_calls)} 个工具调用")
        
        # 转换为统一格式
        tool_calls_list = [{
            "id": tc.id,
            "type": tc.type,
            "function": tc.function
        } for tc in tool_calls]
        
        # 分离 call_agent 调用和普通工具调用
        agent_calls = []
        tool_calls_to_execute = []
        
        for tc in tool_calls_list:
            tool_name = tc["function"]["name"]
            tool_call_data = {
                "tool_call_id": tc["id"],
                "tool_name": tool_name,
                "arguments": tc["function"]["arguments"]
            }
            
            if tool_name == "call_agent":
                # call_agent 特殊处理，不发送 tool message，留到最后执行
                agent_calls.append(tool_call_data)
            else:
                # 其他所有工具（包括内部工具和MCP工具），发送 tool message
                message_obj = MessageBuilder.create_tool_call_message(
                    conversation_id, tool_name, tc["id"], tc["function"]["arguments"]
                )
                await self.send_message(conversation_id, message_obj)
                tool_calls_to_execute.append(tool_call_data)
        
        # 构建执行上下文
        execution_context = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "round_id": round_id,
            "agent": agent,
            "recursion_depth": recursion_depth,
            "tool_timeout": config.tool_execution_timeout
        }
        
        tool_results = []
        
        if tool_calls_to_execute:
            # 分离内部工具和MCP工具
            inner_tool_calls = []
            mcp_tool_calls = []
            
            for tc in tool_calls_to_execute:
                if hasattr(self, 'inner_tool_executor') and self.inner_tool_executor and \
                   self.inner_tool_executor.is_inner_tool(tc["tool_name"]):
                    inner_tool_calls.append(tc)
                else:
                    mcp_tool_calls.append(tc)
            
            # 执行内部工具
            if inner_tool_calls and hasattr(self, 'inner_tool_executor') and self.inner_tool_executor:
                inner_results = await self.inner_tool_executor.execute_batch(inner_tool_calls, execution_context)
                tool_results.extend(inner_results)
            
            # 执行MCP工具
            if mcp_tool_calls and self.tool_executor:
                mcp_results = await self.tool_executor.execute_batch(mcp_tool_calls, execution_context)
                tool_results.extend(mcp_results)
        
        # 立即存储所有工具结果
        for result in tool_results:
            self.history_manager.add_tool_result_message(
                agent=agent,
                user_id=user_id,
                conversation_id=conversation_id,
                round_id=round_id,
                tool_call_id=result["tool_call_id"],
                result=result["result"],
                success=result["success"],
                tool_name=result.get("tool_name")
            )
            message_obj = MessageBuilder.create_tool_response_message(
                conversation_id=conversation_id,
                tool_response=result["result"],
                tool_name=result["tool_name"],
                tool_call_id=result["tool_call_id"],
                status=result["success"]
            )
            await self.send_message(conversation_id, message_obj)
        
        if agent_calls:
            agent_results = await self._execute_agent_calls(
                agent=agent,
                agent_calls=agent_calls,
                user_id=user_id,
                conversation_id=conversation_id,
                round_id=round_id,
                execution_context=execution_context
            )
            tool_results.extend(agent_results)
        
        
        
        return tool_results
    
    async def _execute_agent_calls(self, agent: Agent, agent_calls: List[Dict[str, Any]],
                                   user_id: str, conversation_id: str, round_id: str,
                                   execution_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """执行 call_agent 调用（独立方法，最后执行）
        
        Args:
            agent: Agent实例
            agent_calls: call_agent 调用列表
            user_id: 用户ID
            conversation_id: 会话ID
            round_id: 轮次ID
            execution_context: 执行上下文
            
        Returns:
            Agent 执行结果列表（工具结果格式）
        """
        results = []
        
        # 检查递归深度（工具调用额度）
        recursion_depth = execution_context.get("recursion_depth", 0)
        if recursion_depth <= 0:
            self.logger.warning("工具调用额度耗尽，拒绝执行 call_agent", {
                "conversation_id": conversation_id,
                "agent_calls_count": len(agent_calls)
            })
            # 为所有 agent 调用返回额度用尽的错误
            for call in agent_calls:
                results.append({
                    "tool_call_id": call["tool_call_id"],
                    "tool_name": "call_agent",
                    "result": "工具调用额度已用完：本轮对话的工具调用次数已达上限。请根据已有信息完成任务，或告知用户需要分步执行。",
                    "success": False
                })
            return results
        
        if not self.agent_executor:
            # 如果没有 agent 执行器，返回错误
            for call in agent_calls:
                results.append({
                    "tool_call_id": call["tool_call_id"],
                    "tool_name": "call_agent",
                    "result": "Agent执行器未初始化",
                    "success": False
                })
            return results
        
        # 执行每个 agent 调用
        for call in agent_calls:
            try:
                # 解析 arguments（可能是字符串）
                arguments = call["arguments"]
                if isinstance(arguments, str):
                    import json
                    arguments = json.loads(arguments)
                
                # 构建 AgentCall 对象
                agent_call = AgentCall(
                    agent_id=arguments["agent_id"],
                    task=arguments["task"],
                    context=arguments.get("context", {})
                )
                
                self.logger.info("执行 call_agent", {
                    "agent_id": agent_call.agent_id,
                    "task": agent_call.task[:50] + "..." if len(agent_call.task) > 50 else agent_call.task
                })
                
                # 执行 agent 调用
                result = await self.agent_executor.execute(agent_call, execution_context)
                
                # 存储 agent 调用结果（使用 add_sub_agent_message 保留消息类型区分）
                if result.success:
                    self.history_manager.add_sub_agent_message(
                        agent=agent,
                        user_id=user_id,
                        conversation_id=conversation_id,
                        round_id=round_id,
                        content=result.result,
                        agent_id=agent_call.agent_id,
                        tool_call_id=call["tool_call_id"],  # 添加 tool_call_id
                        sub_conversation_id=result.metadata.get("sub_conversation_id") if result.metadata else None
                    )
                
                # 添加到结果列表
                results.append({
                    "tool_call_id": call["tool_call_id"],
                    "tool_name": "call_agent",
                    "result": result.result if result.success else f"错误: {result.error}",
                    "success": result.success
                })
                
            except Exception as e:
                self.logger.error("执行 call_agent 失败", {
                    "error": str(e),
                    "call": call
                })
                
                error_message = f"执行失败: {str(e)}"
                
                # 尝试提取 agent_id
                agent_id = "unknown"
                try:
                    arguments = call.get("arguments", {})
                    if isinstance(arguments, str):
                        import json
                        arguments = json.loads(arguments)
                    if isinstance(arguments, dict):
                        agent_id = arguments.get("agent_id", "unknown")
                except:
                    pass
                
                # 存储错误结果（仍然使用 add_sub_agent_message）
                self.history_manager.add_sub_agent_message(
                    agent=agent,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    round_id=round_id,
                    content=error_message,
                    agent_id=agent_id,
                    tool_call_id=call["tool_call_id"],
                    sub_conversation_id=None
                )
                
                results.append({
                    "tool_call_id": call["tool_call_id"],
                    "tool_name": "call_agent",
                    "result": error_message,
                    "success": False
                })
        
        return results
    
    def _get_websocket_handler(self):
        """获取WebSocket处理器（子类可以重写）"""
        # 对于HTTP处理器，这里可能返回None
        # 对于WebSocket处理器，返回实际的websocket_handler
        return None
