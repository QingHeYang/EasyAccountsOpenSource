"""
ConversationManager - 会话管理器
负责会话相关的业务逻辑，包括会话列表、分页、筛选等功能
"""

import uuid
from typing import Any, Dict, List, Optional

from ..database.repository_adapter import RepositoryAdapter
from ..models.data_models import Conversation
from ..models.message import Message, MessageType
from ..api.models.frontend_message import (
    FrontendMessage,
    FrontendMessageRole,
    SubAgentInfo,
    TextContent,
    ToolInfo,
)
from .logging_utils import ManagerLogger
from .tool.mcp.mcp_tool_manager import ToolManager


class ConversationManager:
    """会话管理器 - 负责会话相关的业务逻辑"""

    def __init__(self, storage: RepositoryAdapter):
        """
        初始化会话管理器

        Args:
            storage: 数据库适配器
        """
        self.storage = storage
        self.logger = ManagerLogger("ConversationManager")
        # 初始化工具管理器用于分离AI提示语和工具调用
        self.tool_manager = ToolManager(None, None)

    def get_user_conversations(self, user_id: str, application_names: List[str] = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        获取用户会话列表（分页）

        Args:
            user_id: 用户ID
            application_names: 应用名称列表，用于筛选对话
            page: 页码，从1开始
            page_size: 每页大小，默认20

        Returns:
            包含会话列表和分页信息的字典
        """
        try:
            # 参数验证
            if not user_id:
                raise ValueError("用户ID不能为空")

            if page < 1:
                raise ValueError("页码必须大于0")

            if page_size < 1 or page_size > 100:
                raise ValueError("每页大小必须在1-100之间")

            # 计算偏移量
            offset = (page - 1) * page_size

            # 获取会话列表
            conversations = self.storage.get_user_conversations_list(user_id=user_id, application_names=application_names, limit=page_size, offset=offset)
            self.logger.info(f"conversations: {conversations}")
            # 获取总数
            total_count = self.storage.get_user_conversations_count(user_id, application_names)

            # 计算分页信息
            total_pages = (total_count + page_size - 1) // page_size  # 向上取整
            has_next = page < total_pages
            has_prev = page > 1

            result = {"conversations": [self._conversation_to_dict(conv) for conv in conversations], "pagination": {"current_page": page, "page_size": page_size, "total_count": total_count, "total_pages": total_pages, "has_next": has_next, "has_prev": has_prev}}

            self.logger.info("获取用户会话列表成功", extra_data={"user_id": user_id, "application_names": application_names, "page": page, "page_size": page_size, "total_count": total_count, "returned_count": len(conversations)})
            self.logger.info(f"result: {result}")
            return result

        except Exception as e:
            self.logger.error("获取用户会话列表失败", extra_data={"user_id": user_id, "application_names": application_names, "page": page, "page_size": page_size, "error": str(e)})
            raise e
        finally:
            self.logger.info("获取用户会话列表成功", extra_data={"user_id": user_id, "application_names": application_names, "page": page, "page_size": page_size, "total_count": total_count, "returned_count": len(conversations)})

    def get_conversation_detail(self, user_id: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话详细信息

        Args:
            user_id: 用户ID（用于权限验证）
            conversation_id: 会话ID

        Returns:
            会话详细信息字典，如果不存在则返回None
        """
        try:
            # 获取会话信息
            conversation = self.storage.get_conversation_recorder(user_id, conversation_id)

            if not conversation:
                self.logger.warning("会话不存在或无权限访问", extra_data={"user_id": user_id, "conversation_id": conversation_id})
                return None

            result = self._conversation_to_dict(conversation, include_detail=True)

            self.logger.debug("获取会话详情成功", extra_data={"user_id": user_id, "conversation_id": conversation_id})

            return result

        except Exception as e:
            self.logger.error("获取会话详情失败", extra_data={"user_id": user_id, "conversation_id": conversation_id, "error": str(e)})
            raise e

    def get_conversation_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户会话统计信息

        Args:
            user_id: 用户ID

        Returns:
            统计信息字典
        """
        try:
            # 获取总会话数
            total_conversations = self.storage.get_user_conversations_count(user_id)

            # 获取最近的会话（用于统计最近活动）
            recent_conversations = self.storage.get_user_conversations_list(user_id=user_id, limit=10, offset=0)

            # 计算最后活动时间
            last_activity = None
            if recent_conversations:
                last_activity = recent_conversations[0].updated_at

            # 统计最近7天的会话数（简单实现，实际可能需要更复杂的逻辑）
            recent_count = len([conv for conv in recent_conversations if conv.created_at])

            result = {"total_conversations": total_conversations, "recent_conversations": recent_count, "last_activity": last_activity, "has_conversations": total_conversations > 0}

            self.logger.debug("获取会话统计成功", extra_data={"user_id": user_id, "total_conversations": total_conversations})

            return result

        except Exception as e:
            self.logger.error("获取会话统计失败", extra_data={"user_id": user_id, "error": str(e)})
            raise e

    def search_conversations(self, user_id: str, keyword: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        搜索用户会话（基于标题和摘要）

        Args:
            user_id: 用户ID
            keyword: 搜索关键词
            page: 页码，从1开始
            page_size: 每页大小，默认20

        Returns:
            包含搜索结果和分页信息的字典
        """
        try:
            # 参数验证
            if not user_id:
                raise ValueError("用户ID不能为空")

            if not keyword or len(keyword.strip()) < 2:
                raise ValueError("搜索关键词长度至少为2个字符")

            keyword = keyword.strip()

            # 先获取用户所有会话，然后在内存中过滤
            # 注意：这是简单实现，对于大量数据应该在数据库层面实现搜索
            all_conversations = self.storage.get_user_conversations_list(
                user_id=user_id,
                limit=1000,  # 假设用户不会超过1000个会话
                offset=0,
            )

            # 过滤包含关键词的会话
            filtered_conversations = []
            for conv in all_conversations:
                # 搜索标题和摘要
                if (conv.title and keyword.lower() in conv.title.lower()) or (conv.summary and keyword.lower() in conv.summary.lower()):
                    filtered_conversations.append(conv)

            # 分页处理
            total_count = len(filtered_conversations)
            offset = (page - 1) * page_size
            paged_conversations = filtered_conversations[offset : offset + page_size]

            # 计算分页信息
            total_pages = (total_count + page_size - 1) // page_size
            has_next = page < total_pages
            has_prev = page > 1

            result = {"conversations": [self._conversation_to_dict(conv) for conv in paged_conversations], "pagination": {"current_page": page, "page_size": page_size, "total_count": total_count, "total_pages": total_pages, "has_next": has_next, "has_prev": has_prev}, "search_keyword": keyword}

            self.logger.info("搜索会话成功", extra_data={"user_id": user_id, "keyword": keyword, "total_found": total_count, "returned_count": len(paged_conversations)})

            return result

        except Exception as e:
            self.logger.error("搜索会话失败", extra_data={"user_id": user_id, "keyword": keyword, "error": str(e)})
            raise e

    def _conversation_to_dict(self, conversation: Conversation, include_detail: bool = False) -> Dict[str, Any]:
        """
        将Conversation对象转换为字典

        Args:
            conversation: 会话对象
            include_detail: 是否包含详细信息

        Returns:
            会话字典
        """
        result = {"conversation_id": conversation.conversation_id, 
                  "user_id": conversation.user_id, 
                  "title": conversation.title or "未命名会话", 
                  "summary": conversation.summary, 
                  "created_at": conversation.created_at, 
                  "updated_at": conversation.updated_at, 
                  "application_name": conversation.application_name,
                  "total_tokens": conversation.total_tokens or 0, 
                  "rounds_count": conversation.rounds_count or 0}

        if include_detail:
            # 添加更多详细信息
            result.update(
                {
                    "tags": conversation.tags,
                    # 可以在这里添加轮次数量等其他信息
                }
            )

        return result

    def get_conversation_messages(self, user_id: str, conversation_id: str, before_round_id: str = None, limit: int = 20) -> Dict[str, Any]:
        """
        获取对话消息列表（按轮次分页）

        Args:
            user_id: 用户ID
            conversation_id: 对话ID
            before_round_id: 获取此轮次ID之前的轮次（分页）
            limit: 每页轮次数量，默认20

        Returns:
            Dict包含messages和分页信息
        """
        try:
            # 参数验证
            if not user_id:
                raise ValueError("用户ID不能为空")
            if not conversation_id:
                raise ValueError("对话ID不能为空")
            if limit <= 0 or limit > 100:
                raise ValueError("每页数量必须在1-100之间")

            # 验证用户是否有访问该对话的权限
            conversation = self.storage.get_conversation_recorder(user_id, conversation_id)
            if not conversation:
                raise ValueError("对话不存在或无权限访问")
            rounds_count = self.storage.get_rounds_count(conversation_id)

            # 获取消息数据
            raw_messages = self.storage.get_conversation_messages_paginated(conversation_id=conversation_id, before_round_id=before_round_id, limit=limit)
            # 转换消息格式
            frontend_messages = self._process_messages_for_frontend(raw_messages)
            # 转换为字典列表以便 JSON 序列化
            processed_messages = [msg.model_dump(exclude_none=True) for msg in frontend_messages]

            # 分页信息
            has_more = len(raw_messages) > 0 and len(set(msg.round_id for msg in raw_messages)) == limit
            last_round_id = raw_messages[-1].round_id if raw_messages else None

            result = {
                "messages": processed_messages, 
                "pagination": {"has_more": has_more, "last_round_id": last_round_id, "limit": limit, "before_round_id": before_round_id}, 
                "conversation_id": conversation_id,
                "total_tokens": conversation.total_tokens or 0,
                "updated_at": conversation.updated_at,
                "created_at": conversation.created_at,
                "title": conversation.title or "未命名会话",
                "rounds_count": rounds_count
            }

            self.logger.info("获取对话消息成功", extra_data={"user_id": user_id, "conversation_id": conversation_id, "message_count": len(processed_messages), "raw_count": len(raw_messages)})

            return result

        except Exception as e:
            self.logger.error("获取对话消息失败", extra_data={"user_id": user_id, "conversation_id": conversation_id, "error": str(e)})
            raise e

    def _process_messages_for_frontend(self, raw_messages: List[Message]) -> List[FrontendMessage]:
        """
        将数据库原始消息转换为前端需要的格式
        使用字典索引优化查找性能，并处理 tool_call_id 在不同轮次可能重复的问题
        
        Args:
            raw_messages: 原始消息列表（Message 对象）
            
        Returns:
            处理后的前端消息列表
        """
        import json
        
        fmsg_list = []
        
        # 使用复合键 (round_id, tool_call_id) 作为索引
        tool_call_index = {}  # (round_id, tool_call_id) -> FrontendMessage
        agent_call_index = {}  # (round_id, agent_call_id) -> FrontendMessage
        
        # 第一遍：创建前端消息并建立索引
        for msg in raw_messages:
            # 处理 user 消息
            if msg.role == "user" and msg.type == MessageType.CONTENT:
                fmsg = FrontendMessage(
                    round_id=msg.round_id,
                    message_id=str(msg.message_id),
                    timestamp=msg.timestamp,
                    role=FrontendMessageRole.USER,
                    text=TextContent(content=msg.content, reasoning_content=""),
                    token=msg.total_tokens,
                    model=msg.model
                )
                fmsg_list.append(fmsg)
                
            # 处理 assistant 内容消息
            elif msg.role == "assistant" and msg.type == MessageType.CONTENT:
                fmsg = FrontendMessage(
                    round_id=msg.round_id,
                    message_id=str(msg.message_id),
                    timestamp=msg.timestamp,
                    role=FrontendMessageRole.ASSISTANT,
                    text=TextContent(
                        content=msg.content,
                        reasoning_content=msg.reasoning_content or ""
                    ),
                    token=msg.total_tokens,
                    model=msg.model
                )
                fmsg_list.append(fmsg)
                
            # 处理 tool_call 消息
            elif msg.type == MessageType.TOOL_CALL:
               
                # 解析并创建 tool 消息
                tool_calls = self._parse_tool_calls(msg.tool_call_raw)
                for tool_info in tool_calls:
                    tool_fmsg = FrontendMessage(
                        round_id=msg.round_id,
                        message_id=f"{msg.message_id}_tc_{tool_info.tool_call_id}",
                        timestamp=msg.timestamp,
                        role=FrontendMessageRole.TOOL,
                        tool=tool_info,
                        token=msg.total_tokens,
                        model=msg.model
                    )
                    fmsg_list.append(tool_fmsg)
                    # 使用复合键存储索引
                    tool_call_index[(msg.round_id, tool_info.tool_call_id)] = tool_fmsg
                 # 如果有内容，先创建 assistant 消息
                if msg.content:
                    fmsg = FrontendMessage(
                        round_id=msg.round_id,
                        message_id=f"{msg.message_id}_content",
                        timestamp=msg.timestamp,
                        role=FrontendMessageRole.ASSISTANT,
                        text=TextContent(
                            content=msg.content,
                            reasoning_content=msg.reasoning_content or ""
                        ),
                        token=msg.total_tokens,
                        model=msg.model
                    )
                    fmsg_list.append(fmsg)
                
                    
            # 处理 agent_start 消息
            elif msg.type == MessageType.AGENT_START:
            
                # 解析并创建 agent 消息
                agent_calls = self._parse_agent_calls(msg.tool_call_raw)
                for agent_info in agent_calls:
                    # agent_conversation_id 在 AGENT_END 时才设置
                    agent_info.agent_conversation_id = ""  # 初始为空
                    
                    agent_fmsg = FrontendMessage(
                        round_id=msg.round_id,
                        message_id=f"{msg.message_id}_agent_{agent_info.agent_call_id}",
                        timestamp=msg.timestamp,
                        role=FrontendMessageRole.AGENT,
                        sub_agent=agent_info,
                        token=msg.total_tokens,
                        model=msg.model
                    )
                    fmsg_list.append(agent_fmsg)
                    # 使用复合键存储索引
                    agent_call_index[(msg.round_id, agent_info.agent_call_id)] = agent_fmsg
                # 如果有内容，先创建 assistant 消息
                if msg.content:
                    fmsg = FrontendMessage(
                        round_id=msg.round_id,
                        message_id=f"{msg.message_id}_content",
                        timestamp=msg.timestamp,
                        role=FrontendMessageRole.ASSISTANT,
                        text=TextContent(
                            content=msg.content,
                            reasoning_content=msg.reasoning_content or ""
                        ),
                        token=msg.total_tokens,
                        model=msg.model
                    )
                    fmsg_list.append(fmsg)
        
        # 第二遍：更新 tool_result 和 agent_end
        for msg in raw_messages:
            if msg.type == MessageType.TOOL_RESULT:
                # 使用复合键查找
                key = (msg.round_id, msg.tool_call_id)
                if key in tool_call_index:
                    fmsg = tool_call_index[key]
                    if fmsg.tool:
                        fmsg.tool.tool_result = msg.content
                        fmsg.tool.tool_status = msg.tool_success
                        fmsg.tool.completion_time = msg.timestamp
                        # 计算执行时间
                        fmsg.tool.execution_time = self._calculate_execution_time(
                            fmsg.timestamp,  # 开始时间
                            msg.timestamp    # 结束时间
                        )
                        
            elif msg.type == MessageType.AGENT_END:
                # agent_end 使用 tool_call_id 字段
                key = (msg.round_id, msg.tool_call_id)
                if key in agent_call_index:
                    fmsg = agent_call_index[key]
                    if fmsg.sub_agent:
                        fmsg.sub_agent.agent_output = msg.content
                        fmsg.sub_agent.agent_status = True  # agent_end 表示成功完成
                        fmsg.sub_agent.agent_conversation_id = msg.sub_conversation_id or ""  # 设置子会话 ID
                        fmsg.sub_agent.completion_time = msg.timestamp
                        # 计算执行时间
                        fmsg.sub_agent.execution_time = self._calculate_execution_time(
                            fmsg.timestamp,  # 开始时间
                            msg.timestamp    # 结束时间
                        )
        
        return fmsg_list
    
    def _parse_tool_calls(self, tool_call_raw: str) -> List[ToolInfo]:
        """解析 tool_call_raw 字符串，返回 ToolInfo 列表"""
        tool_list = []
        
        if not tool_call_raw:
            return tool_list
            
        try:
            import json
            tool_calls = json.loads(tool_call_raw)
            
            for tool_call in tool_calls:
                tool_info = ToolInfo(
                    tool_name=tool_call["function"]["name"],
                    tool_arguments=tool_call["function"]["arguments"],
                    tool_call_id=tool_call["id"],
                    tool_result="",  # 稍后填充
                    tool_status=False  # 稍后更新
                )
                tool_list.append(tool_info)
                
        except Exception as e:
            self.logger.warning(f"解析 tool_call_raw 失败: {e}, raw: {tool_call_raw}")
            
        return tool_list
    
    def _parse_agent_calls(self, tool_call_raw: str) -> List[SubAgentInfo]:
        """解析 agent 调用（从 tool_call_raw 中提取 call_agent 调用）"""
        agent_list = []
        
        if not tool_call_raw:
            return agent_list
            
        try:
            import json
            tool_calls = json.loads(tool_call_raw)
            
            for tool_call in tool_calls:
                # 只处理 call_agent 函数调用
                if tool_call["function"]["name"] == "call_agent":
                    # 解析 arguments 字符串
                    args = json.loads(tool_call["function"]["arguments"])
                    
                    agent_info = SubAgentInfo(
                        agent_conversation_id="",  # 稍后从 msg.sub_conversation_id 设置
                        agent_id=args.get("agent_id", ""),
                        agent_call_id=tool_call["id"],
                        agent_input=args.get("task", ""),
                        agent_output="",  # 稍后填充
                        agent_status=False  # 稍后更新
                    )
                    agent_list.append(agent_info)
                    
        except Exception as e:
            self.logger.warning(f"解析 agent calls 失败: {e}, raw: {tool_call_raw}")
            
        return agent_list
    
    def _calculate_execution_time(self, start_time: str, end_time: str) -> float:
        """
        计算执行时间（秒）
        
        Args:
            start_time: 开始时间戳，格式：YYYY-MM-DD HH:MM:SS
            end_time: 结束时间戳，格式：YYYY-MM-DD HH:MM:SS
            
        Returns:
            执行时长（秒）
        """
        try:
            from datetime import datetime
            
            # 解析时间字符串
            fmt = "%Y-%m-%d %H:%M:%S"
            start_dt = datetime.strptime(start_time, fmt)
            end_dt = datetime.strptime(end_time, fmt)
            
            # 计算时间差
            duration = end_dt - start_dt
            
            # 返回秒数（包含小数部分）
            return duration.total_seconds()
            
        except Exception as e:
            self.logger.warning(f"计算执行时间失败: {e}, start={start_time}, end={end_time}")
            return 0.0

    def apply_conversation_id(self) -> str:
        """
        申请新的对话ID
        """
        return f"conv_{str(uuid.uuid4())}"

    def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """
        软删除用户对话

        Args:
            user_id: 用户ID（用于权限验证）
            conversation_id: 对话ID

        Returns:
            bool: 删除是否成功
        """
        try:
            # 先验证用户是否有权限操作该对话
            conversation = self.storage.get_conversation_recorder(user_id, conversation_id)
            if not conversation:
                self.logger.warning("对话不存在或无权限删除", extra_data={"user_id": user_id, "conversation_id": conversation_id})
                return False

            # 执行软删除
            success = self.storage.delete_conversation(conversation_id)
            
            if success:
                self.logger.info("对话删除成功", extra_data={"user_id": user_id, "conversation_id": conversation_id})
            else:
                self.logger.warning("对话删除失败", extra_data={"user_id": user_id, "conversation_id": conversation_id})
            
            return success

        except Exception as e:
            self.logger.error("删除对话失败", extra_data={"user_id": user_id, "conversation_id": conversation_id, "error": str(e)})
            raise e

    def update_conversation_title(self, user_id: str, conversation_id: str, title: str) -> bool:
        """
        更新对话标题

        Args:
            user_id: 用户ID（用于权限验证）
            conversation_id: 对话ID
            title: 新标题

        Returns:
            bool: 更新是否成功
        """
        try:
            # 参数验证
            if not title or len(title.strip()) == 0:
                raise ValueError("标题不能为空")
            
            if len(title.strip()) > 200:
                raise ValueError("标题长度不能超过200个字符")

            title = title.strip()

            # 验证用户是否有权限操作该对话
            conversation = self.storage.get_conversation_recorder(user_id, conversation_id)
            if not conversation:
                self.logger.warning("对话不存在或无权限修改", extra_data={"user_id": user_id, "conversation_id": conversation_id})
                return False

            # 更新标题
            self.storage.update_conversation_title(conversation_id, title)
            
            self.logger.info("对话标题更新成功", extra_data={"user_id": user_id, "conversation_id": conversation_id, "title": title})
            return True

        except Exception as e:
            self.logger.error("更新对话标题失败", extra_data={"user_id": user_id, "conversation_id": conversation_id, "title": title, "error": str(e)})
            raise e