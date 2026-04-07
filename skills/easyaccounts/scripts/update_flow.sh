#!/usr/bin/env bash
# 更新流水(自动追加 Claw更新 标记和 from=Claw)
#
# 用法:
#   update_flow.sh \
#     --flow-id 123 \
#     --account-id 1 \
#     --type-id 5 \
#     --action-id 2 \
#     --money 35.00 \
#     --date 2026-04-01 \
#     --note "公司午餐" \
#     [--account-to-id 2] \
#     [--collect false]

set -euo pipefail
source "$(dirname "$0")/_common.sh"

ea_check_deps
ea_check_env

FLOW_ID=""
ACCOUNT_ID=""
TYPE_ID=""
ACTION_ID=""
MONEY=""
F_DATE=""
NOTE=""
ACCOUNT_TO_ID=""
COLLECT="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --flow-id)       FLOW_ID="$2"; shift 2 ;;
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

[[ -n "$FLOW_ID"    ]] || ea_die "缺少 --flow-id"
[[ -n "$ACCOUNT_ID" ]] || ea_die "缺少 --account-id"
[[ -n "$TYPE_ID"    ]] || ea_die "缺少 --type-id"
[[ -n "$ACTION_ID"  ]] || ea_die "缺少 --action-id"
[[ -n "$MONEY"      ]] || ea_die "缺少 --money"
[[ -n "$F_DATE"     ]] || ea_die "缺少 --date"

MONEY=$(ea_normalize_money "$MONEY")
NOTE=$(ea_append_note_tag "$NOTE" "$EA_NOTE_TAG_UPDATE")
CREATE_DATE=$(ea_now)

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

if [[ -n "$ACCOUNT_TO_ID" ]]; then
  BODY=$(echo "$BODY" | jq --argjson aid "$ACCOUNT_TO_ID" '. + {accountToId: $aid}')
fi

ea_put "/flow/updateFlow/${FLOW_ID}" "$BODY" > /dev/null

jq -n \
  --argjson fid "$FLOW_ID" \
  '{success: true, message: "流水更新成功", flowId: $fid}'
