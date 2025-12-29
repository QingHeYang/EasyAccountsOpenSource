import json
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv


class Configuration:
    """全局配置管理器

    管理项目中的所有路径配置和环境变量。
    """

    def __init__(self) -> None:
        """初始化配置管理器"""
        # 设置项目根目录
        self.project_root = Path(__file__).parent.parent.parent

        # 加载环境变量
        self.load_env()

        # 初始化路径配置
        self._init_paths()

        # 初始化环境变量
        self._init_env_vars()

    def _init_paths(self) -> None:
        """初始化所有路径配置"""
        # 配置文件路径
        self.config_dir = self.project_root / "config"
        self.env_file_path = self.config_dir / ".env"
        self.servers_config_path = self.config_dir / "servers_config.json"

        # 从环境变量获取路径配置
        self.agent_config_path = self._get_path_from_env("AGENT", "config/agent.ini")

        # 资源文件路径
        self.resource_dir = self.project_root / "resource"
        self.md_dir = self.resource_dir / "md"
        self.role_dir = self._get_path_from_env("ROLE_DIR", "resource/role")
        self.prompts_dir = self._get_path_from_env("PROMPT_DIR", "resource/prompts")
        self.mcp_dir = self._get_path_from_env("MCP_DIR", "resource/mcp")
        self.user_init_dir = self._get_path_from_env("USER_INIT_DIR", "resource/user")
        self.agent_guide_dir = self._get_path_from_env("AGENT_GUIDE_DIR", "resource/agents")

        # 数据库路径配置（支持环境变量自定义）
        self._init_database_paths()
        # Docker文件路径
        self.docker_dir = self.project_root / "docker"
        self.docker_compose_path = self.docker_dir / "docker-compose.yml"
        self.dockerfile_path = self.docker_dir / "Dockerfile"

    def _init_env_vars(self) -> None:
        """初始化环境变量"""
        # API配置
        self.api_port = int(os.getenv("API_PORT", "8001"))
        self.api_host = os.getenv("API_HOST", "0.0.0.0")

        # 总结相关配置
        self.round_summary_max_length = int(os.getenv("ROUND_SUMMARY_MAX_LENGTH", "200"))
        self.round_summary_times = int(os.getenv("ROUND_SUMMARY_TIMES", "5"))
        self.snapshot_summary_max_length = int(os.getenv("SNAPSHOT_SUMMARY_MAX_LENGTH", "500"))
        self.conversation_summary_snapshots = int(os.getenv("CONVERSATION_SUMMARY_SNAPSHOTS", "3"))
        
        # Agent缓存配置
        self.agent_cache_timeout_minutes = int(os.getenv("AGENT_CACHE_TIMEOUT_MINUTES", "30"))
        self.conversation_summary_max_length = int(os.getenv("CONVERSATION_SUMMARY_MAX_LENGTH", "800"))
        
        # 工具调用模式配置
        self.tool_mode = os.getenv("TOOL_MODE", "function_calling").lower()
        # 验证tool_mode值
        if self.tool_mode not in ["function_calling", "mcp"]:
            print(f"警告: 无效的TOOL_MODE值 '{self.tool_mode}'，使用默认值 'function_calling'")
            self.tool_mode = "function_calling"
        
        # 工具执行超时配置
        self.tool_execution_timeout = int(os.getenv("TOOL_EXECUTION_TIMEOUT", "60"))  # 工具执行超时时间（秒）
        self.mcp_sse_timeout = int(os.getenv("MCP_SSE_TIMEOUT", "120"))  # MCP SSE连接超时时间（秒）
        
        # EasyAccounts 配置
        self.easyaccounts_url = os.getenv("EASYACCOUNTS_URL", "http://localhost:10670")

    @staticmethod
    def load_env() -> None:
        """从.env文件加载环境变量"""
        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / "config" / ".env"

        if env_file.exists():
            load_dotenv(env_file)
        else:
            print(f"警告: 环境变量文件不存在: {env_file}")


    def _get_path_from_env(self, env_key: str, default_path: str) -> Path:
        """从环境变量获取路径配置"""
        path_str = os.getenv(env_key, default_path)
        if path_str.startswith("./"):
            return self.project_root / path_str[2:]
        elif path_str.startswith("/"):
            return Path(path_str)
        else:
            return self.project_root / path_str

    def load_servers_config(self) -> Dict[str, Any]:
        """加载服务器配置

        Returns:
            包含服务器配置的字典

        Raises:
            FileNotFoundError: 如果配置文件不存在
            JSONDecodeError: 如果配置文件不是有效的JSON
        """
        if not self.servers_config_path.exists():
            raise FileNotFoundError(f"服务器配置文件不存在: {self.servers_config_path}")

        with open(self.servers_config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        # 处理不同的配置格式
        if "mcpServers" in config_data:
            # 旧格式：mcpServers
            mcp_servers = config_data["mcpServers"]
            servers = []
            for name, server_config in mcp_servers.items():
                servers.append({"name": name, "url": server_config.get("url", ""), "tools": server_config.get("tools", [])})
            return {"servers": servers}
        elif "servers" in config_data:
            # 新格式：servers
            return config_data
        else:
            # 未知格式
            raise ValueError("配置文件格式不支持，需要包含 'mcpServers' 或 'servers' 字段")

    def get_md_storage_path(self) -> str:
        """获取Markdown存储路径"""
        return str(self.md_dir)

    def _init_database_paths(self) -> None:
        """初始化数据库路径配置"""
        # 从环境变量获取数据库目录配置
        database_dir_env = os.getenv("DATABASE_DIR", "./resource/database")
        database_name_env = os.getenv("DATABASE_NAME", "chatbot.db")

        # 处理相对路径和绝对路径
        if database_dir_env.startswith("./"):
            # 相对路径，相对于项目根目录
            self.database_dir = self.project_root / database_dir_env[2:]
        elif database_dir_env.startswith("/"):
            # 绝对路径
            self.database_dir = Path(database_dir_env)
        else:
            # 相对路径，相对于项目根目录
            self.database_dir = self.project_root / database_dir_env

        # 设置数据库文件路径
        self.database_path = self.database_dir / database_name_env

        # 确保数据库目录存在
        self.database_dir.mkdir(parents=True, exist_ok=True)

    def get_database_path(self) -> str:
        """获取数据库路径"""
        return str(self.database_path)

    def get_role_dir(self) -> Path:
        """获取角色配置目录"""
        return self.role_dir

    def validate_paths(self) -> bool:
        """验证所有必要路径是否存在

        Returns:
            bool: 所有路径都存在返回True，否则返回False
        """
        required_paths = [self.config_dir, self.resource_dir, self.prompts_dir, self.role_dir]

        required_files = [self.env_file_path, self.agent_config_path]

        # 检查目录
        for path in required_paths:
            if not path.exists():
                print(f"错误: 目录不存在: {path}")
                return False

        # 检查文件
        for file_path in required_files:
            if not file_path.exists():
                print(f"错误: 文件不存在: {file_path}")
                return False

        return True

    def print_config_info(self) -> None:
        """打印配置信息（用于调试）"""
        print("=== 项目配置信息 ===")
        print(f"项目根目录: {self.project_root}")
        print(f"配置目录: {self.config_dir}")
        print(f"资源目录: {self.resource_dir}")
        print(f"Markdown目录: {self.md_dir}")
        print(f"角色目录: {self.role_dir}")
        print(f"数据库目录: {self.database_dir}")
        print(f"数据库文件: {self.database_path}")
        print(f"提示词目录: {self.prompts_dir}")
        print(f"MCP目录: {self.mcp_dir}")
        print(f"Docker目录: {self.docker_dir}")
        print()
        print("=== Agent配置信息 ===")
        print(f"Agent配置文件: {self.agent_config_path}")
        print(f"Agent指南目录: {self.agent_guide_dir}")
        print()
        print("=== 系统环境变量 ===")
        print(f"API Port: {self.api_port}")
        print(f"API Host: {self.api_host}")
        print(f"总结配置: 单轮{self.round_summary_max_length}字, {self.round_summary_times}轮后快照")
        print(f"数据库名称: {os.getenv('DATABASE_NAME', 'koalaq.db')}")
        print(f"工具调用模式: {self.tool_mode}")


# 创建全局配置实例
config = Configuration()
