"""
LLM Builder
负责从 llm_config.ini 读取配置并创建 LLM 对象
支持从环境变量覆盖配置
"""

import configparser
import os
from pathlib import Path
from typing import Dict, List, Optional

from ..core.logging_utils import ManagerLogger
from ..models.llm import LLM


class LLMBuilder:
    """LLM 构建器，负责加载和管理所有 LLM 配置"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """初始化 LLM 构建器
        
        Args:
            config_path: LLM 配置文件路径，如果不提供则使用默认路径
        """
        self.logger = ManagerLogger("LLMBuilder")
        
        # 设置配置文件路径
        if config_path is None:
            # 默认路径：项目根目录/config/llm_config.ini
            project_root = Path(__file__).parent.parent.parent
            self.config_path = project_root / "config" / "llm_config.ini"
        else:
            self.config_path = Path(config_path)
        
        # 存储所有 LLM 对象
        self._llms: Dict[str, LLM] = {}
        
        # 加载配置
        self._load_configs()
    
    def _load_configs(self) -> None:
        """从配置文件加载所有 LLM 配置"""
        if not self.config_path.exists():
            self.logger.error(f"LLM 配置文件不存在: {self.config_path}")
            return
        
        try:
            config_parser = configparser.ConfigParser()
            config_parser.read(self.config_path, encoding="utf-8")
            
            # 遍历所有配置段
            for section_name in config_parser.sections():
                # 跳过 settings 段（如果有的话）
                if section_name == "settings":
                    continue
                
                try:
                    section = config_parser[section_name]
                    
                    # 优先从环境变量读取配置，如果没有则使用 ini 文件的配置
                    # 环境变量命名格式：LLM_<SECTION_NAME>_<FIELD>
                    # 例如：LLM_EASY_ACCOUNTS_API_KEY, LLM_EASY_ACCOUNTS_URL, LLM_EASY_ACCOUNTS_MODEL
                    env_prefix = f"LLM_{section_name.upper().replace('-', '_')}_"
                    
                    # 获取配置值（环境变量优先）
                    api_key = os.getenv(f"{env_prefix}API_KEY", section.get("api_key", ""))
                    url = os.getenv(f"{env_prefix}URL", section.get("url", ""))
                    model = os.getenv(f"{env_prefix}MODEL", section.get("model", ""))
                    
                    # 检查必要的配置字段
                    if not api_key:
                        error_msg = f"LLM配置错误: {section_name} 缺少 api_key。请在 llm_config.ini 或通过环境变量 {env_prefix}API_KEY 配置"
                        self.logger.error(error_msg)
                        raise ValueError(error_msg)
                    
                    if not url:
                        error_msg = f"LLM配置错误: {section_name} 缺少 url。请在 llm_config.ini 或通过环境变量 {env_prefix}URL 配置"
                        self.logger.error(error_msg)
                        raise ValueError(error_msg)
                    
                    if not model:
                        error_msg = f"LLM配置错误: {section_name} 缺少 model。请在 llm_config.ini 或通过环境变量 {env_prefix}MODEL 配置"
                        self.logger.error(error_msg)
                        raise ValueError(error_msg)
                    
                    # 如果使用了环境变量，记录日志
                    if os.getenv(f"{env_prefix}API_KEY"):
                        self.logger.info(f"使用环境变量配置 API_KEY: {section_name}")
                    if os.getenv(f"{env_prefix}URL"):
                        self.logger.info(f"使用环境变量配置 URL: {section_name} -> {url}")
                    if os.getenv(f"{env_prefix}MODEL"):
                        self.logger.info(f"使用环境变量配置 MODEL: {section_name} -> {model}")
                    
                    # 创建 LLM 对象
                    llm = LLM(
                        llm_id=section_name,
                        name=section_name,  # 使用 section 名称作为默认名称
                        description=section.get("description", ""),
                        api_key=api_key,
                        url=url,
                        model=model,
                        platform=section.get("platform", section_name),
                        temperature=section.getfloat("temperature", 0.7),
                        top_p=section.getfloat("top_p", 1.0),
                        timeout=section.getfloat("timeout", 120.0),
                        max_tokens=section.getint("max_tokens", 4096),
                        think=section.getboolean("think", False),
                        think_max_tokens=section.getint("think_max_tokens", 0)
                    )
                    
                    self._llms[section_name] = llm
                    self.logger.info("加载 LLM 配置", {
                        "llm_id": section_name,
                        "model": llm.model,
                        "platform": llm.platform
                    })
                    
                except Exception as e:
                    self.logger.error("加载 LLM 配置失败", {
                        "section": section_name,
                        "error": str(e)
                    })
            
            self.logger.info("LLM 配置加载完成", {
                "total": len(self._llms),
                "llms": list(self._llms.keys())
            })
            
        except Exception as e:
            self.logger.error("读取 LLM 配置文件失败", exception=e)
    
    def get_llm(self, llm_id: str) -> Optional[LLM]:
        """获取指定的 LLM 对象
        
        Args:
            llm_id: LLM ID
            
        Returns:
            LLM 对象，如果不存在则返回 None
        """
        return self._llms.get(llm_id)
    
    def get_all_llms(self) -> Dict[str, LLM]:
        """获取所有 LLM 对象
        
        Returns:
            包含所有 LLM 的字典
        """
        return self._llms.copy()
    
    def get_available_llms(self) -> List[str]:
        """获取所有可用的 LLM ID
        
        Returns:
            LLM ID 列表
        """
        return list(self._llms.keys())
    
    def __getitem__(self, llm_id: str) -> Optional[LLM]:
        """支持下标访问
        
        Args:
            llm_id: LLM ID
            
        Returns:
            LLM 对象
        """
        return self.get_llm(llm_id)
    
    def __contains__(self, llm_id: str) -> bool:
        """支持 in 操作符
        
        Args:
            llm_id: LLM ID
            
        Returns:
            是否存在该 LLM
        """
        return llm_id in self._llms
    
    def __len__(self) -> int:
        """返回 LLM 数量"""
        return len(self._llms)
    
    def __iter__(self):
        """支持迭代"""
        return iter(self._llms)
    
    def items(self):
        """返回所有 LLM 的键值对"""
        return self._llms.items()
    
    def values(self):
        """返回所有 LLM 对象"""
        return self._llms.values()
    
    def keys(self):
        """返回所有 LLM ID"""
        return self._llms.keys()


# 创建全局 LLM 构建器实例
llm_builder = LLMBuilder()