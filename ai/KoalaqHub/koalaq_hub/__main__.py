import asyncio
import json
import logging
import sys
from pathlib import Path

# 配置日志（在导入其他模块之前）
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from koalaq_hub.config.agent_builder import agent_builder
from koalaq_hub.config.llm_builder import llm_builder
from koalaq_hub.config.settings import config
from koalaq_hub.core.agents.agent_executor import AgentExecutor
from koalaq_hub.core.agents.agent_registry import AgentRegistry
from koalaq_hub.core.conversation_manager import ConversationManager
from koalaq_hub.core.llm_manager import LLMManager
from koalaq_hub.core.logging_utils import ManagerLogger
from koalaq_hub.core.prompt.function_prompt_assembler import FunctionPromptAssembler
from koalaq_hub.core.summary_manager import SummaryManager
from koalaq_hub.core.tool.mcp.mcp_tool_manager import ToolManager
from koalaq_hub.core.tool.mcp.server_manager import ServerManager
from koalaq_hub.core.user_manager import UserManager
from koalaq_hub.core.websocket_handler import WebSocketHandler
from koalaq_hub.tools import register_builtin_tools

from .api.fastapi_app import create_fastapi_server
from .database.repository_adapter import RepositoryAdapter

# 初始化主程序日志记录器
main_logger = ManagerLogger("MainApp")


def get_package_root() -> Path:
    """获取包根目录"""
    return Path(__file__).parent


def validate_and_print_config():
    """验证并打印配置信息"""
    if not config.validate_paths():
        main_logger.error("配置路径验证失败")
        return False
    config.print_config_info()

    # 验证所有应用配置的LLM配置是否有效
    available_agents = agent_builder.get_available_agents()
    if not available_agents:
        main_logger.error("未找到可用的应用配置")
        return False

    main_logger.info("检查应用配置", {"available_agents": available_agents})

    for agent_id in available_agents:
        app = agent_builder[agent_id]

        # 检查主LLM配置（从ini配置验证）
        if app.llm_use:
            llm_config = llm_builder.get_ini_config(app.llm_use)
            if not llm_config:
                main_logger.error(f"应用 {agent_id} 的主LLM配置不存在", {"llm_use": app.llm_use})
                return False
            if not llm_config.get("api_key"):
                main_logger.error(f"应用 {agent_id} 的主LLM配置缺少有效的API Key", {"llm_use": app.llm_use})
                return False

        # 检查总结LLM配置（如果启用了总结功能）
        if app.enable_summary and app.summary_llm_use:
            summary_llm_config = llm_builder.get_ini_config(app.summary_llm_use)
            if not summary_llm_config:
                main_logger.error(
                    f"应用 {agent_id} 的总结LLM配置不存在",
                    {"summary_llm_use": app.summary_llm_use},
                )
                return False
            if not summary_llm_config.get("api_key"):
                main_logger.error(
                    f"应用 {agent_id} 的总结LLM配置缺少有效的API Key",
                    {"summary_llm_use": app.summary_llm_use},
                )
                return False

        main_logger.info(
            "应用配置验证成功",
            {
                "agent_id": agent_id,
                "name": app.name,
                "llm_use": app.llm_use,
                "summary_llm_use": app.summary_llm_use if app.enable_summary else "disabled",
            },
        )

    return True



def initialize_user_data(db_storage: RepositoryAdapter):
    """初始化用户数据到数据库"""
    try:
        main_logger.info("初始化用户数据...")
        
        # 读取初始化用户文件
        init_file_path = config.user_init_dir / "init.json"
        
        if not init_file_path.exists():
            main_logger.warning(f"用户初始化文件不存在: {init_file_path}")
            return
            
        with open(init_file_path, 'r', encoding='utf-8') as f:
            init_data = json.load(f)
            
        users_data = init_data.get("users", [])
        if not users_data:
            main_logger.warning("用户初始化文件中没有用户数据")
            return
            
        initialized_count = 0
        skipped_count = 0
        
        for user_data in users_data:
            user_id = user_data.get("user_id")
            username = user_data.get("name")
            
            if not user_id or not username:
                main_logger.warning(f"用户数据不完整，跳过: {user_data}")
                continue
                
            # 检查用户是否已存在
            existing_user = db_storage.get_user(user_id)
            if existing_user:
                main_logger.info("用户已存在，跳过初始化", {"user_id": user_id, "username": username})
                skipped_count += 1
                continue
                
            # 创建用户对象
            from koalaq_hub.models.data_models import User
            user = User(
                user_id=user_id,
                username=username,
                # created_at 将自动使用当前时间
                extra_data=None,
                total_tokens=0,
                prompt_tokens=0,
                completion_tokens=0,
                reasoning_tokens=0
            )
            
            # 添加用户到数据库
            db_storage.add_user(user)
            main_logger.info("初始化用户记录", {"user_id": user_id, "username": username})
            initialized_count += 1
            
        main_logger.info("用户数据初始化完成", {
            "total_users": len(users_data),
            "initialized": initialized_count,
            "skipped": skipped_count
        })
        
    except Exception as e:
        main_logger.error("初始化用户数据失败", exception=e)
        raise


