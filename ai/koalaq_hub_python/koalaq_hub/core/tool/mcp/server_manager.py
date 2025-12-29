import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ....config.settings import config
from ...logging_utils import ManagerLogger
from .mcp_tool import McpTool
from .server import Server


@dataclass
class ServerStatus:
    """服务器状态数据类"""

    name: str
    is_connected: bool = False
    last_ping_time: Optional[datetime] = None
    tools_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    last_refresh_time: Optional[datetime] = None


class ServerManager:
    """MCP服务器管理器

    专门负责管理所有MCP服务器的生命周期：
    - 服务器连接管理（初始化、重连、清理）
    - 工具状态维护（定期刷新、内存存储）
    - 健康监控（状态检查、错误统计）
    - 定期任务（工具列表刷新）
    """

    def __init__(self):
        """初始化服务器管理器"""
        # 服务器管理
        self.servers: Dict[str, Server] = {}
        self.server_status: Dict[str, ServerStatus] = {}

        # 工具管理（内存中维护）
        self.all_tools: List[McpTool] = []
        self.tools_by_server: Dict[str, List[McpTool]] = {}
        self.tool_server_map: Dict[str, str] = {}

        # 定期任务管理
        self.refresh_task: Optional[asyncio.Task] = None
        self.refresh_interval: int = 3600  # 5分钟刷新一次
        self._stop_refresh_event = asyncio.Event()

        # 运行时重连配置
        self.runtime_max_retries: int = 4  # 运行时最大重试次数
        self.runtime_retry_delay: float = 15.0  # 运行时重试间隔（秒）

        # 状态统计
        self.last_refresh_time: Optional[datetime] = None
        self.total_refresh_count: int = 0
        self.is_initialized: bool = False

        # 日志记录器
        self.logger = ManagerLogger("ServerManager")

        self.logger.info("ServerManager初始化完成")

    async def initialize_all_servers(self, server_names: Optional[List[str]] = None) -> None:
        """初始化所有MCP服务器

        Args:
            server_names: 要初始化的服务器名称列表，如果为None则加载所有可用服务器
        """
        try:
            self.logger.info("开始初始化所有MCP服务器", {"server_names": server_names})

            # 聚合服务器配置
            servers_config = self._aggregate_servers_config(server_names)
            if not servers_config:
                self.logger.warning("没有找到有效的MCP服务器配置")
                return

            # 创建服务器实例
            for server_config in servers_config:
                server_name = server_config["name"]
                # 添加SSE超时配置
                from ....config.settings import config as app_config
                server_config["timeout"] = app_config.mcp_sse_timeout
                
                server = Server(name=server_name, config=server_config)
                self.servers[server_name] = server
                self.server_status[server_name] = ServerStatus(name=server_name)

                self.logger.info("创建MCP服务器实例", {"server_name": server_name, "sse_timeout": server_config["timeout"]})

            # 并发初始化所有服务器
            await self._initialize_servers_concurrently()

            # 首次刷新工具列表
            await self.refresh_all_tools()

            self.is_initialized = True
            self.logger.info(
                "所有MCP服务器初始化完成",
                {
                    "total_servers": len(self.servers),
                    "connected_servers": len([s for s in self.server_status.values() if s.is_connected]),
                    "total_tools": len(self.all_tools),
                },
            )

        except Exception as e:
            self.logger.error("初始化MCP服务器失败", exception=e)
            await self.cleanup_all_servers()
            raise

    async def _initialize_servers_concurrently(self) -> None:
        """并发初始化所有服务器"""
        tasks = []
        for server_name, server in self.servers.items():
            task = asyncio.create_task(self._initialize_single_server(server_name, server))
            tasks.append(task)

        # 等待所有初始化任务完成（不抛出异常）
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 统计初始化结果
        success_count = sum(1 for r in results if r is True)
        self.logger.info(
            "服务器初始化结果",
            {
                "success_count": success_count,
                "total_count": len(tasks),
                "success_rate": f"{success_count / len(tasks) * 100:.1f}%",
            },
        )

    async def _initialize_single_server(self, server_name: str, server: Server) -> bool:
        """初始化单个服务器"""
        try:
            await server.initialize()
            # 检查连接状态
            if server.is_connected:
                self.server_status[server_name].is_connected = True
                self.server_status[server_name].last_ping_time = datetime.now()
                self.logger.info("服务器初始化成功", {"server_name": server_name})
                return True
            else:
                self._update_server_error(server_name, "初始化失败，服务器未连接")
                return False
        except Exception as e:
            self._update_server_error(server_name, str(e))
            return False

    async def refresh_all_tools(self) -> None:
        """刷新所有服务器的工具列表"""
        try:
            self.logger.info("开始刷新所有服务器的工具列表")

            # 清空当前工具数据
            self.all_tools.clear()
            self.tools_by_server.clear()
            self.tool_server_map.clear()

            # 并发获取所有服务器的工具
            tasks = []
            for server_name, server in self.servers.items():
                if self.server_status[server_name].is_connected:
                    task = asyncio.create_task(self._refresh_server_tools(server_name, server))
                    tasks.append(task)

            # 等待所有刷新任务完成
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                success_count = sum(1 for r in results if isinstance(r, list))

                self.logger.info(
                    "工具刷新完成",
                    {
                        "success_count": success_count,
                        "total_count": len(tasks),
                        "total_tools": len(self.all_tools),
                    },
                )

            # 更新刷新统计
            self.last_refresh_time = datetime.now()
            self.total_refresh_count += 1

        except Exception as e:
            self.logger.error("刷新工具列表失败", exception=e)

    async def _refresh_server_tools(self, server_name: str, server: Server) -> List[McpTool]:
        """刷新单个服务器的工具列表，带自动重连机制"""
        try:
            tools = await server.list_tools()

            # 更新工具数据结构
            self.tools_by_server[server_name] = tools
            self.all_tools.extend(tools)

            # 更新工具到服务器的映射
            for tool in tools:
                self.tool_server_map[tool.name] = server_name

            # 更新服务器状态
            self.server_status[server_name].tools_count = len(tools)
            self.server_status[server_name].last_refresh_time = datetime.now()

            str_tools = [tool.name for tool in tools]
            self.logger.info(
                "服务器工具刷新成功",
                {"server": server_name, "工具数量": len(tools), "工具列表": str_tools},
            )

            return tools

        except Exception as e:
            self.logger.warning(
                "工具刷新失败，可能服务器断线",
                {"server_name": server_name, "error": str(e)},
            )

            # 标记服务器断线
            self.server_status[server_name].is_connected = False

            # 尝试自动重连
            self.logger.info("尝试自动重连服务器", {"server_name": server_name})
            reconnect_success = await self._reconnect_server(server_name)

            if reconnect_success:
                # 重连成功，再次尝试刷新工具
                try:
                    tools = await server.list_tools()

                    # 更新工具数据结构
                    self.tools_by_server[server_name] = tools
                    self.all_tools.extend(tools)

                    # 更新工具到服务器的映射
                    for tool in tools:
                        self.tool_server_map[tool.name] = server_name

                    # 更新服务器状态
                    self.server_status[server_name].tools_count = len(tools)
                    self.server_status[server_name].last_refresh_time = datetime.now()

                    self.logger.info(
                        "重连后工具刷新成功",
                        {"server_name": server_name, "tools_count": len(tools)},
                    )

                    return tools

                except Exception as retry_e:
                    self.logger.error(
                        "重连后工具刷新仍然失败",
                        exception=retry_e,
                        extra_data={"server_name": server_name},
                    )
                    self._update_server_error(server_name, f"重连后刷新失败: {str(retry_e)}")
            else:
                self._update_server_error(server_name, f"自动重连失败，原始错误: {str(e)}")

            return []

    async def start_periodic_refresh(self) -> None:
        """启动定期刷新任务"""
        if self.refresh_task and not self.refresh_task.done():
            self.logger.warning("定期刷新任务已在运行")
            return

        self._stop_refresh_event.clear()
        self.refresh_task = asyncio.create_task(self._periodic_refresh_loop())

        self.logger.info("启动定期刷新任务", {"refresh_interval": self.refresh_interval})

    async def stop_periodic_refresh(self) -> None:
        """停止定期刷新任务"""
        self._stop_refresh_event.set()

        if self.refresh_task and not self.refresh_task.done():
            try:
                await asyncio.wait_for(self.refresh_task, timeout=5.0)
            except asyncio.TimeoutError:
                self.refresh_task.cancel()
                try:
                    await self.refresh_task
                except asyncio.CancelledError:
                    pass

        self.logger.info("定期刷新任务已停止")

    async def _periodic_refresh_loop(self) -> None:
        """定期刷新循环"""
        while not self._stop_refresh_event.is_set():
            try:
                # 等待刷新间隔或停止信号
                await asyncio.wait_for(self._stop_refresh_event.wait(), timeout=self.refresh_interval)
                break  # 收到停止信号

            except asyncio.TimeoutError:
                # 刷新间隔到达，执行刷新
                await self.refresh_all_tools()

    async def refresh_server_tools(self, server_name: str) -> List[McpTool]:
        """刷新指定服务器的工具列表

        Args:
            server_name: 服务器名称

        Returns:
            该服务器的工具列表
        """
        if server_name not in self.servers:
            self.logger.error("服务器不存在", extra_data={"server_name": server_name})
            return []

        if not self.server_status[server_name].is_connected:
            self.logger.warning("服务器未连接，尝试重连", {"server_name": server_name})
            # 尝试重连服务器
            reconnect_success = await self._reconnect_server(server_name)
            if not reconnect_success:
                return []

        server = self.servers[server_name]
        tools = await self._refresh_server_tools(server_name, server)

        self.logger.info(
            "单服务器工具刷新完成",
            {"server_name": server_name, "tools_count": len(tools)},
        )

        return tools

    async def _reconnect_server(self, server_name: str) -> bool:
        """运行时重连服务器

        Args:
            server_name: 服务器名称

        Returns:
            重连是否成功
        """
        if server_name not in self.servers:
            self.logger.error("服务器不存在", extra_data={"server_name": server_name})
            return False

        server = self.servers[server_name]
        retry_count = 0

        self.logger.info(
            "开始运行时重连服务器",
            {
                "server_name": server_name,
                "max_retries": self.runtime_max_retries,
                "retry_delay": self.runtime_retry_delay,
            },
        )

        while retry_count < self.runtime_max_retries:
            try:
                # 先清理现有连接
                await server.cleanup()

                # 重新初始化服务器
                await server.initialize()

                if server.is_connected:
                    # 更新服务器状态
                    self.server_status[server_name].is_connected = True
                    self.server_status[server_name].last_ping_time = datetime.now()
                    self.server_status[server_name].error_count = 0  # 重置错误计数
                    self.server_status[server_name].last_error = None

                    self.logger.info(
                        "运行时重连服务器成功",
                        {"server_name": server_name, "retry_count": retry_count + 1},
                    )
                    return True
                else:
                    raise RuntimeError("服务器初始化后未标记为已初始化")

            except Exception as e:
                retry_count += 1
                self._update_server_error(server_name, f"重连失败: {str(e)}")

                if retry_count < self.runtime_max_retries:
                    self.logger.warning(
                        "运行时重连失败，准备重试",
                        {
                            "server_name": server_name,
                            "retry_count": retry_count,
                            "max_retries": self.runtime_max_retries,
                            "error": str(e),
                            "next_retry_in": self.runtime_retry_delay,
                        },
                    )
                    await asyncio.sleep(self.runtime_retry_delay)
                else:
                    self.logger.error(
                        "运行时重连最终失败",
                        exception=e,
                        extra_data={
                            "server_name": server_name,
                            "total_retries": retry_count,
                        }
                    )

        return False

    async def restart_server(self, server_name: str) -> bool:
        """重启指定的服务器"""
        if server_name not in self.servers:
            self.logger.error("服务器不存在", extra_data={"server_name": server_name})
            return False

        try:
            self.logger.info("正在重启服务器", {"server_name": server_name})

            server = self.servers[server_name]

            # 清理现有连接
            await server.cleanup()

            # 重新初始化
            success = await self._initialize_single_server(server_name, server)

            if success:
                # 刷新该服务器的工具
                await self._refresh_server_tools(server_name, server)
                self.logger.info("服务器重启成功", {"server_name": server_name})

            return success

        except Exception as e:
            self._update_server_error(server_name, f"重启失败: {str(e)}")
            return False

    async def cleanup_all_servers(self) -> None:
        """清理所有服务器资源"""
        try:
            self.logger.info("开始清理所有服务器资源")

            # 停止定期刷新
            await self.stop_periodic_refresh()

            # 清理所有服务器
            cleanup_tasks = []
            for server_name, server in self.servers.items():
                task = asyncio.create_task(server.cleanup())
                cleanup_tasks.append(task)

            if cleanup_tasks:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)

            # 清空状态
            for status in self.server_status.values():
                status.is_connected = False

            self.is_initialized = False
            self.logger.info("所有服务器资源清理完成")

        except Exception as e:
            self.logger.error("清理服务器资源失败", exception=e)

    def get_available_tools(self) -> List[McpTool]:
        """获取所有可用工具"""
        return self.all_tools.copy()

    def get_tools_by_server(self, server_names: List[str]) -> List[McpTool]:
        """获取指定服务器的工具"""
        tools = []
        for server_name in server_names:
            if server_name in self.tools_by_server:
                tools.extend(self.tools_by_server[server_name])
        return tools

    def get_server_status(self, server_name: str) -> Optional[ServerStatus]:
        """获取指定服务器的状态"""
        return self.server_status.get(server_name)

    def get_all_servers_status(self) -> Dict[str, ServerStatus]:
        """获取所有服务器状态"""
        return self.server_status.copy()

    def get_tool_server_mapping(self) -> Dict[str, str]:
        """获取工具到服务器的映射"""
        return self.tool_server_map.copy()

    def _aggregate_servers_config(self, server_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """聚合MCP服务器配置

        Args:
            server_names: 要加载的服务器名称列表，如果为None则加载所有可用服务器

        Returns:
            服务器配置列表
        """
        try:
            # 获取MCP配置目录
            mcp_dir = config.mcp_dir
            if not mcp_dir.exists():
                self.logger.warning(f"MCP配置目录不存在: {mcp_dir}")
                return []

            # 用于过滤重复服务器的字典
            merged_servers = {}

            if server_names:
                # 加载指定的服务器配置
                for server_name in server_names:
                    servers_from_file = self._load_servers_from_file(server_name, mcp_dir)
                    for name, server_config in servers_from_file.items():
                        if name not in merged_servers:
                            merged_servers[name] = server_config
                        else:
                            self.logger.warning("发现重复服务器配置，已过滤", {"server_name": name})
            else:
                # 加载所有可用的服务器配置
                for config_file in mcp_dir.glob("*.json"):
                    file_name = config_file.stem
                    servers_from_file = self._load_servers_from_file(file_name, mcp_dir)
                    for name, server_config in servers_from_file.items():
                        if name not in merged_servers:
                            merged_servers[name] = server_config
                        else:
                            self.logger.warning(
                                "发现重复服务器配置，已过滤",
                                {"server_name": name, "file": file_name},
                            )

            # 转换为配置列表
            servers_config = []
            for server_name, server_config in merged_servers.items():
                # 确保配置包含name字段
                server_config["name"] = server_name
                servers_config.append(server_config)

            self.logger.info(
                "成功聚合MCP服务器配置",
                {
                    "total_servers": len(servers_config),
                    "server_names": [s["name"] for s in servers_config],
                },
            )

            return servers_config

        except Exception as e:
            self.logger.error("聚合MCP服务器配置失败", exception=e)
            return []

    def _load_servers_from_file(self, file_name: str, mcp_dir: Path) -> Dict[str, Dict[str, Any]]:
        """从配置文件加载服务器配置

        Args:
            file_name: 配置文件名（不含扩展名）
            mcp_dir: MCP配置目录

        Returns:
            服务器配置字典，键为服务器名称，值为配置信息
        """
        config_file = mcp_dir / f"{file_name}.json"

        if not config_file.exists():
            self.logger.warning("配置文件不存在", {"file_name": file_name, "config_file": config_file})
            return {}

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                file_config = json.load(f)

            # 解析mcpServers格式
            if "mcpServers" in file_config:
                servers = file_config["mcpServers"]
                self.logger.info(
                    "成功加载配置文件",
                    {
                        "file_name": file_name,
                        "config_file": config_file,
                        "servers_count": len(servers),
                    },
                )
                return servers
            else:
                self.logger.warning("配置文件格式不正确，缺少mcpServers字段", {"file_name": file_name})
                return {}

        except Exception as e:
            self.logger.error(
                "加载配置文件失败",
                exception=e,
                extra_data={"file_name": file_name, "config_file": config_file},
            )
            return {}

    def _update_server_error(self, server_name: str, error_message: str) -> None:
        """更新服务器错误状态"""
        if server_name in self.server_status:
            status = self.server_status[server_name]
            status.is_connected = False
            status.error_count += 1
            status.last_error = error_message

            self.logger.error(
                "服务器错误",
                extra_data={
                    "server_name": server_name,
                    "error_message": error_message,
                    "error_count": status.error_count,
                }
            )

    def get_summary_info(self) -> Dict[str, Any]:
        """获取管理器摘要信息"""
        connected_servers = [s for s in self.server_status.values() if s.is_connected]

        return {
            "is_initialized": self.is_initialized,
            "total_servers": len(self.servers),
            "connected_servers": len(connected_servers),
            "total_tools": len(self.all_tools),
            "last_refresh_time": self.last_refresh_time.isoformat() if self.last_refresh_time else None,
            "total_refresh_count": self.total_refresh_count,
            "refresh_interval": self.refresh_interval,
            "is_refreshing": self.refresh_task and not self.refresh_task.done(),
        }
