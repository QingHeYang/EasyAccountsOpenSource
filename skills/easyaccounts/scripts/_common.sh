#!/usr/bin/env bash
# EasyAccounts skill 公共函数库
# 提供 token 管理、HTTP 调用、错误处理等通用能力
# 用法:在其他脚本里 `source "$(dirname "$0")/_common.sh"`

set -euo pipefail

# ============================================================
#                        配置常量
# ============================================================

EA_CONFIG_DIR="${HOME}/.config/easyaccounts"
EA_TOKEN_FILE="${EA_CONFIG_DIR}/token"

# 来源标记(纯文本,避开后端 JDBC characterEncoding=utf-8 不支持 4 字节 emoji 的问题)
EA_FROM_TAG="Claw"
EA_NOTE_TAG_ADD="#Claw记账"
EA_NOTE_TAG_UPDATE="#Claw更新"

# ============================================================
#                        工具函数
# ============================================================

# 输出错误并退出
ea_die() {
  echo "ERROR: $*" >&2
  exit 1
}

# 检查依赖
ea_check_deps() {
  command -v curl >/dev/null 2>&1 || ea_die "缺少 curl,请先安装"
  command -v jq   >/dev/null 2>&1 || ea_die "缺少 jq,请先安装(brew install jq / apt install jq)"
}

# 检查环境变量
ea_check_env() {
  [[ -n "${EASYACCOUNTS_URL:-}" ]] || ea_die "环境变量 EASYACCOUNTS_URL 未设置"
}

# ============================================================
#                       Token 管理
# ============================================================

# 保存 token
ea_save_token() {
  local token="$1"
  mkdir -p "$EA_CONFIG_DIR"
  printf '%s' "$token" > "$EA_TOKEN_FILE"
  chmod 600 "$EA_TOKEN_FILE"
}

# 读取 token
ea_load_token() {
  [[ -f "$EA_TOKEN_FILE" ]] || ea_die "未登录,请先运行 login.sh"
  cat "$EA_TOKEN_FILE"
}

# 清除 token
ea_clear_token() {
  rm -f "$EA_TOKEN_FILE"
}

# ============================================================
#                       HTTP 调用封装
# ============================================================

# GET 请求(带 token)
# 用法:ea_get <path>
ea_get() {
  local path="$1"
  local token
  token=$(ea_load_token)

  local response
  response=$(curl -sS -w '\n__HTTP_STATUS__:%{http_code}' \
    -H "authorization: $token" \
    "${EASYACCOUNTS_URL}${path}")

  ea_handle_response "$response"
}

# 把 JSON body 写到临时文件
# 重要:Windows + Git Bash 上,curl -d "$body" 会通过 ANSI code page 传递命令行参数,
# 导致 UTF-8 中文被错误转码为 GBK。改用 --data-binary @file 完全绕过该问题。
_ea_write_body_tmp() {
  local body="$1"
  local tmp
  tmp=$(mktemp -t ea_body.XXXXXX.json)
  printf '%s' "$body" > "$tmp"
  echo "$tmp"
}

# POST 请求(带 token,JSON body)
# 用法:ea_post <path> <json_body>
ea_post() {
  local path="$1"
  local body="$2"
  local token
  token=$(ea_load_token)

  local tmp
  tmp=$(_ea_write_body_tmp "$body")

  local response
  response=$(curl -sS -w '\n__HTTP_STATUS__:%{http_code}' \
    -H "authorization: $token" \
    -H "Content-Type: application/json; charset=utf-8" \
    -X POST \
    --data-binary "@$tmp" \
    "${EASYACCOUNTS_URL}${path}")

  rm -f "$tmp"
  ea_handle_response "$response"
}

# PUT 请求(带 token,JSON body)
ea_put() {
  local path="$1"
  local body="$2"
  local token
  token=$(ea_load_token)

  local tmp
  tmp=$(_ea_write_body_tmp "$body")

  local response
  response=$(curl -sS -w '\n__HTTP_STATUS__:%{http_code}' \
    -H "authorization: $token" \
    -H "Content-Type: application/json; charset=utf-8" \
    -X PUT \
    --data-binary "@$tmp" \
    "${EASYACCOUNTS_URL}${path}")

  rm -f "$tmp"
  ea_handle_response "$response"
}

# 不带 token 的 POST(用于 login)
# 用法:ea_post_noauth <path> <json_body>
ea_post_noauth() {
  local path="$1"
  local body="$2"

  local tmp
  tmp=$(_ea_write_body_tmp "$body")

  local response
  response=$(curl -sS -w '\n__HTTP_STATUS__:%{http_code}' \
    -H "Content-Type: application/json; charset=utf-8" \
    -X POST \
    --data-binary "@$tmp" \
    "${EASYACCOUNTS_URL}${path}")

  rm -f "$tmp"
  ea_handle_response "$response"
}

# 处理 HTTP 响应
# 输入格式:<body>\n__HTTP_STATUS__:<code>
# 输出:JSON body(失败时退出)
ea_handle_response() {
  local raw="$1"
  local status body
  status=$(echo "$raw" | grep -o '__HTTP_STATUS__:[0-9]*' | tail -1 | cut -d: -f2)
  body=$(echo "$raw" | sed 's/__HTTP_STATUS__:[0-9]*$//')

  case "$status" in
    200|201)
      # HTTP OK,但还要检查业务 code
      local biz_code
      biz_code=$(echo "$body" | jq -r '.code // 0' 2>/dev/null || echo "0")
      if [[ "$biz_code" != "0" ]]; then
        local msg
        msg=$(echo "$body" | jq -r '.msg // "未知错误"' 2>/dev/null || echo "未知错误")
        ea_die "业务错误[$biz_code]: $msg"
      fi
      echo "$body"
      ;;
    401|418)
      ea_clear_token
      ea_die "认证失败(HTTP $status),token 已清除,请重新运行 login.sh"
      ;;
    *)
      ea_die "HTTP $status: $body"
      ;;
  esac
}

# ============================================================
#                       JSON 构造辅助
# ============================================================

# 处理金额:去掉负号
ea_normalize_money() {
  local money="$1"
  echo "${money#-}"
}

# 给备注追加标记(如未包含)
# 用法:ea_append_note_tag <note> <tag>
ea_append_note_tag() {
  local note="$1"
  local tag="$2"
  if [[ -z "$note" ]]; then
    echo "$tag"
  elif [[ "$note" == *"$tag"* ]]; then
    echo "$note"
  else
    echo "$note $tag"
  fi
}

# 当前时间戳(yyyy-MM-dd HH:mm:ss)
ea_now() {
  date '+%Y-%m-%d %H:%M:%S'
}

# MD5 哈希(小写 hex)
# 用法:ea_md5 <明文字符串>
# 优先 md5sum(Linux/Git Bash 内置),fallback 到 openssl
ea_md5() {
  local input="$1"
  if command -v md5sum >/dev/null 2>&1; then
    printf '%s' "$input" | md5sum | awk '{print $1}'
  elif command -v openssl >/dev/null 2>&1; then
    printf '%s' "$input" | openssl md5 | awk '{print $NF}'
  else
    ea_die "缺少 md5sum 或 openssl,无法计算密码 hash"
  fi
}
