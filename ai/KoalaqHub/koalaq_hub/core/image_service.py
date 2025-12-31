"""
图片服务 - 负责从 EasyAccounts 下载图片并转换为 base64
"""

import base64
import os
from typing import List, Optional

import httpx

from ..core.logging_utils import ManagerLogger
from ..models.message import Attachment

logger = ManagerLogger("ImageService")

# 从环境变量获取 EasyAccounts URL
EASYACCOUNTS_URL = os.getenv("EASYACCOUNTS_URL", "http://localhost:8081")


async def fetch_image_as_base64(filename: str, token: str = None) -> Optional[Attachment]:
    """从 EasyAccounts 下载图片并转换为 base64

    Args:
        filename: 图片文件名
        token: 用户认证 token（可选）

    Returns:
        Attachment 对象，失败返回 None
    """
    url = f"{EASYACCOUNTS_URL}/image/{filename}"
    logger.info("开始下载图片", {"url": url, "filename": filename})

    try:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)

            if response.status_code != 200:
                logger.error("下载图片失败", {
                    "url": url,
                    "status_code": response.status_code
                })
                return None

            # 获取 Content-Type
            content_type = response.headers.get("content-type", "image/png")
            # 只取 MIME 类型部分，去掉可能的 charset 等
            media_type = content_type.split(";")[0].strip()

            # 转换为 base64
            image_data = base64.b64encode(response.content).decode("utf-8")

            logger.info("图片下载成功", {
                "filename": filename,
                "media_type": media_type,
                "size": len(response.content)
            })

            return Attachment(
                filename=filename,
                data=image_data,
                media_type=media_type
            )

    except httpx.TimeoutException:
        logger.error("下载图片超时", {"url": url})
        return None
    except Exception as e:
        logger.error("下载图片异常", {"url": url, "error": str(e)})
        return None


async def convert_attachments(
    raw_attachments: List[dict],
    token: str = None
) -> List[Attachment]:
    """批量转换附件

    将前端发送的 filename 列表转换为包含 base64 数据的 Attachment 列表

    Args:
        raw_attachments: 原始附件列表，格式 [{"filename": "xxx.png"}, ...]
        token: 用户认证 token（可选）

    Returns:
        Attachment 对象列表
    """
    if not raw_attachments:
        return []

    result = []
    for raw in raw_attachments:
        filename = raw.get("filename")
        if not filename:
            logger.warning("附件缺少 filename", {"raw": raw})
            continue

        attachment = await fetch_image_as_base64(filename, token)
        if attachment:
            result.append(attachment)
        else:
            logger.warning("图片转换失败，跳过", {"filename": filename})

    logger.info("附件转换完成", {
        "input_count": len(raw_attachments),
        "output_count": len(result)
    })

    return result
