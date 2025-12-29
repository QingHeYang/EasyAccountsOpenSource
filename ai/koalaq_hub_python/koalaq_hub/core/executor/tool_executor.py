"""
工具执行器 - 负责执行工具调用
"""

import asyncio
from typing import Any, Dict, List

from ...core.tool.mcp.mcp_tool_manager import ToolManager
from ...core.tool.mcp.server_manager import ServerManager
from .base_executor import BaseExecutor, ExecutionResult


class ToolExecutor(BaseExecutor):
    """工具执行器 - 处理MCP工具调用"""
    
    def __init__(self, server_manager, tool_manager=None):
        """
        初始化工具执行器
        
        Args:
            server_manager: MCP服务器管理器
            tool_manager: 工具管理器（可选，用于预处理和黑名单检查）
        """
        super().__init__()
        self.server_manager: ServerManager = server_manager
        self.tool_manager: ToolManager = tool_manager
    
    async def execute(self, call: Any, context: Dict[str, Any]) -> ExecutionResult:
        """
        执行单个工具调用（实现抽象方法）
        
        Args:
            call: 工具调用对象
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        # 将单个调用转换为批量调用格式
        if isinstance(call, dict):
            results = await self.execute_batch([call], context)
            if results:
                result = results[0]
                return self._create_success_result(
                    result=result["result"],
                    metadata={"success": result["success"], "tool_name": result.get("tool_name")}
                ) if result["success"] else self._create_error_result(result["result"])
        
        return self._create_error_result("无效的工具调用格式")
    
    async def execute_batch(self, tool_calls: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        批量并行执行工具调用
        
        Args:
            tool_calls: 工具调用列表，每个包含 tool_call_id, tool_name, arguments
            context: 执行上下文
            
        Returns:
            执行结果列表，每个包含 tool_call_id, result, success
        """
        # 验证上下文
        if not await self.validate_context(context):
            return [{"tool_call_id": tc.get("tool_call_id"), "result": "执行上下文无效", "success": False} 
                    for tc in tool_calls]
        
        # 检查递归深度（工具调用额度）
        recursion_depth = context.get("recursion_depth", 0)
        if recursion_depth <= 0:
            self.logger.warning("工具调用额度耗尽，拒绝执行工具调用", {
                "conversation_id": context.get("conversation_id"),
                "tool_calls_count": len(tool_calls)
            })
            # 为所有工具调用返回额度用尽的错误
            return [{
                "tool_call_id": tc.get("tool_call_id"),
                "tool_name": tc.get("tool_name"),
                "result": "工具调用额度已用完：本轮对话的工具调用次数已达上限。请根据已有信息完成任务，或告知用户需要分步执行。",
                "success": False
            } for tc in tool_calls]
        
        # 创建并行任务
        tasks = []
        for tool_call in tool_calls:
            task = self._execute_single_tool(tool_call, context)
            tasks.append(task)
        
        # 并行执行所有工具
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        final_results = []
        for i, result in enumerate(results):
            tool_call = tool_calls[i]
            tool_call_id = tool_call.get("tool_call_id")
            
            if isinstance(result, Exception):
                error_msg = f"执行错误: {str(result)}"
                self.logger.error("工具批量执行中捕获异常", {
                    "tool_call_id": tool_call_id,
                    "tool_name": tool_call.get("tool_name"),
                    "error": str(result)
                })
                final_results.append({
                    "tool_call_id": tool_call_id,
                    "tool_name": tool_call.get("tool_name"),
                    "result": error_msg,
                    "success": False
                })
            else:
                final_results.append(result)
        
        return final_results
    
    async def _execute_single_tool(self, tool_call: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单个工具调用
        
        Args:
            tool_call: 包含 tool_call_id, tool_name, arguments
            context: 执行上下文
            
        Returns:
            包含 tool_call_id, result, success 的字典
        """
        tool_call_id = tool_call.get("tool_call_id")
        tool_name = tool_call.get("tool_name")
        arguments = tool_call.get("arguments", {})
        
        conversation_id = context.get("conversation_id")
        agent = context.get("agent")
        
        self.logger.info(
            "开始执行工具",
            {
                "tool_name": tool_name,
                "tool_call_id": tool_call_id,
                "arguments": arguments,
                "conversation_id": conversation_id
            }
        )
        
        # 检查黑名单
        if self.tool_manager and agent:
            if not self.tool_manager.is_tool_allowed(agent, tool_name):
                error_msg = f"工具 '{tool_name}' 已被管理员禁用"
                self.logger.info("工具在黑名单中", {"tool_name": tool_name})
                return {
                    "tool_call_id": tool_call_id,
                    "result": error_msg,
                    "success": False
                }
        
        
        # 执行工具调用
        try:
            result = await self._execute_tool_with_preprocessing(tool_name, arguments, context)
            
            # 成功执行
            
            return {
                "tool_call_id": tool_call_id,
                "tool_name": tool_name,
                "result": str(result),
                "success": True
            }
            
        except Exception as e:
            # 工具执行失败 - 改进错误信息处理
            error_str = str(e)
            if not error_str:
                # 如果异常转换为空字符串，尝试获取更多信息
                error_str = f"{type(e).__name__}: {repr(e)}"
            
            error_msg = f"工具执行失败: {error_str}"
            self.logger.warning(
                "工具执行失败",
                {
                    "error": error_str,
                    "error_type": type(e).__name__,
                    "tool": tool_name,
                    "tool_call_id": tool_call_id
                }
            )
            
            
            return {
                "tool_call_id": tool_call_id,
                "tool_name": tool_name,
                "result": error_msg,
                "success": False
            }
    
    
    async def _execute_tool_with_preprocessing(self, tool_name: str, arguments: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """执行工具调用（包含预处理）"""
        # 获取工具到服务器的映射
        tool_server_map = self.server_manager.get_tool_server_mapping()
        server_name = tool_server_map.get(tool_name)
        
        if not server_name:
            available_tools = list(tool_server_map.keys())
            raise ValueError(f"工具 '{tool_name}' 不可用。可用工具: {available_tools}")
        
        # 预处理参数
        processed_arguments = self._preprocess_arguments(tool_name, arguments, context)
        
        # 调用MCP服务器执行工具
        server = self.server_manager.servers.get(server_name)
        if not server:
            raise ValueError(f"服务器 '{server_name}' 未找到")
        
        # 执行工具调用（添加超时控制）
        # 从配置获取超时时间，默认60秒
        tool_timeout = context.get("tool_timeout", 60)
        
        self.logger.info(f"开始执行工具（超时设置: {tool_timeout}秒）", {
            "tool_name": tool_name,
            "server_name": server_name,
            "timeout": tool_timeout
        })
        
        try:
            result = await asyncio.wait_for(
                server.execute_tool(tool_name, processed_arguments),
                timeout=tool_timeout
            )
        except asyncio.TimeoutError:
            self.logger.error("工具执行超时", {
                "tool_name": tool_name,
                "server_name": server_name,
                "timeout": tool_timeout,
                "arguments": processed_arguments
            })
            raise Exception(f"工具 '{tool_name}' 执行超时（{tool_timeout}秒）")
        
        # 检查结果
        if hasattr(result, "isError") and result.isError:
            error_content = getattr(result, "content", [])
            error_text = str(error_content) if error_content else "工具执行错误"
            raise Exception(error_text)
        
        return result
    
    def _preprocess_arguments(self, tool_name: str, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """预处理工具参数"""
        # 如果 arguments 是字符串，先解析
        if isinstance(arguments, str):
            import json
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                # 如果解析失败，返回空字典
                arguments = {}
        
        arguments = arguments.copy()
        
        # 如果有tool_manager，使用它的预处理功能
        if self.tool_manager:
            agent = context.get("agent")
            conversation_id = context.get("conversation_id")
            if agent and conversation_id:
                arguments = self.tool_manager.preprocess_tool_arguments(
                    agent, tool_name, arguments, conversation_id
                )
        
        return arguments
    
