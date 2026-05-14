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
from ..error_codes import (
    E_FLOW_NOT_FOUND,
    E_PARAM_INVALID,
    E_PARAM_MISSING,
    ToolError,
    from_backend_response,
    from_exception,
    make_error,
)
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
        description="收支类型：0=只看收入，1=只看支出，2=只看转账，3=全部。看全部必须传3，不是0。必填",
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
        description="开始日期，格式严格yyyy-MM-dd（10位，如2026-04-09，不要写2026-4-9）",
        required=False
    ),
    ToolParam(
        name="endDate",
        param_type="string",
        description="结束日期，格式严格yyyy-MM-dd（10位）",
        required=False
    ),
    ToolParam(
        name="note",
        param_type="string",
        description="备注关键字，模糊匹配（LIKE）。只传单个关键字，尽量简短",
        required=False
    ),
    ToolParam(
        name="singleMonth",
        param_type="boolean",
        description="是否单月查询。设为true时只看startDate所在月（取yyyy-MM），endDate被忽略",
        required=False
    ),
    ToolParam(
        name="types",
        param_type="array",
        description="分类ID列表。组内OR；选父分类会自动包含其全部子分类。使用types工具获取分类ID",
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
        description="动作ID，必填。优先从types返回的节点action.id字段获取；若该节点action为null，调用actions工具按收支语义选一个。actionId 不是 handle 值",
        required=True
    ),
    ToolParam(
        name="money",
        param_type="string",
        description="金额，必填。只传正数，2位小数（如'30.00'）。方向由action.handle决定，不要带负号；不要预判余额（v2.6.0起允许账户负余额）",
        required=True
    ),
    ToolParam(
        name="fDate",
        param_type="string",
        description="流水业务日期，必填。格式严格yyyy-MM-dd（10位，如2026-04-09，不要写2026-4-9）",
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
        description="转入账户ID。仅当action.handle=2（内部转账）时必填，其他场景不要传。使用accounts工具获取",
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
        description="收支类型：0=只看收入，1=只看支出，2=只看转账，3=全部。看全部必须传3。必填",
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
        description="开始日期，格式严格yyyy-MM-dd（10位）",
        required=False
    ),
    ToolParam(
        name="endDate",
        param_type="string",
        description="结束日期，格式严格yyyy-MM-dd（10位）",
        required=False
    ),
    ToolParam(
        name="note",
        param_type="string",
        description="备注关键字，模糊匹配",
        required=False
    ),
    ToolParam(
        name="singleMonth",
        param_type="boolean",
        description="是否单月查询。true时只看startDate所在月，endDate被忽略",
        required=False
    ),
    ToolParam(
        name="types",
        param_type="array",
        description="分类ID列表。组内OR；选父分类会自动包含其全部子分类",
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

ACTIONS_DESC = (
    "获取所有收支动作(action)列表。返回每个动作的ID、名称和收支类型(handle)。"
    "仅当 types 工具返回的分类节点上 action 为 null（通用分类）时才需要调用本工具。"
    "handle 含义：0=收入，1=支出，2=内部转账。按用户的收支语义选对应 handle 的 action。"
)

ACCOUNTS_DESC = (
    "查询用户的资金账户列表，返回每个账户的 id、name 和当前余额（money，字符串）。"
    "需要 accountId、查询特定账户、或查看余额时调用。"
    "余额可能为负数（信用卡等场景），不要做余额够不够的预判。"
)

TYPES_DESC = (
    "获取记账分类树，每个节点含 id、name、actionId、handle、handleName，并附标注'可用'/'不可用'。"
    "可用性判断：节点没有子分类（叶子）→ 可用；节点有子分类且自身 actionId=null（通用容器）→ 可用；"
    "节点有子分类且自身 actionId 不为 null → 不可用，记账时必须改用其子分类。"
    "误用'不可用'的分类记账，后端会返回 E_TYPE_HAS_CHILDREN 错误。"
)

CURRENT_DATE_DESC = (
    "获取当前服务器日期。涉及日期、周期、时间段查询前必须先调用，拿到 yyyy-MM-dd 作为参考。"
)

YEAR_STATISTICS_DESC = (
    "获取指定年份的概览：年度总收入、总支出、盈余，以及各月份的收支盈余。"
    "用户问某年/某月概况时调用。统计口径不含转账（handle=2）。"
    "需要具体流水明细时改用 flows 工具。"
)

FLOWS_DESC = (
    "按条件查询流水。支持账户、日期范围、分类、动作、关键字、收藏等组合筛选。"
    "返回流水列表 + 收支汇总（totalIn/totalOut/totalEarn，不含转账）。"
    "关键规则：handle=3 表示全部（不是 0）；types 多选组内 OR、选父分类自动包含子分类；"
    "types 与 actions 同时传组间 AND；singleMonth=true 时只看 startDate 所在月。"
    "返回超 100 条会被截断，提示用户用 make_excel 导出完整报表。"
)

ADD_FLOW_DESC = (
    "添加一条流水。流程：1) accounts 拿 accountId；"
    "2) types 拿 typeId（只能用'可用'的分类）和该节点的 action；"
    "3) 节点 action 不为 null → 直接用 action.id 作为 actionId；为 null → 调 actions 按收支语义选；"
    "4) current_date 拿日期（用户没指定时）。"
    "money 只传正数 2 位小数，方向由 action.handle 决定。"
    "仅当 action.handle=2（内部转账）时需要 accountToId。"
)

UPDATE_FLOW_DESC = (
    "更新已有流水。需要先用 flows 或 get_flow 拿到流水 id 和原始 from 字段。"
    "分类只能使用'可用'的分类，actionId 来源同 add_flow。"
    "注意：from 字段不传会被后端置空，必须把 get_flow 拿到的 from 原样传回去。"
)

MAKE_EXCEL_DESC = (
    "按筛选条件生成 Excel 报表。注意：本工具不返回下载链接，"
    "实际是后端生成 Excel 文件后通过邮件发送到用户配置的邮箱。"
    "流水超过 100 条或用户明确要求导出时使用。"
    "若返回 hint 提示邮件未配置（E_MAIL_NOT_CONFIGURED），告诉用户去'系统设置 → 邮件'配 SMTP。"
)

GET_FLOW_DESC = (
    "根据流水 id 获取单条流水的完整信息：账户、转入账户（仅转账）、分类、动作、金额、日期、备注、from、images 等。"
    "更新流水前必须先用本工具拿到 from 字段。"
)

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
        # 使用 tool_execution_timeout（默认 60s），httpx 默认 5s 太短，
        # 后端 JPA+MyBatis 混用 + OSIV 偶发 5+s，会被误报为 E_TIMEOUT
        self.timeout = config.tool_execution_timeout

    def _build_headers(self, content_type: Optional[str] = None) -> Dict[str, str]:
        headers = {}
        if self.auth_token:
            headers["authorization"] = self.auth_token
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def async_client(self) -> "httpx.AsyncClient":
        """返回配置好 timeout 的 httpx 客户端，调用方用 async with 包裹。

        trust_env=True（httpx 默认）：跟随系统代理。
        EasyAccounts 后端若配置为公网域名，需要走代理才能访问；
        本地 127.0.0.1 走代理由代理客户端的 noProxy 规则放行（Clash/V2Ray 默认放行本地）。
        """
        return httpx.AsyncClient(timeout=self.timeout)

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


def _check_response(response: httpx.Response) -> Optional[ToolError]:
    """统一的后端响应错误识别。返回 ToolError 表示需要报错；返回 None 表示成功。

    覆盖：
      - HTTP 4xx/5xx
      - HTTP 200 + BaseDto.code != 0（业务错误）
    """
    backend_code = None
    backend_msg = None
    try:
        body = response.json()
        if isinstance(body, dict):
            backend_code = body.get("code")
            backend_msg = body.get("msg")
    except Exception:
        pass

    if response.status_code != 200:
        return from_backend_response(response.status_code, backend_code, backend_msg)
    if backend_code is not None and backend_code != 0:
        return from_backend_response(response.status_code, backend_code, backend_msg)
    return None


# ==============================================================================
#                              工具实现
# ==============================================================================

@register_tool
@tool(name="actions", description=ACTIONS_DESC, parameters=[])
class ActionsTool(BaseTool):
    """获取收支动作列表"""

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            client = _get_client(context)
            url = f"{client.base_url}/action/getAction"

            async with client.async_client() as http_client:
                response = await http_client.get(url, headers=client._build_headers())

                err = _check_response(response)
                if err:
                    return self._error(error_obj=err)

                raw = response.json()
                data = raw.get("data", []) if isinstance(raw, dict) else raw

                # 格式化：只返回关键信息
                result = []
                for action in data:
                    if action.get("disable"):
                        continue
                    result.append(
                        f"actionId={action.get('id')},name={action.get('hname')},handle={action.get('handle')}"
                    )

                return self._success(result=json.dumps(result, ensure_ascii=False))
        except Exception as e:
            return self._error(error_obj=from_exception(e))


@register_tool
@tool(name="accounts", description=ACCOUNTS_DESC, parameters=[])
class AccountsTool(BaseTool):
    """查询账户列表"""

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            client = _get_client(context)
            url = f"{client.base_url}/account/getAccount"

            async with client.async_client() as http_client:
                response = await http_client.get(url, headers=client._build_headers())

                err = _check_response(response)
                if err:
                    return self._error(error_obj=err)

                return self._success(result=json.dumps(response.json(), ensure_ascii=False))
        except Exception as e:
            return self._error(error_obj=from_exception(e))


@register_tool
@tool(name="types", description=TYPES_DESC, parameters=[])
class TypesTool(BaseTool):
    """获取分类信息"""

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            client = _get_client(context)
            url = f"{client.base_url}/type/getType"

            async with client.async_client() as http_client:
                response = await http_client.get(url, headers=client._build_headers())

                err = _check_response(response)
                if err:
                    return self._error(error_obj=err)

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
                    # 可用性规则：叶子可用；有子分类但自身 actionId=null（通用容器）也可用；
                    # 有子分类且自身 actionId!=null → 不可用（必须用子分类，否则后端 42002）
                    parent_usable = (not has_children) or (cat.get("action") is None)
                    # 子分类（二级）一律按叶子处理
                    children = [format_desc(child, usable=True) for child in children_data]
                    result.append({"description": format_desc(cat, usable=parent_usable), "children": children})

                return self._success(result=json.dumps(result, ensure_ascii=False))
        except Exception as e:
            return self._error(error_obj=from_exception(e))


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
            return self._error(error_obj=from_exception(e))


@register_tool
@tool(name="year_statistics", description=YEAR_STATISTICS_DESC, parameters=YEAR_STATISTICS_PARAMS)
class YearStatisticsTool(BaseTool):
    """获取年度统计"""

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            year = arguments.get("year")
            if not year:
                return self._error(code=E_PARAM_MISSING, message="缺少必要参数: year")

            client = _get_client(context)
            url = f"{client.base_url}/home/getHomeInfoV2/{year}"

            async with client.async_client() as http_client:
                response = await http_client.get(url, headers=client._build_headers())

                err = _check_response(response)
                if err:
                    return self._error(error_obj=err)

                return self._success(result=json.dumps(response.json(), ensure_ascii=False))
        except Exception as e:
            return self._error(error_obj=from_exception(e))


@register_tool
@tool(name="flows", description=FLOWS_DESC, parameters=FLOWS_PARAMS)
class FlowsTool(BaseTool):
    """查询流水"""

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            handle = arguments.get("handle")
            if handle is None:
                return self._error(code=E_PARAM_MISSING, message="缺少必要参数: handle")
            if int(handle) > 3 or int(handle) < 0:
                return self._error(code=E_PARAM_INVALID, message="handle 取值非法，仅允许 0/1/2/3")

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

            async with client.async_client() as http_client:
                response = await http_client.post(
                    url,
                    headers=client._build_headers(content_type="application/json"),
                    json=payload
                )

                err = _check_response(response)
                if err:
                    return self._error(error_obj=err)

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
            return self._error(error_obj=from_exception(e))


@register_tool
@tool(name="add_flow", description=ADD_FLOW_DESC, parameters=ADD_FLOW_PARAMS)
class AddFlowTool(BaseTool):
    """添加流水"""

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            required = ["accountId", "typeId", "actionId", "money", "fDate"]
            for param in required:
                if param not in arguments:
                    return self._error(code=E_PARAM_MISSING, message=f"缺少必要参数: {param}")

            client = _get_client(context)
            url = f"{client.base_url}/flow/addFlow"

            # 处理备注，自动追加 #AI记账 标记
            note = arguments.get("note", "")
            if note and "#AI记账" not in note:
                note = f"{note} #AI记账"
            elif not note:
                note = "#AI记账"

            # 金额修正：去掉负号，系统根据收支类型自动处理正负
            money = str(arguments["money"]).strip()
            if money.startswith("-"):
                money = money[1:]

            payload = {
                "accountId": arguments["accountId"],
                "typeId": arguments["typeId"],
                "actionId": arguments["actionId"],
                "money": money,
                "fDate": arguments["fDate"],
                "note": note,
                "collect": arguments.get("collect", False),
                "createDate": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "from": "ai"
            }
            if arguments.get("accountToId") is not None:
                payload["accountToId"] = arguments["accountToId"]

            async with client.async_client() as http_client:
                response = await http_client.post(
                    url,
                    headers=client._build_headers(content_type="application/json"),
                    json=payload
                )

                err = _check_response(response)
                if err:
                    return self._error(error_obj=err)

                resp_data = response.json()
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
            return self._error(error_obj=from_exception(e))


@register_tool
@tool(name="update_flow", description=UPDATE_FLOW_DESC, parameters=UPDATE_FLOW_PARAMS)
class UpdateFlowTool(BaseTool):
    """更新流水"""

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            required = ["flowId", "accountId", "typeId", "actionId", "money", "fDate"]
            for param in required:
                if param not in arguments:
                    return self._error(code=E_PARAM_MISSING, message=f"缺少必要参数: {param}")

            flow_id = arguments["flowId"]
            client = _get_client(context)
            url = f"{client.base_url}/flow/updateFlow/{flow_id}"

            # 处理备注，自动追加 #AI更新 标记
            note = arguments.get("note", "")
            if note and "#AI更新" not in note:
                note = f"{note} #AI更新"
            elif not note:
                note = "#AI更新"

            # 金额修正：去掉负号，系统根据收支类型自动处理正负
            money = str(arguments["money"]).strip()
            if money.startswith("-"):
                money = money[1:]

            payload = {
                "accountId": arguments["accountId"],
                "typeId": arguments["typeId"],
                "actionId": arguments["actionId"],
                "money": money,
                "fDate": arguments["fDate"],
                "note": note,
                "collect": arguments.get("collect", False),
                "createDate": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "from": "ai"
            }
            if arguments.get("accountToId") is not None:
                payload["accountToId"] = arguments["accountToId"]

            async with client.async_client() as http_client:
                response = await http_client.put(
                    url,
                    headers=client._build_headers(content_type="application/json"),
                    json=payload
                )

                err = _check_response(response)
                if err:
                    return self._error(error_obj=err)

                return self._success(result=json.dumps({
                    "success": True,
                    "message": f"流水ID={flow_id}更新成功",
                    "flowId": flow_id  # 前端可直接用于查看详情
                }, ensure_ascii=False))
        except Exception as e:
            return self._error(error_obj=from_exception(e))


@register_tool
@tool(name="make_excel", description=MAKE_EXCEL_DESC, parameters=MAKE_EXCEL_PARAMS)
class MakeExcelTool(BaseTool):
    """生成Excel报表"""

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            excel_name = arguments.get("excelName")
            handle = arguments.get("handle")
            if not excel_name:
                return self._error(code=E_PARAM_MISSING, message="缺少必要参数: excelName")
            if handle is None:
                return self._error(code=E_PARAM_MISSING, message="缺少必要参数: handle")
            if int(handle) > 3 or int(handle) < 0:
                return self._error(code=E_PARAM_INVALID, message="handle 取值非法，仅允许 0/1/2/3")

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

            async with client.async_client() as http_client:
                response = await http_client.post(
                    url,
                    headers=client._build_headers(content_type="application/json"),
                    json=payload
                )

                err = _check_response(response)
                if err:
                    return self._error(error_obj=err)

                # 后端返回 {success, log}，不含下载链接（实际是发邮件）
                result = response.json()
                data = result.get("data", {}) if isinstance(result, dict) else {}
                return self._success(result=json.dumps({
                    "success": data.get("success", True),
                    "message": "Excel 报表已生成（通过邮件发送到用户邮箱）",
                    "log": data.get("log", "")
                }, ensure_ascii=False))
        except Exception as e:
            return self._error(error_obj=from_exception(e))


@register_tool
@tool(name="get_flow", description=GET_FLOW_DESC, parameters=GET_FLOW_PARAMS)
class GetFlowTool(BaseTool):
    """根据ID获取流水详情"""

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            flow_id = arguments.get("flowId")
            if flow_id is None:
                return self._error(code=E_PARAM_MISSING, message="缺少必要参数: flowId")

            client = _get_client(context)
            url = f"{client.base_url}/flow/getFlow/{flow_id}"

            async with client.async_client() as http_client:
                response = await http_client.get(url, headers=client._build_headers())

                # 特殊：getFlow 不存在的 id 用了 code=403, msg="未查询到该条记录"
                # 直接映射为 E_FLOW_NOT_FOUND，不交给通用 _check_response
                try:
                    resp_data = response.json() if response.status_code == 200 else None
                except Exception:
                    resp_data = None
                if isinstance(resp_data, dict) and resp_data.get("code") == 403:
                    return self._error(
                        error_obj=make_error(
                            E_FLOW_NOT_FOUND,
                            metadata={"flowId": flow_id, "backend_msg": resp_data.get("msg")},
                        )
                    )

                err = _check_response(response)
                if err:
                    return self._error(error_obj=err)

                resp_data = response.json()
                data = resp_data.get("data", {})
                if not data:
                    return self._error(
                        error_obj=make_error(E_FLOW_NOT_FOUND, metadata={"flowId": flow_id})
                    )

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
            return self._error(error_obj=from_exception(e))
