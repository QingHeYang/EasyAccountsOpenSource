"""
工具管理器模块 - 重构版
职责：
1. 根据应用配置筛选可用工具
2. 生成工具提示词供LLM使用
3. 管理工具黑名单
4. 提供工具预处理器接口
"""

from typing import Dict, List, Protocol

from ....config.settings import config
from ....models.agent import Agent
from ...logging_utils import ManagerLogger
from .mcp_tool import McpTool


class ToolPreprocessor(Protocol):
    """工具预处理器接口"""

    def should_handle(self, tool_name: str) -> bool:
        """判断是否需要处理此工具"""
        ...

    def preprocess_arguments(self, agent: Agent, tool_name: str, 
                           arguments: dict, conversation_id: str) -> dict:
        """预处理工具参数"""
        ...


class TextToSpeechPreprocessor:
    """文本转语音工具预处理器"""

    def should_handle(self, tool_name: str) -> bool:
        return tool_name == "text_to_speech"

    def preprocess_arguments(self, agent: Agent, tool_name: str, 
                           arguments: dict, conversation_id: str) -> dict:
        """为text_to_speech工具添加conversation_id参数"""
        arguments = arguments.copy()
        arguments["conversation_id"] = conversation_id
        return arguments


class ToolManager:
    """工具管理器 - 负责工具筛选和提示词生成"""

    def __init__(self, server_manager: "ServerManager", websocket_handler=None):
        """初始化工具管理器

        Args:
            server_manager: 服务器管理器，提供工具和服务器映射
            websocket_handler: WebSocket处理器（保留参数以兼容，但不再使用）
        """
        self.server_manager = server_manager
        self.logger = ManagerLogger("ToolManager")

        # 工具预处理器注册
        self.preprocessors: List[ToolPreprocessor] = [TextToSpeechPreprocessor()]

        # 移除工具缓存，每次都从 ServerManager 获取最新数据
        # 这样可以避免缓存同步问题，ServerManager 已经维护了工具列表

    async def get_tools_for_application(self, agent: Agent) -> List[McpTool]:
        """根据应用配置筛选可用工具

        Args:
            agent: Agent实例

        Returns:
            List[McpTool]: 可用工具列表
        """
        # 每次都从 ServerManager 获取最新的工具列表
        # 不再使用缓存，确保工具描述始终是最新的
        all_tools = await self.server_manager.get_tools_by_server(agent.mcp_servers)

        # 获取应用黑名单
        blacklist = self._get_application_blacklist(agent)

        # 过滤工具
        filtered_tools = []
        for tool in all_tools:
            if tool.name not in blacklist:
                filtered_tools.append(tool)

        self.logger.debug(
            "为应用筛选工具（实时获取）",
            {
                "agent_id": agent.agent_id,
                "total_tools": len(all_tools),
                "filtered_tools": len(filtered_tools),
                "blacklist_count": len(blacklist),
            },
        )

        return filtered_tools

    def _get_application_blacklist(self, agent: Agent) -> List[str]:
        """获取应用的工具黑名单

        Args:
            agent: Agent实例

        Returns:
            List[str]: 黑名单工具名称列表
        """
        blacklist = []

        # 全局黑名单
        global_blacklist = getattr(config, "tool_black_list", [])
        if global_blacklist:
            blacklist.extend(global_blacklist)

        # 应用特定黑名单
        if agent.agent_id:
            agent_blacklist = agent.mcp_tool_black_list
            if agent_blacklist:
                blacklist.extend(agent_blacklist)

        return list(set(blacklist))  # 去重


    def clear_cache(self, agent: Agent):
        """清除缓存

        Args:
            agent: Agent实例
        """
        # 保留此方法以保持向后兼容
        # 但由于已移除工具缓存，此方法现在是空操作
        self.logger.debug("clear_cache 调用（已移除缓存机制）", {
            "agent_id": agent.agent_id if agent else None
        })
        pass

    def preprocess_tool_arguments(self, agent: Agent, tool_name: str, 
                                arguments: dict, conversation_id: str) -> dict:
        """预处理工具参数（供executor使用）

        Args:
            agent: Agent实例
            tool_name: 工具名称
            arguments: 原始参数
            conversation_id: 会话ID

        Returns:
            dict: 处理后的参数
        """
        processed_arguments = arguments.copy()

        for preprocessor in self.preprocessors:
            if preprocessor.should_handle(tool_name):
                processed_arguments = preprocessor.preprocess_arguments(
                    agent, tool_name, processed_arguments, conversation_id
                )
                self.logger.debug(
                    "工具参数预处理",
                    {
                        "tool_name": tool_name,
                        "preprocessor": preprocessor.__class__.__name__,
                    },
                )

        return processed_arguments

    def is_tool_allowed(self, agent: Agent, tool_name: str) -> bool:
        """检查工具是否被允许使用

        Args:
            agent: Agent实例
            tool_name: 工具名称

        Returns:
            bool: 是否允许使用
        """
        blacklist = self._get_application_blacklist(agent)
        return tool_name not in blacklist

