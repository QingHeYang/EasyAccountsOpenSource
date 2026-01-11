"""
EasyAccounts 内部工具集
个人财务管理系统的工具接口
"""

import json
import datetime
from typing import Any, Dict, List, Optional

import httpx

from ..base import BaseTool, ToolParam, tool
from ..registry import register_tool
from ...config.settings import config


# ==============================================================================
#                              参数定义
# ==============================================================================

# 年度统计参数
YEAR_STATISTICS_PARAMS = [
    ToolParam(
        name="year",
        param_type="integer",
        description="年份，必填。请先使用current_date工具获取当前年份",
        required=True
    )
]

# 流水查询参数
FLOWS_PARAMS = [
    ToolParam(
        name="title",
        param_type="string",
        description="操作标题，用于前端显示，如'查询12月支出'、'本月餐饮消费'",
        required=True
    ),
    ToolParam(
        name="handle",
        param_type="integer",
        description="收支类型：0=收入，1=支出，2=内部转账，3=全部。必填",
        required=True
    ),
    ToolParam(
        name="accountId",
        param_type="integer",
        description="账户ID，可选。使用accounts工具获取",
        required=False
    ),
    ToolParam(
        name="startDate",
        param_type="string",
        description="开始日期，格式yyyy-MM-dd",
        required=False
    ),
    ToolParam(
        name="endDate",
        param_type="string",
        description="结束日期，格式yyyy-MM-dd",
        required=False
    ),
    ToolParam(
        name="note",
        param_type="string",
        description="备注关键字，模糊查询。只支持单个关键字，尽量简短",
        required=False
    ),
    ToolParam(
        name="singleMonth",
        param_type="boolean",
        description="是否单月查询。设为true时无需endDate，startDate传当月1号",
        required=False
    ),
    ToolParam(
        name="types",
        param_type="array",
        description="分类ID列表。使用types工具获取分类ID",
        required=False,
        items={"type": "integer"}
    ),
    ToolParam(
        name="analysis",
        param_type="boolean",
        description="是否分析占比。设为true可查看每笔流水的收入/支出占比",
        required=False
    ),
    ToolParam(
        name="orderBy",
        param_type="integer",
        description="排序方式：0=金额升序，1=金额降序，2=时间排序",
        required=False
    )
]

# 添加流水参数
ADD_FLOW_PARAMS = [
    ToolParam(
        name="title",
        param_type="string",
        description="操作标题，用于前端显示，如'记录午餐支出'、'添加工资收入'",
        required=True
    ),
    ToolParam(
        name="accountId",
        param_type="integer",
        description="账户ID，必填。使用accounts工具获取",
        required=True
    ),
    ToolParam(
        name="typeId",
        param_type="integer",
        description="分类ID，必填。使用types工具获取",
        required=True
    ),
    ToolParam(
        name="actionId",
        param_type="integer",
        description="收支动作ID，必填。从types工具返回的action.id字段获取，不是handle值",
        required=True
    ),
    ToolParam(
        name="money",
        param_type="string",
        description="金额，必填。格式如'100.00'",
        required=True
    ),
    ToolParam(
        name="fDate",
        param_type="string",
        description="流水日期，必填。格式yyyy-MM-dd",
        required=True
    ),
    ToolParam(
        name="note",
        param_type="string",
        description="备注，必填。简要描述这笔流水的用途或来源，如'公司午餐'、'12月工资'",
        required=True
    ),
    ToolParam(
        name="accountToId",
        param_type="integer",
        description="转入账户ID，内部转账时必填。使用accounts工具获取",
        required=False
    ),
    ToolParam(
        name="collect",
        param_type="boolean",
        description="是否收藏，可选，默认false",
        required=False
    )
]

# 更新流水参数
UPDATE_FLOW_PARAMS = [
    ToolParam(
        name="title",
        param_type="string",
        description="操作标题，用于前端显示，如'修改午餐金额'、'更新备注信息'",
        required=True
    ),
    ToolParam(
        name="flowId",
        param_type="integer",
        description="流水ID，必填。通过flows工具查询获取",
        required=True
    ),
    # 复用添加流水的参数（跳过title，因为已经定义了）
    *[p for p in ADD_FLOW_PARAMS if p.name != "title"]
]

