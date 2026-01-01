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

    def _build_headers(self, content_type: Optional[str] = None) -> dict[str, str]:
        headers = {}
        if self.auth_token:
            headers["authorization"] = self.auth_token
        if content_type:
            headers["Content-Type"] = content_type
        return headers

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


# ==============================================================================
#                              MCP 工具定义
# ==============================================================================

@mcp.tool
async def accounts(ctx: Context) -> str:
    """查询用户的资金账户列表。返回所有账户的ID、名称和余额信息。

    如果用户需要查询特定账户或需要账户ID，请使用该工具。
    添加流水或查询特定账户的流水时，需要先使用此工具获取账户ID。
    """
    try:
        client = _get_client(ctx)
        url = f"{client.base_url}/account/getAccount"

        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(url, headers=client._build_headers())

            if response.status_code == 401:
                return json.dumps(client._handle_auth_error(), ensure_ascii=False)

            return json.dumps(response.json(), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"获取账户列表失败: {str(e)}"}, ensure_ascii=False)


@mcp.tool
async def types(ctx: Context) -> str:
    """获取所有账单分类(标签)信息。返回分类的层级结构，包含分类ID、名称、父子关系和对应的actionId。

    如果用户需要查询分类ID或了解有哪些分类，请使用该工具。
    添加流水时需要先使用此工具获取分类ID和actionId。
    注意：actionId是添加流水时必需的参数，不是handle值。
    """
    try:
        client = _get_client(ctx)
        url = f"{client.base_url}/type/getType"

        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(url, headers=client._build_headers())

            if response.status_code == 401:
                return json.dumps(client._handle_auth_error(), ensure_ascii=False)

            raw = response.json()
            data = raw.get("data", []) if isinstance(raw, dict) and "data" in raw else (raw if isinstance(raw, list) else [])

            def format_desc(cat):
                action = cat.get("action")
                if action:
                    return f"id={cat.get('id')},name={cat.get('tname')},actionId={action.get('id')},handle={action.get('handle')},handleName={action.get('hname')}"
                return f"id={cat.get('id')},name={cat.get('tname')},actionId=null"

            result = []
            for cat in data:
                children = [format_desc(child) for child in cat.get("childrenTypes") or []]
                result.append({"description": format_desc(cat), "children": children})

            return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"获取分类失败: {str(e)}"}, ensure_ascii=False)


