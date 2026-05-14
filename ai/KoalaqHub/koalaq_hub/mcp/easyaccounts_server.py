"""
EasyAccounts MCP Server

将EasyAccounts工具暴露为MCP服务，供外部客户端调用。
通过URL参数传递token进行鉴权。

使用方式：
    MCP连接地址: http://host:port/mcp?token=<your_token>
"""

import datetime
import json
from typing import Any, Optional

import httpx
from fastmcp import Context, FastMCP
from fastmcp.server.dependencies import get_http_headers, get_http_request

from ..config.settings import config
from ..core.logging_utils import ManagerLogger
from ..tools.error_codes import (
    E_FLOW_NOT_FOUND,
    E_PARAM_INVALID,
    E_PARAM_MISSING,
    ToolError,
    from_backend_response,
    from_exception,
    make_error,
)

# 初始化日志
logger = ManagerLogger("MCPServer")

# 全局token存储（单用户模式）
_global_token: Optional[str] = None


def set_global_token(token: str) -> None:
    """设置全局token（由中间件调用）"""
    global _global_token
    _global_token = token
    logger.info(f"设置全局token: ***{token[-8:] if len(token) > 8 else '***'}")


def get_global_token() -> Optional[str]:
    """获取全局token"""
    return _global_token


# 创建MCP服务器实例
mcp = FastMCP(
    name="EasyAccounts",
    instructions="个人财务管理系统MCP服务。提供账户查询、流水管理、统计分析等功能。"
)


# ==============================================================================
#                              Token 解析
# ==============================================================================

def get_token_from_context(ctx: Context) -> Optional[str]:
    """从MCP Context中获取token

    支持多种获取方式（按优先级）：
    1. 全局token（SSE连接时设置）
    2. HTTP请求URL参数
    3. HTTP Headers
    """
    # 优先使用全局token（SSE连接时设置的）
    token = get_global_token()
    if token:
        logger.info(f"使用全局token: ***{token[-8:]}")
        return token

    # 其他方式作为fallback
    try:
        # 从HTTP请求URL参数获取
        request = get_http_request()
        if request:
            url = request.url
            if hasattr(url, 'query'):
                from urllib.parse import parse_qs
                params = parse_qs(url.query)
                token = params.get('token', [None])[0]

            if not token and hasattr(request, 'query_params'):
                token = request.query_params.get('token')

        # 从HTTP Headers获取
        if not token:
            headers = get_http_headers()
            if headers:
                token = (
                    headers.get('authorization') or
                    headers.get('Authorization') or
                    headers.get('token') or
                    headers.get('x-token')
                )
                if token and token.startswith('Bearer '):
                    token = token[7:]

        if token:
            logger.info(f"获取到token: ***{token[-8:]}")
        else:
            logger.warning("未获取到token")

    except Exception as e:
        logger.warning(f"获取token失败: {e}")

    return token


# ==============================================================================
#                              HTTP 客户端
# ==============================================================================

class EasyAccountsClient:
    """EasyAccounts API 客户端"""

    def __init__(self, auth_token: Optional[str] = None):
        self.base_url = config.easyaccounts_url
        self.auth_token = auth_token
        # 与内部工具一致：使用 tool_execution_timeout（默认 60s），
        # 避免 httpx 默认 5s 误把后端慢查询识别为 E_TIMEOUT
        self.timeout = config.tool_execution_timeout

    def _build_headers(self, content_type: Optional[str] = None) -> dict[str, str]:
        headers = {}
        if self.auth_token:
            headers["authorization"] = self.auth_token
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def async_client(self) -> "httpx.AsyncClient":
        """返回配置好 timeout 的 httpx 客户端。

        trust_env=True（httpx 默认）：跟随系统代理，
        以便后端是公网域名时也能通过用户配置的代理访问。
        """
        return httpx.AsyncClient(timeout=self.timeout)

    def _handle_auth_error(self) -> dict[str, Any]:
        return {
            "error": "认证失败",
            "status": 401,
            "message": "EasyAccounts系统已开启登录鉴权",
            "guidance": "请确保MCP连接URL中包含有效的token参数"
        }


def _get_client(ctx: Context) -> EasyAccountsClient:
    """从Context获取客户端"""
    token = get_token_from_context(ctx)
    return EasyAccountsClient(auth_token=token)


