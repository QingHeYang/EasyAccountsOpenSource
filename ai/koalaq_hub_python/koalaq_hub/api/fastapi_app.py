"""
简化的FastAPI应用
保留通用返回类、日志和跨域，使用分离的endpoint文件
"""

import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from koalaq_hub.api.endpoints.agent import create_agent_router
from koalaq_hub.api.endpoints.chat import create_chat_router
from koalaq_hub.api.endpoints.conversations import create_conversations_router

# 导入分离的endpoints
from koalaq_hub.api.endpoints.users import create_users_router
from koalaq_hub.api.endpoints.websocket import setup_websocket_routes

# 保留通用返回类
from koalaq_hub.api.models.response import ResponseBuilder
from koalaq_hub.core.logging_utils import ManagerLogger


class FastAPIServer:
    """
    简化的FastAPI服务器
    在构造函数中直接注入依赖，使用分离的endpoint文件
    """

    def __init__(self,  user_manager, conversation_manager, agent_registry, agent_executor):
        self.app = FastAPI(title="KoalaQ Hub API", description="智能对话系统API接口", version="1.0.0")

        # 直接注入依赖，不使用复杂的依赖注入框架
        self.user_manager = user_manager
        self.conversation_manager = conversation_manager
        self.agent_registry = agent_registry
        self.agent_executor = agent_executor
        self.logger = ManagerLogger("FastAPIServer")

        # 配置CORS（保留原有功能）
        self._setup_cors()

        # 配置简化的认证中间件
        self._setup_auth_middleware()

        # 配置基础路由
        self._setup_basic_routes()

        # 配置业务路由（使用分离的endpoints）
        self._setup_business_routes()

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
        """配置简化的认证中间件"""

        @self.app.middleware("http")
        async def auth_middleware(request, call_next):
            # 白名单路径 - 无需认证的端点
            whitelist_exact = ["/", "/health", "/docs", "/openapi.json", "/redoc"]

            # 白名单前缀 - 需要更精确控制的路径
            whitelist_prefixes = [
                "/api/v1/users/list",  # 用户列表（无需认证）
                "/api/v1/conversations/debug",  # 调试端点（开发用）
            ]

            # 无需认证的具体端点（支持HTTP方法）
            no_auth_endpoints = [
                ("POST", "/api/v1/users/"),  # 用户创建
                ("GET", "/api/v1/users/list"),  # 用户列表
                ("POST", "/api/v1/conversations/apply_id"),  # 申请对话ID
            ]

            # 检查精确匹配的白名单
            if request.url.path in whitelist_exact:
                return await call_next(request)

            # 检查前缀匹配的白名单
            if any(request.url.path.startswith(prefix) for prefix in whitelist_prefixes):
                return await call_next(request)

            # 检查特定HTTP方法和路径的组合
            current_endpoint = (request.method, request.url.path)
            if current_endpoint in no_auth_endpoints:
                return await call_next(request)

            # 检查动态路径（用户详情）
            if request.method == "GET" and request.url.path.startswith("/api/v1/users/") and len(request.url.path.split("/")) == 5:
                # 格式: /api/v1/users/{user_id} - 允许无认证访问
                return await call_next(request)

            # 检查user_id请求头
            user_id = request.headers.get("user_id") or request.headers.get("User-ID")

            if not user_id:
                self.logger.warning("缺少user_id请求头", {"path": request.url.path})
                return JSONResponse(status_code=401, content=ResponseBuilder.unauthorized("缺少user_id请求头").dict())

            # 验证用户是否存在（在UserManager中验证，如不存在返回401）
            user = self.user_manager.get_user(user_id)
            if not user:
                self.logger.warning("用户不存在", {"user_id": user_id})
                return JSONResponse(status_code=401, content=ResponseBuilder.unauthorized("用户不存在").dict())

            # 将用户信息附加到请求状态
            request.state.user = user
            return await call_next(request)

        self.logger.info("认证中间件配置完成")

    def _setup_basic_routes(self):
        """配置基础路由（健康检查等）"""

        @self.app.get("/")
        async def root():
            """根端点"""
            return ResponseBuilder.success(data={"service": "KoalaQ Hub API", "version": "1.0.0", "docs": "/docs", "status": "running"}, message="API服务正在运行")

        @self.app.get("/health")
        async def health():
            """健康检查端点"""
            return ResponseBuilder.success(data={"status": "healthy", "service": "koalaq-hub-api"}, message="服务健康")

        self.logger.info("基础路由配置完成")

    def _setup_business_routes(self):
        """配置业务路由（使用分离的endpoints）"""

        # 用户管理路由 - 使用函数式依赖注入
        users_router = create_users_router(self.user_manager)
        self.app.include_router(users_router)

        # 会话管理路由 - 使用函数式依赖注入
        conversations_router = create_conversations_router(self.conversation_manager)
        self.app.include_router(conversations_router)

        # 智能代理路由 - 无需依赖注入，直接从配置读取
        agent_router = create_agent_router()
        self.app.include_router(agent_router)

        chat_router = create_chat_router(self.agent_executor)
        # Chat API路由 - 新的HTTP聊天接口
        self.app.include_router(chat_router)
        
        # WebSocket路由 - 使用函数式依赖注入
        setup_websocket_routes(self.app,self.user_manager, self.conversation_manager, self.agent_registry, self.agent_executor)

        self.logger.info("业务路由配置完成")

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
def create_fastapi_server(user_manager, conversation_manager, agent_registry=None, agent_executor=None):
    """创建FastAPI服务器实例，直接注入依赖"""
    return FastAPIServer( user_manager, conversation_manager, agent_registry, agent_executor)
