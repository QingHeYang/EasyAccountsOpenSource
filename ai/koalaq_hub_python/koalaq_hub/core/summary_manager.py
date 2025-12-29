import datetime
import time
from typing import Dict, List

from ..config.settings import config
from ..database.repository_adapter import RepositoryAdapter
from ..models.agent import Agent
from ..models.data_models import SummaryLog
from ..models.message import MessageType
from .llm.enhanced_llm_client import EnhancedLLMClient, LLMResponse, TokenUsage
from .logging_utils import ManagerLogger
from .prompt.function_prompt_assembler import FunctionPromptAssembler
from .token_manager import TokenManager
from .websocket_handler import MessageBuilder, WebSocketHandler


class SummaryManager:
    """
    总结管理器，负责对话、轮次、快照的总结生成与读取。
    由HistoryManager持有，主入口初始化。
    """

    def __init__(self, sqlite_storage: RepositoryAdapter, function_prompt_assembler: FunctionPromptAssembler):
        self.sqlite_storage = sqlite_storage
        # 使用注入的功能提示词组装器
        self.function_prompt_assembler = function_prompt_assembler
        self.websocket_handler = None
        # 初始化TokenManager
        self.token_manager = TokenManager(sqlite_storage)
        # 初始化日志记录器
        self.logger = ManagerLogger("SummaryManager")
        # history_manager的引用，用于累加token到用户
        self.history_manager = None

    def set_websocket_handler(self, websocket_handler: WebSocketHandler):
        self.websocket_handler = websocket_handler

    def set_history_manager(self, history_manager):
        """设置HistoryManager引用，用于token统计"""
        self.history_manager = history_manager

    def create_summary_log_with_token_tracking(
        self, 
        agent: Agent, 
        summary_content: str, 
        conversation_id: str = None, 
        round_id: str = None, 
        snapshot_id: int = None,
        user_id: str = None) -> int:
        """通用的summary_log创建方法，自动集成token管理

        Args:
            summary_content: 总结内容描述
            conversation_id: 会话ID
            round_id: 轮次ID
            snapshot_id: 快照ID

        Returns:
            创建的日志记录ID
        """
        # 检查 agent 是否为 None
        if not agent:
            raise ValueError("Agent 参数不能为 None")
            
        # 获取当前使用的平台和模型信息
        platform, model = agent.summary_llm.platform, agent.summary_llm.model

        # 创建总结日志记录
        summary_log = SummaryLog(
            summary_content=summary_content, 
            status="pending", 
            conversation_id=conversation_id, 
            round_id=round_id, 
            snapshot_id=snapshot_id, 
            platform=platform, 
            model=model, 
            created_at=datetime.datetime.now().isoformat())

        return self.sqlite_storage.create_summary_log(summary_log)

    def update_summary_log_with_token_tracking(
        self,agent: Agent, 
        log_id: int, 
        summary_result: str, 
        token_usage: TokenUsage, 
        execution_time: float, 
        user_id: str = None,
        conversation_id: str = None):
        """通用的summary_log更新方法，自动集成token管理

        Args:
            log_id: 日志记录ID
            summary_result: 总结结果
            total_tokens: 使用的token数量
            execution_time: 执行时间
            user_id: 用户ID (用于将token累加到用户)
        """
        # 保留两位小数
        execution_time_rounded = round(execution_time, 2)

        # 更新日志为成功
        self.sqlite_storage.update_summary_log(
            log_id=log_id, 
            summary_result=summary_result, 
            status="success", 
            execution_time=execution_time_rounded)
        
        # 添加token统计到summary_log

        # 使用TokenManager记录token统计到模型
        self.token_manager.add_tokens(
            token_usage=token_usage, 
            llm=agent.summary_llm, 
            operation_type="summary", 
            conversation_id=conversation_id, 
            summary_id=log_id,
            user_id=user_id)


    def update_summary_log_failed(self,agent: Agent, log_id: int, error_message: str, execution_time: float):
        """更新总结日志为失败状态

        Args:
            log_id: 日志记录ID
            error_message: 错误信息
            execution_time: 执行时间
        """
        # 保留两位小数
        execution_time_rounded = round(execution_time, 2)

        self.sqlite_storage.update_summary_log(log_id=log_id, status="failed", error_message=error_message, execution_time=execution_time_rounded)

    async def generate_conversation_title(self, agent: Agent, conversation_id: str,  round_id: str,  user_id: str = None):
        """生成对话标题"""
        start_time = time.time()
        log_id = None

        try:
            # 创建标题生成日志记录
            round_message = await self._make_summary_message(conversation_id, round_id)
            log_id = self.create_summary_log_with_token_tracking(
                agent=agent,
                summary_content=f"Title生成 - {round_message[:100]}...", 
                conversation_id=conversation_id, 
                round_id=round_id,
                user_id=user_id)

            # 执行标题生成
            round_message = f"```messages\n以下是对话内容：\n{round_message}\n```"
            system_prompt = self.function_prompt_assembler.load_title_summary_prompt()
            llm_request_message = await self._make_llm_request_message(system_prompt, round_message)
            llm_response = await self._call_llm(agent, llm_request_message, conversation_id)
            response = llm_response.content
            token_usage = llm_response.token_usage

            # 更新数据库和发送WebSocket消息
            self.sqlite_storage.update_conversation_title(conversation_id, response)
            if self.websocket_handler:
                message = MessageBuilder.create_title_message(conversation_id, response)
                await self.websocket_handler.send_message(conversation_id, message)

            # 更新日志为成功并记录token统计
            execution_time = time.time() - start_time
            self.update_summary_log_with_token_tracking(
                agent=agent,
                log_id=log_id, 
                summary_result=response, 
                token_usage=token_usage, 
                execution_time=execution_time, 
                user_id=user_id,
                conversation_id=conversation_id)

            self.logger.info(
                "生成对话标题完成", 
                {"conversation_id": conversation_id, 
                 "title": response, 
                 "total_tokens": token_usage.total_tokens, 
                 "prompt_tokens": token_usage.prompt_tokens, 
                 "completion_tokens": token_usage.completion_tokens, 
                 "reasoning_tokens": token_usage.reasoning_tokens, 
                 "log_id": log_id, "execution_time": round(execution_time, 2)})

        except Exception as e:
            # 更新日志为失败
            if log_id:
                execution_time = time.time() - start_time
                self.update_summary_log_failed(agent, log_id, str(e), round(execution_time, 2))

            self.logger.error("生成对话标题失败", exception=e, extra_data={"conversation_id": conversation_id, "round_id": round_id, "log_id": log_id})
            raise

    async def summarize_round(self, agent: Agent, conversation_id: str, round_id: str, user_id: str = None):
        """总结指定轮次（round）"""
        start_time = time.time()
        log_id = None

        try:
            # 创建总结日志记录
            round_message = await self._make_summary_message(conversation_id, round_id)
            log_id = self.create_summary_log_with_token_tracking(
                agent=agent,
                summary_content=f"Round总结 - {round_message[:200]}...", 
                conversation_id=conversation_id, 
                round_id=round_id,
                user_id=user_id)

            # 执行总结
            round_message = f"\n以下是对话内容：\n{round_message}\n"
            system_prompt = self.function_prompt_assembler.load_round_summary_prompt()
            llm_request_message = await self._make_llm_request_message(system_prompt, round_message)
            llm_response = await self._call_llm(agent, llm_request_message, conversation_id)
            response = llm_response.content
            token_usage = llm_response.token_usage
            # 更新数据库
            self.sqlite_storage.update_round_summary(conversation_id, round_id, response)

            # 更新日志为成功并记录token统计
            execution_time = time.time() - start_time
            self.update_summary_log_with_token_tracking(
                agent=agent,
                log_id=log_id, 
                summary_result=response, 
                token_usage=token_usage, 
                execution_time=execution_time, 
                user_id=user_id,
                conversation_id=conversation_id)

            self.logger.info("轮次总结完成", {"conversation_id": conversation_id, "round_id": round_id, "summary_length": len(response), "log_id": log_id, "execution_time": execution_time, "total_tokens": token_usage.total_tokens})

        except Exception as e:
            # 更新日志为失败
            if log_id:
                execution_time = time.time() - start_time
                self.update_summary_log_failed(agent, log_id, str(e), round(execution_time, 2))

            self.logger.error("轮次总结失败", exception=e, extra_data={"conversation_id": conversation_id, "round_id": round_id, "log_id": log_id})
            raise

    async def summarize_snapshot(self, agent: Agent, conversation_id: str, user_id: str = None):
        """总结指定会话的快照（snapshot）"""
        start_time = time.time()
        log_id = None

        try:
            self.logger.info("开始生成快照总结", {"conversation_id": conversation_id})

            # 获取自上次快照后的所有轮次
            rounds_to_summarize = self.sqlite_storage.get_rounds_since_last_snapshot(conversation_id)

            if not rounds_to_summarize:
                self.logger.warning("没有需要总结的轮次", {"conversation_id": conversation_id})
                return

            if len(rounds_to_summarize) < config.round_summary_times:
                self.logger.warning("轮次数量不足，无需生成快照", {"conversation_id": conversation_id, "current_rounds": len(rounds_to_summarize), "required_rounds": config.round_summary_times})
                return

            # 构建轮次总结内容
            rounds_content = []
            for i, round_data in enumerate(rounds_to_summarize[: config.round_summary_times], 1):
                rounds_content.append(f"轮次{i}：{round_data['summary']}")

            snapshot_input = "\n\n".join(rounds_content)

            # 创建总结日志记录
            log_id = self.create_summary_log_with_token_tracking(
                agent=agent,
                summary_content=f"Snapshot总结 - 基于{len(rounds_to_summarize)}个轮次", 
                conversation_id=conversation_id,
                user_id=user_id)

            # 获取快照总结提示词
            system_prompt = self.function_prompt_assembler.load_snapshot_summary_prompt()
            llm_request_message = await self._make_llm_request_message(system_prompt, snapshot_input)
            llm_response = await self._call_llm(agent, llm_request_message, conversation_id)

            # 调用LLM生成快照总结
            response = llm_response.content
            token_usage = llm_response.token_usage
            # 获取最后处理的轮次ID作为基准
            last_round_id = rounds_to_summarize[config.round_summary_times - 1]["round_id"]

            # 保存快照到数据库
            snapshot_id = self.sqlite_storage.create_snapshot(conversation_id=conversation_id, based_on_round_id=last_round_id, context_summary=response)

            # 更新日志为成功并记录token统计
            execution_time = time.time() - start_time
            self.update_summary_log_with_token_tracking(
                agent=agent,
                log_id=log_id, 
                summary_result=response, 
                token_usage=token_usage, 
                execution_time=execution_time, 
                user_id=user_id,
                conversation_id=conversation_id)

            self.logger.info(
                "快照总结完成", {"conversation_id": conversation_id, "snapshot_id": snapshot_id, "based_on_round_id": last_round_id, "rounds_count": len(rounds_to_summarize), "summary_length": len(response), "log_id": log_id, "execution_time": execution_time, "total_tokens": token_usage.total_tokens}
            )

            # 快照总结不发送WebSocket消息给前端（仅记录日志）

        except Exception as e:
            # 更新日志为失败
            if log_id:
                execution_time = time.time() - start_time
                self.update_summary_log_failed(agent, log_id, str(e), round(execution_time, 2))

            self.logger.error("快照总结失败", exception=e, extra_data={"conversation_id": conversation_id, "log_id": log_id})
            raise

    async def summarize_conversation(self, agent: Agent, conversation_id: str, user_id: str = None):
        """总结指定会话（conversation），基于所有快照"""
        start_time = time.time()
        log_id = None

        try:
            self.logger.info("开始生成对话总结", {"conversation_id": conversation_id})

            # 获取所有快照
            snapshots = self.sqlite_storage.get_all_snapshots(conversation_id)

            if not snapshots:
                self.logger.warning("没有快照，无法生成对话总结", {"conversation_id": conversation_id})
                return

            # 构建快照内容
            snapshots_content = []
            for i, snapshot in enumerate(snapshots, 1):
                snapshots_content.append(f"快照{i}：{snapshot['context_summary']}")

            conversation_input = "\n\n".join(snapshots_content)

            # 创建总结日志记录
            log_id = self.create_summary_log_with_token_tracking(
                agent=agent,
                summary_content=f"Conversation总结 - 基于{len(snapshots)}个快照", 
                conversation_id=conversation_id,
                user_id=user_id)

            # 获取对话总结提示词
            system_prompt = self.function_prompt_assembler.load_conversation_summary_prompt()
            llm_request_message = await self._make_llm_request_message(system_prompt, conversation_input)

            # 调用LLM生成对话总结
            llm_response = await self._call_llm(agent, llm_request_message, conversation_id)
            response = llm_response.content
            token_usage = llm_response.token_usage
            # 更新会话总结到数据库
            self.sqlite_storage.update_conversation_summary(conversation_id, response)

            # 更新日志为成功并记录token统计
            execution_time = time.time() - start_time
            self.update_summary_log_with_token_tracking(
                agent=agent,
                log_id=log_id, 
                summary_result=response, 
                token_usage=token_usage, 
                execution_time=execution_time, 
                user_id=user_id,
                conversation_id=conversation_id)

            self.logger.info("对话总结完成", {"conversation_id": conversation_id, "snapshots_count": len(snapshots), "summary_length": len(response), "log_id": log_id, "execution_time": execution_time, "total_tokens": token_usage.total_tokens})

            # 对话总结不发送WebSocket消息给前端（仅记录日志）

        except Exception as e:
            # 更新日志为失败
            if log_id:
                execution_time = time.time() - start_time
                self.update_summary_log_failed(agent, log_id, str(e), round(execution_time, 2))

            self.logger.error("对话总结失败", exception=e, extra_data={"conversation_id": conversation_id, "log_id": log_id})
            raise

    async def load_summary(self, conversation_id: str) -> str:
        """加载指定会话的summary，返回字符串"""
        pass

    async def _make_summary_message(self, conversation_id: str, round_id: str) -> str:
        """生成summary消息"""
        try:
            messages = self.sqlite_storage.get_messages_recorder(round_id)
            user_message = ""
            tool_map = {}
            tool_message = "使用工具："
            assistant_message = ""
            for message in messages:
                if message.role == "user" and message.type == MessageType.CONTENT:
                    user_message += f"用户输入：{message.content}\n"
                elif message.type == MessageType.TOOL_CALL:
                    tool_map[message.tool_name] = message.content
                elif message.type == MessageType.TOOL_RESULT:
                    tool_map[message.tool_name] = f" 执行结果：{message.tool_success}"
                elif message.role == "assistant" and message.type == MessageType.CONTENT:
                    assistant_message += f"回复内容：{message.content}\n"

            for tool_name, tool_content in tool_map.items():
                tool_message += f"{tool_name}：{tool_content}；"
            round_message = user_message + tool_message + assistant_message
            return round_message
        except Exception as e:
            self.logger.error("生成总结消息失败", exception=e, extra_data={"conversation_id": conversation_id, "round_id": round_id})
            raise

    async def _make_llm_request_message(self, system_message: str, user_message: str) -> str:
        """生成LLM请求消息"""
        llm_request_message: List[Dict[str, str]] = []
        llm_request_message.append({"role": "system", "content": system_message})
        llm_request_message.append({"role": "user", "content": user_message})
        return llm_request_message

    async def _call_llm(self, agent, messages: List[Dict[str, str]], conversation_id: str) -> LLMResponse:
        """调用LLM"""
        llm_client = EnhancedLLMClient.create_from_llm(agent.summary_llm)
        llm_response = await llm_client.block(messages=messages, conversation_id=conversation_id)
        self.logger.info("总结token使用情况", llm_response.token_usage)
        return llm_response