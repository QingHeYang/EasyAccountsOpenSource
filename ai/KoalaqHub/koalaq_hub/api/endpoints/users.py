"""
简化的用户管理API端点
使用函数式依赖注入，避免复杂的框架
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from koalaq_hub.api.models.response import ResponseBuilder
from koalaq_hub.core.logging_utils import ManagerLogger


class UserInput(BaseModel):
    """用户输入模型"""

    username: str


def create_users_router(user_manager):
    """
    创建用户管理路由
    使用函数式依赖注入，直接传入user_manager

    Args:
        user_manager: 用户管理器实例

    Returns:
        APIRouter: 配置好的用户路由
    """
    router = APIRouter(prefix="/api/v1/users", tags=["用户管理"])
    logger = ManagerLogger("UsersEndpoint")

    @router.post("/")
    async def create_user(user_input: UserInput):
        """创建用户（无需认证）"""
        try:
            user = user_manager.register_user(user_input.username)
            logger.info("用户创建成功", {"user_id": user.user_id, "username": user.username})

            return ResponseBuilder.created(data=user.model_dump(), message="用户创建成功")
        except ValueError as e:
            logger.warning("用户创建失败", {"error": str(e), "username": user_input.username})
            return JSONResponse(status_code=400, content=ResponseBuilder.bad_request(str(e)).model_dump())
        except Exception as e:
            logger.error("创建用户失败", exception=e, extra_data={"username": user_input.username})
            return JSONResponse(status_code=500, content=ResponseBuilder.internal_error("创建用户失败").model_dump())

    # 将具体路由放在动态路由之前
    @router.get("/list")
    async def list_users():
        """获取用户列表（开发用，生产环境可能需要权限控制）"""
        try:
            # 这里可以添加分页参数
            users = user_manager.list_users() if hasattr(user_manager, "list_users") else []

            logger.info("获取用户列表成功", {"count": len(users)})
            return ResponseBuilder.success(data=users, message="获取用户列表成功")
        except Exception as e:
            logger.error("获取用户列表失败", exception=e)
            return JSONResponse(status_code=500, content=ResponseBuilder.internal_error("获取用户列表失败").model_dump())

    @router.get("/profile/me")
    async def get_current_user_profile(request: Request):
        """获取当前用户信息（需要认证）"""
        try:
            # 由于白名单豁免，需要手动检查认证
            user_id = request.headers.get("user_id") or request.headers.get("User-ID")

            if not user_id:
                logger.warning("缺少user_id请求头")
                return JSONResponse(status_code=401, content=ResponseBuilder.unauthorized("缺少user_id请求头").model_dump())

            # 验证用户是否存在
            user = user_manager.get_user(user_id)
            if not user:
                logger.warning("用户不存在", {"user_id": user_id})
                return JSONResponse(status_code=401, content=ResponseBuilder.unauthorized("用户不存在").model_dump())

            logger.info("获取当前用户信息成功", {"user_id": user.user_id})
            return ResponseBuilder.success(data={"user_id": user.user_id, "username": user.username, "created_at": user.created_at, "total_tokens": user.total_tokens, "prompt_tokens": user.prompt_tokens, "completion_tokens": user.completion_tokens, "reasoning_tokens": user.reasoning_tokens}, message="获取用户信息成功")
        except Exception as e:
            logger.error("获取当前用户信息失败", exception=e)
            return JSONResponse(status_code=500, content=ResponseBuilder.internal_error("获取用户信息失败").model_dump())

    @router.get("/{user_id}")
    async def get_user(user_id: str):
        """获取用户信息（无需认证）"""
        try:
            user = user_manager.get_user(user_id)
            if not user:
                logger.warning("用户不存在", {"user_id": user_id})
                return JSONResponse(status_code=404, content=ResponseBuilder.not_found("用户不存在").model_dump())

            logger.info("获取用户成功", {"user_id": user_id})
            return ResponseBuilder.success(data=user.model_dump(), message="获取用户成功")
        except Exception as e:
            logger.error("获取用户失败", exception=e, extra_data={"user_id": user_id})
            return JSONResponse(status_code=500, content=ResponseBuilder.internal_error("获取用户失败").model_dump())

    logger.info("用户管理路由初始化完成")
    return router
