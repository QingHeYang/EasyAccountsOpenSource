"""
get_time 内部工具
查询当前时间信息
"""

from datetime import datetime
from typing import Any, Dict

from ..base import BaseTool, ToolParam, tool
from ..registry import register_tool


# 星期几的中文映射
WEEKDAY_NAMES = {
    0: "星期一",
    1: "星期二",
    2: "星期三",
    3: "星期四",
    4: "星期五",
    5: "星期六",
    6: "星期日"
}


@register_tool
@tool(
    name="get_time",
    description="获取当前的日期、时间、星期几和时区信息",
    parameters=[
        ToolParam(
            name="timezone",
            param_type="string",
            description="时区名称，如 'Asia/Shanghai'、'UTC'、'America/New_York'。默认为系统本地时区。",
            required=False
        )
    ]
)
class GetTimeTool(BaseTool):
    """获取当前时间信息的工具"""

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行时间查询

        Args:
            arguments: 工具参数
                - timezone: 可选的时区名称
            context: 执行上下文

        Returns:
            包含日期、时间、星期几、时区的结果
        """
        timezone_name = arguments.get("timezone")

        try:
            if timezone_name:
                # 使用指定时区
                try:
                    import zoneinfo
                    tz = zoneinfo.ZoneInfo(timezone_name)
                    now = datetime.now(tz)
                except Exception:
                    # 如果 zoneinfo 不可用或时区无效，回退到本地时间
                    now = datetime.now()
                    timezone_name = "本地时区（指定时区无效）"
            else:
                # 使用本地时区
                now = datetime.now().astimezone()
                timezone_name = str(now.tzinfo) if now.tzinfo else "本地时区"

            # 格式化结果
            result = {
                "日期": now.strftime("%Y年%m月%d日"),
                "时间": now.strftime("%H:%M:%S"),
                "星期": WEEKDAY_NAMES[now.weekday()],
                "时区": timezone_name,
                "完整时间": now.strftime("%Y-%m-%d %H:%M:%S %Z")
            }

            # 返回格式化的字符串给 LLM
            result_text = (
                f"当前时间信息：\n"
                f"- 日期：{result['日期']}\n"
                f"- 时间：{result['时间']}\n"
                f"- 星期：{result['星期']}\n"
                f"- 时区：{result['时区']}"
            )

            return self._success(result=result_text)

        except Exception as e:
            return self._error(error=f"获取时间失败: {str(e)}")
