#!/bin/bash

# EasyAccounts 统一构建脚本
# 交互式菜单，支持版本管理、历史记录和镜像上传

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置文件
CONFIG_FILE="versions.json"
HISTORY_FILE="version-history.csv"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查 jq 是否安装
check_jq() {
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}错误: 需要安装 jq 工具${NC}"
        echo "安装命令: apt-get install jq"
        exit 1
    fi
}

# 读取配置
read_config() {
    NAMESPACE=$(jq -r '.namespace' "$CONFIG_FILE")
}

# 获取组件信息
get_component_info() {
    local component=$1
    local field=$2
    jq -r ".components.${component}.${field}" "$CONFIG_FILE"
}

# 更新版本号
update_version() {
    local component=$1
    local new_version=$2
    local tmp_file=$(mktemp)
    jq ".components.${component}.version = \"${new_version}\"" "$CONFIG_FILE" > "$tmp_file"
    mv "$tmp_file" "$CONFIG_FILE"
    echo -e "${GREEN}版本已更新: ${component} -> ${new_version}${NC}"
}

# 记录版本历史
record_history() {
    local component=$1
    local version=$2
    local description=$3
    local date=$(date '+%Y-%m-%d %H:%M:%S')

    echo "${date},${component},${version},${description}" >> "$HISTORY_FILE"
    echo -e "${GREEN}已记录到版本历史${NC}"
}

# 显示当前版本
show_versions() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}       当前组件版本${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    printf "  %-12s %-20s %s\n" "组件" "镜像名" "版本"
    echo "  ----------------------------------------"

    for component in server web ai mysql; do
        local version=$(get_component_info "$component" "version")
        local image=$(get_component_info "$component" "image")
        printf "  %-12s %-20s ${GREEN}%s${NC}\n" "$component" "$image" "$version"
    done
    echo ""
}

# 显示版本历史
show_history() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}       版本更新历史 (最近20条)${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""

    if [ -f "$HISTORY_FILE" ]; then
        head -1 "$HISTORY_FILE"
        echo "----------------------------------------"
        tail -n +2 "$HISTORY_FILE" | tail -20
    else
        echo "暂无历史记录"
    fi

    echo ""
    read -p "按回车继续..."
}

# 构建单个组件
build_component() {
    local component=$1
    local custom_version=$2
    local description=$3

    local version=$(get_component_info "$component" "version")
    local image=$(get_component_info "$component" "image")
    local context=$(get_component_info "$component" "context")
    local pre_build=$(get_component_info "$component" "pre_build")

    if [ -n "$custom_version" ]; then
        version=$custom_version
    fi

    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  构建组件: ${component}${NC}"
    echo -e "${BLUE}  版本: ${version}${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    # 执行预构建命令（在子shell中执行，避免cd影响当前目录）
    if [ "$pre_build" != "null" ] && [ -n "$pre_build" ]; then
        echo -e "${YELLOW}执行预构建命令...${NC}"
        echo "  $pre_build"
        (eval "$pre_build")
        echo -e "${GREEN}预构建完成${NC}"
        echo ""
    fi

    # 构建镜像
    local full_image="${NAMESPACE}/${image}"
    echo -e "${YELLOW}构建 Docker 镜像...${NC}"
    echo "  镜像: ${full_image}:${version}"
    echo "  上下文: ${context}"
    echo ""

    docker build -t "${full_image}:${version}" "${context}"
    docker tag "${full_image}:${version}" "${full_image}:latest"

    echo ""
    echo -e "${GREEN}构建成功!${NC}"
    echo "  ${full_image}:${version}"
    echo "  ${full_image}:latest"

    if [ -n "$custom_version" ]; then
        update_version "$component" "$custom_version"
    fi

    if [ -n "$description" ]; then
        record_history "$component" "$version" "$description"
    fi
}

# 上传单个组件到 Docker Hub
push_dockerhub() {
    local component=$1
    local specified_version=$2
    local image=$(get_component_info "$component" "image")
    local full_image="${NAMESPACE}/${image}"

    # 如果指定了版本就用指定的，否则从配置读取
    local version
    if [ -n "$specified_version" ]; then
        version=$specified_version
    else
        version=$(get_component_info "$component" "version")
    fi

    echo -e "${YELLOW}推送到 Docker Hub: ${full_image}:${version}${NC}"

    docker push "${full_image}:${version}"
    docker push "${full_image}:latest"

    echo -e "${GREEN}✓ Docker Hub 推送成功${NC}"
}

