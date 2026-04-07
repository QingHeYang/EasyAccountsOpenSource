#!/usr/bin/env bash
# 查询流水 / 导出 Excel
#
# 用法(查询):
#   query_flows.sh \
#     --handle 1 \
#     [--start-date 2026-03-01] \
#     [--end-date 2026-03-31] \
#     [--account-id 1] \
#     [--types 5,8] \
#     [--note 餐饮] \
#     [--single-month true] \
#     [--analysis true] \
#     [--order-by 2]
#
# 用法(导出 Excel):
#   query_flows.sh --export "2026年3月账单" --handle 1 [其他过滤参数...]
#
# handle: 0=收入 1=支出 2=内部转账 3=全部
# order-by: 0=金额升序 1=金额降序 2=时间排序

set -euo pipefail
source "$(dirname "$0")/_common.sh"

ea_check_deps
ea_check_env

HANDLE=""
ACCOUNT_ID=""
START_DATE=""
END_DATE=""
NOTE=""
SINGLE_MONTH=""
TYPES=""
ANALYSIS="false"
ORDER_BY=""
EXPORT_NAME=""
COLLECT="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --handle)       HANDLE="$2"; shift 2 ;;
    --account-id)   ACCOUNT_ID="$2"; shift 2 ;;
    --start-date)   START_DATE="$2"; shift 2 ;;
    --end-date)     END_DATE="$2"; shift 2 ;;
    --note)         NOTE="$2"; shift 2 ;;
    --single-month) SINGLE_MONTH="$2"; shift 2 ;;
    --types)        TYPES="$2"; shift 2 ;;
    --analysis)     ANALYSIS="$2"; shift 2 ;;
    --order-by)     ORDER_BY="$2"; shift 2 ;;
    --export)       EXPORT_NAME="$2"; shift 2 ;;
    --collect)      COLLECT="$2"; shift 2 ;;
    *) ea_die "未知参数: $1" ;;
  esac
done

[[ -n "$HANDLE" ]] || ea_die "缺少 --handle (0=收入,1=支出,2=转账,3=全部)"
if (( HANDLE < 0 || HANDLE > 3 )); then
  ea_die "--handle 必须是 0/1/2/3"
fi

# 构造基础 payload
BODY=$(jq -n \
  --argjson handle "$HANDLE" \
  --arg collect "$COLLECT" \
  '{chooseHandle: $handle, actions: [], collect: $collect}')

# 添加可选参数
add_field() {
  local key="$1" val="$2" type="${3:-string}"
  [[ -z "$val" ]] && return
  if [[ "$type" == "json" ]]; then
    BODY=$(echo "$BODY" | jq --argjson v "$val" ". + {\"$key\": \$v}")
  else
    BODY=$(echo "$BODY" | jq --arg v "$val" ". + {\"$key\": \$v}")
  fi
}

add_field "accountId" "$ACCOUNT_ID" "json"
add_field "startDate" "$START_DATE"
add_field "endDate" "$END_DATE"
add_field "note" "$NOTE"
[[ -n "$SINGLE_MONTH" ]] && BODY=$(echo "$BODY" | jq --argjson v "$SINGLE_MONTH" '. + {singleMonth: $v}')

# types 是逗号分隔的列表 → JSON 数组
if [[ -n "$TYPES" ]]; then
  TYPES_JSON=$(echo "$TYPES" | jq -R 'split(",") | map(tonumber)')
  BODY=$(echo "$BODY" | jq --argjson v "$TYPES_JSON" '. + {types: $v}')
fi

# ============================================================
#                    导出 Excel 分支
# ============================================================
if [[ -n "$EXPORT_NAME" ]]; then
  # excelName 含中文/空格时必须 URL 编码,用 jq 安全编码
  ENCODED_NAME=$(printf '%s' "$EXPORT_NAME" | jq -sRr @uri)
  RESPONSE=$(ea_post "/screen/makeExcel?excelName=${ENCODED_NAME}" "$BODY")
  # 后端返回结构: {data: {success: bool, log: "...file_name: xxx.xlsx"}}
  # 从 log 字符串里解析出文件名
  FILE_NAME=$(echo "$RESPONSE" | jq -r '.data.log // ""' | grep -oE 'file_name: [^ ]+\.xlsx' | sed 's/file_name: //' | head -1)
  echo "$RESPONSE" | jq --arg name "${FILE_NAME:-${EXPORT_NAME}.xlsx}" '{
    success: (.data.success // false),
    message: "Excel 报表生成成功",
    fileName: $name,
    notice: "文件已生成在服务器 Resource/excel/screen/ 目录,请通过前端下载页面或运维拷贝"
  }'
  exit 0