@mcp.tool
async def current_date(ctx: Context) -> str:
    """获取当前服务器日期。如果用户询问的问题涉及日期、周期、时间段，请使用该工具获取当前日期作为参考。

    返回yyyy-MM-dd格式的日期及年、月、日、星期信息。
    查询流水或统计时，建议先调用此工具确定当前日期。
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
        return json.dumps({"error": f"获取日期失败: {str(e)}"}, ensure_ascii=False)


@mcp.tool
async def year_statistics(ctx: Context, year: int) -> str:
    """获取指定年份的统计信息，包含每个月的收入、支出、盈余数据。

    如果用户询问某年某月的收支概况，请使用该工具。流水详情请使用flows工具。
    使用前请先调用current_date获取当前年份。

    Args:
        year: 年份，必填。请先使用current_date工具获取当前年份

    Returns:
        包含每个月的收入、支出、盈余数据
    """
    try:
        client = _get_client(ctx)
        url = f"{client.base_url}/home/getHomeInfoV2/{year}"

        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(url, headers=client._build_headers())

            if response.status_code == 401:
                return json.dumps(client._handle_auth_error(), ensure_ascii=False)

            return json.dumps(response.json(), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"获取年度统计失败: {str(e)}"}, ensure_ascii=False)


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
    """根据条件查询流水记录。支持多种查询条件组合：日期范围、账户、分类、关键字等。返回符合条件的流水列表和收支汇总。

    使用场景：1.查询某段时间的收支情况 2.查询特定分类的流水 3.按关键字搜索 4.分析支出占比
    遇到无法确定的需求时，请先查询types、accounts工具获取必要的ID。

    Args:
        handle: 收支类型：0=收入，1=支出，2=内部转账，3=全部。必填
        accountId: 账户ID，可选。使用accounts工具获取
        startDate: 开始日期，格式yyyy-MM-dd
        endDate: 结束日期，格式yyyy-MM-dd
        note: 备注关键字，模糊查询。只支持单个关键字，尽量简短
        singleMonth: 是否单月查询。设为true时无需endDate，startDate传当月1号
        types: 分类ID列表。使用types工具获取分类ID
        analysis: 是否分析占比。设为true可查看每笔流水的收入/支出占比
        orderBy: 排序方式：0=金额升序，1=金额降序，2=时间排序

    Returns:
        流水列表和收支汇总
    """
    try:
        if handle is None:
            return json.dumps({"error": "缺少必要参数: handle"}, ensure_ascii=False)
        if int(handle) > 3 or int(handle) < 0:
            return json.dumps({"error": "handle参数错误，请传入0-3之间的整数"}, ensure_ascii=False)

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

        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                url,
                headers=client._build_headers(content_type="application/json"),
                json=payload
            )

            if response.status_code == 401:
                return json.dumps(client._handle_auth_error(), ensure_ascii=False)

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
        return json.dumps({"error": f"查询流水失败: {str(e)}"}, ensure_ascii=False)


@mcp.tool
async def get_flow(ctx: Context, flowId: int) -> str:
    """根据流水ID获取单条流水的详细信息。包含完整的账户、分类、金额、日期、备注、图片等信息。

    Args:
        flowId: 流水ID，必填。通过flows工具查询获取，或从add_flow/update_flow返回值获取

    Returns:
        流水详细信息
    """
    try:
        if flowId is None:
            return json.dumps({"error": "缺少必要参数: flowId"}, ensure_ascii=False)

        client = _get_client(ctx)
        url = f"{client.base_url}/flow/getFlow/{flowId}"

        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(url, headers=client._build_headers())

            if response.status_code == 401:
                return json.dumps(client._handle_auth_error(), ensure_ascii=False)

            resp_data = response.json()
            if resp_data.get("code") != 0:
                return json.dumps({"error": resp_data.get("msg", "获取流水失败")}, ensure_ascii=False)

            data = resp_data.get("data", {})
            if not data:
                return json.dumps({"error": f"未找到流水ID={flowId}"}, ensure_ascii=False)

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
        return json.dumps({"error": f"获取流水详情失败: {str(e)}"}, ensure_ascii=False)


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
    """添加一条流水记录。可以记录收入、支出或内部转账。

    使用前请先：1.用accounts获取账户ID 2.用types获取分类ID和actionId 3.用current_date获取日期
    注意：actionId必须从types工具返回的action.id字段获取，不是handle值！

    Args:
        accountId: 账户ID，必填。使用accounts工具获取
        typeId: 分类ID，必填。使用types工具获取
        actionId: 收支动作ID，必填。从types工具返回的action.id字段获取，不是handle值
        money: 金额，必填。格式如'100.00'
        fDate: 流水日期，必填。格式yyyy-MM-dd
        note: 备注，必填。简要描述这笔流水的用途或来源，如'公司午餐'、'12月工资'
        accountToId: 转入账户ID，内部转账时必填。使用accounts工具获取
        collect: 是否收藏，可选，默认false

    Returns:
        添加结果
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

        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                url,
                headers=client._build_headers(content_type="application/json"),
                json=payload
            )

            if response.status_code == 200:
                resp_data = response.json()
                # data 是对象 {"id": 123}
                flow_id = None
                if isinstance(resp_data, dict) and isinstance(resp_data.get("data"), dict):
                    flow_id = resp_data["data"].get("id")

                return json.dumps({
                    "success": True,
                    "message": "流水添加成功",
                    "flowId": flow_id
                }, ensure_ascii=False)
            elif response.status_code == 401:
                return json.dumps(client._handle_auth_error(), ensure_ascii=False)
            else:
                error_msg = response.json().get('msg', response.text) if response.text else "未知错误"
                return json.dumps({"error": f"添加流水失败: {error_msg}"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"添加流水失败: {str(e)}"}, ensure_ascii=False)


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
    """更新已有的流水记录。需要提供流水ID（通过flows工具查询获取）和完整的流水信息。

    使用前请先用flows工具查询获取要修改的流水ID。

    Args:
        flowId: 流水ID，必填。通过flows工具查询获取
        accountId: 账户ID，必填。使用accounts工具获取
        typeId: 分类ID，必填。使用types工具获取
        actionId: 收支动作ID，必填。从types工具返回的action.id字段获取
        money: 金额，必填。格式如'100.00'
        fDate: 流水日期，必填。格式yyyy-MM-dd
        note: 备注，必填。简要描述这笔流水的用途或来源
        accountToId: 转入账户ID，内部转账时使用
        collect: 是否收藏，可选

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

        async with httpx.AsyncClient() as http_client:
            response = await http_client.put(
                url,
                headers=client._build_headers(content_type="application/json"),
                json=payload
            )

            if response.status_code == 200:
                return json.dumps({
                    "success": True,
                    "message": f"流水ID={flowId}更新成功",
                    "flowId": flowId
                }, ensure_ascii=False)
            elif response.status_code == 401:
                return json.dumps(client._handle_auth_error(), ensure_ascii=False)
            else:
                error_msg = response.json().get('msg', response.text) if response.text else "未知错误"
                return json.dumps({"error": f"更新流水失败: {error_msg}"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"更新流水失败: {str(e)}"}, ensure_ascii=False)


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
    """根据流水查询条件生成Excel报表。参数与flows工具类似，输出为Excel文件下载链接。

    当流水数量较多时（超过100条），建议使用此工具导出完整报表而不是使用flows工具。

    Args:
        excelName: Excel文件名称，必填。不需要扩展名，如'2025年1月账单'
        handle: 收支类型：0=收入，1=支出，2=内部转账，3=全部。必填
        accountId: 账户ID，可选。使用accounts工具获取
        startDate: 开始日期，格式yyyy-MM-dd
        endDate: 结束日期，格式yyyy-MM-dd
        note: 备注关键字，模糊查询
        singleMonth: 是否单月查询
        types: 分类ID列表。使用types工具获取分类ID
        collect: 是否只导出收藏的流水

    Returns:
        Excel文件下载链接
    """
    try:
        if not excelName:
            return json.dumps({"error": "缺少必要参数: excelName"}, ensure_ascii=False)
        if handle is None:
            return json.dumps({"error": "缺少必要参数: handle"}, ensure_ascii=False)
        if int(handle) > 3 or int(handle) < 0:
            return json.dumps({"error": "handle参数错误，请传入0-3之间的整数"}, ensure_ascii=False)

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

        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                url,
                headers=client._build_headers(content_type="application/json"),
                json=payload
            )

            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                return json.dumps({
                    "success": True,
                    "message": "Excel报表生成成功",
                    "fileName": data.get("fileName", f"{excelName}.xlsx"),
                    "downloadUrl": data.get("downloadUrl", "")
                }, ensure_ascii=False)
            elif response.status_code == 401:
                return json.dumps(client._handle_auth_error(), ensure_ascii=False)
            else:
                error_msg = response.json().get('msg', response.text) if response.text else "未知错误"
                return json.dumps({"error": f"生成Excel失败: {error_msg}"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"生成Excel失败: {str(e)}"}, ensure_ascii=False)


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