# 上传菜单
upload_menu() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}       上传镜像到 Docker Hub${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    echo -e "  Docker Hub:  ${BLUE}${NAMESPACE}${NC}"
    echo ""

    # 显示本地存在的镜像版本
    echo -e "${CYAN}本地镜像版本:${NC}"
    for component in server web ai mysql; do
        local image=$(get_component_info "$component" "image")
        local tags=$(docker images "${NAMESPACE}/${image}" --format "{{.Tag}}" | grep -v latest | head -3 | tr '\n' ' ')
        printf "  %-10s: %s\n" "$component" "$tags"
    done
    echo ""

    echo -e "${YELLOW}选择要上传的组件:${NC}"
    echo ""
    echo "  1) Server"
    echo "  2) Web"
    echo "  3) AI"
    echo "  4) MySQL"
    echo "  5) 全部"
    echo "  0) 返回"
    echo ""
    read -p "请选择: " component_choice

    local components=()
    case $component_choice in
        1) components=("server") ;;
        2) components=("web") ;;
        3) components=("ai") ;;
        4) components=("mysql") ;;
        5) components=("server" "web" "ai" "mysql") ;;
        0) return ;;
        *) echo -e "${RED}无效选择${NC}"; sleep 1; return ;;
    esac

    echo ""
    # 询问要上传的版本
    echo -e "${YELLOW}输入要上传的版本 (直接回车使用 versions.json 配置的版本):${NC}"
    read -p "版本号: " upload_version
    echo ""

    echo -e "${YELLOW}开始上传...${NC}"
    echo ""

    for comp in "${components[@]}"; do
        echo -e "${BLUE}----------------------------------------${NC}"
        echo -e "${BLUE}  上传: ${comp}${NC}"
        echo -e "${BLUE}----------------------------------------${NC}"
        push_dockerhub "$comp" "$upload_version"
        echo ""
    done

    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  上传完成!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    read -p "按回车继续..."
}

# 主菜单
show_menu() {
    clear
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║     EasyAccounts Docker 构建工具       ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════╝${NC}"

    show_versions

    echo -e "${YELLOW}请选择操作:${NC}"
    echo ""
    echo -e "  ${BLUE}[构建]${NC}"
    echo "  1) 构建 Server  (后端服务)"
    echo "  2) 构建 Web     (前端)"
    echo "  3) 构建 AI      (AI服务)"
    echo "  4) 构建 MySQL   (数据库镜像)"
    echo "  5) 构建全部 (不含MySQL)"
    echo ""
    echo -e "  ${BLUE}[上传]${NC}"
    echo "  6) 上传镜像"
    echo ""
    echo -e "  ${BLUE}[管理]${NC}"
    echo "  7) 修改版本号"
    echo "  8) 查看镜像列表"
    echo "  h) 查看版本历史"
    echo ""
    echo "  0) 退出"
    echo ""
}

# 修改版本号菜单
modify_version_menu() {
    echo ""
    echo -e "${YELLOW}选择要修改版本的组件:${NC}"
    echo ""
    echo "  1) Server"
    echo "  2) Web"
    echo "  3) AI"
    echo "  4) MySQL"
    echo "  5) 全部修改"
    echo "  0) 返回"
    echo ""
    read -p "请选择: " choice

    case $choice in
        1)
            read -p "输入 Server 新版本: " ver
            [ -n "$ver" ] && update_version "server" "$ver"
            ;;
        2)
            read -p "输入 Web 新版本: " ver
            [ -n "$ver" ] && update_version "web" "$ver"
            ;;
        3)
            read -p "输入 AI 新版本: " ver
            [ -n "$ver" ] && update_version "ai" "$ver"
            ;;
        4)
            read -p "输入 MySQL 新版本: " ver
            [ -n "$ver" ] && update_version "mysql" "$ver"
            ;;
        5)
            read -p "输入 Server 新版本: " ver
            [ -n "$ver" ] && update_version "server" "$ver"
            read -p "输入 Web 新版本: " ver
            [ -n "$ver" ] && update_version "web" "$ver"
            read -p "输入 AI 新版本: " ver
            [ -n "$ver" ] && update_version "ai" "$ver"
            read -p "输入 MySQL 新版本: " ver
            [ -n "$ver" ] && update_version "mysql" "$ver"
            ;;
        0)
            return
            ;;
    esac

    echo ""
    read -p "按回车继续..."
}

# 查看镜像列表
show_images() {
    echo ""
    echo -e "${CYAN}本地 EasyAccounts 镜像:${NC}"
    echo ""
    docker images | grep -E "easyaccounts|REPOSITORY" | head -20
    echo ""
    read -p "按回车继续..."
}

# 构建全部
build_all() {
    echo ""
    echo -e "${YELLOW}即将构建全部组件${NC}"
    show_versions

    read -p "是否使用当前版本构建? (Y/n): " confirm
    if [[ "$confirm" =~ ^[Nn] ]]; then
        echo "已取消"
        return
    fi

    read -p "输入本次构建说明 (可选): " description

    for component in server web ai; do
        build_component "$component" "" "$description"
    done

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  全部构建完成!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    read -p "按回车继续..."
}

# 构建单个（带版本询问）
build_single() {
    local component=$1

    echo ""
    local current_version=$(get_component_info "$component" "version")
    echo -e "当前版本: ${GREEN}${current_version}${NC}"

    read -p "输入新版本 (直接回车使用当前版本): " new_version
    read -p "版本说明 (可选): " description

    if [ -z "$new_version" ]; then
        new_version=""
    fi

    build_component "$component" "$new_version" "$description"
    echo ""
    read -p "按回车继续..."
}

# 主循环
main() {
    check_jq
    read_config

    while true; do
        show_menu
        read -p "请选择 [0-9]: " choice

        case $choice in
            1) build_single "server" ;;
            2) build_single "web" ;;
            3) build_single "ai" ;;
            4) build_single "mysql" ;;
            5) build_all ;;
            6) upload_menu ;;
            7) modify_version_menu ;;
            8) show_images ;;
            h|H) show_history ;;
            0)
                echo ""
                echo -e "${GREEN}再见!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}无效选择${NC}"
                sleep 1
                ;;
        esac
    done
}

# 启动
main