def _check_response(response: httpx.Response) -> Optional[ToolError]:
    """统一的后端响应错误识别。返回 ToolError 表示需要报错；返回 None 表示成功。"""
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


def _error_json(err: ToolError) -> str:
    """把 ToolError 序列化为 MCP 客户端可读的 JSON 字符串。

    输出包含 error/code/message/hint/retryable，外部客户端的 LLM 据此引导用户。
    """
    return json.dumps({
        "error": True,
        "code": err.code,
        "message": err.message,
        "hint": err.hint,
        "retryable": err.retryable,
        "metadata": err.metadata,
    }, ensure_ascii=False)


def _param_error(message: str, code: str = E_PARAM_MISSING) -> str:
    return _error_json(make_error(code, message=message))


# ==============================================================================
#                              MCP 工具定义
# ==============================================================================

@mcp.tool
async def accounts(ctx: Context) -> str:
    """查询用户的资金账户列表，返回每个账户的 id、name、余额（money，字符串）。

    需要 accountId、查询特定账户、或查看余额时使用。
    余额可能为负数（信用卡等场景），不要做"余额够不够"的预判。
    """
    try:
        client = _get_client(ctx)
        url = f"{client.base_url}/account/getAccount"

        async with client.async_client() as http_client:
            response = await http_client.get(url, headers=client._build_headers())

            err = _check_response(response)
            if err:
                return _error_json(err)

            return json.dumps(response.json(), ensure_ascii=False)
    except Exception as e:
        return _error_json(from_exception(e))


@mcp.tool
async def types(ctx: Context) -> str:
    """获取记账分类树（最多两级），每个节点含 id、name、actionId、handle、handleName。

    可用性规则（误用会被后端拒绝，错误码 E_TYPE_HAS_CHILDREN）：
    - 节点没有子分类（叶子）→ 可以直接用本节点记账
    - 节点有子分类，且自身 actionId=null（通用容器）→ 可以直接用本节点
    - 节点有子分类，且自身 actionId!=null → 不可以，必须改用其子分类

    actionId 不是 handle 值。actionId 来源：节点 action 字段；为 null 时本 MCP 服务无 actions 工具，
    需要客户端按收支语义自行选择，或在节点已有 action 的层级里选。
    """
    try:
        client = _get_client(ctx)
        url = f"{client.base_url}/type/getType"

        async with client.async_client() as http_client:
            response = await http_client.get(url, headers=client._build_headers())

            err = _check_response(response)
            if err:
                return _error_json(err)

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
                # 可用性：叶子可用；有子分类但 actionId=null（通用容器）也可用；
                # 有子分类且 actionId!=null → 不可用，必须用子分类
                parent_usable = (not has_children) or (cat.get("action") is None)
                children = [format_desc(child, usable=True) for child in children_data]
                result.append({"description": format_desc(cat, usable=parent_usable), "children": children})

            return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return _error_json(from_exception(e))


@mcp.tool
async def current_date(ctx: Context) -> str:
    """获取当前服务器日期（GMT+8）。涉及日期、周期、时间段查询前必须先调用。

    返回 yyyy-MM-dd 及年、月、日、星期。
    """
    try:
        now = datetime.datetime.now()
        result = {
            "today": now.strftime("%Y-%m-%d"),
            "year": now.strftime("%Y"),
            "month": now.strftime("%m"),
            "day": now.strftime("%d"),
            "week": now.strftime("%w")
        }
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return _error_json(from_exception(e))


@mcp.tool
async def year_statistics(ctx: Context, year: int) -> str:
    """获取指定年份的概览：年度总收入、总支出、盈余，以及各月份明细。

    用户询问某年/某月概况时使用。统计口径不含转账（handle=2）。
    需要流水明细改用 flows 工具。
    使用前先调用 current_date 拿当前年份。

    Args:
        year: 年份，必填

    Returns:
        包含 totalAsset/netAsset/yearIncome/yearOutCome/yearBalance/monthDetails 等
    """
    try:
        client = _get_client(ctx)
        url = f"{client.base_url}/home/getHomeInfoV2/{year}"

        async with client.async_client() as http_client:
            response = await http_client.get(url, headers=client._build_headers())

            err = _check_response(response)
            if err:
                return _error_json(err)

            return json.dumps(response.json(), ensure_ascii=False)
    except Exception as e:
        return _error_json(from_exception(e))


