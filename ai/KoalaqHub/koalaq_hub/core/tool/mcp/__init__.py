"""
MCP工具系统
"""

from .mcp_tool import McpTool
from .mcp_tool_manager import ToolManager
from .server_manager import ServerManager
from .server_simple import SimpleServer

# 向后兼容：Server 别名指向 SimpleServer
Server = SimpleServer

__all__ = ['McpTool', 'ToolManager', 'ServerManager', 'SimpleServer', 'Server']