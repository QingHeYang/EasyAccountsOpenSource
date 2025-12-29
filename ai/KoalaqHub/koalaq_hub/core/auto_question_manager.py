import json
import time
from typing import Dict, List, Optional

from ..database.repository_adapter import RepositoryAdapter
from ..models.agent import Agent
from .llm.enhanced_llm_client import EnhancedLLMClient, LLMResponse
from .logging_utils import ManagerLogger
from .prompt.function_prompt_assembler import FunctionPromptAssembler
from .token_manager import TokenManager
from .tool.mcp.mcp_tool_manager import ToolManager
from .websocket_handler import MessageBuilder, WebSocketHandler


class AutoQuestionManager:
    """
    自动问题生成管理器，负责根据对话历史生成用户可能感兴趣的问题。
    与SummaryManager类似，提供异步的问题生成功能。
    """

    def __init__(self, sqlite_storage: RepositoryAdapter, tool_manager: ToolManager, function_prompt_assembler: FunctionPromptAssembler):
        """
        初始化自动问题管理器

        Args:
            sqlite_storage: 数据库适配器
            tool_manager: 工具管理器
            function_prompt_assembler: 功能提示词组装器
        """
        self.sqlite_storage = sqlite_storage
        self.function_prompt_assembler = function_prompt_assembler
        self.tool_manager = tool_manager
        self.websocket_handler = None
        self.token_manager = TokenManager(sqlite_storage)
        self.logger = ManagerLogger("AutoQuestionManager")
        self.history_manager = None

    def set_websocket_handler(self, websocket_handler: WebSocketHandler):
        """设置WebSocket处理器"""
        self.websocket_handler = websocket_handler

    def set_history_manager(self, history_manager):
        """设置HistoryManager引用，用于token统计"""
        self.history_manager = history_manager

    async def generate_auto_question(self, agent: Agent, conversation_id: str, round_id: str, user_id: str = None):
        """
        生成自动问题建议
        
        Args:
            agent: Agent实例
            conversation_id: 对话ID
            round_id: 轮次ID
            user_id: 用户ID
        """
        start_time = time.time()
        
        try:
            self.logger.info("开始生成自动问题", {
                "conversation_id": conversation_id, 
                "round_id": round_id,
                "user_id": user_id
            })

            # 获取对话历史内容
            conversation_content = await self._make_conversation_content(conversation_id, round_id)
            
            if not conversation_content:
                self.logger.warning("对话内容为空，跳过问题生成", {
                    "conversation_id": conversation_id, 
                    "round_id": round_id
                })
                return

            system_message = agent.system_prompt

            # 获取自动问题生成提示词
            enhanced_system_prompt = self.function_prompt_assembler.load_auto_question_prompt(system_message)


            # 构建用户消息
            user_message = f"请根据以下对话内容，生成3个相关的后续问题：\n\n```conversation\n{conversation_content}\n```"
            llm_request_message = await self._make_llm_request_message(enhanced_system_prompt, user_message)
            
            # 调用LLM生成问题
            llm_response = await self._call_llm(agent, llm_request_message, conversation_id)
            response_content = llm_response.content
            token_usage = llm_response.token_usage
            self.logger.info("问题返回", {
                "response_content": response_content
            })
            # 解析JSON响应
            questions = self._parse_questions_response(response_content)
            
            if not questions:
                self.logger.warning("无法解析LLM响应为有效问题", {
                    "conversation_id": conversation_id,
                    "response": response_content[:200]
                })
                return

            # 通过WebSocket发送问题给前端
            if self.websocket_handler:
                message = MessageBuilder.create_question_message(conversation_id, questions)
                await self.websocket_handler.send_message(conversation_id, message)

            # 记录token使用情况
            if self.token_manager and user_id:
                self.token_manager.add_tokens(
                    token_usage=token_usage,
                    llm=agent.summary_llm,
                    operation_type="auto_question",
                    conversation_id=conversation_id,
                    user_id=user_id
                )

            execution_time = time.time() - start_time
            self.logger.info("自动问题生成完成", {
                "conversation_id": conversation_id,
                "round_id": round_id,
                "questions_count": len(questions),
                "total_tokens": token_usage.total_tokens,
                "prompt_tokens": token_usage.prompt_tokens,
                "completion_tokens": token_usage.completion_tokens,
                "reasoning_tokens": token_usage.reasoning_tokens,
                "execution_time": round(execution_time, 2)
            })

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error("自动问题生成失败", exception=e, extra_data={
                "conversation_id": conversation_id, 
                "round_id": round_id,
                "execution_time": round(execution_time, 2)
            })
            # 不抛出异常，避免影响主流程

    async def _make_conversation_content(self, conversation_id: str, round_id: str) -> str:
        """
        构建对话内容用于问题生成
        
        Args:
            conversation_id: 对话ID
            round_id: 轮次ID
            
        Returns:
            格式化的对话内容字符串
        """
        try:
            # 获取当前轮次的消息
            messages = self.sqlite_storage.get_messages_recorder(round_id)
            
            conversation_parts = []
            
            for message in messages:
                if message.role == "user" and message.type.value == "content":
                    conversation_parts.append(f"用户: {message.content}")
                elif message.role == "assistant" and message.type.value == "content":
                    conversation_parts.append(f"助手: {message.content}")
                elif message.type.value == "tool_call":
                    conversation_parts.append(f"工具调用: {message.tool_name}")
                elif message.type.value == "tool_response":
                    success_text = "成功" if message.tool_success else "失败"
                    conversation_parts.append(f"工具结果({success_text}): {message.content[:100]}...")

            return "\n".join(conversation_parts)
            
        except Exception as e:
            self.logger.error("构建对话内容失败", exception=e, extra_data={
                "conversation_id": conversation_id, 
                "round_id": round_id
            })
            return ""

    async def _make_llm_request_message(self, system_message: str, user_message: str) -> List[Dict[str, str]]:
        """
        构建LLM请求消息格式
        
        Args:
            system_message: 系统提示词
            user_message: 用户消息内容
            
        Returns:
            LLM消息列表
        """
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]

    async def _call_llm(self, agent: Agent, messages: List[Dict[str, str]], conversation_id: str) -> LLMResponse:
        """
        调用LLM生成问题
        
        Args:
            agent: Agent实例
            messages: 消息列表
            conversation_id: 对话ID
            
        Returns:
            LLM响应结果
        """
        llm_client = EnhancedLLMClient.create_from_llm(agent.summary_llm)
        llm_response = await llm_client.block(messages=messages, conversation_id=conversation_id)
        
        self.logger.info("自动问题生成token使用情况", {
            "conversation_id": conversation_id,
            "total_tokens": llm_response.token_usage.total_tokens,
            "prompt_tokens": llm_response.token_usage.prompt_tokens,
            "completion_tokens": llm_response.token_usage.completion_tokens,
            "reasoning_tokens": llm_response.token_usage.reasoning_tokens
        })
        
        return llm_response

    def _parse_questions_response(self, response_content: str) -> Optional[List[Dict[str, str]]]:
        """
        解析LLM响应中的JSON格式问题
        
        Args:
            response_content: LLM响应内容
            
        Returns:
            解析后的问题列表，每个问题包含question字段
        """
        try:
            # 尝试直接解析JSON
            try:
                data = json.loads(response_content)
            except json.JSONDecodeError:
                # 如果直接解析失败，尝试提取代码块中的JSON
                json_str = None
                
                # 首先尝试 ```json 标记的代码块
                if "```json" in response_content:
                    start = response_content.find("```json") + 7
                    end = response_content.find("```", start)
                    if end != -1:
                        json_str = response_content[start:end].strip()
                
                # 如果没有找到 ```json，尝试普通的 ``` 代码块
                elif "```" in response_content:
                    start = response_content.find("```") + 3
                    end = response_content.find("```", start)
                    if end != -1:
                        json_str = response_content[start:end].strip()
                
                # 如果找到了JSON字符串，尝试解析
                if json_str:
                    try:
                        data = json.loads(json_str)
                    except json.JSONDecodeError:
                        raise json.JSONDecodeError("代码块中的JSON格式无效", json_str, 0)
                else:
                    raise json.JSONDecodeError("响应中不包含JSON格式", response_content, 0)

            # 验证数据格式 - 简化后的JSON格式
            if isinstance(data, dict) and "questions" in data:
                questions = data["questions"]
            elif isinstance(data, list):
                questions = data
            else:
                self.logger.warning("响应格式不正确", {"response": response_content[:200]})
                return None

            # 验证并转换问题格式 - 适配简化的JSON格式
            valid_questions = []
            for q in questions:
                if isinstance(q, str):
                    # 新格式：直接是字符串
                    valid_questions.append({"question": q})
                elif isinstance(q, dict) and "question" in q:
                    # 旧格式兼容：包含question字段的对象
                    valid_questions.append({"question": q["question"]})

            return valid_questions if valid_questions else None
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            self.logger.error("解析问题响应失败", exception=e, extra_data={
                "response_content": response_content[:200]
            })
            return None