"""
通用API响应模型
类似于Java中的ResultVO、ResponseEntity，统一API返回格式
使用HTTP状态码作为错误码，保持RESTful风格
"""

from typing import Any, Generic, List, Optional, TypeVar

from fastapi import status
from pydantic import BaseModel, Field

# 泛型类型变量
T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    通用API响应类
    类似于Java Spring的ResponseEntity，统一所有API的返回格式
    """

    success: bool = Field(description="请求是否成功")
    message: str = Field(description="响应消息")
    code: int = Field(description="HTTP状态码")
    data: Optional[T] = Field(default=None, description="响应数据")
    request_id: Optional[str] = Field(default=None, description="请求追踪ID")
    timestamp: Optional[int] = Field(default=None, description="响应时间戳")

    class Config:
        json_encoders = {
            # 可以添加自定义编码器
        }


class PaginationInfo(BaseModel):
    """
    分页信息模型
    """

    page: int = Field(ge=1, description="当前页码")
    limit: int = Field(ge=1, le=100, description="每页数量")
    total: int = Field(ge=0, description="总记录数")
    total_pages: int = Field(ge=0, description="总页数")
    has_more: bool = Field(description="是否有更多数据")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    分页响应数据模型
    """

    items: List[T] = Field(description="数据列表")
    pagination: PaginationInfo = Field(description="分页信息")


class ResponseBuilder:
    """
    响应构建器
    类似于Java的Builder模式，方便构建各种类型的API响应
    """

    @staticmethod
    def success(data: Any = None, message: str = "操作成功", request_id: str = None) -> ApiResponse:
        """
        构建成功响应

        Args:
            data: 响应数据
            message: 成功消息
            request_id: 请求ID

        Returns:
            成功响应对象
        """
        import time

        return ApiResponse(success=True, message=message, code=status.HTTP_200_OK, data=data, request_id=request_id, timestamp=int(time.time() * 1000))

    @staticmethod
    def created(data: Any = None, message: str = "创建成功", request_id: str = None) -> ApiResponse:
        """
        构建创建成功响应（201）

        Args:
            data: 响应数据
            message: 成功消息
            request_id: 请求ID

        Returns:
            创建成功响应对象
        """
        import time

        return ApiResponse(success=True, message=message, code=status.HTTP_201_CREATED, data=data, request_id=request_id, timestamp=int(time.time() * 1000))

    @staticmethod
    def no_content(message: str = "操作成功", request_id: str = None) -> ApiResponse:
        """
        构建无内容响应（204）

        Args:
            message: 成功消息
            request_id: 请求ID

        Returns:
            无内容响应对象
        """
        import time

        return ApiResponse(success=True, message=message, code=status.HTTP_204_NO_CONTENT, data=None, request_id=request_id, timestamp=int(time.time() * 1000))

    @staticmethod
    def bad_request(message: str = "请求参数错误", data: Any = None, request_id: str = None) -> ApiResponse:
        """
        构建请求错误响应（400）

        Args:
            message: 错误消息
            data: 错误详情
            request_id: 请求ID

        Returns:
            请求错误响应对象
        """
        import time

        return ApiResponse(success=False, message=message, code=status.HTTP_400_BAD_REQUEST, data=data, request_id=request_id, timestamp=int(time.time() * 1000))

    @staticmethod
    def unauthorized(message: str = "认证失败", request_id: str = None) -> ApiResponse:
        """
        构建认证失败响应（401）

        Args:
            message: 错误消息
            request_id: 请求ID

        Returns:
            认证失败响应对象
        """
        import time

        return ApiResponse(success=False, message=message, code=status.HTTP_401_UNAUTHORIZED, data=None, request_id=request_id, timestamp=int(time.time() * 1000))

    @staticmethod
    def forbidden(message: str = "权限不足", request_id: str = None) -> ApiResponse:
        """
        构建权限不足响应（403）

        Args:
            message: 错误消息
            request_id: 请求ID

        Returns:
            权限不足响应对象
        """
        import time

        return ApiResponse(success=False, message=message, code=status.HTTP_403_FORBIDDEN, data=None, request_id=request_id, timestamp=int(time.time() * 1000))

    @staticmethod
    def not_found(message: str = "资源不存在", request_id: str = None) -> ApiResponse:
        """
        构建资源不存在响应（404）

        Args:
            message: 错误消息
            request_id: 请求ID

        Returns:
            资源不存在响应对象
        """
        import time

        return ApiResponse(success=False, message=message, code=status.HTTP_404_NOT_FOUND, data=None, request_id=request_id, timestamp=int(time.time() * 1000))

    @staticmethod
    def conflict(message: str = "资源冲突", data: Any = None, request_id: str = None) -> ApiResponse:
        """
        构建资源冲突响应（409）

        Args:
            message: 错误消息
            data: 冲突详情
            request_id: 请求ID

        Returns:
            资源冲突响应对象
        """
        import time

        return ApiResponse(success=False, message=message, code=status.HTTP_409_CONFLICT, data=data, request_id=request_id, timestamp=int(time.time() * 1000))

    @staticmethod
    def internal_error(message: str = "服务器内部错误", request_id: str = None) -> ApiResponse:
        """
        构建服务器错误响应（500）

        Args:
            message: 错误消息
            request_id: 请求ID

        Returns:
            服务器错误响应对象
        """
        import time

        return ApiResponse(success=False, message=message, code=status.HTTP_500_INTERNAL_SERVER_ERROR, data=None, request_id=request_id, timestamp=int(time.time() * 1000))

    @staticmethod
    def custom_error(code: int, message: str, data: Any = None, request_id: str = None) -> ApiResponse:
        """
        构建自定义错误响应

        Args:
            code: 自定义状态码
            message: 错误消息
            data: 错误数据
            request_id: 请求ID

        Returns:
            自定义错误响应对象
        """
        import time

        return ApiResponse(success=False, message=message, code=code, data=data, request_id=request_id, timestamp=int(time.time() * 1000))

    @staticmethod
    def paginated(items: List[Any], page: int, limit: int, total: int, message: str = "查询成功", request_id: str = None) -> ApiResponse[PaginatedResponse]:
        """
        构建分页响应

        Args:
            items: 数据列表
            page: 当前页码
            limit: 每页数量
            total: 总记录数
            message: 成功消息
            request_id: 请求ID

        Returns:
            分页响应对象
        """
        import math
        import time

        total_pages = math.ceil(total / limit) if limit > 0 else 0
        has_more = page < total_pages

        pagination = PaginationInfo(page=page, limit=limit, total=total, total_pages=total_pages, has_more=has_more)

        paginated_data = PaginatedResponse(items=items, pagination=pagination)

        return ApiResponse(success=True, message=message, code=status.HTTP_200_OK, data=paginated_data, request_id=request_id, timestamp=int(time.time() * 1000))