# 生成Excel参数
MAKE_EXCEL_PARAMS = [
    ToolParam(
        name="title",
        param_type="string",
        description="操作标题，用于前端显示，如'导出12月账单'、'生成年度报表'",
        required=True
    ),
    ToolParam(
        name="excelName",
        param_type="string",
        description="Excel文件名称，必填。不需要扩展名，如'2025年1月账单'",
        required=True
    ),
    ToolParam(
        name="handle",
        param_type="integer",
        description="收支类型：0=收入，1=支出，2=内部转账，3=全部。必填",
        required=True
    ),
    ToolParam(
        name="accountId",
        param_type="integer",
        description="账户ID，可选",
        required=False
    ),
    ToolParam(
        name="startDate",
        param_type="string",
        description="开始日期，格式yyyy-MM-dd",
        required=False
    ),
    ToolParam(
        name="endDate",
        param_type="string",
        description="结束日期，格式yyyy-MM-dd",
        required=False
    ),
    ToolParam(
        name="note",
        param_type="string",
        description="备注关键字",
        required=False
    ),
    ToolParam(
        name="singleMonth",
        param_type="boolean",
        description="是否单月查询",
        required=False
    ),
    ToolParam(
        name="types",
        param_type="array",
        description="分类ID列表",
        required=False,
        items={"type": "integer"}
    ),
    ToolParam(
        name="collect",
        param_type="boolean",
        description="是否只导出收藏的流水",
        required=False
    )
]


# ==============================================================================
#                              工具描述
# ==============================================================================

ACCOUNTS_DESC = "查询用户的资金账户列表。返回所有账户的ID、名称和余额信息。如果用户需要查询特定账户或需要账户ID，请使用该工具。"

TYPES_DESC = "获取所有账单分类(标签)信息。返回分类的层级结构，包含分类ID、名称、父子关系和对应的actionId。每个分类标注'可用'或'不可用'：有子分类的一级分类不可用，需使用其子分类；无子分类的一级分类和所有二级分类都可用。"

CURRENT_DATE_DESC = "获取当前服务器日期。如果用户询问的问题涉及日期、周期、时间段，请使用该工具获取当前日期作为参考。返回yyyy-MM-dd格式的日期。"

YEAR_STATISTICS_DESC = "获取指定年份的统计信息，包含每个月的收入、支出、盈余数据。如果用户询问某年某月的收支概况，请使用该工具。流水详情请使用flows工具。"

FLOWS_DESC = (
    "根据条件查询流水记录。支持多种查询条件组合：日期范围、账户、分类、关键字等。"
    "返回符合条件的流水列表和收支汇总。"
    "使用场景：1.查询某段时间的收支情况 2.查询特定分类的流水 3.按关键字搜索 4.分析支出占比"
)

ADD_FLOW_DESC = (
    "添加一条流水记录。可以记录收入、支出或内部转账。"
    "使用前请先：1.用accounts获取账户ID 2.用types获取分类ID和actionId（只能使用标注为'可用'的分类） 3.用current_date获取日期"
)

UPDATE_FLOW_DESC = "更新已有的流水记录。需要提供流水ID（通过flows工具查询获取）和完整的流水信息。分类只能使用标注为'可用'的分类。"

MAKE_EXCEL_DESC = (
    "根据流水查询条件生成Excel报表。参数与flows工具类似，输出为Excel文件下载链接。"
    "当流水数量较多时（超过100条），建议使用此工具导出完整报表。"
)

GET_FLOW_DESC = "根据流水ID获取单条流水的详细信息。包含完整的账户、分类、金额、日期、备注、图片等信息。"

# 获取流水详情参数
GET_FLOW_PARAMS = [
    ToolParam(
        name="flowId",
        param_type="integer",
        description="流水ID，必填。通过flows工具查询获取，或从add_flow/update_flow返回值获取",
        required=True
    )
]


# ==============================================================================
#                              HTTP 客户端
# ==============================================================================

