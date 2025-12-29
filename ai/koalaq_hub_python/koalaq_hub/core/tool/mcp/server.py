import asyncio
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession
from mcp.client.sse import sse_client

from ...logging_utils import ManagerLogger
from .mcp_tool import McpTool


class Server:
    """单个MCP服务器连接管理器

    职责：
    - 管理单个服务器的连接和会话
    - 提供工具列表和执行接口
    - 资源清理

    不负责：
    - 重试逻辑（由ServerManager管理）
    - 状态管理（由ServerManager管理）
    - 错误恢复（由ServerManager管理）
    """

    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name: str = name
        self.config: dict[str, Any] = config
        self.session: ClientSession | None = None
        self._cleanup_lock: asyncio.Lock = asyncio.Lock()
        self.exit_stack: AsyncExitStack | None = None  # 延迟创建，确保在同一任务中
        self.timeout = int(self.config.get("timeout", 120))
        self._init_task_id: int | None = None  # 记录初始化任务ID

        # 初始化日志记录器
        self.logger = ManagerLogger("MCPServer")
        self.logger.info("MCP服务器实例创建", {"name": self.name, "config": self.config})

    async def initialize(self) -> None:
        """初始化服务器连接

        Raises:
            Exception: 连接失败时抛出异常，由ServerManager处理重试逻辑
        """
        try:
            # 清理旧的 exit_stack（如果存在）
            if self.exit_stack:
                try:
                    await self.exit_stack.aclose()
                except Exception as e:
                    self.logger.debug("清理旧的exit_stack", {"error": str(e)})
                self.exit_stack = None

            # 创建新的 exit_stack，确保在当前任务中
            self.exit_stack = AsyncExitStack()
            self._init_task_id = id(asyncio.current_task())

            server_url = self.config.get("url", "")
            self.logger.info("正在连接MCP SSE端点", {"server_name": self.name, "url": server_url})

            transport = await self.exit_stack.enter_async_context(sse_client(url=server_url, timeout=self.timeout))
            read_stream, write_stream = transport

            session = await self.exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
            await session.initialize()
            self.session = session

            self.logger.info("成功初始化MCP服务器", {"server_name": self.name})

        except Exception as e:
            self.logger.error("初始化MCP服务器失败", exception=e, extra_data={"server_name": self.name})
            await self.cleanup()
            raise  # 向上抛出异常，由ServerManager处理

    async def list_tools(self) -> list[McpTool]:
        """列出服务器可用的工具

        Returns:
            可用工具列表

        Raises:
            RuntimeError: 如果服务器未初始化
            Exception: 工具列表获取失败时抛出异常
        """
        if not self.session:
            raise RuntimeError(f"MCP服务器 {self.name} 未初始化")

        try:
            tools_response = await self.session.list_tools()
            tools = []

            for item in tools_response:
                if isinstance(item, tuple) and item[0] == "tools":
                    tools.extend(McpTool(tool.name, tool.description, tool.inputSchema) for tool in item[1])

            self.logger.debug("获取工具列表成功", {"server_name": self.name, "tools_count": len(tools)})
            return tools

        except Exception as e:
            # 检查是否是 SSL 错误
            error_msg = str(e).lower()
            if "ssl" in error_msg or "decryption" in error_msg:
                self.logger.warning("检测到SSL错误，标记连接已断开", {"server_name": self.name, "error": str(e)})
                # 标记连接已断开，需要重连
                self.session = None

            self.logger.error("列出MCP服务器的工具时出错", exception=e, extra_data={"server_name": self.name})
            raise  # 向上抛出异常，由ServerManager处理

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """执行工具

        Args:
            tool_name: 要执行的工具名称
            arguments: 工具参数

        Returns:
            工具执行结果

        Raises:
            RuntimeError: 如果服务器未初始化
            Exception: 工具执行失败时抛出异常
        """
        if not self.session:
            raise RuntimeError(f"MCP服务器 {self.name} 未初始化")

        # 检查连接状态
        if not self.is_connected:
            self.logger.warning("MCP服务器连接已断开，需要重新初始化", {"server_name": self.name})
            raise RuntimeError(f"MCP服务器 {self.name} 连接已断开，请重新初始化")

        try:
            self.logger.info("正在执行工具", {"tool_name": tool_name, "server_name": self.name, "arguments": arguments})
            result = await self.session.call_tool(tool_name, arguments)

            self.logger.debug("工具执行成功", {"tool_name": tool_name, "server_name": self.name})
            return result

        except Exception as e:
            # 特殊处理 SSE 连接错误
            error_msg = str(e)

            # 处理空错误信息
            if not error_msg:
                error_msg = f"{type(e).__name__}: {repr(e)}"
                self.logger.error("工具执行失败（空错误信息）", exception=e, extra_data={"tool_name": tool_name, "server_name": self.name, "error_type": type(e).__name__, "error_repr": repr(e)})

            if "post_writer" in error_msg.lower():
                self.logger.error("MCP SSE连接错误（连接已断开）", exception=e, extra_data={"tool_name": tool_name, "server_name": self.name, "error_type": "sse_connection_error", "error_detail": "SSE连接已关闭，可能需要重新初始化"})
                # 标记连接已断开
                self.session = None
                # 重新抛出一个更清晰的错误信息
                raise RuntimeError(f"MCP服务器 '{self.name}' 连接已断开，请重新初始化后再试")
            else:
                self.logger.error("工具执行失败", exception=e, extra_data={"tool_name": tool_name, "server_name": self.name, "error_msg": error_msg})
                raise  # 向上抛出异常，由ServerManager或ToolManager处理

    async def cleanup(self) -> None:
        """清理服务器资源"""
        async with self._cleanup_lock:
            try:
                # 检查是否在同一个任务中
                current_task_id = id(asyncio.current_task())

                if self.exit_stack:
                    # 如果不是在同一个任务中，记录警告但不尝试关闭
                    if self._init_task_id and self._init_task_id != current_task_id:
                        self.logger.warning("检测到跨任务的exit_stack访问，跳过清理", {"server_name": self.name, "init_task_id": self._init_task_id, "current_task_id": current_task_id})
                        # 只重置引用，不尝试关闭
                        self.exit_stack = None
                    else:
                        # 在同一个任务中，可以安全关闭
                        try:
                            await self.exit_stack.aclose()
                        except RuntimeError as e:
                            if "different task" in str(e):
                                self.logger.warning("跨任务清理exit_stack失败，忽略错误", {"server_name": self.name, "error": str(e)})
                            else:
                                raise
                        finally:
                            self.exit_stack = None

                self.session = None
                self._init_task_id = None
                self.logger.debug("MCP服务器资源清理完成", {"server_name": self.name})

            except Exception as e:
                # 过滤已知的跨任务错误
                if "different task" not in str(e):
                    self.logger.error("清理MCP服务器时出错", exception=e, extra_data={"server_name": self.name})
                # 即使清理失败，也要确保session被重置
                self.session = None
                self.exit_stack = None
                self._init_task_id = None

    @property
    def is_connected(self) -> bool:
        """检查服务器是否已连接"""
        return self.session is not None
