"""
简化的WebSocket端点
使用函数式依赖注入，避免复杂的框架
"""

import json

from fastapi import WebSocket

from koalaq_hub.core.agents.agent_executor import AgentExecutor
from koalaq_hub.core.agents.agent_registry import AgentRegistry
from koalaq_hub.core.conversation_manager import ConversationManager
from koalaq_hub.core.logging_utils import ManagerLogger
from koalaq_hub.core.user_manager import UserManager
from koalaq_hub.models.agent import Agent


def create_websocket_handler( user_manager: UserManager, conversation_manager: ConversationManager, agent_registry: AgentRegistry, agent_executor: AgentExecutor):
    """
    创建WebSocket处理函数
    使用函数式依赖注入，直接传入所需的服务

    Args:
        chat_session: 聊天会话管理器实例
        user_manager: 用户管理器实例
        conversation_manager: 会话管理器实例
        agent_registry: Agent注册表实例
        agent_executor: Agent执行器实例

    Returns:
        WebSocket处理函数
    """
    logger = ManagerLogger("WebSocketEndpoint")

    async def websocket_chat_handler(websocket: WebSocket):
        """WebSocket聊天处理函数"""
        conversation_id = None
        user_id = None
        agent_id = None

        try:
            # 从查询参数获取user_id
            user_id = websocket.query_params.get("user_id")
            agent_id = websocket.query_params.get("agent_id")
            tool_tokens = websocket.query_params.get("tool_tokens")
            if not user_id:
                logger.warning("WebSocket连接拒绝：缺少user_id参数")
                await websocket.close(code=4400, reason="缺少user_id参数")
                return
            if not agent_id:
                logger.warning("WebSocket连接拒绝：缺少agent_id参数")
                await websocket.close(code=4400, reason="缺少agent_id参数")
                return
            
            # 验证agent_registry是否存在
            if not agent_registry:
                logger.error("AgentRegistry未初始化")
                await websocket.close(code=5000, reason="服务器内部错误")
                return
            
            user = user_manager.get_user(user_id)
            if not user:
                logger.warning("WebSocket连接拒绝：用户不存在")
                await websocket.close(code=4401, reason="用户不存在")
                return
            
            # 从注册表获取或创建用户的Agent实例
            agent: Agent = await agent_registry.get_or_create_user_agent(user_id, agent_id)
            agent.websocket_mode = True
            if not agent:
                logger.warning("WebSocket连接拒绝：Agent不存在或未启用", {"agent_id": agent_id})
                await websocket.close(code=4402, reason="Agent不存在或未启用")
                return
            
            # 解析tool_tokens参数，使用"|"分割
            if tool_tokens:
                try:
                    token_dict = {}
                    for token_pair in tool_tokens.split("|"):
                        if "=" in token_pair:
                            key, value = token_pair.split("=", 1)
                            token_dict[key.strip()] = value.strip()
                    if token_dict:
                        agent.tool_tokens = token_dict
                        logger.info("WebSocket更新tool_tokens", {"agent_id": agent_id, "tokens_count": len(token_dict)})
                except Exception as e:
                    logger.warning("WebSocket解析tool_tokens失败", {"tool_tokens": tool_tokens, "error": str(e)})
            
            logger.info("WebSocket参数解析", {
                "user_id": user_id,
                "agent_id": agent_id, 
                "tool_tokens_param": tool_tokens,
                "tool_tokens_count": len(agent.tool_tokens)
            })
            
            #agent_builder.print_agent_info(agent_id)

            # 接受WebSocket连接
            await websocket.accept()
            logger.info("WebSocket连接已建立", {"user_id": user_id})

            # 持续监听消息
            while True:
                try:
                    # 接收消息
                    message = await websocket.receive_text()
                    # 解析消息
                    try:
                        data = json.loads(message)
                        
                        # 检查是否为心跳包
                        if data.get("type") == "ping":
                            # 立即回复心跳包，不消耗任何资源
                            await websocket.send_text(json.dumps({"type": "pong"}))
                            continue
                        
                        
                        conversation_id = data.get("conversation_id")
                        content = data.get("content")

                        # 正确解析布尔参数：字符串"true"、"1"、"yes"为True，其他为False
                        if agent.enable_thinking:
                            if data.get("use_think_llm") is not None:
                                agent.use_think_llm = data.get("use_think_llm")
                            else:
                                agent.use_think_llm = False
                        else:
                            agent.use_think_llm = False

                        if not conversation_id:
                            conversation_id = conversation_manager.apply_conversation_id()
                            logger.info("生成新的对话ID", {"conversation_id": conversation_id})

                        agent.current_conversation_id = conversation_id
                        if not content:
                            await websocket.send_text(json.dumps({"error": "缺少content"}))
                            logger.warning("收到无效消息：缺少content", {"user_id": user_id})
                            continue

                        # 保存WebSocket连接并处理消息
                        await agent_executor.websocket_handler.connect(websocket, conversation_id)
                        logger.info("开始处理消息", {"user_id": user_id, "conversation_id": conversation_id, "content_length": len(content)})
                        
                        # 如果配置了use_think_llm，设置到agent上
                        if agent.enable_thinking and data.get("use_think_llm") is not None:
                            agent.use_think_llm = data.get("use_think_llm")
                        
                        # 如果配置了tool_tokens，设置到agent上
                        if hasattr(agent, 'tool_tokens') and agent.tool_tokens:
                            agent.tool_tokens = agent.tool_tokens
                        
                        # 更新Agent使用统计
                        agent.update_usage()
                        
                        # 组装系统提示词并存储到agent
                        system_prompt = agent_registry.build_system_prompt(agent, user_id, conversation_id)
                        agent.system_prompt = system_prompt
                        
                        # 使用agent_executor执行
                        await agent_executor.execute(
                            agent=agent,
                            message=content,
                            conversation_id=conversation_id,
                            user_id=user_id,
                            source='websocket'
                        )

                    except json.JSONDecodeError as e:
                        logger.error(
                            "解析消息失败",
                            exception=e,
                            extra_data={
                                "user_id": user_id,
                                "message": message[:100],  # 只记录前100个字符
                            },
                        )
                        await websocket.send_text(json.dumps({"error": "消息格式无效"}))

                except Exception as e:
                    logger.error("处理消息时出错", exception=e, extra_data={"conversation_id": conversation_id, "user_id": user_id})
                    # 发送错误消息给客户端
                    try:
                        await websocket.send_text(json.dumps({"error": "服务器处理消息时出错"}))
                    except:
                        # 如果连接已断开，立即清理连接和Agent
                        if conversation_id and agent_executor:
                            try:
                                await agent_executor.websocket_handler.disconnect(conversation_id)
                                logger.info("连接断开时立即清理", {"conversation_id": conversation_id})
                            except Exception as cleanup_error:
                                logger.debug("清理连接时出错", extra_data={"error": str(cleanup_error)})
                        
                        # 标记用户Agent为断开状态
                        if user_id and agent_id and agent_registry:
                            try:
                                await agent_registry.mark_agent_disconnected(user_id, agent_id)
                                logger.info("连接断开时标记Agent为断开状态", {"user_id": user_id, "agent_id": agent_id})
                            except Exception as cleanup_error:
                                logger.debug("标记Agent断开状态时出错", extra_data={"error": str(cleanup_error)})
                    break

        except Exception as e:
            logger.error("WebSocket连接出错", exception=e, extra_data={"conversation_id": conversation_id, "user_id": user_id})
        finally:
            # 清理WebSocket连接（防止遗漏清理）
            if conversation_id and agent_executor:
                try:
                    # 检查连接是否还存在，避免重复清理
                    if agent_executor.websocket_handler.is_connected(conversation_id):
                        await agent_executor.websocket_handler.disconnect(conversation_id)
                        logger.info("WebSocket连接已清理", {"user_id": user_id, "conversation_id": conversation_id})
                    else:
                        logger.debug("WebSocket连接已经清理过了", {"user_id": user_id, "conversation_id": conversation_id})
                except Exception as e:
                    logger.error("断开WebSocket连接时出错", exception=e, extra_data={"conversation_id": conversation_id, "user_id": user_id})
            
            # 标记用户的Agent为断开状态
            if user_id and agent_id and agent_registry:
                try:
                    await agent_registry.mark_agent_disconnected(user_id, agent_id)
                    logger.info("用户Agent已标记为断开状态", {"user_id": user_id, "agent_id": agent_id})
                except Exception as e:
                    logger.error("标记Agent断开状态时出错", exception=e, extra_data={"user_id": user_id, "agent_id": agent_id})
            
            # 显式清理 agent 引用，帮助垃圾回收
            agent = None

    logger.info("WebSocket处理器初始化完成")
    return websocket_chat_handler


def setup_websocket_routes(app, user_manager, conversation_manager, agent_registry, agent_executor):
    """
    在FastAPI应用中设置WebSocket路由

    Args:
        app: FastAPI应用实例
        chat_session: 聊天会话管理器实例
        user_manager: 用户管理器实例
        conversation_manager: 会话管理器实例
        agent_registry: Agent注册表实例
        agent_executor: Agent执行器实例
    """
    logger = ManagerLogger("WebSocketSetup")

    # 创建WebSocket处理函数
    websocket_handler = create_websocket_handler( user_manager, conversation_manager, agent_registry, agent_executor)

    # 注册WebSocket路由
    @app.websocket("/ws/chat")
    async def websocket_chat(websocket: WebSocket):
        """WebSocket聊天端点"""
        await websocket_handler(websocket)

    logger.info("WebSocket路由设置完成", {"endpoint": "/ws/chat"})