async def initialize_services():
    """初始化所有服务，返回 chat_session, db_storage, user_manager, conversation_manager"""
    try:
        # 注册内置工具（call_agent等）
        main_logger.info("注册内置工具...")
        register_builtin_tools()

        # 创建并初始化ServerManager
        server_manager = ServerManager()
        await server_manager.initialize_all_servers()

        # 启动时连接所有MCP服务器并获取工具列表
        main_logger.info("连接所有MCP服务器并获取工具列表...")
        tool_mapping = await server_manager.refresh_tool_mapping()
        main_logger.info(f"MCP工具加载完成，共 {len(tool_mapping)} 个工具")

        # 创建WebSocket处理器
        websocket_handler = WebSocketHandler()

        # 创建数据库存储（使用Repository系统）
        db_path = config.get_database_path()
        db_storage = RepositoryAdapter(str(db_path)) if db_path else None

        # 创建 LLM 管理器并保存 ini 配置到数据库
        llm_manager = None
        if db_storage:
            llm_manager = LLMManager(db_storage)
            main_logger.info("保存 LLM 配置到数据库...")
            saved_count = llm_builder.save_to_database(llm_manager)
            main_logger.info(f"LLM 配置保存完成，共 {saved_count} 个")

        # 初始化用户数据
        if db_storage:
            initialize_user_data(db_storage)

        # 创建工具管理器
        tool_manager = ToolManager(server_manager, websocket_handler)

        # 创建新的提示词组装器
        main_logger.info("初始化提示词组装器...")
        function_prompt_assembler = FunctionPromptAssembler()
        
        # 创建SummaryManager（不再需要prompt_manager）
        summary_manager = SummaryManager(db_storage, function_prompt_assembler)
        
        # 创建并初始化 Agent 注册表（注入正确的依赖）
        main_logger.info("初始化 Agent 注册表...")
        agent_registry = AgentRegistry(
            tool_manager=tool_manager,
            repository_adapter=db_storage,
            llm_manager=llm_manager,
            cache_timeout_minutes=config.agent_cache_timeout_minutes
        )
        await agent_registry.initialize()
        
        # 创建 Agent 执行器
        main_logger.info("初始化 Agent 执行器...")
        agent_executor = AgentExecutor(
            agent_registry=agent_registry,
            repository_adapter=db_storage,
            summary_manager=summary_manager,
            server_manager=server_manager,
            function_prompt_assembler=function_prompt_assembler,
            websocket_handler=websocket_handler
        )
        
        # 创建用户管理器
        user_manager = UserManager(db_storage) if db_storage else None

        # 创建会话管理器
        conversation_manager = ConversationManager(db_storage) if db_storage else None

        return (
            db_storage,
            user_manager,
            conversation_manager,
            server_manager,
            agent_registry,
            agent_executor,
        )
    except Exception as e:
        main_logger.error("初始化服务时出错", exception=e)
        raise


async def main() -> None:
    """主函数"""
    try:
        # 验证 LLM 配置已加载（从 ini 文件）
        main_logger.info("检查 LLM 配置...")
        ini_configs = llm_builder.get_ini_configs()
        if not ini_configs:
            main_logger.error("没有找到任何 LLM 配置")
            return
        main_logger.info(f"已加载 {len(ini_configs)} 个 LLM 配置: {list(ini_configs.keys())}")
        
        # 验证 Agent 配置已加载
        main_logger.info("检查 Agent 配置...")
        all_agents = agent_builder.get_all_agents()
        if not all_agents:
            main_logger.error("没有找到任何 Agent 配置")
            return
        main_logger.info(f"已加载 {len(all_agents)} 个 Agent 配置: {list(all_agents.keys())}")
        
        if not validate_and_print_config():
            return

        # 初始化服务
        (
            db_storage,
            user_manager,
            conversation_manager,
            server_manager,
            agent_registry,
            agent_executor,
        ) = await initialize_services()

        # 创建简化的FastAPI服务器，直接注入依赖
        fastapi_server = create_fastapi_server(user_manager, conversation_manager, agent_registry, agent_executor, db_storage)

        main_logger.info("启动FastAPI服务器...")
        await fastapi_server.start()
    except Exception as e:
        main_logger.error("启动失败", exception=e)
        raise


if __name__ == "__main__":
    asyncio.run(main())
