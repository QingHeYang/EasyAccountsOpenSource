"""
Token统计管理器
负责统计和管理各个模型的token使用量，支持新的TokenUsage数据结构
"""

from typing import Optional

from ..database.repository_adapter import RepositoryAdapter
from ..models.llm import LLM
from .llm.enhanced_llm_client import TokenUsage
from .logging_utils import ManagerLogger


class TokenManager:
    """Token统计管理器 - 支持TokenUsage数据结构和现代化配置"""

    def __init__(self, repository_adapter: RepositoryAdapter):
        """
        初始化Token管理器
        
        Args:
            repository_adapter: 数据库适配器
        """
        self.repository_adapter = repository_adapter
        self.logger = ManagerLogger("TokenManager")

    def add_tokens_to_model(self, token_usage: TokenUsage, llm: Optional[LLM] = None, operation_type: str = "chat"):
        """记录token使用量到模型统计

        Args:
            token_usage: TokenUsage对象，包含详细的token统计
            llm: LLM实例（动态传入）
            operation_type: 操作类型 ("chat", "summary")
        """
        try:
            # 获取 LLM 配置信息
            if llm:
                llm_config_name = llm.llm_config_name
                platform = llm.platform
                model = llm.model
            else:
                llm_config_name = "unknown"
                platform = "unknown"
                model = "unknown"
                self.logger.warning("LLM实例为空，使用默认值")

            # 累加到模型统计（使用 llm_config_name 作为索引）
            self.repository_adapter.add_tokens_to_model(llm_config_name, token_usage)

            self.logger.info(
                "累加token统计成功",
                {
                    "llm_config_name": llm_config_name,
                    "platform": platform,
                    "model": model,
                    "total_tokens": token_usage.total_tokens,
                    "prompt_tokens": token_usage.prompt_tokens,
                    "completion_tokens": token_usage.completion_tokens,
                    "reasoning_tokens": token_usage.reasoning_tokens,
                    "operation_type": operation_type
                }
            )
            return platform, model
            
        except Exception as e:
            self.logger.error(
                "累加token统计失败", 
                exception=e, 
                extra_data={
                    "token_usage": {
                        "total_tokens": token_usage.total_tokens,
                        "prompt_tokens": token_usage.prompt_tokens,
                        "completion_tokens": token_usage.completion_tokens,
                        "reasoning_tokens": token_usage.reasoning_tokens
                    }, 
                    "operation_type": operation_type
                }
            )
            raise

    def add_tokens(self, token_usage: TokenUsage, 
                    llm: Optional[LLM] = None,
                    operation_type: str = "chat",
                    user_id: str = None, 
                    conversation_id: str = None, 
                    round_id: str = None,
                    message_id: int = None,
                    summary_id: int = None):
        """将token添加到完整的层级结构中
        
        Args:
            token_usage: TokenUsage对象
            user_id: 用户ID
            conversation_id: 会话ID (可选)
            round_id: 轮次ID (可选)
            llm: LLM实例（动态传入）
            operation_type: 操作类型 ("chat", "summary")
        """
        try:
            # 累加到模型统计
            platform, model = self.add_tokens_to_model(token_usage, llm, operation_type)
            
            # 累加到用户
            self.repository_adapter.add_tokens_to_user(user_id, token_usage)
            
            # 累加到会话
            if conversation_id:
                self.repository_adapter.add_tokens_to_conversation(conversation_id, token_usage)
            if operation_type == "chat":
                # 累加到轮次
                if round_id:
                    self.repository_adapter.add_tokens_to_round(round_id, token_usage)
                # 累加到消息
                if message_id:
                    self.repository_adapter.add_tokens_to_message(message_id, token_usage, platform, model)
            elif operation_type == "summary":
                # 累加到总结
                if summary_id:
                    self.repository_adapter.add_tokens_to_summary(summary_id, token_usage)
            elif operation_type == "auto_question":
                self.logger.info("auto_question操作类型，不累加token", {"operation_type": operation_type})
            else:
                self.logger.error("操作类型错误", {"operation_type": operation_type})
                raise ValueError("操作类型错误")
            
        except Exception as e:
            self.logger.error(
                "累加token到层级结构失败", 
                exception=e, 
                extra_data={
                    "token_usage": {
                        "total_tokens": token_usage.total_tokens,
                        "prompt_tokens": token_usage.prompt_tokens,
                        "completion_tokens": token_usage.completion_tokens,
                        "reasoning_tokens": token_usage.reasoning_tokens
                    },
                    "user_id": user_id, 
                    "conversation_id": conversation_id, 
                    "round_id": round_id, 
                    "operation_type": operation_type
                }
            )
            raise

    # ==================== 统计查询方法 ====================

    def get_model_statistics(self):
        """获取模型token使用统计"""
        return self.repository_adapter.get_model_statistics()

    def get_platform_statistics(self):
        """获取平台token使用统计"""
        return self.repository_adapter.get_platform_statistics()

    def get_current_platform_and_model_info(self, llm: Optional[LLM] = None, operation_type: str = "chat") -> dict:
        """获取当前使用的平台和模型详细信息
        
        Args:
            llm: LLM实例（动态传入）
            operation_type: 操作类型 ("chat", "think", "summary")
            
        Returns:
            包含平台、模型和配置信息的字典
        """
        if llm:
            return {
                "platform": llm.platform,
                "model": llm.model,
                "base_url": llm.url,
                "temperature": llm.temperature,
                "max_tokens": llm.max_tokens,
                "description": llm.description,
            }
        else:
            # 返回默认值
            return {
                "platform": "unknown",
                "model": "unknown",
                "base_url": "",
                "temperature": 0.7,
                "max_tokens": 4096,
                "description": "",
            }