"""
工具调用结构化错误

把工具失败信息从裸字符串升级为结构化对象，让前端能据此渲染 UI、给出重试按钮，
让 LLM 能据 hint 字段自我修复。

错误码命名规范：E_<DOMAIN>_<DETAIL>，全大写，下划线分隔。
"""

from dataclasses import dataclass, asdict, field
from typing import Any, Dict, Optional


# ==============================================================================
#                              错误码常量
# ==============================================================================

# —— 网络 / 通信类（一般可重试）——
E_NETWORK = "E_NETWORK"                      # httpx / 连接异常
E_TIMEOUT = "E_TIMEOUT"                      # 请求超时

# —— 参数 / 调用形态类（不可重试）——
E_PARAM_MISSING = "E_PARAM_MISSING"          # 缺必填参数
E_PARAM_INVALID = "E_PARAM_INVALID"          # 参数取值非法（含 JSON 解析失败）
E_UNKNOWN_TOOL = "E_UNKNOWN_TOOL"            # 未知工具名

# —— 鉴权 / 注册类（不可重试，需用户处理）——
E_AUTH_FAILED = "E_AUTH_FAILED"              # 后端 401
E_NEED_REGISTER = "E_NEED_REGISTER"          # 后端 418，未注册

# —— 业务规则类（不可重试，但 LLM 可换参数再调）——
E_INSUFFICIENT_BALANCE = "E_INSUFFICIENT_BALANCE"        # 42001
E_TYPE_HAS_CHILDREN = "E_TYPE_HAS_CHILDREN"              # 42002，父分类不能记账
E_TYPE_DISABLED = "E_TYPE_DISABLED"                      # 42009
E_TYPE_ARCHIVED = "E_TYPE_ARCHIVED"                      # 42010
E_ACCOUNT_DISABLED = "E_ACCOUNT_DISABLED"                # 42008
E_TRANSFER_ACCOUNT_REQUIRED = "E_TRANSFER_ACCOUNT_REQUIRED"  # 42016
E_MAIL_NOT_CONFIGURED = "E_MAIL_NOT_CONFIGURED"          # 42017
E_BUSINESS_OTHER = "E_BUSINESS_OTHER"                    # 42xxx 其他业务错误兜底

# —— 资源不存在类（不可重试，需 LLM 改参或改路径）——
E_ACCOUNT_NOT_FOUND = "E_ACCOUNT_NOT_FOUND"  # 44001
E_TYPE_NOT_FOUND = "E_TYPE_NOT_FOUND"        # 44002
E_FLOW_NOT_FOUND = "E_FLOW_NOT_FOUND"        # 44003
E_ACTION_NOT_FOUND = "E_ACTION_NOT_FOUND"    # 44006

# —— LLM / Agent 调度类 ——
E_TOOL_BUDGET_EXHAUSTED = "E_TOOL_BUDGET_EXHAUSTED"  # 工具调用次数额度耗尽

# —— 系统类（一般不可重试，但若是偶发可重试）——
E_INTERNAL = "E_INTERNAL"                    # 兜底，未分类的异常 / 50xxx

# —— 邮件未配（兼容用，与 E_MAIL_NOT_CONFIGURED 相同语义）——
# 保留扩展位


# ==============================================================================
#                              错误对象
# ==============================================================================

@dataclass
class ToolError:
    """结构化工具错误。

    Attributes:
        code: 错误码常量（E_*）
        message: 用户可读的简短描述（前端可直接展示）
        hint: 给 LLM 的指引，告诉它下一步该做什么；也可作前端"操作建议"展示
        retryable: 同参数原样重试是否可能成功（网络/超时为 True，业务/参数为 False）
        metadata: 额外调试信息（后端原始 code/msg、HTTP 状态码、异常类型等）
    """
    code: str
    message: str
    hint: str = ""
    retryable: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ==============================================================================
#                              工厂方法
# ==============================================================================

