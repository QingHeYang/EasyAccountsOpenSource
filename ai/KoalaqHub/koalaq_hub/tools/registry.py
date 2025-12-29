"""
工具注册表（工厂）
负责管理所有内部工具的注册和获取
"""

from typing import Dict, List, Optional, Type

from .base import BaseTool, ToolDefinition
from ..core.logging_utils import ManagerLogger


class ToolRegistry:
    """工具注册表 - 单例模式管理所有内部工具"""

    _instance: Optional['ToolRegistry'] = None
    _initialized: bool = False

    def __new__(cls) -> 'ToolRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 避免重复初始化
        if ToolRegistry._initialized:
            return

        self.logger = ManagerLogger("ToolRegistry")
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}

        ToolRegistry._initialized = True
        self.logger.info("工具注册表初始化完成")

    def register(self, tool_class: Type[BaseTool]) -> Type[BaseTool]:
        """注册工具类

        Args:
            tool_class: 工具类（继承自BaseTool）

        Returns:
            原工具类（支持作为装饰器使用）

        Raises:
            ValueError: 如果工具名称为空或已存在
        """
        # 创建实例以获取name
        instance = tool_class()
        tool_name = instance.name

        if not tool_name:
            raise ValueError(f"工具类 {tool_class.__name__} 必须定义 name 属性")

        if tool_name in self._tool_classes:
            self.logger.warning(f"工具 '{tool_name}' 已存在，将被覆盖")

        self._tool_classes[tool_name] = tool_class
        self._tools[tool_name] = instance

        self.logger.info("注册工具", {
            "tool_name": tool_name,
            "tool_class": tool_class.__name__,
            "description": instance.description[:50] + "..." if len(instance.description) > 50 else instance.description
        })

        return tool_class

    def get(self, tool_name: str) -> Optional[BaseTool]:
        """获取工具实例

        Args:
            tool_name: 工具名称

        Returns:
            工具实例，不存在返回None
        """
        return self._tools.get(tool_name)

    def get_definition(self, tool_name: str) -> Optional[ToolDefinition]:
        """获取工具定义

        Args:
            tool_name: 工具名称

        Returns:
            工具定义，不存在返回None
        """
        tool = self.get(tool_name)
        if tool:
            return tool.definition
        return None

    def list_tools(self) -> List[str]:
        """列出所有已注册的工具名称"""
        return list(self._tools.keys())

    def list_definitions(self) -> List[ToolDefinition]:
        """列出所有工具定义"""
        return [tool.definition for tool in self._tools.values()]

    def is_inner_tool(self, tool_name: str) -> bool:
        """判断是否为内部工具

        Args:
            tool_name: 工具名称

        Returns:
            是否为已注册的内部工具
        """
        return tool_name in self._tools

    def unregister(self, tool_name: str) -> bool:
        """注销工具

        Args:
            tool_name: 工具名称

        Returns:
            是否成功注销
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            del self._tool_classes[tool_name]
            self.logger.info(f"注销工具: {tool_name}")
            return True
        return False

    def clear(self):
        """清空所有注册的工具"""
        self._tools.clear()
        self._tool_classes.clear()
        self.logger.info("清空所有工具注册")

    @classmethod
    def reset(cls):
        """重置单例（主要用于测试）"""
        cls._instance = None
        cls._initialized = False


# 全局工具注册表实例
tool_registry = ToolRegistry()


def register_tool(tool_class: Type[BaseTool]) -> Type[BaseTool]:
    """工具注册装饰器

    使用方式:
    ```python
    @register_tool
    @tool(name="my_tool", description="...")
    class MyTool(BaseTool):
        async def execute(self, arguments, context):
            ...
    ```
    """
    return tool_registry.register(tool_class)
