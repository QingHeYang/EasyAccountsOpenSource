"""
工具执行器
统一的内部工具执行入口
"""

import json
import traceback
from typing import Any, Dict, List, Optional, Union

from .registry import tool_registry
from ..core.logging_utils import ManagerLogger


class ToolExecutor:
    """工具执行器 - 统一执行内部工具调用"""

    def __init__(self):
        """初始化执行器"""
        self.logger = ManagerLogger("ToolExecutor")
        self.registry = tool_registry

    async def execute(self, tool_name: str, arguments: Union[str, Dict[str, Any]],
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个工具调用

        Args:
            tool_name: 工具名称
            arguments: 工具参数（来自LLM，可能是JSON字符串或字典）
            context: 执行上下文

        Returns:
            执行结果字典:
                - success: bool
                - result: Any（成功时）
                - error: str（失败时）
                - metadata: dict（可选）
        """
        # 如果arguments是字符串，解析为字典
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments) if arguments else {}
            except json.JSONDecodeError as e:
                self.logger.warning("工具参数JSON解析失败", {
                    "tool_name": tool_name,
                    "arguments": arguments[:100],
                    "error": str(e)
                })
                return {
                    "success": False,
                    "error": f"工具参数格式错误: {str(e)}"
                }

        # 获取工具实例
        tool = self.registry.get(tool_name)
        if not tool:
            self.logger.warning(f"未找到工具: {tool_name}")
            return {
                "success": False,
                "error": f"未知的内部工具: {tool_name}"
            }

        # 验证参数
        validation_error = tool.validate_arguments(arguments)
        if validation_error:
            self.logger.warning("工具参数验证失败", {
                "tool_name": tool_name,
                "error": validation_error
            })
            return {
                "success": False,
                "error": validation_error
            }

        # 执行工具
        try:
            self.logger.info("执行内部工具", {
                "tool_name": tool_name,
                "arguments_keys": list(arguments.keys()),
                "conversation_id": context.get("conversation_id")
            })

            result = await tool.execute(arguments, context)

            self.logger.info("内部工具执行完成", {
                "tool_name": tool_name,
                "success": result.get("success", False)
            })

            return result

        except Exception as e:
            error_msg = f"工具执行异常: {str(e)}"
            self.logger.error("内部工具执行失败", {
                "tool_name": tool_name,
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            return {
                "success": False,
                "error": error_msg,
                "metadata": {"exception_type": type(e).__name__}
            }

    async def execute_batch(self, tool_calls: List[Dict[str, Any]],
                           context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """批量执行工具调用

        Args:
            tool_calls: 工具调用列表，每个元素包含:
                - tool_call_id: 调用ID
                - tool_name: 工具名称
                - arguments: 工具参数
            context: 执行上下文

        Returns:
            执行结果列表，每个元素包含:
                - tool_call_id: 调用ID
                - tool_name: 工具名称
                - result: 结果字符串
                - success: 是否成功
        """
        # 检查递归深度（工具调用额度）
        recursion_depth = context.get("recursion_depth", 0)
        if recursion_depth <= 0:
            self.logger.warning("工具调用额度耗尽", {
                "conversation_id": context.get("conversation_id"),
                "tool_calls_count": len(tool_calls)
            })
            return [{
                "tool_call_id": tc.get("tool_call_id"),
                "tool_name": tc.get("tool_name"),
                "result": "工具调用额度已用完：本轮对话的工具调用次数已达上限。请根据已有信息完成任务，或告知用户需要分步执行。",
                "success": False
            } for tc in tool_calls]

        results = []
        for tool_call in tool_calls:
            tool_call_id = tool_call.get("tool_call_id")
            tool_name = tool_call.get("tool_name")
            arguments = tool_call.get("arguments", {})

            # 执行单个工具
            exec_result = await self.execute(tool_name, arguments, context)

            # 格式化结果
            if exec_result.get("success"):
                result_str = str(exec_result.get("result", ""))
            else:
                result_str = exec_result.get("error", "执行失败")

            results.append({
                "tool_call_id": tool_call_id,
                "tool_name": tool_name,
                "result": result_str,
                "success": exec_result.get("success", False)
            })

        return results

    def is_inner_tool(self, tool_name: str) -> bool:
        """判断是否为内部工具

        Args:
            tool_name: 工具名称

        Returns:
            是否为内部工具
        """
        return self.registry.is_inner_tool(tool_name)


# 全局执行器实例
tool_executor = ToolExecutor()