fi

# ============================================================
#                    查询流水分支
# ============================================================
RESPONSE=$(ea_post "/screen/getFlowByScreen" "$BODY")

# 提取汇总
TOTAL_IN=$(echo "$RESPONSE" | jq -r '.data.totalIn // "0"')
TOTAL_OUT=$(echo "$RESPONSE" | jq -r '.data.totalOut // "0"')
TOTAL_EARN=$(echo "$RESPONSE" | jq -r '.data.totalEarn // "0"')

# 提取流水列表
FLOWS=$(echo "$RESPONSE" | jq '.data.flows // []')
TOTAL_COUNT=$(echo "$FLOWS" | jq 'length')

# 排序
case "${ORDER_BY:-}" in
  0) FLOWS=$(echo "$FLOWS" | jq 'sort_by(.money | tonumber)') ;;
  1) FLOWS=$(echo "$FLOWS" | jq 'sort_by(.money | tonumber) | reverse') ;;
  2) FLOWS=$(echo "$FLOWS" | jq 'sort_by(.fdate)') ;;
esac

# 截断到 100 条
MAX=100
IS_TRUNCATED=false
if (( TOTAL_COUNT > MAX )); then
  IS_TRUNCATED=true
  FLOWS=$(echo "$FLOWS" | jq ".[0:$MAX]")
fi

RETURNED=$(echo "$FLOWS" | jq 'length')

# 格式化流水(用 jq 拼字符串)
if [[ "$ANALYSIS" == "true" ]]; then
  FLOWS_FORMATTED=$(echo "$FLOWS" | jq \
    --argjson handle "$HANDLE" \
    --arg totalIn "$TOTAL_IN" \
    --arg totalOut "$TOTAL_OUT" \
    'map(
      "流水ID:\(.id);收支:\(.hname);金额:\(.money);账户:\(.aname);分类:\(.tname);时间:\(.fdate)" +
      (if $handle == 0 and ($totalIn | tonumber) > 0 then ";占比:\(((.money | tonumber) / ($totalIn | tonumber) * 100) | tostring | .[0:5])%" else "" end) +
      (if $handle == 1 and ($totalOut | tonumber) > 0 then ";占比:\(((.money | tonumber) / ($totalOut | tonumber) * 100) | tostring | .[0:5])%" else "" end) +
      (if .toAName then ";转到:\(.toAName)" else "" end) +
      (if .note then ";备注:\(.note)" else "" end)
    )')
else
  FLOWS_FORMATTED=$(echo "$FLOWS" | jq 'map(
    "流水ID:\(.id);收支:\(.hname);金额:\(.money);账户:\(.aname);分类:\(.tname);时间:\(.fdate)" +
    (if .toAName then ";转到:\(.toAName)" else "" end) +
    (if .note then ";备注:\(.note)" else "" end)
  )')
fi

# 输出结果
RESULT=$(jq -n \
  --arg summary "收入=${TOTAL_IN},支出=${TOTAL_OUT},盈余=${TOTAL_EARN}" \
  --argjson flows "$FLOWS_FORMATTED" \
  --argjson total "$TOTAL_COUNT" \
  --argjson returned "$RETURNED" \
  --argjson truncated "$IS_TRUNCATED" \
  '{
    summary: $summary,
    flows: $flows,
    total_count: $total,
    returned_count: $returned,
    is_truncated: $truncated
  }')

if [[ "$IS_TRUNCATED" == "true" ]]; then
  RESULT=$(echo "$RESULT" | jq --arg n "$TOTAL_COUNT" --arg m "$MAX" \
    '. + {notice: "共\($n)条,仅返回前\($m)条,建议使用 make_excel 导出完整报表"}')
fi

echo "$RESULT"
