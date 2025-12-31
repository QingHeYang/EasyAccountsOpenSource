"""
简化的FastAPI应用
保留通用返回类、日志和跨域，使用分离的endpoint文件
支持MCP服务器挂载
"""

import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from koalaq_hub.api.endpoints.agent import create_agent_router
from koalaq_hub.api.endpoints.chat import create_chat_router
from koalaq_hub.api.endpoints.config import create_config_router
from koalaq_hub.api.endpoints.conversations import create_conversations_router

# 导入分离的endpoints
from koalaq_hub.api.endpoints.users import create_users_router
from koalaq_hub.api.endpoints.websocket import setup_websocket_routes

# 保留通用返回类
from koalaq_hub.api.models.response import ResponseBuilder
from koalaq_hub.core.logging_utils import ManagerLogger

# MCP服务器
from koalaq_hub.mcp.easyaccounts_server import create_mcp_app, set_global_token


class FastAPIServer:
    """
    简化的FastAPI服务器
    在构造函数中直接注入依赖，使用分离的endpoint文件
    """

    def __init__(self, user_manager, conversation_manager, agent_registry, agent_executor, repository_adapter=None):
        self.logger = ManagerLogger("FastAPIServer")

        # 直接注入依赖，不使用复杂的依赖注入框架
        self.user_manager = user_manager
        self.conversation_manager = conversation_manager
        self.agent_registry = agent_registry
        self.agent_executor = agent_executor
        self.repository_adapter = repository_adapter

        # 先创建MCP应用以获取lifespan
        self.mcp_app = self._create_mcp_app()

        # 创建FastAPI应用，传入MCP的lifespan
        if self.mcp_app:
            self.app = FastAPI(
                title="KoalaQ Hub API",
                description="智能对话系统API接口",
                version="1.0.0",
                lifespan=self.mcp_app.lifespan
            )
        else:
            self.app = FastAPI(
                title="KoalaQ Hub API",
                description="智能对话系统API接口",
                version="1.0.0"
            )

        # 配置CORS（保留原有功能）
        self._setup_cors()

        # 配置简化的认证中间件
        self._setup_auth_middleware()

        # 配置基础路由
        self._setup_basic_routes()

        # 配置业务路由（使用分离的endpoints）
        self._setup_business_routes()

        # 挂载MCP服务器
        self._mount_mcp_server()

    def _setup_cors(self):
        """配置CORS（保留原有功能）"""
        dev_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:5173",
            "http://localhost:8080",
            "http://localhost:8081",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:8081",
        ]

        prod_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
        allowed_origins = dev_origins + [origin.strip() for origin in prod_origins if origin.strip()]

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*", "user_id", "User-ID"],
            expose_headers=["*"],
        )

        self.logger.info("CORS配置完成")

    def _setup_auth_middleware(self):
        """配置简化的认证中间件（使用纯ASGI中间件，兼容SSE）"""

        # 白名单路径 - 无需认证的端点
        whitelist_exact = ["/", "/health", "/docs", "/openapi.json", "/redoc"]

        # 白名单前缀 - 需要更精确控制的路径（包括SSE/MCP）
        whitelist_prefixes = [
            "/api/v1/users/list",  # 用户列表（无需认证）
            "/api/v1/conversations/debug",  # 调试端点（开发用）
            "/mcp",  # MCP服务器（使用自己的token鉴权）
            "/sse",  # MCP SSE端点
            "/messages",  # MCP消息端点
            "/.well-known",  # OAuth发现端点
            "/register",  # MCP OAuth注册
        ]

        # 无需认证的具体端点（支持HTTP方法）
        no_auth_endpoints = [
            ("POST", "/api/v1/users/"),  # 用户创建
            ("GET", "/api/v1/users/list"),  # 用户列表
            ("POST", "/api/v1/conversations/apply_id"),  # 申请对话ID
        ]

        user_manager = self.user_manager
        logger = self.logger

        class AuthMiddleware:
            """纯ASGI中间件，兼容SSE流式响应"""

            def __init__(self, app):
                self.app = app

            async def __call__(self, scope, receive, send):
                if scope["type"] != "http":
                    # 非HTTP请求（如WebSocket）直接放行
                    await self.app(scope, receive, send)
                    return

                path = scope["path"]
                method = scope["method"]

                # 检查精确匹配的白名单
                if path in whitelist_exact:
                    await self.app(scope, receive, send)
                    return

                # 检查前缀匹配的白名单（包括SSE/MCP路径）
                if any(path.startswith(prefix) for prefix in whitelist_prefixes):
                    # 如果是SSE连接，提取URL中的token并保存
                    if path.startswith("/sse"):
                        query_string = scope.get("query_string", b"").decode()
                        params = dict(p.split("=") for p in query_string.split("&") if "=" in p)
                        token = params.get("token")
                        if token:
                            set_global_token(token)
                            logger.info(f"从SSE连接提取token: ***{token[-8:] if len(token) > 8 else '***'}")
                    await self.app(scope, receive, send)
                    return

                # 检查特定HTTP方法和路径的组合
                current_endpoint = (method, path)
                if current_endpoint in no_auth_endpoints:
                    await self.app(scope, receive, send)
                    return

                # 检查动态路径（用户详情）
                if method == "GET" and path.startswith("/api/v1/users/") and len(path.split("/")) == 5:
                    await self.app(scope, receive, send)
                    return

                # 从headers中获取user_id
                headers = dict(scope.get("headers", []))
                user_id = headers.get(b"user_id", b"").decode() or headers.get(b"user-id", b"").decode()

                if not user_id:
                    logger.warning("缺少user_id请求头", {"path": path})
                    response = JSONResponse(status_code=401, content=ResponseBuilder.unauthorized("缺少user_id请求头").model_dump())
                    await response(scope, receive, send)
                    return

                # 验证用户是否存在
                user = user_manager.get_user(user_id)
                if not user:
                    logger.warning("用户不存在", {"user_id": user_id})
                    response = JSONResponse(status_code=401, content=ResponseBuilder.unauthorized("用户不存在").model_dump())
                    await response(scope, receive, send)
                    return

                # 将用户信息存入 scope，供后续路由使用
                # Starlette 会将 scope["state"] 映射到 request.state
                if "state" not in scope:
                    scope["state"] = {}
                scope["state"]["user"] = user

                # 放行请求
                await self.app(scope, receive, send)

        self.app.add_middleware(AuthMiddleware)
        self.logger.info("认证中间件配置完成（ASGI模式）")

    def _setup_basic_routes(self):
        """配置基础路由（健康检查等）"""

        @self.app.get("/")
        async def root():
            """根端点"""
            return ResponseBuilder.success(data={"service": "KoalaQ Hub API", "version": "1.0.0", "docs": "/docs", "status": "running"}, message="API服务正在运行")

        @self.app.get("/health")
        async def health():
            """健康检查端点，包含 LLM 配置检测"""
            # 检查 LLM 环境变量配置
            llm_api_key = os.getenv("LLM_EASY_ACCOUNTS_API_KEY", "")
            llm_url = os.getenv("LLM_EASY_ACCOUNTS_URL", "")
            llm_model = os.getenv("LLM_EASY_ACCOUNTS_MODEL", "")

            llm_configured = bool(llm_api_key and llm_url and llm_model)
            missing_configs = []
            if not llm_api_key:
                missing_configs.append("LLM_EASY_ACCOUNTS_API_KEY")
            if not llm_url:
                missing_configs.append("LLM_EASY_ACCOUNTS_URL")
            if not llm_model:
                missing_configs.append("LLM_EASY_ACCOUNTS_MODEL")

            health_data = {
                "status": "healthy" if llm_configured else "degraded",
                "service": "koalaq-hub-api",
                "llm": {
                    "configured": llm_configured,
                    "model": llm_model if llm_model else None,
                    "missing": missing_configs if missing_configs else None
                }
            }

            if llm_configured:
                return ResponseBuilder.success(data=health_data, message="服务健康")
            else:
                return ResponseBuilder.success(data=health_data, message="服务运行中，但 LLM 未配置完整")

        self.logger.info("基础路由配置完成")

    def _setup_business_routes(self):
        """配置业务路由（使用分离的endpoints）"""

        # 用户管理路由 - 使用函数式依赖注入
        users_router = create_users_router(self.user_manager)
        self.app.include_router(users_router)

        # 会话管理路由 - 使用函数式依赖注入
        conversations_router = create_conversations_router(self.conversation_manager, self.agent_executor)
        self.app.include_router(conversations_router)

        # 智能代理路由 - 无需依赖注入，直接从配置读取
        agent_router = create_agent_router()
        self.app.include_router(agent_router)

        chat_router = create_chat_router(self.agent_executor)
        # Chat API路由 - 新的HTTP聊天接口
        self.app.include_router(chat_router)

        # 系统配置和统计路由
        if self.repository_adapter:
            config_router = create_config_router(self.user_manager, self.conversation_manager, self.repository_adapter)
            self.app.include_router(config_router)

        # WebSocket路由 - 使用函数式依赖注入
        setup_websocket_routes(self.app,self.user_manager, self.conversation_manager, self.agent_registry, self.agent_executor)

        self.logger.info("业务路由配置完成")

    def _create_mcp_app(self):
        """创建MCP应用（需要在FastAPI创建之前调用以获取lifespan）"""
        try:
            mcp_enabled = os.getenv("MCP_SERVER_ENABLED", "true").lower() == "true"
            if not mcp_enabled:
                self.logger.info("MCP服务器已禁用")
                return None

            # 获取传输模式
            self.mcp_transport_mode = os.getenv("MCP_TRANSPORT_MODE", "sse").lower()
            if self.mcp_transport_mode not in ["sse", "streamable-http"]:
                self.logger.warning(f"无效的MCP传输模式: {self.mcp_transport_mode}，使用默认值sse")
                self.mcp_transport_mode = "sse"

            # 创建MCP应用
            mcp_app = create_mcp_app(transport_mode=self.mcp_transport_mode)
            self.logger.info(f"MCP应用创建成功，模式: {self.mcp_transport_mode}")
            return mcp_app

        except Exception as e:
            self.logger.error(f"MCP应用创建失败: {e}")
            return None

    def _mount_mcp_server(self):
        """挂载MCP服务器到FastAPI"""
        if not self.mcp_app:
            return

        try:
            # 挂载到根路径
            self.app.mount("/", self.mcp_app)

            self.logger.info("MCP服务器已挂载")
            if self.mcp_transport_mode == "sse":
                self.logger.info("MCP SSE地址: http://{host}:{port}/sse?token=<your_token>")
            else:
                self.logger.info("MCP HTTP地址: http://{host}:{port}/mcp?token=<your_token>")

        except Exception as e:
            self.logger.error(f"MCP服务器挂载失败: {e}")

    async def start(self):
        """启动FastAPI服务器"""
        port = int(os.getenv("API_PORT", "8001"))
        host = os.getenv("API_HOST", "0.0.0.0")

        self.logger.info(f"启动API服务器: {host}:{port}")
        self.logger.info(f"API文档地址: http://{host}:{port}/docs")

        config = uvicorn.Config(app=self.app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()


# 工厂函数，在main中调用时直接注入依赖
def create_fastapi_server(user_manager, conversation_manager, agent_registry=None, agent_executor=None, repository_adapter=None):
    """创建FastAPI服务器实例，直接注入依赖"""
    return FastAPIServer(user_manager, conversation_manager, agent_registry, agent_executor, repository_adapter)
