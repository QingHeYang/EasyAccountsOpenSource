"""
call_agent 内部工具
用于调用其他Agent协作完成任务
"""

from typing import Any, Dict, List

from ..base import BaseTool, ToolParam, tool
from ..registry import register_tool
from ...models import AgentCall


@register_tool
@tool(
    name="call_agent",
    description="调用其他智能助手来协助完成特定任务",
    parameters=[
        ToolParam(
            name="agent_id",
            param_type="string",
            description="要调用的智能助手ID",
            required=True,
            enum=[]  # 动态填充，由AgentToolBinder设置
        ),
        ToolParam(
            name="task",
            param_type="string",
            description="需要该智能助手完成的具体任务描述",
            required=True
        ),
        ToolParam(
            name="context",
            param_type="object",
            description="传递给智能助手的上下文信息（可选）",
            required=False
        )
    ]
)
class CallAgentTool(BaseTool):
    """调用其他Agent的内部工具"""

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行Agent调用

        Args:
            arguments: 工具参数
                - agent_id: 目标Agent ID
                - task: 任务描述
                - context: 上下文信息（可选）
            context: 执行上下文
                - sub_agent_executor: SubAgentExecutor实例
                - conversation_id: 当前会话ID
                - user_id: 用户ID
                - agent: 当前Agent实例

        Returns:
            执行结果
        """
        # 提取参数
        agent_id = arguments.get("agent_id")
        task = arguments.get("task")
        agent_context = arguments.get("context", {})

        # 获取SubAgentExecutor
        sub_agent_executor = context.get("sub_agent_executor")
        if not sub_agent_executor:
            return self._error("缺少SubAgentExecutor，无法执行Agent调用")

        # 构建AgentCall对象
        agent_call = AgentCall(
            agent_id=agent_id,
            task=task,
            context=agent_context
        )

        # 调用SubAgentExecutor执行
        try:
            result = await sub_agent_executor.execute(agent_call, context)

            # SubAgentExecutor返回ExecutionResult对象
            if result.success:
                return self._success(
                    result=result.result,
                    metadata={
                        "agent_id": agent_id,
                        **(result.metadata or {})
                    }
                )
            else:
                return self._error(
                    error=result.error or "Agent执行失败",
                    metadata={"agent_id": agent_id}
                )

        except Exception as e:
            return self._error(
                error=f"Agent调用异常: {str(e)}",
                metadata={"agent_id": agent_id}
            )
