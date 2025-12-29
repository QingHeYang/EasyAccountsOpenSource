"""
总结Repository
负责总结相关的所有数据库操作，包括快照(summary_snapshots)和日志(summary_log)
"""

import datetime
from typing import Any, Dict, List, Optional, Union

from ...core.logging_utils import ManagerLogger
from ...models.data_models import SummaryLog
from ..base.base_repository import BaseRepository
from ..base.database_connection import DatabaseConnection


class SummaryRepository(BaseRepository):
    """总结数据访问对象"""
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection)
        self.logger = ManagerLogger("SummaryRepository")

    # ==================== 总结日志(summary_log)操作 ====================

    def create_summary_log(self, summary_log: SummaryLog) -> int:
        """创建总结日志记录

        Args:
            summary_log: 总结日志对象

        Returns:
            int: 新创建的日志记录ID
        """
        try:
            sql = """
                INSERT INTO summary_log (
                    summary_content, summary_result, status, conversation_id, 
                    round_id, snapshot_id, platform, model, created_at, updated_at, 
                    error_message, execution_time, total_tokens
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                summary_log.summary_content,
                summary_log.summary_result,
                summary_log.status,
                summary_log.conversation_id,
                summary_log.round_id,
                summary_log.snapshot_id,
                summary_log.platform,
                summary_log.model,
                summary_log.created_at,
                summary_log.updated_at,
                summary_log.error_message,
                summary_log.execution_time,
                summary_log.total_tokens,
            )

            log_id = self._execute_insert(sql, params)
            self.logger.info(f"总结日志创建成功: log_id={log_id}")
            return log_id

        except Exception as e:
            self.logger.error(f"创建总结日志失败: {e}")
            raise e

    def update_summary_log(self, log_id: int, summary_result: str = None, status: str = None, error_message: str = None, execution_time: float = None) -> bool:
        """更新总结日志记录

        Args:
            log_id: 日志记录ID
            summary_result: 总结结果
            status: 状态
            error_message: 错误信息
            execution_time: 执行时间
            total_tokens: 总token数量

        Returns:
            bool: 更新是否成功
        """
        try:
            # 构建动态更新语句
            updates = {}
            if summary_result is not None:
                updates["summary_result"] = summary_result
            if status is not None:
                updates["status"] = status
            if error_message is not None:
                updates["error_message"] = error_message
            if execution_time is not None:
                updates["execution_time"] = execution_time
            # 总是更新 updated_at
            updates["updated_at"] = datetime.datetime.now().isoformat()

            if not updates:
                self.logger.warning("没有字段需要更新")
                return False

            set_clause, params = self._build_update_clause(updates)
            sql = f"UPDATE summary_log {set_clause} WHERE log_id = ?"
            params = params + (log_id,)

            rows_affected = self._execute_update(sql, params)

            if rows_affected > 0:
                self.logger.info(f"总结日志更新成功: log_id={log_id}")
                return True
            else:
                self.logger.warning(f"总结日志记录不存在: log_id={log_id}")
                return False

        except Exception as e:
            self.logger.error(f"更新总结日志失败: {e}")
            raise e

    def get_summary_log(self, log_id: int) -> Optional[SummaryLog]:
        """根据log_id获取总结日志记录

        Args:
            log_id: 日志记录ID

        Returns:
            Optional[SummaryLog]: 总结日志对象，如果不存在则返回None
        """
        try:
            sql = """
                SELECT log_id, summary_content, summary_result, status, 
                       conversation_id, round_id, snapshot_id, platform, model,
                       created_at, updated_at, error_message, execution_time, total_tokens
                FROM summary_log
                WHERE log_id = ?
            """
            row = self._fetch_one(sql, (log_id,))

            if row:
                log_data = self._row_to_dict(row)
                self.logger.debug(f"获取总结日志成功: log_id={log_id}")
                return SummaryLog.from_dict(log_data)
            else:
                self.logger.warning(f"总结日志不存在: log_id={log_id}")
                return None

        except Exception as e:
            self.logger.error(f"获取总结日志失败: {e}")
            raise e

    def get_summary_logs_by_conversation(self, conversation_id: str, limit: int = 50) -> List[SummaryLog]:
        """获取指定会话的总结日志记录

        Args:
            conversation_id: 会话ID
            limit: 返回记录数限制

        Returns:
            List[SummaryLog]: 总结日志列表
        """
        try:
            sql = """
                SELECT log_id, summary_content, summary_result, status, 
                       conversation_id, round_id, snapshot_id, platform, model,
                       created_at, updated_at, error_message, execution_time, total_tokens
                FROM summary_log
                WHERE conversation_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """
            rows = self._fetch_all(sql, (conversation_id, limit))

            logs = [SummaryLog.from_dict(self._row_to_dict(row)) for row in rows]
            self.logger.debug(f"获取会话总结日志成功: conversation_id={conversation_id}, 共{len(logs)}条记录")
            return logs

        except Exception as e:
            self.logger.error(f"获取会话总结日志失败: {e}")
            raise e

    def get_summary_logs_by_llm_config(self, llm_choose: str, limit: int = 100) -> List[SummaryLog]:
        """根据LLM配置获取总结日志记录（兼容原方法名）

        Args:
            llm_choose: LLM配置名称
            limit: 返回记录数限制

        Returns:
            List[SummaryLog]: 总结日志列表
        """
        try:
            sql = """
                SELECT log_id, summary_content, summary_result, status, 
                       conversation_id, round_id, snapshot_id, platform, model,
                       created_at, updated_at, error_message, execution_time, total_tokens
                FROM summary_log
                WHERE platform = ? OR model = ?
                ORDER BY created_at DESC
                LIMIT ?
            """
            rows = self._fetch_all(sql, (llm_choose, llm_choose, limit))

            logs = [SummaryLog.from_dict(self._row_to_dict(row)) for row in rows]
            self.logger.debug(f"根据LLM配置获取总结日志成功: llm_choose={llm_choose}, 共{len(logs)}条记录")
            return logs

        except Exception as e:
            self.logger.error(f"根据LLM配置获取总结日志失败: {e}")
            raise e

    def get_summary_logs_by_status(self, status: str, limit: int = 100) -> List[SummaryLog]:
        """根据状态获取总结日志记录

        Args:
            status: 状态 ('pending', 'processing', 'completed', 'failed')
            limit: 返回记录数限制

        Returns:
            List[SummaryLog]: 总结日志列表
        """
        try:
            sql = """
                SELECT log_id, summary_content, summary_result, status, 
                       conversation_id, round_id, snapshot_id, platform, model,
                       created_at, updated_at, error_message, execution_time, total_tokens
                FROM summary_log
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ?
            """
            rows = self._fetch_all(sql, (status, limit))

            logs = [SummaryLog.from_dict(self._row_to_dict(row)) for row in rows]
            self.logger.debug(f"根据状态获取总结日志成功: status={status}, 共{len(logs)}条记录")
            return logs

        except Exception as e:
            self.logger.error(f"根据状态获取总结日志失败: {e}")
            raise e

    def delete_summary_log(self, log_id: int) -> bool:
        """删除总结日志记录

        Args:
            log_id: 日志记录ID

        Returns:
            bool: 删除是否成功
        """
        try:
            sql = "DELETE FROM summary_log WHERE log_id = ?"
            rows_affected = self._execute_update(sql, (log_id,))

            if rows_affected > 0:
                self.logger.info(f"总结日志删除成功: log_id={log_id}")
                return True
            else:
                self.logger.warning(f"总结日志记录不存在: log_id={log_id}")
                return False

        except Exception as e:
            self.logger.error(f"删除总结日志失败: {e}")
            raise e

    def add_tokens_to_summary(self, summary_id: int, total_tokens: int, prompt_tokens: int = 0, completion_tokens: int = 0, reasoning_tokens: int = 0) -> None:
        """为总结日志累加Token数量

        Args:
            summary_id: 总结日志ID
            total_tokens: 要累加的总Token数量
            prompt_tokens: 要累加的提示Token数量
            completion_tokens: 要累加的完成Token数量
            reasoning_tokens: 要累加的推理Token数量
        """
        try:
            sql = """
                UPDATE summary_log 
                SET total_tokens = total_tokens + ?, 
                    prompt_tokens = prompt_tokens + ?, 
                    completion_tokens = completion_tokens + ?, 
                    reasoning_tokens = reasoning_tokens + ?,
                    updated_at = ?
                WHERE log_id = ?
            """
            now = datetime.datetime.now().isoformat()
            rows_affected = self._execute_update(sql, (total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, now, summary_id))

            if rows_affected > 0:
                self.logger.info(f"总结日志Token累加成功: summary_id={summary_id}, total_tokens={total_tokens}, prompt_tokens={prompt_tokens}, completion_tokens={completion_tokens}, reasoning_tokens={reasoning_tokens}")
            else:
                self.logger.warning(f"总结日志不存在，Token累加失败: summary_id={summary_id}")

        except Exception as e:
            self.logger.error(f"累加总结日志Token失败: {e}")
            raise e

    def get_summary_log_statistics(self) -> Dict[str, Union[int, float, Dict]]:
        """获取总结日志统计信息

        Returns:
            Dict[str, Union[int, float, Dict]]: 统计信息字典
        """
        try:
            # 统计各状态的记录数
            status_sql = """
                SELECT status, COUNT(*) as count
                FROM summary_log
                GROUP BY status
            """
            status_rows = self._fetch_all(status_sql)
            status_stats = {row["status"]: row["count"] for row in status_rows}

            # 统计各平台的使用次数
            platform_sql = """
                SELECT platform, COUNT(*) as count
                FROM summary_log
                WHERE platform IS NOT NULL
                GROUP BY platform
            """
            platform_rows = self._fetch_all(platform_sql)
            platform_stats = {row["platform"]: row["count"] for row in platform_rows}

            # 总记录数
            total_sql = "SELECT COUNT(*) as count FROM summary_log"
            total_row = self._fetch_one(total_sql)
            total_count = total_row["count"] if total_row else 0

            # 平均执行时间
            avg_time_sql = """
                SELECT AVG(execution_time) as avg_time
                FROM summary_log 
                WHERE execution_time IS NOT NULL AND status = 'completed'
            """
            avg_time_row = self._fetch_one(avg_time_sql)
            avg_execution_time = avg_time_row["avg_time"] if avg_time_row and avg_time_row["avg_time"] else 0

            # 总Token使用量
            total_tokens_sql = """
                SELECT SUM(total_tokens) as total_tokens
                FROM summary_log
                WHERE total_tokens IS NOT NULL
            """
            tokens_row = self._fetch_one(total_tokens_sql)
            total_tokens = tokens_row["total_tokens"] if tokens_row and tokens_row["total_tokens"] else 0

            stats = {"total_count": total_count, "status_stats": status_stats, "platform_stats": platform_stats, "avg_execution_time": round(avg_execution_time, 3), "total_tokens": total_tokens}

            self.logger.debug("获取总结日志统计信息成功")
            return stats

        except Exception as e:
            self.logger.error(f"获取总结日志统计信息失败: {e}")
            raise e

    # ==================== 总结快照(summary_snapshots)操作 ====================

    def create_snapshot(self, conversation_id: str, based_on_round_id: str, context_summary: str, summary_type: str = "context") -> int:
        """创建快照总结记录

        Args:
            conversation_id: 会话ID
            based_on_round_id: 基于的最后轮次ID
            context_summary: 快照总结内容
            summary_type: 总结类型

        Returns:
            int: 新创建的快照ID
        """
        try:
            now = datetime.datetime.now().isoformat()
            sql = """
                INSERT INTO summary_snapshots (conversation_id, based_on_round_id, context_summary, created_at, summary_type)
                VALUES (?, ?, ?, ?, ?)
            """
            snapshot_id = self._execute_insert(sql, (conversation_id, based_on_round_id, context_summary, now, summary_type))

            self.logger.info(f"快照总结创建成功: snapshot_id={snapshot_id}")
            return snapshot_id

        except Exception as e:
            self.logger.error(f"创建快照总结失败: {e}")
            raise e

    def get_snapshot(self, snapshot_id: int) -> Optional[Dict[str, Any]]:
        """获取快照记录

        Args:
            snapshot_id: 快照ID

        Returns:
            Optional[Dict[str, Any]]: 快照记录，如果不存在则返回None
        """
        try:
            sql = """
                SELECT snapshot_id, conversation_id, based_on_round_id, context_summary, created_at, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, summary_type
                FROM summary_snapshots
                WHERE snapshot_id = ?
            """
            row = self._fetch_one(sql, (snapshot_id,))

            if row:
                snapshot_data = self._row_to_dict(row)
                self.logger.debug(f"获取快照成功: snapshot_id={snapshot_id}")
                return snapshot_data
            else:
                self.logger.warning(f"快照不存在: snapshot_id={snapshot_id}")
                return None

        except Exception as e:
            self.logger.error(f"获取快照失败: {e}")
            raise e

    def get_latest_snapshot(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """获取指定会话的最新快照

        Args:
            conversation_id: 会话ID

        Returns:
            Optional[Dict[str, Any]]: 最新的快照记录，如果没有则返回None
        """
        try:
            sql = """
                SELECT snapshot_id, conversation_id, based_on_round_id, context_summary, created_at, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, summary_type
                FROM summary_snapshots 
                WHERE conversation_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """
            row = self._fetch_one(sql, (conversation_id,))

            if row:
                snapshot_data = self._row_to_dict(row)
                self.logger.debug(f"获取最新快照成功: conversation_id={conversation_id}")
                return snapshot_data
            else:
                self.logger.debug(f"会话没有快照: conversation_id={conversation_id}")
                return None

        except Exception as e:
            self.logger.error(f"获取最新快照失败: {e}")
            raise e

    def get_all_snapshots(self, conversation_id: str) -> List[Dict[str, Any]]:
        """获取指定会话的所有快照

        Args:
            conversation_id: 会话ID

        Returns:
            List[Dict[str, Any]]: 所有快照记录列表
        """
        try:
            sql = """
                SELECT snapshot_id, conversation_id, based_on_round_id, context_summary, created_at, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, summary_type
                FROM summary_snapshots 
                WHERE conversation_id = ?
                ORDER BY created_at ASC
            """
            rows = self._fetch_all(sql, (conversation_id,))

            snapshots = [self._row_to_dict(row) for row in rows]
            self.logger.debug(f"获取所有快照成功: conversation_id={conversation_id}, 共{len(snapshots)}个快照")
            return snapshots

        except Exception as e:
            self.logger.error(f"获取所有快照失败: {e}")
            raise e

    def get_recent_snapshots(self, conversation_id: str, limit: int = 2) -> List[Dict[str, Any]]:
        """获取指定会话的最近N个快照

        Args:
            conversation_id: 会话ID
            limit: 返回快照数量限制

        Returns:
            List[Dict[str, Any]]: 最近的快照记录列表，按时间倒序
        """
        try:
            sql = """
                SELECT snapshot_id, conversation_id, based_on_round_id, context_summary, created_at, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, summary_type
                FROM summary_snapshots 
                WHERE conversation_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """
            rows = self._fetch_all(sql, (conversation_id, limit))

            snapshots = [self._row_to_dict(row) for row in rows]
            self.logger.debug(f"获取最近快照成功: conversation_id={conversation_id}, 数量={len(snapshots)}")
            return snapshots

        except Exception as e:
            self.logger.error(f"获取最近快照失败: {e}")
            raise e

    def get_snapshots_count(self, conversation_id: str) -> int:
        """获取指定会话的快照数量

        Args:
            conversation_id: 会话ID

        Returns:
            int: 快照数量
        """
        try:
            sql = "SELECT COUNT(*) as count FROM summary_snapshots WHERE conversation_id = ?"
            row = self._fetch_one(sql, (conversation_id,))
            count = row["count"] if row else 0

            self.logger.debug(f"获取快照数量: conversation_id={conversation_id}, 数量={count}")
            return count

        except Exception as e:
            self.logger.error(f"获取快照数量失败: {e}")
            raise e

    def get_rounds_since_last_snapshot(self, conversation_id: str) -> List[Dict[str, Any]]:
        """获取自上次快照后的所有轮次记录

        Args:
            conversation_id: 会话ID

        Returns:
            List[Dict[str, Any]]: 轮次记录列表
        """
        try:
            # 先获取最新快照的基准轮次ID
            latest_snapshot = self.get_latest_snapshot(conversation_id)

            if latest_snapshot:
                # 获取基准轮次后的所有轮次
                sql = """
                    SELECT r.round_id, r.conversation_id, r.summary, r.created_at, r.user_rating, r.extra_data
                    FROM rounds r
                    WHERE r.conversation_id = ? AND r.created_at > (
                        SELECT created_at FROM rounds WHERE round_id = ?
                    )
                    ORDER BY r.created_at ASC
                """
                params = (conversation_id, latest_snapshot["based_on_round_id"])
            else:
                # 如果没有快照，获取所有轮次
                sql = """
                    SELECT round_id, conversation_id, summary, created_at, user_rating, extra_data
                    FROM rounds 
                    WHERE conversation_id = ?
                    ORDER BY created_at ASC
                """
                params = (conversation_id,)

            rows = self._fetch_all(sql, params)

            rounds = [self._row_to_dict(row) for row in rows]
            self.logger.debug(f"获取快照后轮次成功: conversation_id={conversation_id}, 共{len(rounds)}个轮次")
            return rounds

        except Exception as e:
            self.logger.error(f"获取快照后轮次失败: {e}")
            raise e

    def update_snapshot_tokens(self, snapshot_id: int, total_tokens: int, prompt_tokens: int = 0, completion_tokens: int = 0, reasoning_tokens: int = 0) -> None:
        """更新快照的Token使用量

        Args:
            snapshot_id: 快照ID
            total_tokens: 总Token数量
            prompt_tokens: 提示Token数量
            completion_tokens: 完成Token数量
            reasoning_tokens: 推理Token数量
        """
        try:
            sql = """
                UPDATE summary_snapshots 
                SET total_tokens = ?, prompt_tokens = ?, completion_tokens = ?, reasoning_tokens = ?
                WHERE snapshot_id = ?
            """
            rows_affected = self._execute_update(sql, (total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, snapshot_id))

            if rows_affected > 0:
                self.logger.info(f"快照Token更新成功: snapshot_id={snapshot_id}, total_tokens={total_tokens}, prompt_tokens={prompt_tokens}, completion_tokens={completion_tokens}, reasoning_tokens={reasoning_tokens}")
            else:
                self.logger.warning(f"快照不存在，Token更新失败: snapshot_id={snapshot_id}")

        except Exception as e:
            self.logger.error(f"更新快照Token失败: {e}")
            raise e

    def delete_snapshot(self, snapshot_id: int) -> bool:
        """删除快照记录

        Args:
            snapshot_id: 快照ID

        Returns:
            bool: 删除是否成功
        """
        try:
            sql = "DELETE FROM summary_snapshots WHERE snapshot_id = ?"
            rows_affected = self._execute_update(sql, (snapshot_id,))

            if rows_affected > 0:
                self.logger.info(f"快照删除成功: snapshot_id={snapshot_id}")
                return True
            else:
                self.logger.warning(f"快照不存在，删除失败: snapshot_id={snapshot_id}")
                return False

        except Exception as e:
            self.logger.error(f"删除快照失败: {e}")
            raise e
