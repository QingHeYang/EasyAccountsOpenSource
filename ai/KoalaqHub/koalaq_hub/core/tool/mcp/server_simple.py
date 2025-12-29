"""
简化版MCP服务器连接管理器

避免AsyncExitStack跨任务问题的简单实现。
"""

from typing import Any, Optional

from mcp import ClientSession
from mcp.client.sse import sse_client

from ...logging_utils import ManagerLogger
from .mcp_tool import McpTool


class SimpleServer:
    """简化版MCP服务器连接管理器
    
    核心理念：
    1. 不使用AsyncExitStack
    2. 不保持长期连接，每次操作时重新连接
    3. 使用async with确保资源在同一任务中被清理
    """
    
    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name = name
        self.config = config
        self.url = config.get("url", "")
        self.timeout = int(config.get("timeout", 120))
        self.logger = ManagerLogger("SimpleServer")
        
        # 状态标志
        self._is_available = False
        self._last_error: Optional[str] = None
        
        # 缓存工具列表
        self._tools_cache: list[McpTool] = []
        self._tools_cache_valid = False
        
        self.logger.info(f"SimpleServer实例创建: {name}")
    
    async def test_connection(self) -> bool:
        """测试连接是否可用
        
        Returns:
            连接是否成功
        """
        try:
            async with sse_client(url=self.url, timeout=self.timeout) as transport:
                read_stream, write_stream = transport
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    self._is_available = True
                    self._last_error = None
                    self.logger.info(f"连接测试成功: {self.name}")
                    return True
                    
        except Exception as e:
            self._is_available = False
            self._last_error = str(e)
            self.logger.error(f"连接测试失败 {self.name}: {e}")
            return False
    
    async def list_tools(self) -> list[McpTool]:
        """列出服务器可用的工具
        
        Returns:
            可用工具列表
        """
        # 如果缓存有效，直接返回
        if self._tools_cache_valid:
            return self._tools_cache
        
        try:
            # 每次都创建新连接，确保在同一任务中完成
            async with sse_client(url=self.url, timeout=self.timeout) as transport:
                read_stream, write_stream = transport
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    # 获取工具列表
                    tools_response = await session.list_tools()
                    tools = []
                    
                    for item in tools_response:
                        if isinstance(item, tuple) and item[0] == "tools":
                            tools.extend(
                                McpTool(tool.name, tool.description, tool.inputSchema) 
                                for tool in item[1]
                            )
                    
                    # 更新缓存
                    self._tools_cache = tools
                    self._tools_cache_valid = True
                    self._is_available = True
                    
                    self.logger.info(f"获取工具列表成功 {self.name}: {len(tools)} 个工具")
                    return tools
                    
        except Exception as e:
            self._is_available = False
            self._last_error = str(e)
            self.logger.error(f"获取工具列表失败 {self.name}: {e}")
            # 返回缓存的工具（如果有）
            return self._tools_cache
    
    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """执行工具
        
        Args:
            tool_name: 要执行的工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
            
        Raises:
            RuntimeError: 如果执行失败
        """
        try:
            self.logger.info(f"正在执行工具 {tool_name} @ {self.name}")
            
            # 每次都创建新连接
            async with sse_client(url=self.url, timeout=self.timeout) as transport:
                read_stream, write_stream = transport
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    # 执行工具
                    result = await session.call_tool(tool_name, arguments)
                    
                    self._is_available = True
                    self.logger.info(f"工具执行成功 {tool_name} @ {self.name}")
                    return result
                    
        except Exception as e:
            self._is_available = False
            self._last_error = str(e)
            error_msg = f"工具执行失败 {tool_name} @ {self.name}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    async def initialize(self) -> None:
        """初始化服务器连接
        
        对于简化版，只是测试连接是否可用。
        """
        success = await self.test_connection()
        if not success:
            raise RuntimeError(f"无法连接到服务器 {self.name}: {self._last_error}")
    
    async def cleanup(self) -> None:
        """清理服务器资源
        
        对于简化版，没有长期连接需要清理。
        """
        self._is_available = False
        self._tools_cache_valid = False
        self.logger.info(f"服务器资源已清理: {self.name}")
    
    async def soft_disconnect(self) -> None:
        """软断开连接
        
        对于简化版，只是标记为不可用。
        """
        self._is_available = False
        self._tools_cache_valid = False
        self.logger.info(f"服务器已软断开: {self.name}")
    
    @property
    def is_connected(self) -> bool:
        """检查服务器是否已连接
        
        对于简化版，返回上次测试的结果。
        """
        return self._is_available
    
    @property
    def last_error(self) -> Optional[str]:
        """获取最后的错误信息"""
        return self._last_error
    
    def invalidate_cache(self) -> None:
        """使工具缓存失效"""
        self._tools_cache_valid = False
        self.logger.debug(f"工具缓存已失效: {self.name}")