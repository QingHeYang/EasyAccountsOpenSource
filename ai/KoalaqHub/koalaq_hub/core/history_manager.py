import uuid
from typing import Any, Dict, List, Optional

from ..config.settings import config
from ..database.repository_adapter import RepositoryAdapter
from ..models.agent import Agent
from ..models.message import Attachment, Message, MessageType
from .auto_question_manager import AutoQuestionManager
from .llm.enhanced_llm_client import TokenUsage
from .logging_utils import ManagerLogger
from .summary_manager import SummaryManager
from .token_manager import TokenManager
from .tool.mcp.mcp_tool_manager import ToolManager
from .websocket_handler import WebSocketHandler


class HistoryManager:
    def __init__(self, sqlite_storage: RepositoryAdapter, summary_manager: SummaryManager, auto_question_manager: AutoQuestionManager, tool_manager: ToolManager):
        # 多用户模式：{user_id: {conversation_id: {...}}}
        self.histories: Dict[str, Dict[str, Dict]] = {}
        self.sqlite_storage = sqlite_storage
        self.summary_manager = summary_manager
        self.auto_question_manager = auto_question_manager
        self.tool_manager = tool_manager
        # 设置summary_manager的history_manager引用
        self.summary_manager.set_history_manager(self)
        # 设置auto_question_manager的history_manager引用
        self.auto_question_manager.set_history_manager(self)
        # 初始化TokenManager
        self.token_manager = TokenManager(sqlite_storage)
        # 初始化日志记录器
        self.logger = ManagerLogger("HistoryManager")

    def load_history(self, agent: Agent, user_id: str, conversation_id: str):
        """加载历史记录（system message 不再存储于内存，每次get_history动态获取）"""
        is_first_load = False
        try:
            if user_id not in self.histories:
                self.histories[user_id] = {}
            if conversation_id not in self.histories[user_id]:
                self.histories[user_id][conversation_id] = {"rounds": {}}
            if not self.sqlite_storage.get_conversation_recorder(user_id, conversation_id):
                # 检查是否是agent子对话（通过conversation_id格式判断）
                is_agent_call = 1 if "_sub_" in conversation_id else 0
                parent_conversation_id = None
                if is_agent_call:
                    # 从conversation_id中提取父对话ID
                    parent_conversation_id = conversation_id.split("_sub_")[0]
                
                self.sqlite_storage.create_conversation(
                    user_id, conversation_id, agent.agent_id, 
                    is_agent_call, parent_conversation_id
                )
                is_first_load = True
                # 不再存储system消息
            else:
                memory_window = agent.llm_memory_window
                rounds = self.sqlite_storage.get_rounds_recorder_by_memory_window(conversation_id, memory_window)
                self.histories[user_id][conversation_id]["rounds"] = {}
                for round in rounds:
                    round_id = round.round_id
                    self.histories[user_id][conversation_id]["rounds"][round_id] = []
                    messages = self.sqlite_storage.get_messages_recorder(round_id)
                    for message in messages:
                        if message.type != MessageType.ERROR:
                            self.histories[user_id][conversation_id]["rounds"][round_id].append(message)
            return is_first_load
        except Exception as e:
            self.logger.error("加载历史记录失败", exception=e, extra_data={"user_id": user_id, "conversation_id": conversation_id})
            return False

    def load_round(self,agent: Agent, user_id: str, conversation_id: str, round_id: str) -> str:
        """加载轮次，如果轮次不存在，则新建轮次，返回轮次id"""
        if user_id not in self.histories or conversation_id not in self.histories[user_id]:  # 如果会话不存在，返回空值
            return None
        if round_id not in self.histories[user_id][conversation_id]["rounds"]:
            return self._start_new_round(agent, user_id, conversation_id)
        return round_id


    def _start_new_round(self,agent: Agent, user_id: str, conversation_id: str) -> str:
        """新建轮次"""
        round_id = str(uuid.uuid4())
        # 先检查是否需要滚动移除旧的对话记录
        self._roll_memory_window(agent, user_id, conversation_id)
        # 然后添加新轮次到内存缓存
        self.histories[user_id][conversation_id]["rounds"][round_id] = []
        # 创建轮次（会自动记录created_at时间）
        self.sqlite_storage.create_round(conversation_id, round_id)
        return round_id

    async def on_round_end(self, agent: Agent, conversation_id: str, round_id: str, websocket_handler: WebSocketHandler):
        """轮次结束处理 - 严格按顺序执行"""

        if not agent.enable_summary:
            self.logger.info("轮次结束处理完成，summary未开启", {"conversation_id": conversation_id, "round_id": round_id})
            return
        try:
            self.logger.info("开始轮次结束处理", {"conversation_id": conversation_id, "round_id": round_id})

            # 获取用户ID用于token统计
            conversation = self.sqlite_storage.get_conversation_recorder(None, conversation_id)
            user_id = conversation.user_id if conversation else None

            # 计算轮次执行时间（基于round的created_at字段）
            round_record = self.sqlite_storage.get_round_recorder(conversation_id, round_id)
            if round_record and round_record.created_at:
                try:
                    from datetime import datetime

                    created_time = datetime.fromisoformat(round_record.created_at)
                    current_time = datetime.now()
                    execution_time = (current_time - created_time).total_seconds()
                    self.sqlite_storage.update_round_execution_time(round_id, execution_time)
                    self.logger.info("轮次执行时间记录", {"conversation_id": conversation_id, "round_id": round_id, "execution_time": round(execution_time, 2)})
                except Exception as e:
                    self.logger.warning("计算轮次执行时间失败", exception=e, extra_data={"conversation_id": conversation_id, "round_id": round_id})

            # 1. 标题生成（如果没有标题，则生成）
            if not self.sqlite_storage.get_conversation_recorder(user_id, conversation_id).title:
                await self.summary_manager.generate_conversation_title(agent, conversation_id, round_id, user_id)


            if agent.enable_auto_question:
                # 设置websocket_handler
                self.auto_question_manager.set_websocket_handler(websocket_handler)
                
                # 使用asyncio.create_task创建并行任务，不等待完成
                import asyncio
                asyncio.create_task(
                    self.auto_question_manager.generate_auto_question(
                        agent=agent,
                        conversation_id=conversation_id,
                        round_id=round_id,
                        user_id=user_id
                    )
                )
                self.logger.info("已启动自动问题生成任务", {
                    "conversation_id": conversation_id, 
                    "round_id": round_id
                })

            # 2. Round总结 - 必须完成后才能继续
            await self.summary_manager.summarize_round(agent, conversation_id, round_id, user_id)
            self.logger.info("Round总结完成", {"conversation_id": conversation_id, "round_id": round_id})

            # 3. 检查是否需要Snapshot总结（等待round总结完成后才检查）
            rounds = self.sqlite_storage.get_all_rounds_recorder(conversation_id)
            rounds_count = len(rounds)
            if rounds_count % config.round_summary_times == 0:
                self.logger.info("达到快照总结条件，开始生成快照", {"conversation_id": conversation_id, "round_count": rounds_count})

                # 4. Snapshot总结 - 必须完成后才能继续
                await self.summary_manager.summarize_snapshot(agent, conversation_id, user_id)
                self.logger.info("快照总结完成", {"conversation_id": conversation_id})

                # 5. 检查是否需要Conversation总结
                snapshots_count = self.sqlite_storage.get_snapshots_count(conversation_id)
                if snapshots_count % config.conversation_summary_snapshots == 0:
                    self.logger.info("达到对话总结条件，开始生成对话总结", {"conversation_id": conversation_id, "snapshots_count": snapshots_count})

                    # 6. Conversation总结 - 基于最新的snapshots
                    await self.summary_manager.summarize_conversation(agent, conversation_id, user_id)
                    self.logger.info("对话总结完成", {"conversation_id": conversation_id})

            # 7. 自动问题生成 - 并行执行，不阻塞主流程


            self.logger.info("轮次结束处理完成", {"conversation_id": conversation_id, "round_id": round_id})

        except Exception as e:
            self.logger.error("轮次结束处理失败", exception=e, extra_data={"conversation_id": conversation_id, "round_id": round_id})
            raise

    def add_user_message(self, agent: Agent, user_id: str,
                        conversation_id: str, round_id: str, content: str,
                        attachments: Optional[List[Attachment]] = None):
        """添加用户消息

        Args:
            agent: Agent实例
            user_id: 用户ID
            conversation_id: 会话ID
            round_id: 轮次ID
            content: 消息内容
            attachments: VL 附件列表（Attachment 对象）
        """
        try:
            if user_id not in self.histories or conversation_id not in self.histories[user_id]:
                raise ValueError(f"用户或会话不存在: {user_id}, {conversation_id}")
            if round_id not in self.histories[user_id][conversation_id]["rounds"]:
                raise ValueError(f"轮次ID不存在: {round_id}")

            # 创建消息
            message = Message.create_user_message(content, round_id, attachments=attachments)
            self.histories[user_id][conversation_id]["rounds"][round_id].append(message)
            self.sqlite_storage.add_message(round_id, message)

            # VL 日志
            if attachments:
                self.logger.info("用户消息包含附件", {
                    "conversation_id": conversation_id,
                    "round_id": round_id,
                    "attachments_count": len(attachments),
                    "filenames": [att.filename for att in attachments]
                })

        except Exception as e:
            self.logger.error("添加用户消息失败", exception=e, extra_data={
                "user_id": user_id, 
                "conversation_id": conversation_id, 
                "round_id": round_id
            })
            raise
    
    def add_assistant_message(self, agent: Agent, user_id: str,
                             conversation_id: str, round_id: str,
                             content: str, tool_calls: Optional[List[Dict[str, Any]]] = None,
                             token_usage: TokenUsage = None,
                             reasoning_content: str = "",
                             is_agent: bool = False,
                             agent_id: Optional[str] = None):
        """添加助手消息
        
        Args:
            agent: Agent实例
            user_id: 用户ID
            conversation_id: 会话ID
            round_id: 轮次ID
            content: 消息内容
            tool_calls: 工具调用列表（可选）
            token_usage: Token使用情况
            reasoning_content: 思维链内容
            is_agent: 是否是 Agent 开始消息
            agent_id: Agent ID（当 is_agent 为 True 时使用）
        """
        try:
            if user_id not in self.histories or conversation_id not in self.histories[user_id]:
                raise ValueError(f"用户或会话不存在: {user_id}, {conversation_id}")
            if round_id not in self.histories[user_id][conversation_id]["rounds"]:
                raise ValueError(f"轮次ID不存在: {round_id}")

            # 内存与数据库版本均带 reasoning_content：
            # DeepSeek-R1 等思考模型在 thinking 模式下，要求历史中所有 assistant 消息的
            # reasoning_content 原样回传，否则 API 返回 400
            # ("The `reasoning_content` in the thinking mode must be passed back to the API.")
            # 其他平台（OpenAI/智谱等）会忽略未知字段，统一带回最稳妥
            message = Message.create_assistant_message(content, round_id, tool_calls,
                                                     reasoning_content=reasoning_content,
                                                     is_agent=is_agent, agent_id=agent_id)
            self.histories[user_id][conversation_id]["rounds"][round_id].append(message)

            db_message = Message.create_assistant_message(content, round_id, tool_calls, reasoning_content,
                                                        is_agent=is_agent, agent_id=agent_id)
            message_id = self.sqlite_storage.add_message(round_id, db_message)

            # Token统计
            if token_usage and token_usage.total_tokens > 0:
                self.token_manager.add_tokens(
                    token_usage=token_usage,
                    llm=agent.get_llm_for_mode(),
                    operation_type="chat",
                    conversation_id=conversation_id,
                    round_id=round_id,
                    message_id=message_id,
                    user_id=user_id)

        except Exception as e:
            self.logger.error("添加助手消息失败", exception=e, extra_data={
                "user_id": user_id,
                "conversation_id": conversation_id,
                "round_id": round_id,
                "has_tool_calls": bool(tool_calls)
            })
            raise


    def add_error_message(self, user_id: str, conversation_id: str, round_id: str, error_message: str):
        """添加错误消息"""
        try:
            if user_id not in self.histories or conversation_id not in self.histories[user_id]:
                raise ValueError(f"用户或会话不存在: {user_id}, {conversation_id}")
            if round_id not in self.histories[user_id][conversation_id]["rounds"]:
                raise ValueError(f"轮次ID不存在: {round_id}")
            message = Message.create_error_message(error_message, round_id)
            self.sqlite_storage.add_message(round_id, message)
        except Exception as e:
            self.logger.error("添加错误消息失败", exception=e, extra_data={"user_id": user_id, "conversation_id": conversation_id, "round_id": round_id})
            raise
    
    
    def add_tool_result_message(self, agent: Agent, user_id: str,
                               conversation_id: str, round_id: str,
                               tool_call_id: str, result: str, success: bool = True,
                               tool_name: Optional[str] = None):
        """添加工具结果消息
        
        Args:
            agent: Agent实例
            user_id: 用户ID
            conversation_id: 会话ID
            round_id: 轮次ID
            tool_call_id: 工具调用ID
            result: 执行结果
            success: 执行是否成功
            tool_name: 工具名称
        """
        try:
            if user_id not in self.histories or conversation_id not in self.histories[user_id]:
                raise ValueError(f"用户或会话不存在: {user_id}, {conversation_id}")
            if round_id not in self.histories[user_id][conversation_id]["rounds"]:
                raise ValueError(f"轮次ID不存在: {round_id}")
                
            message = Message.create_tool_message(tool_call_id, result, round_id, success, tool_name)
            self.histories[user_id][conversation_id]["rounds"][round_id].append(message)
            self.sqlite_storage.add_message(round_id, message)
            
        except Exception as e:
            self.logger.error("添加工具结果消息失败", exception=e, extra_data={
                "user_id": user_id,
                "conversation_id": conversation_id,
                "round_id": round_id,
                "tool_call_id": tool_call_id,
                "success": success
            })
            raise
    
    def add_sub_agent_message(self, agent: Agent, user_id: str,
                             conversation_id: str, round_id: str,
                             content: str, agent_id: str,
                             tool_call_id: Optional[str] = None,
                             sub_conversation_id: Optional[str] = None):
        """添加子 Agent 消息
        
        Args:
            agent: Agent实例
            user_id: 用户ID
            conversation_id: 会话ID
            round_id: 轮次ID
            content: 消息内容
            agent_id: 子 Agent 的 ID
            tool_call_id: 工具调用ID（当通过 Function Calling 调用时）
            sub_conversation_id: 子会话 ID
        """
        try:
            if user_id not in self.histories or conversation_id not in self.histories[user_id]:
                raise ValueError(f"用户或会话不存在: {user_id}, {conversation_id}")
            if round_id not in self.histories[user_id][conversation_id]["rounds"]:
                raise ValueError(f"轮次ID不存在: {round_id}")
            
            # 创建子 Agent 消息（传递 tool_call_id）
            message = Message.create_sub_agent_message(content, round_id, agent_id, sub_conversation_id, tool_call_id)
            self.histories[user_id][conversation_id]["rounds"][round_id].append(message)
            self.sqlite_storage.add_message(round_id, message)
            
        except Exception as e:
            self.logger.error("添加子 Agent 消息失败", exception=e, extra_data={
                "user_id": user_id,
                "conversation_id": conversation_id,
                "round_id": round_id,
                "agent_id": agent_id
            })
            raise

    def _roll_memory_window(self, agent: Agent, user_id: str, conversation_id: str):
        """滚动移除旧的对话记录"""
        if user_id not in self.histories or conversation_id not in self.histories[user_id]:
            return
        rounds = self.histories[user_id][conversation_id]["rounds"]
        if len(rounds) <= agent.llm_memory_window:
            return
        sorted_rounds = sorted(rounds.items(), key=lambda x: x[1][0].timestamp if x[1] else "0")
        keep_rounds = dict(sorted_rounds[-agent.llm_memory_window :])
        self.histories[user_id][conversation_id]["rounds"] = keep_rounds

    def get_history(self, agent: Agent, user_id: str, conversation_id: str) -> List[Dict[str, Any]]:
        """获取历史记录，根据 tool_mode 返回不同格式
        
        Returns:
            - MCP 模式：保持现有格式（工具调用作为 assistant/user 角色）
            - Function Calling 模式：标准格式（包含 tool_calls 和 tool 角色）
        """
        if user_id not in self.histories or conversation_id not in self.histories[user_id]:
            return []
            
        result: List[Dict[str, Any]] = []
        
        # 添加 system message
        system_message = agent.system_prompt
        result.append({"role": "system", "content": system_message})
        
        # 获取所有轮次并按时间排序
        all_rounds = self.histories[user_id][conversation_id].get("rounds", {})
        sorted_round_items = sorted(all_rounds.items(), key=lambda item: item[1][0].timestamp if item[1] else "")
        

        # Function Calling 格式
        total_msg_count = 0
        
        # 遍历所有轮次，同时进行数据校验
        for round_id, messages in sorted_round_items:
            round_tool_calls = {}  # 当前轮次的待匹配 tool_calls
            
            for idx, msg in enumerate(messages):
                total_msg_count += 1
                
                if msg.type == MessageType.TOOL_CALL or msg.type == MessageType.AGENT_START:
                    # assistant 消息包含 tool_calls

                    # 数据校验1：如果没有 tool_calls 且 content 为空，添加中断提示
                    content = msg.content
                    if not msg.tool_calls and not content:
                        content = "[思考被中断...]"
                        self.logger.warning(f"[{round_id}][{idx}] assistant 消息内容为空，可能是思维链被中断")

                    message_dict = {
                        "role": "assistant",
                        "content": content
                    }
                    # DeepSeek-R1 等思考模型要求把历史 assistant 的 reasoning_content 一起送回
                    if msg.reasoning_content:
                        message_dict["reasoning_content"] = msg.reasoning_content

                    if msg.tool_calls:
                        # 兜底清洗历史中的残缺 tool_call：
                        #   - 缺 function.name → 丢弃（无法执行也无法配对）
                        #   - 缺 function.arguments → 补 "{}"（OpenAI/智谱协议 required）
                        # 不清洗会让 LLM API 在请求体校验阶段直接 400。
                        # 来源：旧版本未做生产侧过滤时已落库的污染数据。
                        cleaned_tool_calls = []
                        for tc in msg.tool_calls:
                            fn = (tc.get("function") or {}) if isinstance(tc, dict) else {}
                            if not fn.get("name"):
                                self.logger.warning(f"[{round_id}][{idx}] 丢弃历史中无 name 的 tool_call", {
                                    "tool_call_id": tc.get("id") if isinstance(tc, dict) else None,
                                })
                                continue
                            if "arguments" not in fn or fn["arguments"] is None:
                                fn = dict(fn)
                                fn["arguments"] = "{}"
                            cleaned_tc = dict(tc)
                            cleaned_tc["function"] = fn
                            cleaned_tool_calls.append(cleaned_tc)

                        if cleaned_tool_calls:
                            message_dict["tool_calls"] = cleaned_tool_calls
                            # 记录待匹配的 tool_calls（只注册清洗后保留下来的）
                            for tc in cleaned_tool_calls:
                                if tc.get("id"):
                                    round_tool_calls[tc["id"]] = tc.get("function", {}).get("name", "unknown")

                            self.logger.debug(f"[{round_id}][{idx}] {msg.type.value} with tools", {
                                "tool_count": len(cleaned_tool_calls),
                                "tool_ids": [tc.get("id") for tc in cleaned_tool_calls],
                                "dropped": len(msg.tool_calls) - len(cleaned_tool_calls),
                            })

                    result.append(message_dict)
                    
                elif msg.type == MessageType.TOOL_RESULT:
                    # tool 角色的结果消息
                    tool_id = msg.tool_call_ids
                    if tool_id in round_tool_calls:
                        del round_tool_calls[tool_id]  # 找到匹配，移除
                    
                    result.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "name": msg.tool_name,
                        "content": msg.content
                    })
                    self.logger.debug(f"[{round_id}][{idx}] TOOL_RESULT", {
                        "tool_call_id": tool_id,
                        "tool_name": msg.tool_name
                    })
                    
                elif msg.type == MessageType.AGENT_END:
                    # 子 Agent 消息（作为 tool 响应）
                    tool_id = msg.tool_call_ids
                    if tool_id in round_tool_calls:
                        del round_tool_calls[tool_id]  # 找到匹配，移除
                    
                    result.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "name": "call_agent",  # 使用 call_agent 作为工具名
                        "content": msg.content
                    })
                    self.logger.debug(f"[{round_id}][{idx}] AGENT_END as tool", {
                        "tool_call_id": tool_id,
                        "agent_id": msg.agent_id,
                        "has_content": bool(msg.content)
                    })
                    
                elif msg.type == MessageType.TOOL_CALL and msg.role == "assistant" and not msg.tool_calls:
                    # 旧的 MCP 格式（没有 tool_calls 的情况）
                    if msg.content:  # 确保有内容
                        result.append({"role": "assistant", "content": msg.content})
                    
                else:
                    # 普通消息
                    # 数据校验2：处理空的 assistant 消息
                    content = msg.content
                    if msg.role == "assistant" and not content:
                        content = "[思考被中断...]"
                        self.logger.warning(f"[{round_id}][{idx}] 普通 assistant 消息内容为空，可能被中断")

                    # 对于用户消息，使用 to_llm_content() 处理 VL 附件
                    if msg.role == "user":
                        llm_content = msg.to_llm_content()
                        result.append({"role": msg.role, "content": llm_content})
                        # VL 日志：记录附件转换
                        if msg.attachments:
                            self.logger.info(f"[{round_id}][{idx}] VL 附件转换为 LLM 格式", {
                                "attachments_count": len(msg.attachments),
                                "filenames": [att.filename for att in msg.attachments],
                                "content_parts": len(llm_content) if isinstance(llm_content, list) else 1
                            })
                    else:
                        plain_msg = {"role": msg.role, "content": content}
                        # assistant 消息带回 reasoning_content（DeepSeek-R1 thinking mode 协议要求）
                        if msg.role == "assistant" and msg.reasoning_content:
                            plain_msg["reasoning_content"] = msg.reasoning_content
                        result.append(plain_msg)
                    self.logger.debug(f"[{round_id}][{idx}] {msg.type.value}", {
                        "role": msg.role
                    })
            
            # 轮次结束，检查未匹配的 tool_calls
            if round_tool_calls:
                self.logger.warning(f"[{round_id}] 轮次结束，发现未匹配的 tool_calls", {
                    "count": len(round_tool_calls),
                    "tool_ids": list(round_tool_calls.keys())
                })
                # 为未匹配的 tool_calls 添加虚拟响应
                for tool_id, tool_name in round_tool_calls.items():
                    result.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "name": tool_name,
                        "content": "[执行被中断]"
                    })
                    self.logger.info(f"[{round_id}] 添加中断的 tool 响应", {
                        "tool_call_id": tool_id,
                        "tool_name": tool_name
                    })
        
        self.logger.info("构建对话历史完成", {
            "conversation_id": conversation_id,
            "total_messages": total_msg_count,
            "result_messages": len(result)
        })
        
                        
        return result

    def get_all_rounds(self, user_id: str, conversation_id: str) -> List[str]:
        """获取所有轮次"""
        if user_id not in self.histories or conversation_id not in self.histories[user_id]:
            return []
        return list(self.histories[user_id][conversation_id]["rounds"].keys())

    def clear_history(self, user_id: str, conversation_id: str):
        """清空历史记录"""
        if user_id not in self.histories:
            self.histories[user_id] = {}
        self.histories[user_id][conversation_id] = {"system": None, "rounds": {}}
        # 清空存储
        if self.storages:
            for storage in self.storages:
                storage.clear_conversation(conversation_id)

    def get_current_round_id(self, user_id: str, conversation_id: str) -> Optional[str]:
        """获取当前会话最新的轮次id（如果有）"""
        if user_id not in self.histories or conversation_id not in self.histories[user_id]:
            return None
        rounds = self.histories[user_id][conversation_id]["rounds"]
        if not rounds:
            return None
        # 返回最后一个轮次id
        return list(rounds.keys())[-1]

    def clear_memory_cache(self, user_id: str, conversation_id: str):
        """清除指定会话的内存缓存

        只清除内存中的对话记录（rounds），保留 system 消息。
        此操作不会影响持久化存储的数据。

        Args:
            conversation_id: 会话ID
        """
        if user_id not in self.histories or conversation_id not in self.histories[user_id]:
            return

        # 保留 system 消息，清空所有对话轮次
        system_msg = self.histories[user_id][conversation_id].get("system")
        self.histories[user_id][conversation_id] = {"system": system_msg, "rounds": {}}
