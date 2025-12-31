"""
FastAPI应用配置
集成HTTP拦截器、通用返回类等组件
类似于Java Spring Boot的Application配置类
"""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from koalaq_hub.api.examples.usage_example import router as example_router
from koalaq_hub.api.middleware.http_interceptor import HTTPInterceptorMiddleware, RequestContextMiddleware
from koalaq_hub.api.models.response import ResponseBuilder

logger = logging.getLogger(__name__)


def create_api_app() -> FastAPI:
    """
    创建配置好的FastAPI应用实例

    Returns:
        配置完成的FastAPI应用
    """
    app = FastAPI(title="KoalaQ Hub API", description="智能对话系统API接口", version="1.0.0", docs_url="/docs", redoc_url="/redoc")

    # 配置中间件
    configure_middleware(app)

    # 配置异常处理器
    configure_exception_handlers(app)

    # 配置路由
    configure_routes(app)

    return app


def configure_middleware(app: FastAPI):
    """
    配置中间件

    Args:
        app: FastAPI应用实例
    """
    # 添加请求上下文中间件（最先执行）
    app.add_middleware(RequestContextMiddleware)

    # 添加HTTP拦截器中间件
    app.add_middleware(
        HTTPInterceptorMiddleware,
        enable_auth=True,  # 启用认证
        enable_logging=True,  # 启用日志
    )

    logger.info("中间件配置完成")


def configure_exception_handlers(app: FastAPI):
    """
    配置全局异常处理器
    类似于Java Spring的@ControllerAdvice

    Args:
        app: FastAPI应用实例
    """

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        处理HTTP异常

        Args:
            request: 请求对象
            exc: HTTP异常

        Returns:
            统一格式的错误响应
        """
        request_id = getattr(request.state, "request_id", "unknown")

        return JSONResponse(status_code=exc.status_code, content=ResponseBuilder.custom_error(code=exc.status_code, message=exc.detail, request_id=request_id).model_dump())

    @app.exception_handler(StarletteHTTPException)
    async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
        """
        处理Starlette HTTP异常

        Args:
            request: 请求对象
            exc: Starlette HTTP异常

        Returns:
            统一格式的错误响应
        """
        request_id = getattr(request.state, "request_id", "unknown")

        return JSONResponse(status_code=exc.status_code, content=ResponseBuilder.custom_error(code=exc.status_code, message=exc.detail, request_id=request_id).model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        处理请求验证异常

        Args:
            request: 请求对象
            exc: 验证异常

        Returns:
            统一格式的验证错误响应
        """
        request_id = getattr(request.state, "request_id", "unknown")

        # 提取验证错误详情
        error_details = []
        for error in exc.errors():
            field = ".".join(str(x) for x in error["loc"][1:])  # 跳过'body'
            message = error["msg"]
            error_details.append(f"{field}: {message}")

        return JSONResponse(status_code=422, content=ResponseBuilder.bad_request(message="请求参数验证失败", data={"errors": error_details}, request_id=request_id).model_dump())

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """
        处理所有其他异常

        Args:
            request: 请求对象
            exc: 异常

        Returns:
            统一格式的服务器错误响应
        """
        request_id = getattr(request.state, "request_id", "unknown")

        logger.error(f"未处理的异常 [RequestID: {request_id}]: {str(exc)}", exc_info=True)

        return JSONResponse(status_code=500, content=ResponseBuilder.internal_error(message="服务器内部错误", request_id=request_id).model_dump())

    logger.info("异常处理器配置完成")


def configure_routes(app: FastAPI):
    """
    配置路由

    Args:
        app: FastAPI应用实例
    """

    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查接口"""
        return ResponseBuilder.success(data={"status": "healthy", "service": "koalaq-hub-api"}, message="服务正常")

    @app.get("/")
    async def root():
        """根路径接口"""
        return ResponseBuilder.success(data={"message": "欢迎使用KoalaQ Hub API", "docs": "/docs"}, message="API服务正在运行")

    # 包含示例路由
    app.include_router(example_router)

    logger.info("路由配置完成")


# 用于测试的应用实例
def get_test_app() -> FastAPI:
    """
    创建用于测试的应用实例

    Returns:
        测试用的FastAPI应用
    """
    app = create_api_app()

    # 可以在这里添加测试专用的配置
    # 比如禁用认证、添加测试路由等

    return app


if __name__ == "__main__":
    # 用于开发测试
    import uvicorn

    app = create_api_app()
    uvicorn.run(app, host="0.0.0.0", port=8001)
