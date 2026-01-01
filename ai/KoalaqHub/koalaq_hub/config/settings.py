import os
from pathlib import Path

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
        # 资源文件路径
        self.resource_dir = self.project_root / "resource"
        self.resource_config_dir = self.resource_dir / "config"

        # 环境变量文件在项目根目录
        self.env_file_path = self.project_root / ".env"

        # 配置文件路径（在 resource/config 下）
        self.agent_config_path = self._get_path_from_env("AGENT", "resource/config/agent.ini")
        self.llm_config_path = self._get_path_from_env("LLM_CONFIG", "resource/config/llm_config.ini")

        # 其他资源文件路径
        self.md_dir = self.resource_dir / "md"
        self.role_dir = self._get_path_from_env("ROLE_DIR", "resource/role")
        self.prompts_dir = self._get_path_from_env("PROMPT_DIR", "resource/prompts")
        self.user_init_dir = self._get_path_from_env("USER_INIT_DIR", "resource/user")
        self.agent_guide_dir = self._get_path_from_env("AGENT_GUIDE_DIR", "resource/agents")

        # MCP配置目录
        self.mcp_dir = self._get_path_from_env("MCP_DIR", "resource/mcp")

        # 数据库路径配置（支持环境变量自定义）
        self._init_database_paths()

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
        
        # 工具执行超时配置
        self.tool_execution_timeout = int(os.getenv("TOOL_EXECUTION_TIMEOUT", "60"))  # 工具执行超时时间（秒）

        # MCP SSE超时配置
        self.mcp_sse_timeout = int(os.getenv("MCP_SSE_TIMEOUT", "30"))  # MCP SSE连接超时时间（秒）

        # LLM 超时配置
        self.llm_timeout = float(os.getenv("LLM_TIMEOUT", "120.0"))  # LLM API 调用超时时间（秒）

        # EasyAccounts API 配置
        # Docker 内部网络使用服务名:内部端口，外部访问使用映射端口
        self.easyaccounts_url = os.getenv("EASYACCOUNTS_URL", "http://server:8081")

    @staticmethod
    def load_env() -> None:
        """从.env文件加载环境变量"""
        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / ".env"

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

    def get_md_storage_path(self) -> str:
        """获取Markdown存储路径"""
        return str(self.md_dir)

    def _init_database_paths(self) -> None:
        """初始化数据库路径配置"""
        # 从环境变量获取数据库目录配置
        database_dir_env = os.getenv("DATABASE_DIR", "./resource/database")
        database_name_env = os.getenv("DATABASE_NAME", "koalaq.db")

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
        required_paths = [self.resource_dir, self.resource_config_dir, self.prompts_dir, self.role_dir]

        # .env 文件在 Docker 环境中不是必需的（通过 compose 注入环境变量）
        required_files = [self.agent_config_path, self.llm_config_path]

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
        print(f"资源目录: {self.resource_dir}")
        print(f"配置目录: {self.resource_config_dir}")
        print(f"角色目录: {self.role_dir}")
        print(f"提示词目录: {self.prompts_dir}")
        print(f"数据库目录: {self.database_dir}")
        print(f"数据库文件: {self.database_path}")
        print()
        print("=== Agent配置信息 ===")
        print(f"Agent配置文件: {self.agent_config_path}")
        print(f"LLM配置文件: {self.llm_config_path}")
        print(f"Agent指南目录: {self.agent_guide_dir}")
        print()
        print("=== 系统环境变量 ===")
        print(f"API Port: {self.api_port}")
        print(f"API Host: {self.api_host}")
        print(f"总结配置: 单轮{self.round_summary_max_length}字, {self.round_summary_times}轮后快照")


# 创建全局配置实例
config = Configuration()
