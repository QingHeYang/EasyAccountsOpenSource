#!/usr/bin/env bash
# 系统信息查询(版本配置 + 公告)
#
# 用法:
#   system_info.sh notices        # 获取项目公告列表
#   system_info.sh version        # 获取版本和系统配置(含云端更新提示)
#   system_info.sh all            # 同时获取两者(默认)
#
# 用途:
# - notices:用户问"有什么公告/通知/项目动态"时使用
# - version:用户问"系统版本/有没有新版/我的配置"时使用
# - all:用户首次使用 skill 或问"系统状态"时使用

set -euo pipefail
source "$(dirname "$0")/_common.sh"

ea_check_deps
ea_check_env

TYPE="${1:-all}"

case "$TYPE" in
  notices|version|all) ;;
  *) ea_die "未知参数: $TYPE  (支持: notices | version | all)" ;;
esac

# 拉取 notices,只保留有效字段
fetch_notices() {
  local raw
  raw=$(ea_get "/home/getNotices")
  echo "$raw" | jq '{
    notices: (.data // [] | map({
      id, title, content, date,
      url: (if .url == "" then null else .url end),
      expire: (if .expire == "" then null else .expire end)
    })),
    count: (.data // [] | length)
  }'
}

# 拉取 version,把更新状态变成易读字段
fetch_version() {
  local raw
  raw=$(ea_get "/home/getVersion")
  echo "$raw" | jq '{
    versions: .data.versions,
    auth: .data.auth,
    backup: .data.backup,
    update: (
      if .data.update == null then
        {hasUpdate: false, message: "当前已是最新版本"}
      else
        {
          hasUpdate: true,
          newVersion: .data.update.version,
          newVersionCode: .data.update.versionCode,
          releaseDate: .data.update.releaseDate,
          changelog: .data.update.changelog,
          currentVersionCode: .data.versions.versionCode
        }
      end
    )
  }'
}

case "$TYPE" in
  notices)
    fetch_notices
    ;;
  version)
    fetch_version
    ;;
  all)
    NOTICES=$(fetch_notices)
    VERSION=$(fetch_version)
    jq -n --argjson notices "$NOTICES" --argjson version "$VERSION" \
      '{notices: $notices, version: $version}'
    ;;
esac