# 便捷的响应函数，类似于Java Spring的ResponseEntity静态方法
def ok(data: Any = None, message: str = "操作成功") -> ApiResponse:
    """快捷创建成功响应"""
    return ResponseBuilder.success(data, message)


def created(data: Any = None, message: str = "创建成功") -> ApiResponse:
    """快捷创建创建成功响应"""
    return ResponseBuilder.created(data, message)


def bad_request(message: str = "请求参数错误", data: Any = None) -> ApiResponse:
    """快捷创建请求错误响应"""
    return ResponseBuilder.bad_request(message, data)


def unauthorized(message: str = "认证失败") -> ApiResponse:
    """快捷创建认证失败响应"""
    return ResponseBuilder.unauthorized(message)


def forbidden(message: str = "权限不足") -> ApiResponse:
    """快捷创建权限不足响应"""
    return ResponseBuilder.forbidden(message)


def not_found(message: str = "资源不存在") -> ApiResponse:
    """快捷创建资源不存在响应"""
    return ResponseBuilder.not_found(message)


def internal_error(message: str = "服务器内部错误") -> ApiResponse:
    """快捷创建服务器错误响应"""
    return ResponseBuilder.internal_error(message)


def paginated(items: List[Any], page: int, limit: int, total: int, message: str = "查询成功") -> ApiResponse[PaginatedResponse]:
    """快捷创建分页响应"""
    return ResponseBuilder.paginated(items, page, limit, total, message)