@mcp.tool
async def flows(
    ctx: Context,
    handle: int,
    accountId: int = None,
    startDate: str = None,
    endDate: str = None,
    note: str = None,
    singleMonth: bool = None,
    types: list[int] = None,
    analysis: bool = False,
    orderBy: int = None
) -> str:
    """按条件查询流水。支持账户、日期范围、分类、关键字、收藏等组合筛选，返回流水列表 + 收支汇总。

    关键规则：
    - handle=3 表示全部（不是 0）
    - types 多选组内 OR；选父分类自动包含其全部子分类
    - singleMonth=true 时只看 startDate 所在月，endDate 被忽略
    - totalIn/totalOut/totalEarn 不含转账（handle=2）
    - 返回超 100 条会被截断，建议改用 make_excel 导出完整报表

    使用前先调用 accounts、types 拿必要的 ID。

    Args:
        handle: 收支类型：0=只看收入，1=只看支出，2=只看转账，3=全部。看全部传 3，必填
        accountId: 账户 ID。使用 accounts 工具获取
        startDate: 开始日期，格式严格 yyyy-MM-dd（10 位，如 2026-04-09）
        endDate: 结束日期，格式严格 yyyy-MM-dd（10 位）
        note: 备注关键字，模糊匹配。只传单个关键字、尽量简短
        singleMonth: true 时只看 startDate 所在月，endDate 被忽略
        types: 分类 ID 列表。组内 OR；选父分类自动覆盖子分类
        analysis: true 时返回每笔流水占比
        orderBy: 0=金额升序，1=金额降序，2=时间排序

    Returns:
        流水列表 + 收支汇总
    """
    try:
        if handle is None:
            return _param_error("缺少必要参数: handle")
        if int(handle) > 3 or int(handle) < 0:
            return _param_error("handle 取值非法，仅允许 0/1/2/3", code=E_PARAM_INVALID)

        client = _get_client(ctx)
        url = f"{client.base_url}/screen/getFlowByScreen"

        payload = {
            "accountId": accountId,
            "actions": [],
            "chooseHandle": handle,
            "collect": "false",
            "endDate": endDate,
            "note": note,
            "singleMonth": singleMonth,
            "startDate": startDate,
            "types": types,
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
                return _error_json(err)

            flows_data = response.json()
            data = flows_data.get("data", {})
            totalIn, totalOut, totalEarn = data.get("totalIn", "0"), data.get("totalOut", "0"), data.get("totalEarn", "0")
            flows_list_raw = data.get("flows", [])
            total_count = len(flows_list_raw)

            # 排序
            if orderBy == 0:
                flows_list_raw.sort(key=lambda x: float(x.get("money", 0)))
            elif orderBy == 1:
                flows_list_raw.sort(key=lambda x: float(x.get("money", 0)), reverse=True)

            # 截断
            MAX_FLOWS = 100
            is_truncated = total_count > MAX_FLOWS
            if is_truncated:
                flows_list_raw = flows_list_raw[:MAX_FLOWS]

            # 格式化
            flows_list = []
            for flow in flows_list_raw:
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

            result = {
                "summary": f"收入={totalIn},支出={totalOut},盈余={totalEarn}",
                "flows": flows_list,
                "total_count": total_count,
                "returned_count": len(flows_list),
                "is_truncated": is_truncated
            }
            if is_truncated:
                result["notice"] = f"共{total_count}条，仅返回前{MAX_FLOWS}条，建议使用make_excel导出完整报表"

            return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return _error_json(from_exception(e))


@mcp.tool
async def get_flow(ctx: Context, flowId: int) -> str:
    """根据流水 id 获取单条流水的完整信息：账户、转入账户（仅转账）、分类、动作、金额、日期、备注、from、images。

    更新流水前必须先用本工具拿到 from 字段，否则 update_flow 会把 from 置空。

    Args:
        flowId: 流水 ID，必填。通过 flows 工具查询，或从 add_flow/update_flow 返回值获取

    Returns:
        流水详细信息（含 from 字段，update_flow 时务必传回）
    """
    try:
        if flowId is None:
            return _param_error("缺少必要参数: flowId")

        client = _get_client(ctx)
        url = f"{client.base_url}/flow/getFlow/{flowId}"

        async with client.async_client() as http_client:
            response = await http_client.get(url, headers=client._build_headers())

            # 特殊：getFlow 不存在的 id 后端用了 code=403, msg="未查询到该条记录"
            try:
                resp_data = response.json() if response.status_code == 200 else None
            except Exception:
                resp_data = None
            if isinstance(resp_data, dict) and resp_data.get("code") == 403:
                return _error_json(make_error(
                    E_FLOW_NOT_FOUND,
                    metadata={"flowId": flowId, "backend_msg": resp_data.get("msg")},
                ))

            err = _check_response(response)
            if err:
                return _error_json(err)

            resp_data = response.json()
            data = resp_data.get("data", {})
            if not data:
                return _error_json(make_error(E_FLOW_NOT_FOUND, metadata={"flowId": flowId}))

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

            return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return _error_json(from_exception(e))


@mcp.tool
async def add_flow(
    ctx: Context,
    accountId: int,
    typeId: int,
    actionId: int,
    money: str,
    fDate: str,
    note: str,
    accountToId: int = None,
    collect: bool = False
) -> str:
    """添加一条流水。可记录收入、支出或内部转账。

    流程：
    1) accounts 拿 accountId
    2) types 拿 typeId（只能用"可用"的分类）和该节点的 action
    3) 节点 action 不为 null → 直接用 action.id 作为 actionId；
       节点 action 为 null（通用分类）→ 本 MCP 服务无 actions 工具，需在已有 action 的层级里选
    4) current_date 拿日期（用户没指定时）

    money 只传正数 2 位小数，方向由 action.handle 决定。
    仅当 action.handle=2（内部转账）时需要 accountToId。
    不要预判余额（v2.6.0 起允许账户负余额）。

    Args:
        accountId: 账户 ID，必填
        typeId: 分类 ID，必填（必须是"可用"分类，否则后端 E_TYPE_HAS_CHILDREN）
        actionId: 动作 ID，必填。来源 types 节点的 action.id，不是 handle 值
        money: 金额，必填。正数字符串，2 位小数（如 '30.00'）
        fDate: 流水日期，必填。格式严格 yyyy-MM-dd（10 位）
        note: 备注，必填。简要描述用途或来源
        accountToId: 转入账户 ID。仅 action.handle=2 时必填
        collect: 是否收藏，默认 false

    Returns:
        添加结果（含 flowId）
    """
    try:
        client = _get_client(ctx)
        url = f"{client.base_url}/flow/addFlow"

        # 处理备注，自动追加 #AI记账 标记
        final_note = note if note else ""
        if final_note and "#AI记账" not in final_note:
            final_note = f"{final_note} #AI记账"
        elif not final_note:
            final_note = "#AI记账"

        payload = {
            "accountId": accountId,
            "typeId": typeId,
            "actionId": actionId,
            "money": money,
            "fDate": fDate,
            "note": final_note,
            "collect": collect,
            "createDate": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "from": "mcp"
        }
        if accountToId is not None:
            payload["accountToId"] = accountToId

        async with client.async_client() as http_client:
            response = await http_client.post(
                url,
                headers=client._build_headers(content_type="application/json"),
                json=payload
            )

            err = _check_response(response)
            if err:
                return _error_json(err)

            resp_data = response.json()
            flow_id = None
            if isinstance(resp_data, dict) and isinstance(resp_data.get("data"), dict):
                flow_id = resp_data["data"].get("id")

            return json.dumps({
                "success": True,
                "message": "流水添加成功",
                "flowId": flow_id
            }, ensure_ascii=False)
    except Exception as e:
        return _error_json(from_exception(e))


@mcp.tool
async def update_flow(
    ctx: Context,
    flowId: int,
    accountId: int,
    typeId: int,
    actionId: int,
    money: str,
    fDate: str,
    note: str,
    accountToId: int = None,
    collect: bool = False
) -> str:
    """更新已有流水。需要先用 flows 或 get_flow 拿到流水 id 和原始 from 字段。

    分类只能使用"可用"分类，actionId 来源同 add_flow。
    后端会自动按原流水回滚账户余额再正向应用新参数，不需要客户端做差额计算。

    Args:
        flowId: 流水 ID，必填
        accountId: 账户 ID，必填
        typeId: 分类 ID，必填（必须"可用"分类）
        actionId: 动作 ID，必填。来源 types 节点的 action.id
        money: 金额，必填。正数字符串，2 位小数
        fDate: 流水日期，必填。格式严格 yyyy-MM-dd（10 位）
        note: 备注，必填
        accountToId: 转入账户 ID，仅 action.handle=2 时使用
        collect: 是否收藏

    Returns:
        更新结果
    """
    try:
        client = _get_client(ctx)
        url = f"{client.base_url}/flow/updateFlow/{flowId}"

        # 处理备注，自动追加 #AI更新 标记
        final_note = note if note else ""
        if final_note and "#AI更新" not in final_note:
            final_note = f"{final_note} #AI更新"
        elif not final_note:
            final_note = "#AI更新"

        payload = {
            "accountId": accountId,
            "typeId": typeId,
            "actionId": actionId,
            "money": money,
            "fDate": fDate,
            "note": final_note,
            "collect": collect,
            "createDate": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "from": "mcp"
        }
        if accountToId is not None:
            payload["accountToId"] = accountToId

        async with client.async_client() as http_client:
            response = await http_client.put(
                url,
                headers=client._build_headers(content_type="application/json"),
                json=payload
            )

            err = _check_response(response)
            if err:
                return _error_json(err)

            return json.dumps({
                "success": True,
                "message": f"流水ID={flowId}更新成功",
                "flowId": flowId
            }, ensure_ascii=False)
    except Exception as e:
        return _error_json(from_exception(e))


@mcp.tool
async def make_excel(
    ctx: Context,
    excelName: str,
    handle: int,
    accountId: int = None,
    startDate: str = None,
    endDate: str = None,
    note: str = None,
    singleMonth: bool = None,
    types: list[int] = None,
    collect: bool = False
) -> str:
    """按筛选条件生成 Excel 报表。

    重要：本工具不返回下载链接。
    实际行为是后端生成 Excel 后通过邮件发送到用户配置的邮箱。
    若返回 hint 提示邮件未配置（E_MAIL_NOT_CONFIGURED），告诉用户去"系统设置 → 邮件"配 SMTP。

    流水超过 100 条或用户明确要求导出时使用。

    Args:
        excelName: Excel 文件名，必填。不带扩展名（如 '2026年4月账单'）
        handle: 收支类型：0=只看收入，1=只看支出，2=只看转账，3=全部。看全部传 3，必填
        accountId: 账户 ID
        startDate: 开始日期，格式严格 yyyy-MM-dd（10 位）
        endDate: 结束日期，格式严格 yyyy-MM-dd（10 位）
        note: 备注关键字，模糊匹配
        singleMonth: true 时只看 startDate 所在月，endDate 被忽略
        types: 分类 ID 列表。组内 OR；选父分类自动覆盖子分类
        collect: 是否只导出收藏

    Returns:
        生成结果（含 success / log），不含下载链接
    """
    try:
        if not excelName:
            return _param_error("缺少必要参数: excelName")
        if handle is None:
            return _param_error("缺少必要参数: handle")
        if int(handle) > 3 or int(handle) < 0:
            return _param_error("handle 取值非法，仅允许 0/1/2/3", code=E_PARAM_INVALID)

        client = _get_client(ctx)
        url = f"{client.base_url}/screen/makeExcel?excelName={excelName}"

        payload = {
            "accountId": accountId,
            "actions": [],
            "chooseHandle": handle,
            "endDate": endDate,
            "note": note,
            "singleMonth": singleMonth,
            "startDate": startDate,
            "types": types,
            "collect": str(collect).lower()
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
                return _error_json(err)

            # 后端返回 {success, log}，不含下载链接（实际是发邮件）
            result = response.json()
            data = result.get("data", {}) if isinstance(result, dict) else {}
            return json.dumps({
                "success": data.get("success", True),
                "message": "Excel 报表已生成（通过邮件发送到用户邮箱）",
                "log": data.get("log", "")
            }, ensure_ascii=False)
    except Exception as e:
        return _error_json(from_exception(e))


# ==============================================================================
#                              MCP App 导出
# ==============================================================================

def create_mcp_app(transport_mode: str = "sse"):
    """创建MCP ASGI应用，用于挂载到FastAPI

    Args:
        transport_mode: 传输模式，"sse" 或 "streamable-http"

    Returns:
        ASGI应用
    """
    if transport_mode == "streamable-http":
        logger.info("创建MCP应用 (Streamable HTTP模式)")
        return mcp.http_app(transport="streamable-http")
    else:
        logger.info("创建MCP应用 (SSE模式)")
        return mcp.http_app(transport="sse")


def get_mcp_server() -> FastMCP:
    """获取MCP服务器实例"""
    return mcp
