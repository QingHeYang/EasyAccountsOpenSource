"""
基础Repository抽象类
为所有Repository提供通用的数据库操作方法
"""

import logging
import sqlite3
from abc import ABC
from typing import Any, Dict, List, Optional, Tuple

from .database_connection import DatabaseConnection


class BaseRepository(ABC):
    """所有Repository的基类，提供通用数据库操作方法"""

    def __init__(self, db_connection: DatabaseConnection):
        """初始化Repository

        Args:
            db_connection: 数据库连接管理器
        """
        self.db_connection = db_connection
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    def connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        return self.db_connection.get_connection()

    def _execute_query(self, sql: str, params: Optional[Tuple] = None) -> sqlite3.Cursor:
        """执行查询语句（SELECT）

        Args:
            sql: SQL查询语句
            params: 查询参数

        Returns:
            sqlite3.Cursor: 查询结果游标
        """
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor
        except Exception as e:
            self.logger.error(f"执行查询失败: {sql}, 参数: {params}, 错误: {e}")
            raise

    def _execute_insert(self, sql: str, params: Optional[Tuple] = None) -> int:
        """执行插入语句（INSERT）

        Args:
            sql: SQL插入语句
            params: 插入参数

        Returns:
            int: 新插入记录的ID
        """
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"执行插入失败: {sql}, 参数: {params}, 错误: {e}")
            raise

    def _execute_update(self, sql: str, params: Optional[Tuple] = None) -> int:
        """执行更新语句（UPDATE/DELETE）

        Args:
            sql: SQL更新语句
            params: 更新参数

        Returns:
            int: 受影响的行数
        """
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            self.connection.commit()
            return cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"执行更新失败: {sql}, 参数: {params}, 错误: {e}")
            raise

    def _fetch_one(self, sql: str, params: Optional[Tuple] = None) -> Optional[sqlite3.Row]:
        """查询单条记录

        Args:
            sql: SQL查询语句
            params: 查询参数

        Returns:
            Optional[sqlite3.Row]: 单条记录，如果不存在则返回None
        """
        try:
            cursor = self._execute_query(sql, params)
            return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"查询单条记录失败: {sql}, 参数: {params}, 错误: {e}")
            raise

    def _fetch_all(self, sql: str, params: Optional[Tuple] = None) -> List[sqlite3.Row]:
        """查询多条记录

        Args:
            sql: SQL查询语句
            params: 查询参数

        Returns:
            List[sqlite3.Row]: 记录列表
        """
        try:
            cursor = self._execute_query(sql, params)
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"查询多条记录失败: {sql}, 参数: {params}, 错误: {e}")
            raise

    def _execute_batch(self, sql: str, params_list: List[Tuple]) -> None:
        """批量执行SQL语句

        Args:
            sql: SQL语句
            params_list: 参数列表
        """
        try:
            cursor = self.connection.cursor()
            cursor.executemany(sql, params_list)
            self.connection.commit()
            self.logger.info(f"批量执行完成，共{len(params_list)}条记录")
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"批量执行失败: {sql}, 错误: {e}")
            raise

    def _dict_to_row(self, data: Dict[str, Any]) -> sqlite3.Row:
        """将字典转换为sqlite3.Row对象

        Args:
            data: 字典数据

        Returns:
            sqlite3.Row: Row对象
        """
        # 创建一个模拟的Row对象
        row = sqlite3.Row.__new__(sqlite3.Row)
        row._index_map = {key: i for i, key in enumerate(data.keys())}
        row._data = tuple(data.values())
        return row

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """将sqlite3.Row对象转换为字典

        Args:
            row: Row对象

        Returns:
            Dict[str, Any]: 字典数据
        """
        if row is None:
            return {}
        return dict(row)

    def _build_where_clause(self, conditions: Dict[str, Any]) -> Tuple[str, Tuple]:
        """构建WHERE子句

        Args:
            conditions: 查询条件字典

        Returns:
            Tuple[str, Tuple]: WHERE子句和参数
        """
        if not conditions:
            return "", ()

        where_parts = []
        params = []

        for key, value in conditions.items():
            if value is None:
                where_parts.append(f"{key} IS NULL")
            elif isinstance(value, (list, tuple)):
                # IN 查询
                placeholders = ",".join(["?" for _ in value])
                where_parts.append(f"{key} IN ({placeholders})")
                params.extend(value)
            else:
                where_parts.append(f"{key} = ?")
                params.append(value)

        where_clause = " AND ".join(where_parts)
        return f"WHERE {where_clause}", tuple(params)

    def _build_update_clause(self, updates: Dict[str, Any]) -> Tuple[str, Tuple]:
        """构建UPDATE的SET子句

        Args:
            updates: 更新字段字典

        Returns:
            Tuple[str, Tuple]: SET子句和参数
        """
        if not updates:
            return "", ()

        set_parts = []
        params = []

        for key, value in updates.items():
            set_parts.append(f"{key} = ?")
            params.append(value)

        set_clause = ", ".join(set_parts)
        return f"SET {set_clause}", tuple(params)
