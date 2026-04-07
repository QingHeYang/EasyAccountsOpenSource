#!/usr/bin/env bash
# EasyAccounts 登录脚本
# 用法:login.sh <username> <password>
# 成功:保存 token 到 ~/.config/easyaccounts/token,输出成功信息
# 失败:退出码非 0,输出错误原因

set -euo pipefail
source "$(dirname "$0")/_common.sh"

ea_check_deps
ea_check_env

if [[ $# -lt 2 ]]; then
  ea_die "用法: $0 <username> <password>"
fi

USERNAME="$1"
PASSWORD="$2"

# 后端要求密码 MD5 hash(与前端 MD5(password).toString() 一致)
HASHED=$(ea_md5 "$PASSWORD")

# 构造 JSON body(用 jq 安全转义)
BODY=$(jq -n --arg u "$USERNAME" --arg p "$HASHED" \
  '{username: $u, password: $p}')

# 调用登录接口(无需 token)
RESPONSE=$(ea_post_noauth "/auth/login" "$BODY")

# 提取 token
TOKEN=$(echo "$RESPONSE" | jq -r '.data.token // empty')

if [[ -z "$TOKEN" ]]; then
  ea_die "登录响应未包含 token: $RESPONSE"
fi

# 保存 token
ea_save_token "$TOKEN"

echo "✅ 登录成功,token 已保存到 $EA_TOKEN_FILE"