class EasyAccountsClient:
    """EasyAccounts API 客户端"""

    def __init__(self, auth_token: Optional[str] = None):
        self.base_url = config.easyaccounts_url
        self.auth_token = auth_token

    def _build_headers(self, content_type: Optional[str] = None) -> Dict[str, str]:
        headers = {}
        if self.auth_token:
            headers["authorization"] = self.auth_token
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _handle_auth_error(self, response_text: str) -> Dict[str, Any]:
        return {
            "error": "认证失败",
            "status": 401,
            "message": "EasyAccounts系统已开启登录鉴权",
            "guidance": "请先在EasyAccounts网页端登录，然后重新连接AI对话"
        }


def _get_client(context: Dict[str, Any]) -> EasyAccountsClient:
    """从上下文获取客户端

    token 查找优先级：
    1. authorization / Authorization
    2. auth_token
    3. token
    4. easyaccounts_token
    """
    auth_token = None
    agent = context.get("agent")
    if agent:
        tool_tokens = getattr(agent, "tool_tokens", {})
        if isinstance(tool_tokens, dict):
            # 按优先级查找 token
            auth_token = (
                tool_tokens.get("authorization") or
                tool_tokens.get("Authorization") or
                tool_tokens.get("auth_token") or
                tool_tokens.get("token") or
                tool_tokens.get("easyaccounts_token")
            )
    return EasyAccountsClient(auth_token=auth_token)


# ==============================================================================
#                              工具实现
# ==============================================================================

@register_tool
@tool(name="accounts", description=ACCOUNTS_DESC, parameters=[])
class AccountsTool(BaseTool):
    """查询账户列表"""

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            client = _get_client(context)
            url = f"{client.base_url}/account/getAccount"

            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(url, headers=client._build_headers())

                if response.status_code == 401:
                    return self._error(error=json.dumps(client._handle_auth_error(response.text), ensure_ascii=False))

                return self._success(result=json.dumps(response.json(), ensure_ascii=False))
        except Exception as e:
            return self._error(error=f"获取账户列表失败: {str(e)}")


@register_tool
@tool(name="types", description=TYPES_DESC, parameters=[])
class TypesTool(BaseTool):
    """获取分类信息"""

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            client = _get_client(context)
            url = f"{client.base_url}/type/getType"

            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(url, headers=client._build_headers())

                if response.status_code == 401:
                    return self._error(error=json.dumps(client._handle_auth_error(response.text), ensure_ascii=False))

                raw = response.json()
                data = raw.get("data", []) if isinstance(raw, dict) and "data" in raw else (raw if isinstance(raw, list) else [])

                def format_desc(cat, usable: bool):
                    action = cat.get("action")
                    usable_str = "可用" if usable else "不可用"
                    if action:
                        return f"id={cat.get('id')},name={cat.get('tname')},actionId={action.get('id')},handle={action.get('handle')},handleName={action.get('hname')},{usable_str}"
                    return f"id={cat.get('id')},name={cat.get('tname')},actionId=null,{usable_str}"

                result = []
                for cat in data:
                    children_data = cat.get("childrenTypes") or []
                    has_children = len(children_data) > 0
                    # 一级分类有子分类则不可用，二级分类都可用
                    children = [format_desc(child, usable=True) for child in children_data]
                    result.append({"description": format_desc(cat, usable=not has_children), "children": children})

                return self._success(result=json.dumps(result, ensure_ascii=False))
        except Exception as e:
            return self._error(error=f"获取分类失败: {str(e)}")


@register_tool
@tool(name="current_date", description=CURRENT_DATE_DESC, parameters=[])
class CurrentDateTool(BaseTool):
    """获取当前日期"""

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            now = datetime.datetime.now()
            result = {
                "today": now.strftime("%Y-%m-%d"),
                "year": now.strftime("%Y"),
                "month": now.strftime("%m"),
                "day": now.strftime("%d"),
                "week": now.strftime("%w")
            }
            return self._success(result=json.dumps(result, ensure_ascii=False))
        except Exception as e:
            return self._error(error=f"获取日期失败: {str(e)}")


@register_tool
@tool(name="year_statistics", description=YEAR_STATISTICS_DESC, parameters=YEAR_STATISTICS_PARAMS)
class YearStatisticsTool(BaseTool):
    """获取年度统计"""

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            year = arguments.get("year")
            if not year:
                return self._error(error="缺少必要参数: year")

            client = _get_client(context)
            url = f"{client.base_url}/home/getHomeInfoV2/{year}"

            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(url, headers=client._build_headers())

                if response.status_code == 401:
                    return self._error(error=json.dumps(client._handle_auth_error(response.text), ensure_ascii=False))

                return self._success(result=json.dumps(response.json(), ensure_ascii=False))
        except Exception as e:
            return self._error(error=f"获取年度统计失败: {str(e)}")


