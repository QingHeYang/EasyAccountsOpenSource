"""
工具执行器
统一的内部工具执行入口
"""

import json
import traceback
from typing import Any, Dict, List, Optional, Union

from .error_codes import (
    E_PARAM_INVALID,
    E_TOOL_BUDGET_EXHAUSTED,
    E_UNKNOWN_TOOL,
    from_exception,
    make_error,
)
from .registry import tool_registry
from ..core.logging_utils import ManagerLogger


def _llm_text(err) -> str:
    """把 ToolError 拼成给 LLM 看的可读字符串。"""
    if err.hint:
        return f"{err.message}（{err.hint}）"
    return err.message


def _structured_error(err) -> Dict[str, Any]:
    """构造统一的失败响应字典（与 BaseTool._error 输出形状对齐）。"""
    return {
        "success": False,
        "error": _llm_text(err),
        "error_object": err.to_dict(),
        "metadata": err.metadata or {},
    }


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
                return _structured_error(
                    make_error(
                        E_PARAM_INVALID,
                        message=f"工具参数 JSON 解析失败: {str(e)}",
                    )
                )

        # 获取工具实例
        tool = self.registry.get(tool_name)
        if not tool:
            self.logger.warning(f"未找到工具: {tool_name}")
            return _structured_error(
                make_error(E_UNKNOWN_TOOL, message=f"未知的内部工具: {tool_name}")
            )

        # 验证参数
        validation_error = tool.validate_arguments(arguments)
        if validation_error:
            self.logger.warning("工具参数验证失败", {
                "tool_name": tool_name,
                "error": validation_error
            })
            return _structured_error(
                make_error(E_PARAM_INVALID, message=validation_error)
            )

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
            self.logger.error("内部工具执行失败", {
                "tool_name": tool_name,
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            return _structured_error(from_exception(e))

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
            budget_err = make_error(E_TOOL_BUDGET_EXHAUSTED)
            return [{
                "tool_call_id": tc.get("tool_call_id"),
                "tool_name": tc.get("tool_name"),
                "result": _llm_text(budget_err),
                "success": False,
                "error_object": budget_err.to_dict(),
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

            entry: Dict[str, Any] = {
                "tool_call_id": tool_call_id,
                "tool_name": tool_name,
                "result": result_str,
                "success": exec_result.get("success", False),
            }
            # 失败时把结构化错误一起带上，给前端做 UI 展示
            if not entry["success"] and "error_object" in exec_result:
                entry["error_object"] = exec_result["error_object"]
            results.append(entry)

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
