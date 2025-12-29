"""
智能代理API端点
提供应用代理列表和配置信息
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from koalaq_hub.api.models.response import ResponseBuilder
from koalaq_hub.config.agent_builder import agent_builder
from koalaq_hub.core.agents.agent_registry import agent_registry
from koalaq_hub.core.logging_utils import ManagerLogger


def create_agent_router():
    """
    创建智能代理路由
    
    Returns:
        APIRouter: 配置好的代理路由
    """
    router = APIRouter(prefix="/api/v1/agents", tags=["智能代理"])
    logger = ManagerLogger("AgentEndpoint")

    @router.get("/")
    async def get_agents_list():
        """
        获取所有可用的智能代理列表
        返回agent.ini中配置的所有Agent
        """
        try:
            agents_data = []
            all_agents = agent_builder.get_all_agents()
            
            for agent_id, agent_config in all_agents.items():
                if not agent_config.enable:
                    continue
                    
                # 构建精简的agent信息
                agent_info = {
                    "agent_id": agent_id,
                    "name": agent_config.name,
                    "description": agent_config.description,
                    "enable": agent_config.enable,
                    # 主要功能配置
                    "enable_thinking": agent_config.enable_thinking,
                    "enable_summary": agent_config.enable_summary,
                    "enable_auto_question": agent_config.enable_auto_question,
                    "enable_react_mode": agent_config.enable_react_mode,
                    # LLM配置
                    "llm_use": agent_config.llm_use,
                    "llm_think_use": agent_config.llm_think_use if agent_config.enable_thinking else None,
                    "summary_llm_use": agent_config.summary_llm_use if agent_config.enable_summary else None,
                    # 工具和子Agent配置
                    "mcp_servers": agent_config.mcp_servers,
                    "agent_list": agent_config.agent_list,
                    "has_tools": len(agent_config.mcp_servers) > 0,
                    "has_sub_agents": len(agent_config.agent_list) > 0,
                    # 性能配置
                    "llm_memory_window": agent_config.llm_memory_window,
                    "tool_round": agent_config.tool_round
                }
                agents_data.append(agent_info)
            
            logger.info("获取代理列表成功", {"agents_count": len(agents_data)})
            
            return ResponseBuilder.success(
                data={
                    "agents": agents_data,
                    "total_count": len(agents_data)
                },
                message="获取智能代理列表成功"
            )
            
        except Exception as e:
            logger.error("获取代理列表失败", exception=e)
            return JSONResponse(
                status_code=500,
                content=ResponseBuilder.internal_error("获取代理列表失败").model_dump()
            )

    @router.get("/{agent_id}")
    async def get_agent_detail(agent_id: str):
        """
        获取指定智能代理的详细信息
        
        Args:
            agent_id: 代理ID
        """
        try:
            agent_config = agent_builder.get_agent(agent_id)
            if not agent_config:
                logger.warning("Agent不存在", {"agent_id": agent_id})
                return JSONResponse(
                    status_code=404,
                    content=ResponseBuilder.not_found("指定的智能代理不存在").model_dump()
                )
            if not agent_config.enable:
                logger.warning("该智能代理未启用", {"agent_id": agent_id})
                return JSONResponse(
                    status_code=404,
                    content=ResponseBuilder.not_found("该智能代理未启用").model_dump()
                )
            
            # 构建详细的agent信息
            agent_detail = {
                "agent_id": agent_id,
                "name": agent_config.name,
                "description": agent_config.description,
                "enable": agent_config.enable,
                
                # 功能配置
                "features": {
                    "enable_thinking": agent_config.enable_thinking,
                    "enable_summary": agent_config.enable_summary,
                    "enable_auto_question": agent_config.enable_auto_question,
                    "enable_react_mode": agent_config.enable_react_mode,
                    "react_style": agent_config.react_style if agent_config.enable_react_mode else None
                },
                
                # LLM配置
                "llm_config": {
                    "main_llm": agent_config.llm_use,
                    "thinking_llm": agent_config.llm_think_use if agent_config.enable_thinking else None,
                    "summary_llm": agent_config.summary_llm_use if agent_config.enable_summary else None,
                    "memory_window": agent_config.llm_memory_window
                },
                
                # 工具配置
                "tool_config": {
                    "mcp_servers": agent_config.mcp_servers,
                    "mcp_tool_black_list": agent_config.mcp_tool_black_list,
                    "tool_round": agent_config.tool_round,
                    "tool_tokens": list(agent_config.tool_tokens.keys()) if agent_config.tool_tokens else []
                },
                
                # 子Agent配置
                "sub_agents": {
                    "agent_list": agent_config.agent_list,
                    "has_sub_agents": len(agent_config.agent_list) > 0
                },
                
                # 文件配置
                "files": {
                    "role_file": agent_config.role_file,
                    "agent_guide": agent_config.agent_guide,
                    "task_instructions_file": agent_config.task_instructions_file,
                    "base_modules": agent_config.base_modules
                }
            }
            
            logger.info("获取代理详情成功", {"agent_id": agent_id})
            
            return ResponseBuilder.success(
                data=agent_detail,
                message="获取智能代理详情成功"
            )
            
        except Exception as e:
            logger.error("获取代理详情失败", exception=e, extra_data={"agent_id": agent_id})
            return JSONResponse(
                status_code=500,
                content=ResponseBuilder.internal_error("获取代理详情失败").model_dump()
            )

    @router.get("/available/names")
    async def get_available_agent_names():
        """
        获取所有可用的智能代理名称列表（简化版本）
        仅返回基本信息，用于下拉选择等场景
        """
        try:
            available_agents = agent_builder.get_available_agents()
            
            agents_list = []
            for agent_id in available_agents:
                agent_config = agent_builder.get_agent(agent_id)
                if agent_config:
                    agents_list.append({
                        "agent_id": agent_id,
                        "name": agent_config.name,
                        "description": agent_config.description,
                        "has_tools": len(agent_config.mcp_servers) > 0,
                        "has_sub_agents": len(agent_config.agent_list) > 0
                    })
            
            logger.info("获取代理名称列表成功", {"agents_count": len(agents_list)})
            
            return ResponseBuilder.success(
                data={
                    "agents": agents_list,
                    "total_count": len(agents_list)
                },
                message="获取代理名称列表成功"
            )
            
        except Exception as e:
            logger.error("获取代理名称列表失败", exception=e)
            return JSONResponse(
                status_code=500,
                content=ResponseBuilder.internal_error("获取代理名称列表失败").model_dump()
            )

    @router.get("/status/all")
    async def get_agents_status():
        """
        获取所有已构建的Agent实例状态
        展示运行时的Agent信息，包括使用统计等
        """
        try:
            if not agent_registry:
                logger.warning("Agent注册表未初始化")
                return ResponseBuilder.success(
                    data={"loaded_agents": [], "total_loaded": 0},
                    message="Agent注册表未初始化"
                )
            
            loaded_agents = []
            all_loaded = agent_registry.get_all_agents()
            
            for agent_id, agent in all_loaded.items():
                agent_status = {
                    "agent_id": agent_id,
                    "name": agent.name,
                    "description": agent.description,
                    "is_active": agent.is_active,
                    "created_at": agent.created_at.isoformat(),
                    "last_used_at": agent.last_used_at.isoformat() if agent.last_used_at else None,
                    "usage_count": agent.usage_count,
                    "tools_count": len(agent.available_tools),
                    "available_tools": agent.available_tools[:5],  # 只显示前5个工具
                    "memory_window": agent.memory_window,
                    "has_think_llm": agent.think_llm_client is not None,
                    "has_summary_llm": agent.summary_llm_client is not None,
                }
                loaded_agents.append(agent_status)
            
            # 按使用次数排序
            loaded_agents.sort(key=lambda x: x["usage_count"], reverse=True)
            
            logger.info("获取Agent状态成功", {"loaded_count": len(loaded_agents)})
            
            return ResponseBuilder.success(
                data={
                    "loaded_agents": loaded_agents,
                    "total_loaded": len(loaded_agents),
                    "registry_status": "active"
                },
                message="获取Agent运行状态成功"
            )
            
        except Exception as e:
            logger.error("获取Agent状态失败", exception=e)
            return JSONResponse(
                status_code=500,
                content=ResponseBuilder.internal_error("获取Agent状态失败").model_dump()
            )
    
    @router.get("/status/{agent_id}")
    async def get_agent_runtime_status(agent_id: str):
        """
        获取指定Agent的运行时状态
        
        Args:
            agent_id: Agent ID
        """
        try:
            if not agent_registry:
                logger.warning("Agent注册表未初始化")
                return JSONResponse(
                    status_code=503,
                    content=ResponseBuilder.error(
                        "Agent注册表未初始化",
                        code="SERVICE_UNAVAILABLE"
                    ).model_dump()
                )
            
            agent = agent_registry.get_agent(agent_id)
            if not agent:
                logger.warning("Agent未加载", {"agent_id": agent_id})
                return JSONResponse(
                    status_code=404,
                    content=ResponseBuilder.not_found("Agent未加载到内存中").model_dump()
                )
            
            # 获取详细的运行时信息
            runtime_info = agent.get_info()
            
            # 添加额外的运行时状态
            runtime_info.update({
                "llm_client_status": "connected" if agent.llm_client else "not_initialized",
                "tool_manager_status": "ready" if agent.tool_manager else "not_configured",
                "prompt_loaded": bool(agent.system_prompt or agent.role_prompt),
                "full_prompt_length": len(agent.full_prompt),
            })
            
            logger.info("获取Agent运行时状态成功", {"agent_id": agent_id})
            
            return ResponseBuilder.success(
                data=runtime_info,
                message="获取Agent运行时状态成功"
            )
            
        except Exception as e:
            logger.error("获取Agent运行时状态失败", exception=e, extra_data={"agent_id": agent_id})
            return JSONResponse(
                status_code=500,
                content=ResponseBuilder.internal_error("获取Agent运行时状态失败").model_dump()
            )

    logger.info("智能代理路由初始化完成")
    return router