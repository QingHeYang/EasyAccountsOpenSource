"""
系统配置和统计API端点
提供系统配置信息和使用统计查询
"""

import os

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

from koalaq_hub.api.models.response import ResponseBuilder
from koalaq_hub.core.logging_utils import ManagerLogger


def create_config_router(user_manager, conversation_manager, repository_adapter):
    """
    创建系统配置路由

    Args:
        user_manager: 用户管理器
        conversation_manager: 对话管理器
        repository_adapter: 数据库适配器

    Returns:
        APIRouter: 配置好的路由
    """
    router = APIRouter(prefix="/api/v1/config", tags=["系统配置"])
    logger = ManagerLogger("ConfigEndpoint")

    @router.get("/stats")
    async def get_user_stats(user_id: str = Header(None, alias="user_id")):
        """
        获取用户使用统计和系统配置

        返回：
        - token使用量（从users表）
        - 对话数
        - 工具调用数
        - MCP配置状态
        """
        try:
            if not user_id:
                return JSONResponse(
                    status_code=400,
                    content=ResponseBuilder.bad_request("缺少user_id请求头").model_dump()
                )

            # 1. 获取用户信息（包含token统计）
            user = repository_adapter.get_user(user_id)
            if not user:
                # 用户不存在，返回空统计
                token_stats = {
                    "total_tokens": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "reasoning_tokens": 0
                }
            else:
                token_stats = {
                    "total_tokens": user.total_tokens or 0,
                    "prompt_tokens": user.prompt_tokens or 0,
                    "completion_tokens": user.completion_tokens or 0,
                    "reasoning_tokens": user.reasoning_tokens or 0
                }

            # 2. 获取对话数
            conversation_count = repository_adapter.get_user_conversations_count(user_id)

            # 3. 获取工具调用数
            tool_call_count = repository_adapter.get_user_tool_call_count(user_id)

            # 4. 获取MCP配置
            mcp_enabled = os.getenv("MCP_SERVER_ENABLED", "false").lower() == "true"
            mcp_transport_mode = os.getenv("MCP_TRANSPORT_MODE", "sse").lower()

            stats_data = {
                "token": token_stats,
                "conversation_count": conversation_count,
                "tool_call_count": tool_call_count,
                "mcp": {
                    "enabled": mcp_enabled,
                    "transport_mode": mcp_transport_mode
                }
            }

            logger.info("获取用户统计", {
                "user_id": user_id,
                "total_tokens": token_stats["total_tokens"],
                "conversations": conversation_count,
                "tool_calls": tool_call_count
            })

            return ResponseBuilder.success(
                data=stats_data,
                message="获取统计成功"
            )

        except Exception as e:
            logger.error("获取用户统计失败", exception=e, extra_data={"user_id": user_id})
            return JSONResponse(
                status_code=500,
                content=ResponseBuilder.internal_error("获取统计失败").model_dump()
            )

    logger.info("系统配置路由初始化完成")
    return router
