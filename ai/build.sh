#!/bin/bash

# EasyAccounts AI 服务镜像构建脚本
# 构建并标记AI服务镜像

set -e

# 定义镜像信息
DOCKER_HUB_USER="775495797"
IMAGE_NAME="easyaccounts-ai"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}"
LOCAL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

echo "================================================"
echo "EasyAccounts AI 服务镜像构建"
echo "================================================"
echo ""
echo "镜像名称: ${FULL_IMAGE_NAME}"
echo "本地标签: ${LOCAL_IMAGE_NAME}"
echo ""

# 构建镜像（使用host网络模式，禁用代理）
echo "开始构建镜像（使用host网络模式）..."
docker build \
    --network=host \
    --build-arg HTTP_PROXY= \
    --build-arg HTTPS_PROXY= \
    --build-arg http_proxy= \
    --build-arg https_proxy= \
    --build-arg no_proxy= \
    -t ${LOCAL_IMAGE_NAME} .

if [ $? -eq 0 ]; then
    echo "✓ 镜像构建成功: ${LOCAL_IMAGE_NAME}"
    
    # 为 Docker Hub 添加标签
    echo "添加 Docker Hub 标签..."
    docker tag ${LOCAL_IMAGE_NAME} ${FULL_IMAGE_NAME}
    echo "✓ 已添加标签: ${FULL_IMAGE_NAME}"
    
    echo ""
    echo "================================================"
    echo "构建完成！"
    echo "================================================"
    echo ""
    echo "本地使用:"
    echo "  docker run -d --name easyaccounts-ai ${LOCAL_IMAGE_NAME}"
    echo ""
    echo "推送到 Docker Hub:"
    echo "  docker push ${FULL_IMAGE_NAME}"
    echo ""
    echo "查看镜像:"
    echo "  docker images | grep ${IMAGE_NAME}"
else
    echo "✗ 镜像构建失败"
    exit 1
fi