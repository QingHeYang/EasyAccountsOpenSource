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
# 不存在时返回空字符串(支持 ENABLE_LOGIN=false 的服务端,无需登录直接调用)
ea_load_token() {
  if [[ -f "$EA_TOKEN_FILE" ]]; then
    cat "$EA_TOKEN_FILE"
  else
    echo ""
  fi
}

# 清除 token
ea_clear_token() {
  rm -f "$EA_TOKEN_FILE"
}

# ============================================================
#                       HTTP 调用封装
# ============================================================

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

# 检查响应是否 401(纯检查,无副作用)
_ea_is_401() {
  local raw="$1"
  local status
  status=$(echo "$raw" | grep -o '__HTTP_STATUS__:[0-9]*' | tail -1 | cut -d: -f2)
  [[ "$status" == "401" || "$status" == "418" ]]
}

# 尝试用环境变量自动登录
# 返回 0 = 成功,1 = 失败(无凭据或登录失败)
# 不打印任何东西到 stdout(避免污染调用方)
_ea_try_auto_login() {
  if [[ -z "${EASYACCOUNTS_USERNAME:-}" || -z "${EASYACCOUNTS_PASSWORD:-}" ]]; then
    return 1
  fi

  local hashed body tmp response status biz_code token
  hashed=$(ea_md5 "$EASYACCOUNTS_PASSWORD")
  body=$(jq -n --arg u "$EASYACCOUNTS_USERNAME" --arg p "$hashed" \
    '{username: $u, password: $p}')
  tmp=$(_ea_write_body_tmp "$body")

  response=$(curl -sS -w '\n__HTTP_STATUS__:%{http_code}' \
    -H "Content-Type: application/json; charset=utf-8" \
    -X POST \
    --data-binary "@$tmp" \
    "${EASYACCOUNTS_URL}/auth/login" 2>/dev/null) || { rm -f "$tmp"; return 1; }
  rm -f "$tmp"

  status=$(echo "$response" | grep -o '__HTTP_STATUS__:[0-9]*' | tail -1 | cut -d: -f2)
  [[ "$status" == "200" ]] || return 1

  body=$(echo "$response" | sed 's/__HTTP_STATUS__:[0-9]*$//')
  biz_code=$(echo "$body" | jq -r '.code // 0' 2>/dev/null || echo "0")
  [[ "$biz_code" == "0" ]] || return 1

  token=$(echo "$body" | jq -r '.data.token // empty')
  [[ -n "$token" ]] || return 1

  ea_save_token "$token"
  return 0
}

# 内部:执行一次 HTTP 调用,返回响应
# 用法:_ea_curl <method> <path> [<body>]
_ea_curl() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  local token
  token=$(ea_load_token)

  if [[ "$method" == "GET" ]]; then
    curl -sS -w '\n__HTTP_STATUS__:%{http_code}' \
      -H "authorization: $token" \
      "${EASYACCOUNTS_URL}${path}"
  else
    local tmp
    tmp=$(_ea_write_body_tmp "$body")
    curl -sS -w '\n__HTTP_STATUS__:%{http_code}' \
      -H "authorization: $token" \
      -H "Content-Type: application/json; charset=utf-8" \
      -X "$method" \
      --data-binary "@$tmp" \
      "${EASYACCOUNTS_URL}${path}"
    rm -f "$tmp"
  fi
}

# 内部:带 401 自动重试的 HTTP 调用
# 401 时尝试用 env 凭据自动登录,成功后重试一次
_ea_call() {
  local method="$1"
  local path="$2"
  local body="${3:-}"

  local response
  response=$(_ea_curl "$method" "$path" "$body")

  if _ea_is_401 "$response" && _ea_try_auto_login; then
    response=$(_ea_curl "$method" "$path" "$body")
  fi

  ea_handle_response "$response"
}

# 公共 HTTP 接口
ea_get() { _ea_call "GET" "$1"; }
ea_post() { _ea_call "POST" "$1" "$2"; }
ea_put() { _ea_call "PUT" "$1" "$2"; }

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
      ea_die "认证失败(HTTP $status)。可能原因:1) 服务端开启了登录但未提供 token;2) token 已过期(默认 30 分钟)。请运行 login.sh 重新登录(需要用户名密码)。"
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
