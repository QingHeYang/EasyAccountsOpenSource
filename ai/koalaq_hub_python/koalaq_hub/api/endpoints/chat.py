from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from ...api.models.response import ApiResponse, ResponseBuilder
from ...config.agent_builder import agent_builder
from ...core.agents.agent_executor import AgentExecutor
from ...core.logging_utils import ManagerLogger

router = APIRouter()
logger = ManagerLogger("ChatAPI")


class ChatRequest(BaseModel):
    """聊天请求模型"""

    conversation_id: str
    app_id: str  # 应用ID
    content: str
    use_think_llm: bool = False
    is_mcp: bool = False # 是否是MCP模式，如果是MCP模式，则不进行总结 & MCP是单轮对话
    tool_tokens: Optional[str] = None  # 工具Token配置，格式："key1=value1|key2=value2"


def create_chat_router(agent_executor: AgentExecutor):
    router = APIRouter(prefix="/api/v1/chat", tags=["聊天管理"])
    logger = ManagerLogger("ChatEndpoint")

    @router.post("/chat", response_model=ApiResponse)
    async def chat_message(request: ChatRequest, user_id: str = Header(..., description="用户ID")) -> ApiResponse:
        """
        HTTP聊天接口 - 阻塞式返回完整结果

        Args:
            request: 聊天请求
            user_id: 用户ID(从Header获取)

        Returns:
            ChatResponse: 完整的聊天响应
        """
        try:
            # 验证agent_builder是否存在
            if not agent_builder:
                logger.error("AgentBuilder未初始化")
                raise HTTPException(status_code=500, detail="服务器内部错误：AgentBuilder未初始化")
            
            # 验证应用配置
            app_config = agent_builder.get_agent(request.app_id)
            if not app_config:
                raise HTTPException(status_code=400, detail=f"应用配置不存在: {request.app_id}")
            if not app_config.enable:
                raise HTTPException(status_code=400, detail=f"该智能代理未启用: {request.app_id}")

            if request.is_mcp:
                app_config.enable_summary = False
                request.conversation_id = await apply_conversation_id()
            if app_config.enable_thinking:
                if request.use_think_llm is not None:
                    app_config.use_think_llm = request.use_think_llm
                else:
                    app_config.use_think_llm = False
            else:
                app_config.use_think_llm = False
            
            # 解析tool_tokens参数，使用"|"分割
            if request.tool_tokens:
                try:
                    token_dict = {}
                    for token_pair in request.tool_tokens.split("|"):
                        if "=" in token_pair:
                            key, value = token_pair.split("=", 1)
                            token_dict[key.strip()] = value.strip()
                    if token_dict:
                        app_config.tool_tokens = token_dict
                        logger.info("HTTP更新tool_tokens", {"app_id": request.app_id, "tokens_count": len(token_dict)})
                except Exception as e:
                    logger.warning("HTTP解析tool_tokens失败", {"tool_tokens": request.tool_tokens, "error": str(e)})
            # 处理消息 - 指定来源为HTTP
            result = await chat_manager.process_message(
                message=request.content, 
                user_id=user_id, 
                conversation_id=request.conversation_id, 
                app_config=app_config,
                source="http")

            return ResponseBuilder.success(data=result)

        except Exception as e:
            logger.error("HTTP聊天请求处理失败", exception=e, extra_data={"user_id": user_id, "conversation_id": request.conversation_id, "application": request.application})
            raise HTTPException(status_code=500, detail=f"聊天处理失败: {str(e)}")

    async def apply_conversation_id():
        """
        申请新的对话ID
        生成新的UUID作为conversation_id
        无需认证，任何人都可以申请
        """
        try:
            import uuid
            conversation_id = f"mcp_conv_{uuid.uuid4()}"
            return conversation_id
        except Exception as e:
            logger.error("申请对话ID失败", exception=e)
            raise HTTPException(status_code=500, detail=f"申请对话ID失败: {str(e)}")
        
    logger.info("聊天管理路由初始化完成")
    return router