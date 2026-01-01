"""
内置工具模块
包含系统内置的内部工具
"""

from .call_agent import CallAgentTool
from .get_time import GetTimeTool
from .easy_accounts import (
    AccountsTool,
    TypesTool,
    CurrentDateTool,
    YearStatisticsTool,
    FlowsTool,
    AddFlowTool,
    UpdateFlowTool,
    MakeExcelTool,
    GetFlowTool,
)

__all__ = [
    "CallAgentTool",
    "GetTimeTool",
    # EasyAccounts 工具
    "AccountsTool",
    "TypesTool",
    "CurrentDateTool",
    "YearStatisticsTool",
    "FlowsTool",
    "AddFlowTool",
    "UpdateFlowTool",
    "MakeExcelTool",
    "GetFlowTool",
]


def register_builtin_tools():
    """注册所有内置工具

    在应用启动时调用此函数以注册所有内置工具
    """
    # 导入即自动注册（通过 @register_tool 装饰器）
    from . import call_agent
    from . import get_time
    from . import easy_accounts
