"""
LLM Builder
负责从 llm_config.ini 读取配置，支持环境变量覆盖
直接在内存中管理 LLM 配置，不依赖数据库
"""

import configparser
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.logging_utils import ManagerLogger
from ..models.llm import LLM


class LLMBuilder:
    """LLM 构建器 - 从 ini + 环境变量读取配置，存储在内存中

    环境变量覆盖规则：
    - Section: [easy-accounts]
    - 前缀: LLM_EASY_ACCOUNTS_ (大写 + 横杠转下划线)
    - 支持的环境变量:
        - LLM_EASY_ACCOUNTS_API_KEY
        - LLM_EASY_ACCOUNTS_URL
        - LLM_EASY_ACCOUNTS_MODEL
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.logger = ManagerLogger("LLMBuilder")

        # 配置文件路径
        if config_path is None:
            project_root = Path(__file__).parent.parent.parent
            self.config_path = project_root / "resource" / "config" / "llm_config.ini"
        else:
            self.config_path = Path(config_path)

        # 内存缓存 LLM 对象
        self._llms: Dict[str, LLM] = {}

        # 加载配置
        self._load_configs()

    def _get_env_prefix(self, section_name: str) -> str:
        """生成环境变量前缀

        Args:
            section_name: ini section 名称，如 "easy-accounts"

        Returns:
            环境变量前缀，如 "LLM_EASY_ACCOUNTS_"
        """
        return f"LLM_{section_name.upper().replace('-', '_')}_"

    def _load_configs(self) -> None:
        """从配置文件 + 环境变量加载所有 LLM 配置"""
        if not self.config_path.exists():
            self.logger.error(f"LLM 配置文件不存在: {self.config_path}")
            return

        try:
            config_parser = configparser.ConfigParser()
            config_parser.read(self.config_path, encoding="utf-8")

            for section_name in config_parser.sections():
                if section_name == "settings":
                    continue

                try:
                    section = config_parser[section_name]
                    env_prefix = self._get_env_prefix(section_name)

                    # ========== 环境变量优先覆盖 ==========
                    api_key = os.getenv(f"{env_prefix}API_KEY", section.get("api_key", ""))
                    url = os.getenv(f"{env_prefix}URL", section.get("url", ""))
                    model = os.getenv(f"{env_prefix}MODEL", section.get("model", ""))

                    # 记录环境变量使用情况
                    if os.getenv(f"{env_prefix}API_KEY"):
                        self.logger.info(f"使用环境变量 API_KEY: {section_name}")
                    if os.getenv(f"{env_prefix}URL"):
                        self.logger.info(f"使用环境变量 URL: {section_name} -> {url}")
                    if os.getenv(f"{env_prefix}MODEL"):
                        self.logger.info(f"使用环境变量 MODEL: {section_name} -> {model}")

                    # 检查必要字段
                    if not api_key:
                        self.logger.warning(
                            f"LLM配置 {section_name} 缺少 api_key，"
                            f"请通过环境变量 {env_prefix}API_KEY 或 ini 文件配置"
                        )
                    if not url:
                        self.logger.warning(
                            f"LLM配置 {section_name} 缺少 url，"
                            f"请通过环境变量 {env_prefix}URL 或 ini 文件配置"
                        )
                    if not model:
                        self.logger.warning(
                            f"LLM配置 {section_name} 缺少 model，"
                            f"请通过环境变量 {env_prefix}MODEL 或 ini 文件配置"
                        )

                    # 创建 LLM 对象
                    llm = LLM(
                        llm_id=str(uuid.uuid4()),
                        llm_config_name=section_name,
                        api_key=api_key,
                        url=url,
                        model=model,
                        platform=section.get("platform", section_name),
                        temperature=section.getfloat("temperature", 0.7),
                        top_p=section.getfloat("top_p", 1.0),
                        max_tokens=section.getint("max_tokens", 4096),
                        description=section.get("description", ""),
                        think=section.getboolean("think", False),
                        think_max_tokens=section.getint("think_max_tokens", 0),
                    )

                    self._llms[section_name] = llm
                    self.logger.info(
                        "加载 LLM 配置",
                        {
                            "llm_config_name": section_name,
                            "model": model,
                            "platform": llm.platform,
                        },
                    )

                except Exception as e:
                    self.logger.error(f"加载 LLM 配置失败: section={section_name}, error={e}")

            self.logger.info(
                "LLM 配置加载完成",
                {"total": len(self._llms), "configs": list(self._llms.keys())},
            )

        except Exception as e:
            self.logger.error("读取 LLM 配置文件失败", exception=e)

    # ==================== 查询方法 ====================

    def get_llm(self, llm_config_name: str) -> Optional[LLM]:
        """根据配置名称获取 LLM

        Args:
            llm_config_name: 配置名称（ini section 名）

        Returns:
            LLM 对象，不存在返回 None
        """
        return self._llms.get(llm_config_name)

    def get_llm_by_name(self, llm_config_name: str) -> Optional[LLM]:
        """get_llm 的别名"""
        return self.get_llm(llm_config_name)

    def get_all_llms(self) -> Dict[str, LLM]:
        """获取所有 LLM"""
        return self._llms.copy()

    def list_all(self) -> List[LLM]:
        """获取所有 LLM 列表"""
        return list(self._llms.values())

    def get_available_names(self) -> List[str]:
        """获取所有可用的配置名称"""
        return list(self._llms.keys())

    def exists(self, llm_config_name: str) -> bool:
        """检查配置是否存在"""
        return llm_config_name in self._llms

    # ==================== 魔术方法 ====================

    def __getitem__(self, llm_config_name: str) -> Optional[LLM]:
        """支持下标访问: llm_builder["easy-accounts"]"""
        return self.get_llm(llm_config_name)

    def __contains__(self, llm_config_name: str) -> bool:
        """支持 in 操作符"""
        return llm_config_name in self._llms

    def __len__(self) -> int:
        """返回 LLM 数量"""
        return len(self._llms)

    def __iter__(self):
        """支持迭代"""
        return iter(self._llms)

    def items(self):
        """返回所有键值对"""
        return self._llms.items()

    def values(self):
        """返回所有 LLM 对象"""
        return self._llms.values()

    def keys(self):
        """返回所有配置名称"""
        return self._llms.keys()

    # ==================== 兼容方法（不再使用数据库） ====================

    def save_to_database(self, llm_manager) -> int:
        """兼容旧接口，但不再实际保存到数据库

        Returns:
            int: 配置数量
        """
        self.logger.info("跳过数据库保存，使用内存配置")
        return len(self._llms)

    def get_ini_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有配置（字典格式）"""
        return {name: llm.to_llm_config() for name, llm in self._llms.items()}

    def get_ini_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """获取指定配置（字典格式）"""
        llm = self._llms.get(config_name)
        return llm.to_llm_config() if llm else None

    def get_config_names(self) -> List[str]:
        """获取所有配置名称"""
        return list(self._llms.keys())


# 创建全局 LLM 构建器实例
llm_builder = LLMBuilder()