@register_tool
@tool(name="flows", description=FLOWS_DESC, parameters=FLOWS_PARAMS)
class FlowsTool(BaseTool):
    """查询流水"""

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            handle = arguments.get("handle")
            if handle is None:
                return self._error(error="缺少必要参数: handle")
            if int(handle) > 3 or int(handle) < 0:
                return self._error(error="handle参数错误，请传入0-3之间的整数")

            client = _get_client(context)
            url = f"{client.base_url}/screen/getFlowByScreen"

            payload = {
                "accountId": arguments.get("accountId"),
                "actions": [],
                "chooseHandle": handle,
                "collect": "false",
                "endDate": arguments.get("endDate"),
                "note": arguments.get("note"),
                "singleMonth": arguments.get("singleMonth"),
                "startDate": arguments.get("startDate"),
                "types": arguments.get("types"),
            }
            payload = {k: v for k, v in payload.items() if v is not None}

            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(
                    url,
                    headers=client._build_headers(content_type="application/json"),
                    json=payload
                )

                if response.status_code == 401:
                    return self._error(error=json.dumps(client._handle_auth_error(response.text), ensure_ascii=False))

                flows_data = response.json()
                data = flows_data.get("data", {})
                totalIn, totalOut, totalEarn = data.get("totalIn", "0"), data.get("totalOut", "0"), data.get("totalEarn", "0")
                flows = data.get("flows", [])
                total_count = len(flows)

                # 排序
                orderBy = arguments.get("orderBy")
                if orderBy == 0:
                    flows.sort(key=lambda x: float(x.get("money", 0)))
                elif orderBy == 1:
                    flows.sort(key=lambda x: float(x.get("money", 0)), reverse=True)

                # 截断
                MAX_FLOWS = 100
                is_truncated = total_count > MAX_FLOWS
                if is_truncated:
                    flows = flows[:MAX_FLOWS]

                # 格式化
                analysis = arguments.get("analysis", False)
                flows_list = []
                for flow in flows:
                    parts = [
                        f"流水ID:{flow.get('id')}", f"收支:{flow.get('hname')}", f"金额:{flow.get('money')}",
                        f"账户:{flow.get('aname')}", f"分类:{flow.get('tname')}", f"时间:{flow.get('fdate')}"
                    ]
                    if analysis:
                        money = float(flow.get("money", 0))
                        if handle == 0 and float(totalIn) > 0:
                            parts.append(f"占比:{money/float(totalIn)*100:.2f}%")
                        elif handle == 1 and float(totalOut) > 0:
                            parts.append(f"占比:{money/float(totalOut)*100:.2f}%")
                    if flow.get('toAName'):
                        parts.append(f"转到:{flow.get('toAName')}")
                    if flow.get('note'):
                        parts.append(f"备注:{flow.get('note')}")
                    flows_list.append(";".join(parts))

                # 构建前端可直接使用的查询参数（与前端调用接口一致）
                query_params = {
                    "accountId": arguments.get("accountId"),
                    "actions": [],
                    "chooseHandle": handle,
                    "collect": "false",
                    "endDate": arguments.get("endDate"),
                    "note": arguments.get("note"),
                    "singleMonth": arguments.get("singleMonth"),
                    "startDate": arguments.get("startDate"),
                    "types": arguments.get("types"),
                }
                # 移除 None 值
                query_params = {k: v for k, v in query_params.items() if v is not None}

                result = {
                    "summary": f"收入={totalIn},支出={totalOut},盈余={totalEarn}",
                    "flows": flows_list,
                    "total_count": total_count,
                    "returned_count": len(flows_list),
                    "is_truncated": is_truncated,
                    "queryParams": query_params  # 前端可直接用于调用筛选接口
                }
                if is_truncated:
                    result["notice"] = f"共{total_count}条，仅返回前{MAX_FLOWS}条，建议使用make_excel导出完整报表"

                return self._success(result=json.dumps(result, ensure_ascii=False))
        except Exception as e:
            return self._error(error=f"查询流水失败: {str(e)}")


