#!/usr/bin/env bash
# 添加流水(自动追加 Claw记账 标记和 from=Claw)
#
# 用法:
#   add_flow.sh \
#     --account-id 1 \
#     --type-id 5 \
#     --action-id 2 \
#     --money 30.00 \
#     --date 2026-04-01 \
#     --note "公司午餐" \
#     [--account-to-id 2] \
#     [--collect false]

set -euo pipefail
source "$(dirname "$0")/_common.sh"

ea_check_deps
ea_check_env

# 默认参数
ACCOUNT_ID=""
TYPE_ID=""
ACTION_ID=""
MONEY=""
F_DATE=""
NOTE=""
ACCOUNT_TO_ID=""
COLLECT="false"

# 参数解析
while [[ $# -gt 0 ]]; do
  case "$1" in
    --account-id)    ACCOUNT_ID="$2"; shift 2 ;;
    --type-id)       TYPE_ID="$2"; shift 2 ;;
    --action-id)     ACTION_ID="$2"; shift 2 ;;
    --money)         MONEY="$2"; shift 2 ;;
    --date)          F_DATE="$2"; shift 2 ;;
    --note)          NOTE="$2"; shift 2 ;;
    --account-to-id) ACCOUNT_TO_ID="$2"; shift 2 ;;
    --collect)       COLLECT="$2"; shift 2 ;;
    *) ea_die "未知参数: $1" ;;
  esac
done

# 必填校验
[[ -n "$ACCOUNT_ID" ]] || ea_die "缺少 --account-id"
[[ -n "$TYPE_ID"    ]] || ea_die "缺少 --type-id"
[[ -n "$ACTION_ID"  ]] || ea_die "缺少 --action-id"
[[ -n "$MONEY"      ]] || ea_die "缺少 --money"
[[ -n "$F_DATE"     ]] || ea_die "缺少 --date"

# 业务处理
MONEY=$(ea_normalize_money "$MONEY")
NOTE=$(ea_append_note_tag "$NOTE" "$EA_NOTE_TAG_ADD")
CREATE_DATE=$(ea_now)

# 构造 JSON(用 jq 保证类型正确和转义)
BODY=$(jq -n \
  --argjson accountId "$ACCOUNT_ID" \
  --argjson typeId "$TYPE_ID" \
  --argjson actionId "$ACTION_ID" \
  --arg money "$MONEY" \
  --arg fDate "$F_DATE" \
  --arg note "$NOTE" \
  --argjson collect "$COLLECT" \
  --arg createDate "$CREATE_DATE" \
  --arg from "$EA_FROM_TAG" \
  '{
    accountId: $accountId,
    typeId: $typeId,
    actionId: $actionId,
    money: $money,
    fDate: $fDate,
    note: $note,
    collect: $collect,
    createDate: $createDate,
    from: $from
  }')

# 内部转账时追加 accountToId
if [[ -n "$ACCOUNT_TO_ID" ]]; then
  BODY=$(echo "$BODY" | jq --argjson aid "$ACCOUNT_TO_ID" '. + {accountToId: $aid}')
fi

# 调用 API
RESPONSE=$(ea_post "/flow/addFlow" "$BODY")

# 提取 flowId 并友好输出
FLOW_ID=$(echo "$RESPONSE" | jq -r '.data.id // empty')

jq -n \
  --arg fid "$FLOW_ID" \
  '{success: true, message: "流水添加成功", flowId: ($fid | tonumber? // null)}'
