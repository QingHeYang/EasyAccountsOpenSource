import configparser
import json
from pathlib import Path
from typing import Any, Dict, Optional

from .settings import config


class ApplicationConfig:
    """应用配置类，用于管理单个应用的配置"""

    def __init__(self, app_id: str, app_data: Dict[str, Any]):
        self.app_id = app_id
        self._data = app_data
        self._use_think_llm = False  # 初始化use_think_llm属性

    @property
    def enable(self) -> bool:
        """是否启用"""
        return self._data.get("enable", "true").lower() == "true"

    @property
    def system_prompt_file(self) -> str:
        """获取系统提示词文件名（不读取内容）"""
        return self._data.get("system_prompt", "system.prompt")

    @property
    def llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        llm_use = self._data.get("llm_use", "")
        return config.get_llm_config(llm_use)

    @property
    def llm_think_config(self) -> Dict[str, Any]:
        """获取LLM思考配置"""
        llm_think_use = self._data.get("llm_think_use", "")
        if llm_think_use:
            return config.get_llm_config(llm_think_use)
        return self.llm_config

    @property
    def summary_llm_config(self) -> Dict[str, Any]:
        """获取总结LLM配置"""
        summary_llm_use = self._data.get("summary_llm_use", "")
        if summary_llm_use:
            return config.get_llm_config(summary_llm_use)
        return self.llm_config

    @property
    def mcp_servers(self) -> list:
        """获取MCP服务器名称列表"""
        # 新配置格式：mcp_servers = ["baidu-maps", "weather"]
        mcp_servers_str = self._data.get("mcp_servers", "[]")
        try:
            servers_list = json.loads(mcp_servers_str)
            return servers_list if isinstance(servers_list, list) else []
        except Exception as e:
            print(f"解析MCP服务器列表失败: {e}")
            return []

    @property
    def role_file(self) -> str:
        """获取角色配置文件名（不读取内容）"""
        return self._data.get("role", "")

    @property
    def name(self) -> str:
        """应用名称"""
        return self._data.get("name", "")

    @property
    def description(self) -> str:
        """应用描述"""
        return self._data.get("description", "")

    @property
    def llm_use(self) -> str:
        """LLM使用配置"""
        return self._data.get("llm_use", "")

    @property
    def llm_think_use(self) -> str:
        """LLM思考使用配置"""
        return self._data.get("llm_think_use", "")

    @property
    def summary_llm_use(self) -> str:
        """总结LLM使用配置"""
        return self._data.get("summary_llm_use", "")

    @property
    def enable_summary(self) -> bool:
        """是否启用总结"""
        return self._data.get("enable_summary", "true").lower() == "true"

    @property
    def enable_auto_question(self) -> bool:
        """是否启用自动生成问题"""
        return self._data.get("enable_auto_question", "true").lower() == "true"

    @enable_summary.setter
    def enable_summary(self, value: bool):
        self._data["enable_summary"] = str(value).lower()

    @property
    def enable_thinking(self) -> bool:
        """是否启用思考"""
        return self._data.get("enable_thinking", "true").lower() == "true"

    @property
    def llm_memory_window(self) -> int:
        """LLM记忆窗口大小"""
        return int(self._data.get("llm_memory_window", "10"))

    @property
    def tool_round(self) -> int:
        """工具调用轮次"""
        return int(self._data.get("tool_round", "5"))

    @property
    def mcp_tool_black_list(self) -> list:
        """MCP工具黑名单"""
        black_list_str = self._data.get("mcp_tool_black_list", "[]")
        try:
            return json.loads(black_list_str)
        except Exception as e:
            print(f"解析工具黑名单失败: {e}")
            return []

    @property
    def tool_tokens(self) -> Dict[str, str]:
        """工具Token配置，用于MCP鉴权"""
        tool_tokens_str = self._data.get("tool_tokens", "[]")
        try:
            # 支持两种格式：
            # 1. JSON格式: ["key1=value1", "key2=value2"]
            # 2. 直接字典格式: {"key1": "value1", "key2": "value2"}
            tokens_data = json.loads(tool_tokens_str)
            if isinstance(tokens_data, list):
                # 处理 ["key=value"] 格式
                result = {}
                for item in tokens_data:
                    if "=" in str(item):
                        key, value = str(item).split("=", 1)
                        result[key.strip()] = value.strip()
                return result
            elif isinstance(tokens_data, dict):
                # 直接返回字典格式
                return tokens_data
            else:
                return {}
        except Exception as e:
            print(f"解析工具Token配置失败: {e}")
            return {}

    @tool_tokens.setter
    def tool_tokens(self, value: Dict[str, str]):
        """设置工具Token配置"""
        # 将字典转换为JSON字符串存储
        self._data["tool_tokens"] = json.dumps(value, ensure_ascii=False)
    
    @property
    def use_think_llm(self) -> bool:
        """是否使用思考LLM"""
        return self._use_think_llm
    
    @use_think_llm.setter
    def use_think_llm(self, value: bool):
        self._use_think_llm = value


class ApplicationSettings:
    """应用配置管理器"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        # 使用config中的路径配置
        self.app_config_path = config.application_config_path
        self._apps = {}
        self._load_applications()

    def _load_applications(self) -> None:
        """加载应用配置"""
        if not self.app_config_path.exists():
            print(f"应用配置文件不存在: {self.app_config_path}")
            return

        try:
            config_parser = configparser.ConfigParser()
            config_parser.read(self.app_config_path, encoding="utf-8")

            for section_name in config_parser.sections():
                section = config_parser[section_name]
                app_data = {key: value for key, value in section.items()}
                self._apps[section_name] = ApplicationConfig(section_name, app_data)

            print(f"成功加载应用配置，共 {len(self._apps)} 个应用: {list(self._apps.keys())}")

        except Exception as e:
            print(f"加载应用配置失败: {e}")

    def print_application_info(self, app_id: str) -> None:
        """打印应用配置信息（用于调试）"""
        app = self.get_application(app_id)
        if not app:
            print(f"应用不存在: {app_id}")
            return

        print(f"=== 应用配置信息: {app_id} ===")
        print(f"启用: {app.enable}")
        print(f"应用名称: {app.name}")
        print(f"描述: {app.description}")
        print(f"主LLM: {app.llm_use}")
        print(f"思考LLM: {app.llm_think_use}")
        print(f"总结LLM: {app.summary_llm_use}")
        print(f"启用总结: {app.enable_summary}")
        print(f"启用自动生成问题: {app.enable_auto_question}")
        print(f"使用思考LLM: {app.use_think_llm}")
        print(f"记忆窗口: {app.llm_memory_window}")
        print(f"工具轮次: {app.tool_round}")
        print(f"MCP服务器: {app._data.get('mcp_servers', '')}")
        print(f"工具黑名单: {app.mcp_tool_black_list}")
        print(f"角色文件: {app._data.get('role', '无')}")
        print(f"提示词文件: {app._data.get('system_prompt', '无')}")

    def get_application(self, app_id: str) -> Optional[ApplicationConfig]:
        """获取指定应用配置"""
        return self._apps.get(app_id)

    def __getitem__(self, app_id: str) -> ApplicationConfig:
        """支持 application[app_id] 语法"""
        app = self.get_application(app_id)
        if app is None:
            raise KeyError(f"应用配置不存在: {app_id}")
        return app

    def get_all_applications(self) -> Dict[str, ApplicationConfig]:
        """获取所有应用配置"""
        return self._apps

    def get_available_apps(self) -> list:
        """获取可用应用列表"""
        return list(self._apps.keys())


# 创建全局应用配置实例
application = ApplicationSettings()
