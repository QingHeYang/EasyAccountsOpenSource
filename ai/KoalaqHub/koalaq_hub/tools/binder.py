"""
Agent-工具绑定器
负责管理Agent与内部工具的绑定关系，替代InnerToolManager
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .registry import tool_registry
from ..core.logging_utils import ManagerLogger

if TYPE_CHECKING:
    from ..models.agent import Agent


class AgentToolBinder:
    """Agent-工具绑定器 - 管理Agent可用的内部工具"""

    def __init__(self):
        """初始化绑定器"""
        self.logger = ManagerLogger("AgentToolBinder")
        self.registry = tool_registry

    def get_tools_for_agent(self, agent: 'Agent') -> List[Dict[str, Any]]:
        """获取Agent可用的内部工具列表（Function Calling格式）

        根据Agent的配置，返回该Agent可用的内部工具定义

        Args:
            agent: Agent实例

        Returns:
            内部工具定义列表（Function Calling格式）
        """
        tools = []

        # 1. 根据 agent.inner_tools 配置绑定内部工具
        for tool_name in agent.inner_tools:
            if tool_name == "call_agent":
                # call_agent 需要特殊处理（动态设置可调用的agent列表）
                continue
            tool_def = self.get_tool_definition(tool_name)
            if tool_def:
                tools.append(tool_def)
            else:
                self.logger.warning(f"内部工具未注册: {tool_name}", {
                    "agent_id": agent.agent_id
                })

        # 2. 检查是否需要call_agent工具（仅当Agent有子Agent列表时）
        if agent.agent_list:
            call_agent_tool = self._build_call_agent_tool(agent)
            if call_agent_tool:
                tools.append(call_agent_tool)

        if tools:
            self.logger.info("为Agent构建内部工具列表", {
                "agent_id": agent.agent_id,
                "tool_count": len(tools),
                "tools": [t["function"]["name"] for t in tools]
            })

        return tools

    def _build_call_agent_tool(self, agent: 'Agent') -> Optional[Dict[str, Any]]:
        """构建call_agent工具定义

        Args:
            agent: Agent实例（包含agent_list）

        Returns:
            call_agent工具定义，如果工具未注册则返回None
        """
        tool = self.registry.get("call_agent")
        if not tool:
            self.logger.warning("call_agent工具未注册")
            return None

        # 使用动态参数设置agent_id的可选值
        return tool.definition.to_function_calling_format(
            agent_id_enum=agent.agent_list
        )

    def get_tool_definition(self, tool_name: str, **dynamic_params) -> Optional[Dict[str, Any]]:
        """获取指定工具的Function Calling定义

        Args:
            tool_name: 工具名称
            **dynamic_params: 动态参数

        Returns:
            工具定义，不存在返回None
        """
        tool = self.registry.get(tool_name)
        if tool:
            return tool.definition.to_function_calling_format(**dynamic_params)
        return None

    def is_inner_tool(self, tool_name: str) -> bool:
        """判断是否为内部工具

        Args:
            tool_name: 工具名称

        Returns:
            是否为内部工具
        """
        return self.registry.is_inner_tool(tool_name)

    def list_available_tools(self) -> List[str]:
        """列出所有可用的内部工具名称"""
        return self.registry.list_tools()


# 全局绑定器实例
agent_tool_binder = AgentToolBinder()
