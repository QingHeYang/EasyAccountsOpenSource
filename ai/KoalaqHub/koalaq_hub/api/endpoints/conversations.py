"""
会话管理API端点
提供会话列表、详情、搜索等功能
"""

from typing import List, Optional

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from koalaq_hub.api.models.response import ResponseBuilder
from koalaq_hub.config.agent_builder import agent_builder
from koalaq_hub.core.conversation_manager import ConversationManager
from koalaq_hub.core.logging_utils import ManagerLogger


class UpdateTitleRequest(BaseModel):
    """更新对话标题请求模型"""
    title: str

def create_conversations_router(conversation_manager: ConversationManager, agent_executor=None):
    """
    创建会话管理路由
    使用函数式依赖注入，直接传入conversation_manager

    Args:
        conversation_manager: 会话管理器实例
        agent_executor: Agent执行器实例（用于停止功能）

    Returns:
        APIRouter: 配置好的会话路由
    """
    router = APIRouter(prefix="/api/v1/conversations", tags=["会话管理"])
    logger = ManagerLogger("ConversationsEndpoint")

    def get_user_from_request(request: Request):
        """从请求中获取用户信息（中间件会设置）"""
        user = getattr(request.state, "user", None)
        if not user:
            raise ValueError("用户认证失败，请检查user_id请求头")
        return user

    @router.get("/")
    async def get_user_conversations(request: Request, page: int = Query(1, ge=1, description="页码，从1开始"), page_size: int = Query(20, ge=1, le=100, description="每页大小，1-100"), search: Optional[str] = Query(None, description="搜索关键词"), application_names: Optional[List[str]] = Query(None, description="应用名称列表，用于筛选对话")):
        """
        获取当前用户的会话列表
        支持分页、搜索和应用筛选功能
        """
        try:
            user = get_user_from_request(request)
            user_id = user.user_id

            # 如果有搜索关键词，使用搜索功能
            if search and search.strip():
                result = conversation_manager.search_conversations(user_id=user_id, keyword=search.strip(), page=page, page_size=page_size)
                logger.info("搜索用户会话成功", {"user_id": user_id, "keyword": search, "page": page, "total_found": result["pagination"]["total_count"]})
            else:
                # 普通分页获取，支持应用筛选
                if application_names:
                    # 验证agent_builder是否存在
                    if not agent_builder:
                        logger.error("获取会话列表失败：AgentBuilder未初始化")
                        return JSONResponse(status_code=500, content=ResponseBuilder.internal_error("AgentBuilder未初始化").model_dump())
                    
                    for app_name in application_names:
                        agent_config = agent_builder.get_agent(app_name)
                        if agent_config and not agent_config.enable:   
                            application_names.remove(app_name)
                if not application_names:
                    return ResponseBuilder.success(data=[], message="没有可用的agents，当前agents已被禁用")
                result = conversation_manager.get_user_conversations(user_id=user_id, application_names=application_names, page=page, page_size=page_size)
                logger.info("获取用户会话列表成功", {"user_id": user_id, "application_names": application_names, "page": page, "total_count": result["pagination"]["total_count"]})

            return ResponseBuilder.success(data=result, message="获取会话列表成功")

        except ValueError as e:
            logger.warning("获取会话列表参数错误", {"error": str(e), "page": page, "page_size": page_size, "search": search})
            return JSONResponse(status_code=400, content=ResponseBuilder.bad_request(str(e)).model_dump())
        # 移除HTTPException重新抛出，中间件已处理认证
        except Exception as e:
            logger.error("获取会话列表失败", exception=e, extra_data={"page": page, "page_size": page_size, "search": search})
            return JSONResponse(status_code=500, content=ResponseBuilder.internal_error("获取会话列表失败").model_dump())

    @router.get("/{conversation_id}")
    async def get_conversation_detail(conversation_id: str, request: Request):
        """
        获取指定会话的详细信息
        """
        try:
            user = get_user_from_request(request)
            user_id = user.user_id

            # 获取会话详情
            conversation = conversation_manager.get_conversation_detail(user_id=user_id, conversation_id=conversation_id)

            if not conversation:
                logger.warning("会话不存在或无权限访问", {"user_id": user_id, "conversation_id": conversation_id})
                return JSONResponse(status_code=404, content=ResponseBuilder.not_found("会话不存在或无权限访问").model_dump())

            logger.info("获取会话详情成功", {"user_id": user_id, "conversation_id": conversation_id})

            return ResponseBuilder.success(data=conversation, message="获取会话详情成功")

        # 移除HTTPException重新抛出，中间件已处理认证
        except Exception as e:
            logger.error("获取会话详情失败", exception=e, extra_data={"conversation_id": conversation_id})
            return JSONResponse(status_code=500, content=ResponseBuilder.internal_error("获取会话详情失败").model_dump())

    @router.get("/statistics/overview")
    async def get_user_conversation_statistics(request: Request):
        """
        获取当前用户的会话统计信息
        """
        try:
            user = get_user_from_request(request)
            user_id = user.user_id

            # 获取统计信息
            statistics = conversation_manager.get_conversation_statistics(user_id)

            logger.info("获取会话统计成功", {"user_id": user_id, "total_conversations": statistics["total_conversations"]})

            return ResponseBuilder.success(data=statistics, message="获取会话统计成功")

        # 移除HTTPException重新抛出，中间件已处理认证
        except Exception as e:
            logger.error("获取会话统计失败", exception=e)
            return JSONResponse(status_code=500, content=ResponseBuilder.internal_error("获取会话统计失败").model_dump())

    # 开发和调试用的端点（生产环境可能需要权限控制）
    @router.get("/debug/all")
    async def debug_list_all_conversations(limit: int = Query(50, ge=1, le=100, description="返回记录数限制")):
        """
        调试用：获取所有会话（仅开发环境使用）
        注意：生产环境应该移除或添加管理员权限控制
        """
        try:
            # 这里可以添加管理员权限验证
            # 暂时为了开发方便，不做权限控制

            logger.warning("使用调试接口获取所有会话", {"limit": limit})

            # 可以在这里实现获取所有会话的逻辑
            # 目前暂时返回空数据
            return ResponseBuilder.success(data={"conversations": [], "message": "调试接口：功能待实现"}, message="调试接口调用成功")

        except Exception as e:
            logger.error("调试接口调用失败", exception=e)
            return JSONResponse(status_code=500, content=ResponseBuilder.internal_error("调试接口调用失败").model_dump())

    @router.get("/{conversation_id}/messages")
    async def get_conversation_messages(conversation_id: str, request: Request, before_round_id: Optional[str] = Query(None, description="获取此轮次ID之前的消息（分页）"), limit: int = Query(20, ge=1, le=100, description="每页消息数量，1-100")):
        """
        获取指定对话的消息列表（分页）
        """
        try:
            user = get_user_from_request(request)
            user_id = user.user_id

            # 获取消息列表
            result = conversation_manager.get_conversation_messages(user_id=user_id, conversation_id=conversation_id, before_round_id=before_round_id, limit=limit)

            logger.info("获取对话消息列表成功", {"user_id": user_id, "conversation_id": conversation_id, "message_count": len(result["messages"]), "has_more": result["pagination"]["has_more"]})

            return ResponseBuilder.success(data=result, message="获取消息列表成功")

        except ValueError as e:
            logger.warning("获取消息列表参数错误", {"error": str(e), "conversation_id": conversation_id, "before_round_id": before_round_id, "limit": limit})
            return JSONResponse(status_code=400, content=ResponseBuilder.bad_request(str(e)).model_dump())
        except Exception as e:
            logger.error("获取消息列表失败", exception=e, extra_data={"conversation_id": conversation_id, "before_round_id": before_round_id, "limit": limit})
            return JSONResponse(status_code=500, content=ResponseBuilder.internal_error("获取消息列表失败").model_dump())

    @router.delete("/{conversation_id}")
    async def delete_conversation(conversation_id: str, request: Request):
        """
        软删除指定对话
        """
        try:
            user = get_user_from_request(request)
            user_id = user.user_id

            # 执行软删除
            success = conversation_manager.delete_conversation(user_id, conversation_id)
            
            if success:
                logger.info("对话删除成功", {"user_id": user_id, "conversation_id": conversation_id})
                return ResponseBuilder.success(data={"conversation_id": conversation_id}, message="对话删除成功")
            else:
                logger.warning("对话不存在或无权限删除", {"user_id": user_id, "conversation_id": conversation_id})
                return JSONResponse(status_code=404, content=ResponseBuilder.not_found("对话不存在或无权限删除").model_dump())

        except Exception as e:
            logger.error("删除对话失败", exception=e, extra_data={"conversation_id": conversation_id})
            return JSONResponse(status_code=500, content=ResponseBuilder.internal_error("删除对话失败").model_dump())
    
    @router.put("/{conversation_id}/title")
    async def update_conversation_title(conversation_id: str, request: Request, title_request: UpdateTitleRequest):
        """
        更新对话标题
        """
        try:
            user = get_user_from_request(request)
            user_id = user.user_id

            # 执行标题更新
            success = conversation_manager.update_conversation_title(user_id, conversation_id, title_request.title)
            
            if success:
                logger.info("对话标题更新成功", {"user_id": user_id, "conversation_id": conversation_id, "title": title_request.title})
                return ResponseBuilder.success(data={"conversation_id": conversation_id, "title": title_request.title}, message="对话标题更新成功")
            else:
                logger.warning("对话不存在或无权限修改", {"user_id": user_id, "conversation_id": conversation_id})
                return JSONResponse(status_code=404, content=ResponseBuilder.not_found("对话不存在或无权限修改").model_dump())

        except ValueError as e:
            logger.warning("更新对话标题参数错误", {"error": str(e), "conversation_id": conversation_id, "title": title_request.title})
            return JSONResponse(status_code=400, content=ResponseBuilder.bad_request(str(e)).model_dump())
        except Exception as e:
            logger.error("更新对话标题失败", exception=e, extra_data={"conversation_id": conversation_id, "title": title_request.title})
            return JSONResponse(status_code=500, content=ResponseBuilder.internal_error("更新对话标题失败").model_dump())

    @router.post("/apply_id")
    async def apply_conversation_id():
        """
        申请新的对话ID
        生成新的UUID作为conversation_id
        无需认证，任何人都可以申请
        """
        try:
            import uuid

            conversation_id = f"conv_{uuid.uuid4()}"

            logger.info("生成新的对话ID", {"conversation_id": conversation_id})

            return ResponseBuilder.success(data={"conversation_id": conversation_id}, message="申请对话ID成功")

        except Exception as e:
            logger.error("申请对话ID失败", exception=e)
            return JSONResponse(status_code=500, content=ResponseBuilder.internal_error("申请对话ID失败").model_dump())

    @router.post("/stop/{conversation_id}")
    async def stop_conversation(
        conversation_id: str,
        cascade: bool = Query(True, description="是否级联停止子对话（默认True）")
    ):
        """
        停止指定会话的 LLM 生成

        通过独立的 HTTP 通道发送停止信号，避免被 WebSocket 高速数据流淹没。

        Args:
            conversation_id: 要停止的会话 ID
            cascade: 是否级联停止子对话（默认True）
                     当为 True 时，会同时停止所有通过 call_agent 调用的子Agent

        Returns:
            成功/失败状态
        """
        try:
            if not agent_executor:
                logger.error("停止会话失败：AgentExecutor未初始化")
                return JSONResponse(
                    status_code=500,
                    content=ResponseBuilder.internal_error("停止功能未启用").model_dump()
                )

            # 调用 agent_executor 的 stop 方法
            success = await agent_executor.stop(conversation_id, cascade=cascade)

            if success:
                logger.info("停止会话成功", {
                    "conversation_id": conversation_id,
                    "cascade": cascade
                })
                return ResponseBuilder.success(
                    data={
                        "conversation_id": conversation_id,
                        "stopped": True,
                        "cascade": cascade
                    },
                    message="已发送停止信号" + ("（含子对话）" if cascade else "")
                )
            else:
                logger.warning("停止会话：未找到活跃任务", {"conversation_id": conversation_id})
                return ResponseBuilder.success(
                    data={"conversation_id": conversation_id, "stopped": False},
                    message="未找到正在执行的任务"
                )

        except Exception as e:
            logger.error("停止会话失败", exception=e, extra_data={"conversation_id": conversation_id})
            return JSONResponse(
                status_code=500,
                content=ResponseBuilder.internal_error("停止会话失败").model_dump()
            )

    logger.info("会话管理路由初始化完成")
    return router
