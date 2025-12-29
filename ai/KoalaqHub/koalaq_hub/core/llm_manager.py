"""
LLM 管理器
从 llm_builder 内存读取 LLM 配置，不依赖数据库
"""

from typing import List, Optional

from ..config.llm_builder import llm_builder
from ..models.llm import LLM
from .logging_utils import ManagerLogger


class LLMManager:
    """LLM 管理器 - 从 llm_builder 内存读取配置

    不再依赖数据库，所有配置来自:
    1. llm_config.ini 文件
    2. 环境变量覆盖 (LLM_EASY_ACCOUNTS_API_KEY 等)
    """

    def __init__(self, repository_adapter=None):
        """初始化 LLM 管理器

        Args:
            repository_adapter: 保留参数以兼容旧代码，但不再使用
        """
        self.logger = ManagerLogger("LLMManager")
        # 不再使用 repository_adapter

    # ==================== 查询方法（从 llm_builder 读取） ====================

    def get_llm_by_name(self, llm_config_name: str) -> Optional[LLM]:
        """根据配置名称获取 LLM

        Args:
            llm_config_name: 配置名称（ini section 名）

        Returns:
            LLM 对象，不存在返回 None
        """
        llm = llm_builder.get_llm(llm_config_name)

        if llm:
            self.logger.debug(f"获取 LLM 成功: {llm_config_name}")
        else:
            self.logger.warning(f"LLM 配置不存在: {llm_config_name}")

        return llm

    def get_llm_by_id(self, llm_id: str) -> Optional[LLM]:
        """根据 ID 获取 LLM

        注意：由于不再使用数据库，ID 匹配改为遍历查找

        Args:
            llm_id: LLM ID

        Returns:
            LLM 对象，不存在返回 None
        """
        for llm in llm_builder.values():
            if llm.llm_id == llm_id:
                self.logger.debug(f"获取 LLM 成功: llm_id={llm_id}")
                return llm

        self.logger.warning(f"LLM 配置不存在: llm_id={llm_id}")
        return None

    def list_all(self) -> List[LLM]:
        """获取所有 LLM 配置

        Returns:
            LLM 列表
        """
        llm_list = llm_builder.list_all()
        self.logger.debug(f"获取所有 LLM 配置，共 {len(llm_list)} 个")
        return llm_list

    def get_available_names(self) -> List[str]:
        """获取所有可用的 LLM 配置名称

        Returns:
            配置名称列表
        """
        return llm_builder.get_available_names()

    # ==================== 创建/更新/删除方法（不再支持，仅日志提示） ====================

    def create_llm(self, *args, **kwargs) -> str:
        """创建 LLM 配置（已禁用）"""
        self.logger.warning("create_llm 已禁用，请修改 llm_config.ini 文件")
        return ""

    def create_if_not_exists(self, *args, **kwargs) -> str:
        """创建 LLM 配置（已禁用）"""
        self.logger.info("跳过数据库创建，使用 llm_builder 内存配置")
        llm_config_name = kwargs.get("llm_config_name", "")
        llm = llm_builder.get_llm(llm_config_name)
        return llm.llm_id if llm else ""

    def update_llm(self, *args, **kwargs) -> bool:
        """更新 LLM 配置（已禁用）"""
        self.logger.warning("update_llm 已禁用，请修改 llm_config.ini 文件或环境变量")
        return False

    def delete_llm(self, *args, **kwargs) -> bool:
        """删除 LLM 配置（已禁用）"""
        self.logger.warning("delete_llm 已禁用，请修改 llm_config.ini 文件")
        return False

    # ==================== 检查方法 ====================

    def exists(self, llm_config_name: str) -> bool:
        """检查配置是否存在

        Args:
            llm_config_name: 配置名称

        Returns:
            是否存在
        """
        return llm_builder.exists(llm_config_name)

    def count(self) -> int:
        """获取 LLM 配置总数

        Returns:
            配置总数
        """
        return len(llm_builder)

    # ==================== 兼容方法 ====================

    def get_llm(self, llm_config_name: str) -> Optional[LLM]:
        """获取 LLM（兼容旧 API）"""
        return self.get_llm_by_name(llm_config_name)

    def __getitem__(self, llm_config_name: str) -> Optional[LLM]:
        """支持下标访问"""
        return self.get_llm_by_name(llm_config_name)

    def __contains__(self, llm_config_name: str) -> bool:
        """支持 in 操作符"""
        return self.exists(llm_config_name)

    def __len__(self) -> int:
        """返回 LLM 配置数量"""
        return self.count()