# 错误码 → (默认 message, 默认 hint, retryable)
_DEFAULTS: Dict[str, tuple] = {
    E_NETWORK: ("网络连接失败", "网络问题，可以稍后重试。", True),
    E_TIMEOUT: ("请求超时", "服务响应较慢，可以稍后重试。", True),

    E_PARAM_MISSING: ("缺少必要参数", "请检查工具调用参数是否完整。", False),
    E_PARAM_INVALID: ("参数格式错误", "请按工具说明检查参数取值与格式。", False),
    E_UNKNOWN_TOOL: ("未知工具", "调用了不存在的工具，请检查工具名。", False),

    E_AUTH_FAILED: ("登录已失效", "请用户重新登录后再试。", False),
    E_NEED_REGISTER: ("系统未初始化", "请先在网页端完成账号注册。", False),

    E_INSUFFICIENT_BALANCE: ("余额不足", "该账户余额不足，建议换账户或调整金额。", False),
    E_TYPE_HAS_CHILDREN: (
        "该分类不能直接记账",
        "选中的分类有子分类且自身已绑定动作，必须改用其子分类。请重新调用 types 工具，从其子分类里选一个。",
        False,
    ),
    E_TYPE_DISABLED: (
        "分类已停用",
        "该分类已被停用。请重新调用 types 工具换一个未停用的分类。",
        False,
    ),
    E_TYPE_ARCHIVED: (
        "分类已归档",
        "该分类已归档。请重新调用 types 工具换一个未归档的分类。",
        False,
    ),
    E_ACCOUNT_DISABLED: (
        "账户已停用",
        "该账户已被停用。请重新调用 accounts 工具换一个未停用的账户。",
        False,
    ),
    E_TRANSFER_ACCOUNT_REQUIRED: (
        "转账缺少目标账户",
        "内部转账（handle=2）必须传 accountToId。请用 accounts 工具拿一个目标账户后重试。",
        False,
    ),
    E_MAIL_NOT_CONFIGURED: (
        "邮件未配置",
        "Excel 报表通过邮件发送，但用户尚未配置 SMTP。请告诉用户到「系统设置 → 邮件」完成配置。",
        False,
    ),
    E_BUSINESS_OTHER: ("业务规则错误", "请按返回的具体说明调整后再试。", False),

    E_ACCOUNT_NOT_FOUND: ("账户不存在", "请重新调用 accounts 工具确认 accountId。", False),
    E_TYPE_NOT_FOUND: ("分类不存在", "请重新调用 types 工具确认 typeId。", False),
    E_FLOW_NOT_FOUND: ("流水不存在", "请用 flows 工具重新查询确认 flowId。", False),
    E_ACTION_NOT_FOUND: ("动作不存在", "请重新调用 actions 工具确认 actionId。", False),

    E_TOOL_BUDGET_EXHAUSTED: (
        "工具调用次数已达上限",
        "本轮对话工具调用额度已用完。请基于已有信息回答用户，或建议分步操作。",
        False,
    ),

    E_INTERNAL: ("系统错误", "服务端出错，可以稍后重试，或如实告诉用户。", False),
}


