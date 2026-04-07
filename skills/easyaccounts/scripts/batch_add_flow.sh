#!/usr/bin/env bash
# 批量添加流水(自动追加 Claw记账 标记和 from=Claw)
#
# 用法:
#   batch_add_flow.sh <json_file>      # 从文件读取
#   batch_add_flow.sh -                # 从 stdin 读取
#
# 输入格式(JSON 数组):
# [
#   {
#     "accountId": 1,        # 必填
#     "typeId": 5,           # 必填
#     "actionId": 2,         # 必填
#     "money": "30.00",      # 必填(只传正数)
#     "fDate": "2026-04-01", # 必填
#     "note": "公司午餐",     # 可选
#     "accountToId": 2,      # 可选(内部转账时必填)
#     "collect": false       # 可选,默认 false
#   },
#   ...
# ]
#
# 输出:每条结果 + 汇总(成功/失败计数、失败明细)
# 行为:单条失败不中断,继续处理下一条

set -uo pipefail
source "$(dirname "$0")/_common.sh"

ea_check_deps
ea_check_env

if [[ $# -lt 1 ]]; then
  ea_die "用法: $0 <json_file>  或  $0 -"
fi

# 读取输入
if [[ "$1" == "-" ]]; then
  INPUT=$(cat)
else
  [[ -f "$1" ]] || ea_die "文件不存在: $1"
  INPUT=$(cat "$1")
fi

# 校验是 JSON 数组
if ! echo "$INPUT" | jq -e 'type == "array"' >/dev/null 2>&1; then
  ea_die "输入必须是 JSON 数组"
fi

TOTAL=$(echo "$INPUT" | jq 'length')
if (( TOTAL == 0 )); then
  ea_die "输入数组为空"
fi

echo "📋 共 $TOTAL 条待记账..." >&2

# 结果收集
SUCCESS_LIST="[]"
FAILED_LIST="[]"
SUCCESS_COUNT=0
FAILED_COUNT=0
CREATE_DATE=$(ea_now)

# 逐条处理
for (( i = 0; i < TOTAL; i++ )); do
  ITEM=$(echo "$INPUT" | jq ".[$i]")

  # 提取字段
  ACCOUNT_ID=$(echo "$ITEM" | jq -r '.accountId // empty')
  TYPE_ID=$(echo "$ITEM" | jq -r '.typeId // empty')
  ACTION_ID=$(echo "$ITEM" | jq -r '.actionId // empty')
  MONEY=$(echo "$ITEM" | jq -r '.money // empty')
  F_DATE=$(echo "$ITEM" | jq -r '.fDate // empty')
  NOTE=$(echo "$ITEM" | jq -r '.note // ""')
  ACCOUNT_TO_ID=$(echo "$ITEM" | jq -r '.accountToId // empty')
  COLLECT=$(echo "$ITEM" | jq -r '.collect // false')

  # 必填校验
  MISSING=""
  [[ -z "$ACCOUNT_ID" ]] && MISSING="${MISSING}accountId,"
  [[ -z "$TYPE_ID"    ]] && MISSING="${MISSING}typeId,"
  [[ -z "$ACTION_ID"  ]] && MISSING="${MISSING}actionId,"
  [[ -z "$MONEY"      ]] && MISSING="${MISSING}money,"
  [[ -z "$F_DATE"     ]] && MISSING="${MISSING}fDate,"

  if [[ -n "$MISSING" ]]; then
    REASON="第$((i+1))条缺少必填字段: ${MISSING%,}"
    echo "❌ $REASON" >&2
    FAILED_LIST=$(echo "$FAILED_LIST" | jq \
      --argjson idx "$i" --arg reason "$REASON" \
      '. + [{index: $idx, reason: $reason}]')
    FAILED_COUNT=$((FAILED_COUNT + 1))
    continue
  fi

  # 业务处理:去金额负号、追加标记
  MONEY=$(ea_normalize_money "$MONEY")
  NOTE=$(ea_append_note_tag "$NOTE" "$EA_NOTE_TAG_ADD")

  # 构造 payload
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

  # 调用 API(单条失败不中断,关闭 errexit)
  set +e
  RESPONSE=$(ea_post "/flow/addFlow" "$BODY" 2>&1)
  RC=$?
  set -e

  if (( RC != 0 )); then
    REASON="第$((i+1))条失败: $RESPONSE"
    echo "❌ $REASON" >&2
    FAILED_LIST=$(echo "$FAILED_LIST" | jq \
      --argjson idx "$i" --arg reason "$REASON" \
      '. + [{index: $idx, reason: $reason}]')
    FAILED_COUNT=$((FAILED_COUNT + 1))
    continue
  fi

  FLOW_ID=$(echo "$RESPONSE" | jq -r '.data.id // empty')
  echo "✅ 第$((i+1))条成功 (flowId=$FLOW_ID, money=$MONEY, note=$NOTE)" >&2

  SUCCESS_LIST=$(echo "$SUCCESS_LIST" | jq \
    --argjson idx "$i" \
    --arg fid "$FLOW_ID" \
    --arg money "$MONEY" \
    '. + [{index: $idx, flowId: ($fid | tonumber? // null), money: $money}]')
  SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
done

# 输出汇总(标准输出,JSON 格式给 AI 解析)
jq -n \
  --argjson total "$TOTAL" \
  --argjson success "$SUCCESS_COUNT" \
  --argjson failed "$FAILED_COUNT" \
  --argjson successList "$SUCCESS_LIST" \
  --argjson failedList "$FAILED_LIST" \
  '{
    success: ($failed == 0),
    message: "批量记账完成: 成功 \($success)/\($total) 条, 失败 \($failed) 条",
    total: $total,
    successCount: $success,
    failedCount: $failed,
    successList: $successList,
    failedList: $failedList
  }'

# 全部失败时返回非 0
if (( SUCCESS_COUNT == 0 )); then
  exit 1
fi
