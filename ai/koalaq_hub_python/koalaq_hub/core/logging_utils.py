"""
日志工具模块
为各个manager提供统一的日志记录功能
"""

import logging
import os
from typing import Optional
from datetime import datetime


def get_logger(manager_name: str) -> logging.Logger:
    """
    获取带有manager标识的logger

    Args:
        manager_name: Manager名称，如 'ChatSession', 'PromptManager' 等

    Returns:
        配置好的logger实例
    """
    logger_name = f"koalaq.{manager_name.lower()}"
    logger = logging.getLogger(logger_name)
    
    # 使用父logger的配置（在__main__.py中已配置）
    # 不再单独配置，避免重复
    return logger


class ManagerLogger:
    """
    Manager日志记录器基类
    为各个manager提供统一的日志接口
    """

    def __init__(self, manager_name: str):
        """
        初始化Manager日志记录器

        Args:
            manager_name: Manager名称
        """
        self.manager_name = manager_name
        self.logger = get_logger(manager_name)

    def info(self, message: str, extra_data: Optional[dict] = None) -> None:
        """记录INFO级别日志"""
        formatted_msg = f"[{self.manager_name}] {message}"
        if extra_data:
            formatted_msg += f" | 详情: {extra_data}"
        self.logger.info(formatted_msg)

    def error(self, message: str, exception: Optional[Exception] = None, extra_data: Optional[dict] = None) -> None:
        """记录ERROR级别日志"""
        formatted_msg = f"[{self.manager_name}] {message}"
        if exception:
            formatted_msg += f" | 异常: {exception}"
        if extra_data:
            formatted_msg += f" | 详情: {extra_data}"
        self.logger.error(formatted_msg)

    def warning(self, message: str, extra_data: Optional[dict] = None) -> None:
        """记录WARNING级别日志"""
        formatted_msg = f"[{self.manager_name}] {message}"
        if extra_data:
            formatted_msg += f" | 详情: {extra_data}"
        self.logger.warning(formatted_msg)

    def debug(self, message: str, extra_data: Optional[dict] = None) -> None:
        """记录DEBUG级别日志"""
        formatted_msg = f"[{self.manager_name}] {message}"
        if extra_data:
            formatted_msg += f" | 详情: {extra_data}"
        self.logger.debug(formatted_msg)

    def log_method_entry(self, method_name: str, params: Optional[dict] = None) -> None:
        """记录方法进入日志"""
        msg = f"进入方法: {method_name}"
        if params:
            msg += f" | 参数: {params}"
        self.debug(msg)

    def log_method_exit(self, method_name: str, result: Optional[str] = None) -> None:
        """记录方法退出日志"""
        msg = f"退出方法: {method_name}"
        if result:
            msg += f" | 结果: {result}"
        self.debug(msg)

    def log_operation(self, operation: str, status: str = "SUCCESS", details: Optional[dict] = None) -> None:
        """记录操作日志"""
        msg = f"操作: {operation} | 状态: {status}"
        if details:
            msg += f" | 详情: {details}"

        if status == "SUCCESS":
            self.info(msg)
        elif status == "ERROR":
            self.error(msg)
        else:
            self.warning(msg)
