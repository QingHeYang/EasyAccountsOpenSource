"""
简化版MCP服务器管理器

使用按需连接模式，不再维护长连接。
每次工具调用时建立连接，用完即关。
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ....config.settings import config
from ...logging_utils import ManagerLogger
from .mcp_tool import McpTool
from .server_simple import SimpleServer


class ServerManager:
    """MCP服务器管理器（简化版）

    职责：
    - 管理 SimpleServer 实例
    - 提供工具列表查询
    - 提供工具到服务器的映射

    不再负责：
    - 长连接维护
    - 自动重连
    - 定期刷新
    """

    def __init__(self):
        """初始化服务器管理器"""
        # 服务器实例
        self.servers: Dict[str, SimpleServer] = {}

        # 工具映射缓存
        self._tool_server_map: Dict[str, str] = {}
        self._tool_server_map_valid: bool = False

        # 日志记录器
        self.logger = ManagerLogger("ServerManager")
        self.logger.info("ServerManager初始化完成（简化版）")

    async def initialize_all_servers(self, server_names: Optional[List[str]] = None) -> None:
        """初始化所有MCP服务器

        只创建 SimpleServer 实例，不建立连接。
        连接会在实际使用时按需建立。

        Args:
            server_names: 要初始化的服务器名称列表，如果为None则加载所有可用服务器
        """
        try:
            self.logger.info("开始初始化MCP服务器", {"server_names": server_names})

            # 聚合服务器配置
            servers_config = self._aggregate_servers_config(server_names)
            if not servers_config:
                self.logger.warning("没有找到有效的MCP服务器配置")
                return

            # 创建 SimpleServer 实例（不建立连接）
            for server_config in servers_config:
                server_name = server_config["name"]
                # 添加超时配置
                server_config["timeout"] = config.mcp_sse_timeout

                server = SimpleServer(name=server_name, config=server_config)
                self.servers[server_name] = server

                self.logger.info("创建MCP服务器实例", {
                    "server_name": server_name,
                    "url": server_config.get("url", ""),
                    "timeout": server_config["timeout"]
                })

            self.logger.info("MCP服务器初始化完成", {
                "total_servers": len(self.servers),
                "server_names": list(self.servers.keys())
            })

        except Exception as e:
            self.logger.error("初始化MCP服务器失败", exception=e)
            raise

    async def get_tools_by_server(self, server_names: List[str]) -> List[McpTool]:
        """获取指定服务器的工具列表

        按需连接，获取工具后自动断开。

        Args:
            server_names: 服务器名称列表

        Returns:
            工具列表
        """
        tools = []
        for server_name in server_names:
            if server_name in self.servers:
                server = self.servers[server_name]
                try:
                    server_tools = await server.list_tools()
                    tools.extend(server_tools)

                    # 更新工具映射
                    for tool in server_tools:
                        self._tool_server_map[tool.name] = server_name

                except Exception as e:
                    self.logger.error("获取服务器工具失败", extra_data={
                        "server_name": server_name,
                        "error": str(e)
                    })
            else:
                self.logger.warning("服务器不存在", {"server_name": server_name})

        return tools

    def get_tool_server_mapping(self) -> Dict[str, str]:
        """获取工具到服务器的映射

        Returns:
            工具名称 -> 服务器名称 的映射字典
        """
        return self._tool_server_map.copy()

    async def refresh_tool_mapping(self) -> Dict[str, str]:
        """刷新工具到服务器的映射

        遍历所有服务器，获取工具列表并构建映射。

        Returns:
            工具名称 -> 服务器名称 的映射字典
        """
        self._tool_server_map.clear()

        for server_name, server in self.servers.items():
            try:
                tools = await server.list_tools()
                for tool in tools:
                    self._tool_server_map[tool.name] = server_name

                self.logger.debug("刷新服务器工具映射", {
                    "server_name": server_name,
                    "tools_count": len(tools)
                })
            except Exception as e:
                self.logger.error("刷新工具映射失败", extra_data={
                    "server_name": server_name,
                    "error": str(e)
                })

        self.logger.info("工具映射刷新完成", {
            "total_tools": len(self._tool_server_map)
        })

        return self._tool_server_map.copy()

    async def get_available_tools(self) -> List[McpTool]:
        """获取所有可用工具

        Returns:
            所有服务器的工具列表
        """
        return await self.get_tools_by_server(list(self.servers.keys()))

    async def cleanup_all_servers(self) -> None:
        """清理所有服务器资源"""
        try:
            self.logger.info("开始清理所有服务器资源")

            for server_name, server in self.servers.items():
                try:
                    await server.cleanup()
                except Exception as e:
                    self.logger.error("清理服务器失败", extra_data={
                        "server_name": server_name,
                        "error": str(e)
                    })

            # 清空映射
            self._tool_server_map.clear()

            self.logger.info("所有服务器资源清理完成")

        except Exception as e:
            self.logger.error("清理服务器资源失败", exception=e)

    def invalidate_all_caches(self) -> None:
        """使所有服务器的工具缓存失效"""
        for server in self.servers.values():
            server.invalidate_cache()
        self._tool_server_map.clear()
        self.logger.info("所有工具缓存已失效")

    def get_server(self, server_name: str) -> Optional[SimpleServer]:
        """获取指定的服务器实例

        Args:
            server_name: 服务器名称

        Returns:
            SimpleServer 实例，如果不存在则返回 None
        """
        return self.servers.get(server_name)

    def get_summary_info(self) -> Dict[str, Any]:
        """获取管理器摘要信息"""
        return {
            "total_servers": len(self.servers),
            "server_names": list(self.servers.keys()),
            "total_tools_mapped": len(self._tool_server_map),
            "mode": "on-demand"  # 按需连接模式
        }

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
                    # 跳过 .example.json 模板文件
                    if file_name.endswith(".example"):
                        self.logger.debug("跳过模板文件", {"file_name": file_name})
                        continue
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
