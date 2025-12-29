"""
内部工具管理器
负责管理系统内部工具，如Agent调用等
"""

from typing import Any, Dict, List

from ....models.agent import Agent
from ...logging_utils import ManagerLogger
from .easyaccounts import EASYACCOUNTS_TOOLS, EasyAccountsTools, get_tool_names


class InnerToolManager:
    """内部工具管理器 - 负责管理内部Function Calling工具"""
    
    def __init__(self):
        """初始化内部工具管理器"""
        self.logger = ManagerLogger("InnerToolManager")
        # 初始化 EasyAccounts 工具实例
        self.easyaccounts_tools = EasyAccountsTools()
        # 获取所有 EasyAccounts 工具名称
        self.easyaccounts_tool_names = get_tool_names()
    
    def get_tools_for_agent(self, agent: Agent) -> List[Dict[str, Any]]:
        """获取Agent可用的内部工具列表
        
        Args:
            agent: Agent实例
            
        Returns:
            内部工具定义列表（Function Calling格式）
        """
        tools = []
        
        # 添加 EasyAccounts 工具
        tools.extend(EASYACCOUNTS_TOOLS)
        
        # 如果Agent有子Agent列表，添加ask_agent工具
        if agent.agent_list:
            ask_agent_tool = self._build_ask_agent_tool(agent.agent_list)
            tools.append(ask_agent_tool)
        
        self.logger.info("构建内部工具列表", {
            "agent_id": agent.agent_id,
            "easyaccounts_tools": self.easyaccounts_tool_names,
            "sub_agents": agent.agent_list if agent.agent_list else [],
            "tool_count": len(tools)
        })
        
        return tools
    
    def _build_ask_agent_tool(self, agent_list: List[str]) -> Dict[str, Any]:
        """构建ask_agent工具定义
        
        Args:
            agent_list: 可用的子Agent ID列表
            
        Returns:
            ask_agent工具的Function Calling定义
        """
        return {
            "type": "function",
            "function": {
                "name": "call_agent",
                "description": "调用其他智能助手来协助完成特定任务",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "description": "要调用的智能助手ID",
                            "enum": agent_list  # 动态填充可用的agent列表
                        },
                        "task": {
                            "type": "string",
                            "description": "需要该智能助手完成的具体任务描述"
                        },
                        "context": {
                            "type": "object",
                            "description": "传递给智能助手的上下文信息（可选）",
                            "additionalProperties": True
                        }
                    },
                    "required": ["agent_id", "task"]
                }
            }
        }
    
    def is_inner_tool(self, tool_name: str) -> bool:
        """判断是否为内部工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            是否为内部工具
        """
        # 检查是否为 EasyAccounts 工具或 call_agent
        return tool_name in self.easyaccounts_tool_names or tool_name == "call_agent"