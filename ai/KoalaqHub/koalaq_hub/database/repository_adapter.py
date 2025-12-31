"""
Repository适配器
提供与原SqliteStorage完全兼容的接口，内部委托给新的Repository系统
"""

from typing import Any, Dict, List, Optional

from ..core.llm.enhanced_llm_client import TokenUsage
from ..models.data_models import Conversation, Round, SummaryLog, User
from ..models.message import Message
from .factory.repository_factory import RepositoryFactory


class RepositoryAdapter:
    """Repository适配器 - 完全兼容原SqliteStorage接口"""

    def __init__(self, db_path: str = None):
        """初始化适配器

        Args:
            db_path: 数据库文件路径
        """
        self.factory = RepositoryFactory()
        if db_path:
            # 如果指定了路径，重新创建连接
            from .base.database_connection import DatabaseConnection

            self.factory.db_connection = DatabaseConnection(db_path)

    def close(self):
        """关闭数据库连接"""
        return self.factory.close()

    def _extract_token_values(self, token_usage: TokenUsage) -> tuple:
        """从TokenUsage对象中提取token值
        
        Args:
            token_usage: TokenUsage对象
            
        Returns:
            tuple: (total_tokens, prompt_tokens, completion_tokens, reasoning_tokens)
        """
        return (
            token_usage.total_tokens,
            token_usage.prompt_tokens,
            token_usage.completion_tokens,
            token_usage.reasoning_tokens
        )

    # ==================== 用户相关方法 ====================

    def add_user(self, user: User):
        """添加用户"""
        return self.factory.get_user_repository().add_user(user)

    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户"""
        return self.factory.get_user_repository().get_user(user_id)

    def add_tokens_to_user(self, user_id: str, token_usage: TokenUsage):
        """为用户累加Token
        
        Args:
            user_id: 用户ID
            token_usage: TokenUsage对象
        """
        total_tokens, prompt_tokens, completion_tokens, reasoning_tokens = self._extract_token_values(token_usage)
        return self.factory.get_user_repository().add_tokens_to_user(
            user_id, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens
        )

    def get_all_users(self, limit: int = 100) -> List[User]:
        """获取用户列表"""
        # UserRepository.list_users返回的是Dict列表，需要转换为User对象
        user_dicts = self.factory.get_user_repository().list_users(limit=limit)
        users = []
        for user_dict in user_dicts:
            user = User(
                user_id=user_dict["user_id"],
                username=user_dict["username"],
                created_at=user_dict["created_at"],
                extra_data=None,
                total_tokens=user_dict.get("total_tokens", 0),
                prompt_tokens=user_dict.get("prompt_tokens", 0),
                completion_tokens=user_dict.get("completion_tokens", 0),
                reasoning_tokens=user_dict.get("reasoning_tokens", 0)
            )
            users.append(user)
        return users

    def get_user_count(self) -> int:
        """获取用户总数"""
        return self.factory.get_user_repository().get_user_count()

    # ==================== 对话相关方法 ====================

    def create_conversation(self, user_id: str, conversation_id: str, application_name: str, 
                          is_agent_call: int = 0, parent_conversation_id: str = None):
        """创建对话"""
        return self.factory.get_conversation_repository().create_conversation(
            user_id, conversation_id, application_name, is_agent_call, parent_conversation_id
        )

    def update_coversation_time(self, conversation_id: str):
        """更新对话时间（保持拼写错误）"""
        return self.factory.get_conversation_repository().update_coversation_time(conversation_id)

    def update_conversation_title(self, conversation_id: str, title: str):
        """更新对话标题"""
        return self.factory.get_conversation_repository().update_conversation_title(conversation_id, title)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """软删除对话"""
        return self.factory.get_conversation_repository().delete_conversation(conversation_id)
    
    def restore_conversation(self, conversation_id: str) -> bool:
        """恢复已删除的对话"""
        return self.factory.get_conversation_repository().restore_conversation(conversation_id)
    
    def permanently_delete_conversation(self, conversation_id: str) -> bool:
        """永久删除对话"""
        return self.factory.get_conversation_repository().permanently_delete_conversation(conversation_id)

    def update_coversation_summary(self, conversation_id: str, summary: str):
        """更新对话摘要（保持拼写错误）"""
        return self.factory.get_conversation_repository().update_coversation_summary(conversation_id, summary)

    def update_conversation_summary(self, conversation_id: str, summary: str):
        """更新对话摘要"""
        return self.factory.get_conversation_repository().update_conversation_summary(conversation_id, summary)

    def get_conversation_recorder(self, user_id: str, conversation_id: str) -> Optional[Conversation]:
        """获取对话记录"""
        return self.factory.get_conversation_repository().get_conversation_recorder(user_id, conversation_id)

    def get_all_conversations_recorder(self, user_id: str) -> List[Conversation]:
        """获取所有对话记录"""
        return self.factory.get_conversation_repository().get_all_conversations_recorder(user_id)

    def get_user_conversations_list(self, user_id: str, application_names: List[str] = None, limit: int = 50, offset: int = 0) -> List[Conversation]:
        """获取用户会话列表（用于API返回）

        Args:
            user_id: 用户ID
            application_names: 应用名称列表，用于筛选对话
            limit: 返回记录数限制，默认50
            offset: 偏移量，默认0

        Returns:
            List[Conversation]: 按更新时间倒序排列的对话列表
        """
        return self.factory.get_conversation_repository().get_user_conversations(user_id, application_names, limit, offset)

    def get_user_conversations_count(self, user_id: str, application_names: List[str] = None) -> int:
        """获取用户会话总数

        Args:
            user_id: 用户ID
            application_names: 应用名称列表，用于筛选对话

        Returns:
            int: 用户的会话总数
        """
        return self.factory.get_conversation_repository().get_user_conversations_count(user_id, application_names)

    def add_tokens_to_conversation(self, conversation_id: str, token_usage: TokenUsage):
        """为对话累加Token
        
        Args:
            conversation_id: 对话ID
            token_usage: TokenUsage对象
        """
        total_tokens, prompt_tokens, completion_tokens, reasoning_tokens = self._extract_token_values(token_usage)
        return self.factory.get_conversation_repository().add_tokens_to_conversation(
            conversation_id, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens
        )

    # ==================== 轮次相关方法 ====================

    def create_round(self, conversation_id: str, round_id: str):
        """创建轮次"""
        return self.factory.get_conversation_repository().create_round(conversation_id, round_id)

    def update_round_summary(self, conversation_id: str, round_id: str, summary: str):
        """更新轮次摘要"""
        return self.factory.get_conversation_repository().update_round_summary(round_id, summary)

    def get_round_recorder(self, conversation_id: str, round_id: str) -> Optional[Round]:
        """获取轮次记录"""
        return self.factory.get_conversation_repository().get_round_recorder(conversation_id, round_id)

    def get_rounds_recorder_by_memory_window(self, conversation_id: str, memory_window: int) -> List[Round]:
        """根据内存窗口获取轮次"""
        return self.factory.get_conversation_repository().get_rounds_recorder_by_memory_window(conversation_id, memory_window)

    def get_all_rounds_recorder(self, conversation_id: str) -> List[Round]:
        """获取所有轮次记录"""
        return self.factory.get_conversation_repository().get_all_rounds_recorder(conversation_id)

    def get_rounds_count(self, conversation_id: str) -> int:
        """获取指定会话的轮次数量"""
        return self.factory.get_conversation_repository().get_rounds_count(conversation_id)

    def add_tokens_to_round(self, round_id: str, token_usage: TokenUsage):
        """为轮次累加Token
        
        Args:
            round_id: 轮次ID
            token_usage: TokenUsage对象
        """
        total_tokens, prompt_tokens, completion_tokens, reasoning_tokens = self._extract_token_values(token_usage)
        return self.factory.get_conversation_repository().add_tokens_to_round(
            round_id, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens
        )

    def update_round_execution_time(self, round_id: str, execution_time: float):
        """更新轮次执行时间"""
        return self.factory.get_conversation_repository().update_round_execution_time(round_id, execution_time)

    # ==================== 消息相关方法 ====================

    def add_message(self, round_id: str, message: Message) -> int:
        """添加消息"""
        return self.factory.get_message_repository().add_message(round_id, message)

    def get_messages_recorder(self, round_id: str) -> List[Message]:
        """获取消息记录"""
        return self.factory.get_message_repository().get_messages_recorder(round_id)

    def create_system_message(self, conversation_id: str, message: Message) -> int:
        """创建系统消息"""
        return self.factory.get_message_repository().create_system_message(conversation_id, message)

    def get_system_message(self, conversation_id: str) -> Optional[Message]:
        """获取系统消息"""
        return self.factory.get_message_repository().get_system_message(conversation_id)

    def update_system_message(self, conversation_id: str, message: Message):
        """更新系统消息"""
        return self.factory.get_message_repository().update_system_message(conversation_id, message)

    def add_tokens_to_message(self, message_id: int, token_usage: TokenUsage, platform: str, model: str):
        """为消息添加Token信息
        
        Args:
            message_id: 消息ID
            token_usage: TokenUsage对象
            platform: 平台名称
            model: 模型名称
        """
        total_tokens, prompt_tokens, completion_tokens, reasoning_tokens = self._extract_token_values(token_usage)
        return self.factory.get_message_repository().add_tokens_to_message(
            message_id, total_tokens, platform, model, prompt_tokens, completion_tokens, reasoning_tokens
        )

    def get_conversation_messages_paginated(self, conversation_id: str, before_round_id: str = None, limit: int = 20) -> List[Message]:
        """获取对话消息（按轮次分页）"""
        return self.factory.get_message_repository().get_conversation_messages_paginated(conversation_id, before_round_id, limit)

    def get_user_attachments_by_round(self, round_id: str) -> List[str]:
        """获取轮次中用户消息的附件文件名列表"""
        return self.factory.get_message_repository().get_user_attachments_by_round(round_id)

    # ==================== 总结相关方法 ====================

    def create_summary_log(self, summary_log: SummaryLog) -> int:
        """创建总结日志"""
        return self.factory.get_summary_repository().create_summary_log(summary_log)

    def update_summary_log(self, log_id: int, summary_result: str = None, status: str = None, error_message: str = None, execution_time: float = None) -> bool:
        """更新总结日志"""
        return self.factory.get_summary_repository().update_summary_log(log_id, summary_result, status, error_message, execution_time)

    def get_summary_log(self, log_id: int) -> Optional[SummaryLog]:
        """获取总结日志"""
        return self.factory.get_summary_repository().get_summary_log(log_id)

    def get_summary_logs_by_conversation(self, conversation_id: str, limit: int = 50) -> List[SummaryLog]:
        """根据对话获取总结日志"""
        return self.factory.get_summary_repository().get_summary_logs_by_conversation(conversation_id, limit)

    def get_summary_logs_by_status(self, status: str, limit: int = 100) -> List[SummaryLog]:
        """根据状态获取总结日志"""
        return self.factory.get_summary_repository().get_summary_logs_by_status(status, limit)

    def get_summary_logs_by_llm_config(self, llm_choose: str, limit: int = 100) -> List[SummaryLog]:
        """根据LLM配置获取总结日志"""
        return self.factory.get_summary_repository().get_summary_logs_by_llm_config(llm_choose, limit)

    def delete_summary_log(self, log_id: int) -> bool:
        """删除总结日志"""
        return self.factory.get_summary_repository().delete_summary_log(log_id)

    def add_tokens_to_summary(self, summary_id: int, token_usage: TokenUsage):
        """为总结日志添加Token信息
        
        Args:
            summary_id: 总结日志ID
            token_usage: TokenUsage对象
        """
        total_tokens, prompt_tokens, completion_tokens, reasoning_tokens = self._extract_token_values(token_usage)
        return self.factory.get_summary_repository().add_tokens_to_summary(
            summary_id, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens
        )

    # ==================== 快照相关方法 ====================

    def create_snapshot(self, conversation_id: str, based_on_round_id: str, context_summary: str) -> int:
        """创建快照"""
        return self.factory.get_summary_repository().create_snapshot(conversation_id, based_on_round_id, context_summary)

    def get_latest_snapshot(self, conversation_id: str) -> Optional[Dict]:
        """获取最新快照"""
        return self.factory.get_summary_repository().get_latest_snapshot(conversation_id)

    def get_all_snapshots(self, conversation_id: str) -> List[Dict]:
        """获取所有快照"""
        return self.factory.get_summary_repository().get_all_snapshots(conversation_id)

    def get_recent_snapshots(self, conversation_id: str, limit: int = 2) -> List[Dict]:
        """获取最近快照"""
        return self.factory.get_summary_repository().get_recent_snapshots(conversation_id, limit)

    def get_snapshots_count(self, conversation_id: str) -> int:
        """获取快照数量"""
        return self.factory.get_summary_repository().get_snapshots_count(conversation_id)

    def get_rounds_since_last_snapshot(self, conversation_id: str) -> List[Dict]:
        """获取快照后的轮次"""
        return self.factory.get_summary_repository().get_rounds_since_last_snapshot(conversation_id)

    # ==================== LLM 配置相关方法 ====================

    def create_llm_config(
        self,
        llm_config_name: str,
        platform: str,
        model: str,
        api_key: str = None,
        url: str = None,
        temperature: float = 0.7,
        top_p: float = 1.0,
        max_tokens: int = 4096,
        description: str = "",
    ) -> str:
        """创建 LLM 配置

        Returns:
            str: 生成的 llm_id
        """
        return self.factory.get_llm_repository().create_llm(
            llm_config_name=llm_config_name,
            platform=platform,
            model=model,
            api_key=api_key,
            url=url,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            description=description,
        )

    def create_llm_config_if_not_exists(
        self,
        llm_config_name: str,
        platform: str,
        model: str,
        api_key: str = None,
        url: str = None,
        temperature: float = 0.7,
        top_p: float = 1.0,
        max_tokens: int = 4096,
        description: str = "",
    ) -> str:
        """创建 LLM 配置（如果不存在）

        Returns:
            str: llm_id（新建或已存在的）
        """
        return self.factory.get_llm_repository().create_if_not_exists(
            llm_config_name=llm_config_name,
            platform=platform,
            model=model,
            api_key=api_key,
            url=url,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            description=description,
        )

    def get_llm_config_by_name(self, llm_config_name: str):
        """根据配置名称获取 LLM 配置"""
        return self.factory.get_llm_repository().get_by_config_name(llm_config_name)

    def get_llm_config_by_id(self, llm_id: str):
        """根据 ID 获取 LLM 配置"""
        return self.factory.get_llm_repository().get_by_id(llm_id)

    def list_llm_configs(self):
        """获取所有 LLM 配置列表"""
        return self.factory.get_llm_repository().list_all()

    def update_llm_config(self, llm_id: str, **kwargs) -> bool:
        """更新 LLM 配置"""
        return self.factory.get_llm_repository().update_llm(llm_id, **kwargs)

    def delete_llm_config(self, llm_id: str) -> bool:
        """删除 LLM 配置"""
        return self.factory.get_llm_repository().delete_by_id(llm_id)

    # ==================== Token 统计相关方法 ====================

    def add_tokens_to_model(self, llm_config_name: str, token_usage: TokenUsage):
        """为 LLM 配置累加 Token

        Args:
            llm_config_name: LLM 配置名称
            token_usage: TokenUsage 对象
        """
        total_tokens, prompt_tokens, completion_tokens, reasoning_tokens = self._extract_token_values(token_usage)
        return self.factory.get_token_repository().add_tokens_by_config_name(
            llm_config_name, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens
        )

    def update_model_stats(self, llm_config_name: str, success: bool = True, response_time: float = None):
        """更新模型统计信息"""
        return self.factory.get_token_repository().update_model_stats_by_config_name(
            llm_config_name, success, response_time
        )

    def reset_model_stats(self, llm_config_name: str) -> bool:
        """重置模型统计数据"""
        return self.factory.get_token_repository().reset_stats_by_config_name(llm_config_name)

    def get_model_statistics(self) -> List[Dict]:
        """获取模型统计"""
        return self.factory.get_token_repository().get_model_statistics()

    def get_platform_statistics(self) -> List[Dict]:
        """获取平台统计"""
        return self.factory.get_token_repository().get_platform_statistics()

    def get_user_tool_call_count(self, user_id: str) -> int:
        """获取用户的工具调用总数"""
        return self.factory.get_message_repository().get_user_tool_call_count(user_id)