@register_tool
@tool(name="add_flow", description=ADD_FLOW_DESC, parameters=ADD_FLOW_PARAMS)
class AddFlowTool(BaseTool):
    """添加流水"""

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            required = ["accountId", "typeId", "actionId", "money", "fDate"]
            for param in required:
                if param not in arguments:
                    return self._error(error=f"缺少必要参数: {param}")

            client = _get_client(context)
            url = f"{client.base_url}/flow/addFlow"

            # 处理备注，自动追加 #AI记账 标记
            note = arguments.get("note", "")
            if note and "#AI记账" not in note:
                note = f"{note} #AI记账"
            elif not note:
                note = "#AI记账"

            payload = {
                "accountId": arguments["accountId"],
                "typeId": arguments["typeId"],
                "actionId": arguments["actionId"],
                "money": arguments["money"],
                "fDate": arguments["fDate"],
                "note": note,
                "collect": arguments.get("collect", False),
                "createDate": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "from": "ai"
            }
            if arguments.get("accountToId") is not None:
                payload["accountToId"] = arguments["accountToId"]

            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(
                    url,
                    headers=client._build_headers(content_type="application/json"),
                    json=payload
                )

                if response.status_code == 401:
                    return self._error(error=json.dumps(client._handle_auth_error(response.text), ensure_ascii=False))

                resp_data = response.json()

                # 检查业务错误码（HTTP 200 但 code 不为 0）
                if resp_data.get("code") != 0:
                    error_code = resp_data.get("code")
                    error_msg = resp_data.get("msg", "未知错误")
                    return self._error(error=f"记账失败[{error_code}]: {error_msg}")

                # 成功：data 是对象 {"id": 123}
                flow_id = None
                if isinstance(resp_data.get("data"), dict):
                    flow_id = resp_data["data"].get("id")

                return self._success(result=json.dumps({
                    "success": True,
                    "message": "流水添加成功",
                    "flowId": flow_id  # 前端可直接用于查看详情
                }, ensure_ascii=False))
        except Exception as e:
            return self._error(error=f"添加流水失败: {str(e)}")


@register_tool
@tool(name="update_flow", description=UPDATE_FLOW_DESC, parameters=UPDATE_FLOW_PARAMS)
class UpdateFlowTool(BaseTool):
    """更新流水"""

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            required = ["flowId", "accountId", "typeId", "actionId", "money", "fDate"]
            for param in required:
                if param not in arguments:
                    return self._error(error=f"缺少必要参数: {param}")

            flow_id = arguments["flowId"]
            client = _get_client(context)
            url = f"{client.base_url}/flow/updateFlow/{flow_id}"

            # 处理备注，自动追加 #AI更新 标记
            note = arguments.get("note", "")
            if note and "#AI更新" not in note:
                note = f"{note} #AI更新"
            elif not note:
                note = "#AI更新"

            payload = {
                "accountId": arguments["accountId"],
                "typeId": arguments["typeId"],
                "actionId": arguments["actionId"],
                "money": arguments["money"],
                "fDate": arguments["fDate"],
                "note": note,
                "collect": arguments.get("collect", False),
                "createDate": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "from": "ai"
            }
            if arguments.get("accountToId") is not None:
                payload["accountToId"] = arguments["accountToId"]

            async with httpx.AsyncClient() as http_client:
                response = await http_client.put(
                    url,
                    headers=client._build_headers(content_type="application/json"),
                    json=payload
                )

                if response.status_code == 401:
                    return self._error(error=json.dumps(client._handle_auth_error(response.text), ensure_ascii=False))

                resp_data = response.json()

                # 检查业务错误码（HTTP 200 但 code 不为 0）
                if resp_data.get("code") != 0:
                    error_code = resp_data.get("code")
                    error_msg = resp_data.get("msg", "未知错误")
                    return self._error(error=f"更新失败[{error_code}]: {error_msg}")

                return self._success(result=json.dumps({
                    "success": True,
                    "message": f"流水ID={flow_id}更新成功",
                    "flowId": flow_id  # 前端可直接用于查看详情
                }, ensure_ascii=False))
        except Exception as e:
            return self._error(error=f"更新流水失败: {str(e)}")