def make_error(
    code: str,
    *,
    message: Optional[str] = None,
    hint: Optional[str] = None,
    retryable: Optional[bool] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ToolError:
    """构造 ToolError，未指定的字段从 _DEFAULTS 取。"""
    default_msg, default_hint, default_retryable = _DEFAULTS.get(
        code, ("操作失败", "请告知用户具体情况。", False)
    )
    return ToolError(
        code=code,
        message=message or default_msg,
        hint=hint or default_hint,
        retryable=default_retryable if retryable is None else retryable,
        metadata=metadata or {},
    )


# ==============================================================================
#                              后端 → AI 错误码映射
# ==============================================================================

# 后端 BaseDto.code → AI 错误码
_BACKEND_CODE_MAP: Dict[int, str] = {
    401: E_AUTH_FAILED,
    418: E_NEED_REGISTER,
    40000: E_PARAM_INVALID,
    40001: E_PARAM_MISSING,
    40002: E_PARAM_INVALID,
    40003: E_PARAM_INVALID,
    40004: E_PARAM_INVALID,
    42001: E_INSUFFICIENT_BALANCE,
    42002: E_TYPE_HAS_CHILDREN,
    42003: E_BUSINESS_OTHER,
    42004: E_BUSINESS_OTHER,
    42005: E_BUSINESS_OTHER,
    42006: E_BUSINESS_OTHER,
    42007: E_BUSINESS_OTHER,
    42008: E_ACCOUNT_DISABLED,
    42009: E_TYPE_DISABLED,
    42010: E_TYPE_ARCHIVED,
    42011: E_BUSINESS_OTHER,
    42012: E_BUSINESS_OTHER,
    42013: E_BUSINESS_OTHER,
    42014: E_BUSINESS_OTHER,
    42015: E_BUSINESS_OTHER,
    42016: E_TRANSFER_ACCOUNT_REQUIRED,
    42017: E_MAIL_NOT_CONFIGURED,
    44001: E_ACCOUNT_NOT_FOUND,
    44002: E_TYPE_NOT_FOUND,
    44003: E_FLOW_NOT_FOUND,
    44006: E_ACTION_NOT_FOUND,
    50001: E_INTERNAL,
    50002: E_INTERNAL,
    50003: E_INTERNAL,
    50004: E_INTERNAL,
    50005: E_INTERNAL,
}


def from_backend_response(
    http_status: int,
    backend_code: Optional[int],
    backend_msg: Optional[str],
) -> ToolError:
    """把后端 HTTP 响应（含 BaseDto.code）转成结构化错误。

    优先级：后端 BaseDto.code（HTTP 200 + code != 0）> HTTP 状态码。
    backend_msg 会作为 metadata 保留，并在 message 末尾追加（如有）。
    """
    code: Optional[str] = None

    # 1. 先看 BaseDto.code
    if backend_code is not None and backend_code != 0:
        code = _BACKEND_CODE_MAP.get(int(backend_code))

    # 2. 再看 HTTP 状态码
    if code is None:
        if http_status == 401:
            code = E_AUTH_FAILED
        elif http_status == 418:
            code = E_NEED_REGISTER
        elif http_status >= 500:
            code = E_INTERNAL
        else:
            code = E_BUSINESS_OTHER

    err = make_error(
        code,
        metadata={
            "http_status": http_status,
            "backend_code": backend_code,
            "backend_msg": backend_msg,
        },
    )
    # 把后端给的 msg 拼到 message 末尾，给 LLM 更具体的语境
    if backend_msg:
        err.message = f"{err.message}：{backend_msg}"
    return err


def from_exception(exc: BaseException) -> ToolError:
    """把 Python 异常映射成结构化错误。"""
    import asyncio
    try:
        import httpx  # 可能未导入，做容错
    except ImportError:  # pragma: no cover
        httpx = None  # type: ignore

    exc_type = type(exc).__name__

    # 超时类
    if isinstance(exc, asyncio.TimeoutError):
        return make_error(E_TIMEOUT, metadata={"exception_type": exc_type})
    if httpx is not None and isinstance(exc, httpx.TimeoutException):
        return make_error(E_TIMEOUT, metadata={"exception_type": exc_type})

    # 网络类
    if httpx is not None and isinstance(exc, (httpx.ConnectError, httpx.NetworkError, httpx.RemoteProtocolError)):
        return make_error(E_NETWORK, metadata={"exception_type": exc_type, "detail": str(exc)})

    # 兜底
    return make_error(
        E_INTERNAL,
        message=f"系统错误：{exc_type}",
        metadata={"exception_type": exc_type, "detail": str(exc)},
    )