@register_tool
@tool(name="make_excel", description=MAKE_EXCEL_DESC, parameters=MAKE_EXCEL_PARAMS)
class MakeExcelTool(BaseTool):
    """生成Excel报表"""

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            excel_name = arguments.get("excelName")
            handle = arguments.get("handle")
            if not excel_name:
                return self._error(error="缺少必要参数: excelName")
            if handle is None:
                return self._error(error="缺少必要参数: handle")
            if int(handle) > 3 or int(handle) < 0:
                return self._error(error="handle参数错误，请传入0-3之间的整数")

            client = _get_client(context)
            url = f"{client.base_url}/screen/makeExcel?excelName={excel_name}"

            payload = {
                "accountId": arguments.get("accountId"),
                "actions": [],
                "chooseHandle": handle,
                "endDate": arguments.get("endDate"),
                "note": arguments.get("note"),
                "singleMonth": arguments.get("singleMonth"),
                "startDate": arguments.get("startDate"),
                "types": arguments.get("types"),
                "collect": str(arguments.get("collect", False)).lower()
            }
            payload = {k: v for k, v in payload.items() if v is not None}

            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(
                    url,
                    headers=client._build_headers(content_type="application/json"),
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    data = result.get("data", {})
                    return self._success(result=json.dumps({
                        "success": True,
                        "message": "Excel报表生成成功",
                        "fileName": data.get("fileName", f"{excel_name}.xlsx"),
                        "downloadUrl": data.get("downloadUrl", "")
                    }, ensure_ascii=False))
                elif response.status_code == 401:
                    return self._error(error=json.dumps(client._handle_auth_error(response.text), ensure_ascii=False))
                else:
                    error_msg = response.json().get('msg', response.text) if response.text else "未知错误"
                    return self._error(error=f"生成Excel失败: {error_msg}")
        except Exception as e:
            return self._error(error=f"生成Excel失败: {str(e)}")


@register_tool
@tool(name="get_flow", description=GET_FLOW_DESC, parameters=GET_FLOW_PARAMS)
class GetFlowTool(BaseTool):
    """根据ID获取流水详情"""

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            flow_id = arguments.get("flowId")
            if flow_id is None:
                return self._error(error="缺少必要参数: flowId")

            client = _get_client(context)
            url = f"{client.base_url}/flow/getFlow/{flow_id}"

            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(url, headers=client._build_headers())

                if response.status_code == 401:
                    return self._error(error=json.dumps(client._handle_auth_error(response.text), ensure_ascii=False))

                resp_data = response.json()
                if resp_data.get("code") != 0:
                    return self._error(error=resp_data.get("msg", "获取流水失败"))

                data = resp_data.get("data", {})
                if not data:
                    return self._error(error=f"未找到流水ID={flow_id}")

                # 格式化返回结果
                result = {
                    "flowId": data.get("id"),
                    "money": data.get("money"),
                    "date": data.get("fdate"),
                    "note": data.get("note"),
                    "collect": data.get("collect"),
                    "from": data.get("from"),
                    "images": data.get("images", []),
                    # 账户信息
                    "account": {
                        "id": data.get("account", {}).get("id"),
                        "name": data.get("account", {}).get("aname"),
                        "balance": data.get("account", {}).get("money")
                    } if data.get("account") else None,
                    # 转入账户（内部转账时）
                    "accountTo": {
                        "id": data.get("accountTo", {}).get("id"),
                        "name": data.get("accountTo", {}).get("aname"),
                        "balance": data.get("accountTo", {}).get("money")
                    } if data.get("accountTo") else None,
                    # 收支动作
                    "action": {
                        "id": data.get("action", {}).get("id"),
                        "handle": data.get("action", {}).get("handle"),
                        "name": data.get("action", {}).get("hname")
                    } if data.get("action") else None,
                    # 分类信息
                    "type": {
                        "id": data.get("type", {}).get("id"),
                        "name": data.get("type", {}).get("tname"),
                        "parent": data.get("type", {}).get("parent")
                    } if data.get("type") else None
                }

                return self._success(result=json.dumps(result, ensure_ascii=False))
        except Exception as e:
            return self._error(error=f"获取流水详情失败: {str(e)}")
