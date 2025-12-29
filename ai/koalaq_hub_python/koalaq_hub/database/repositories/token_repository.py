"""
Token统计Repository
负责模型(models)和Token统计相关的所有数据库操作
"""

import datetime
from typing import Any, Dict, List, Optional

from ...core.logging_utils import ManagerLogger
from ...models.data_models import Model
from ..base.base_repository import BaseRepository
from ..base.database_connection import DatabaseConnection


class TokenRepository(BaseRepository):
    """Token统计数据访问对象"""
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection)
        self.logger = ManagerLogger("TokenRepository")

    # ==================== 模型(models)操作 ====================

    def create_or_update_model(self, platform: str, model: str) -> int:
        """创建或获取模型记录

        Args:
            platform: 平台名称
            model: 模型名称

        Returns:
            int: 模型ID
        """
        try:
            now = datetime.datetime.now().isoformat()

            # 尝试插入，如果已存在则忽略
            insert_sql = """
                INSERT OR IGNORE INTO models (platform, model, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, request_count, success_count, error_count, avg_response_time, created_at, updated_at)
                VALUES (?, ?, 0, 0, 0, 0, 0, 0, 0, 0, ?, ?)
            """
            self._execute_insert(insert_sql, (platform, model, now, now))

            # 获取模型ID
            select_sql = """
                SELECT model_id FROM models WHERE platform = ? AND model = ?
            """
            row = self._fetch_one(select_sql, (platform, model))

            if row:
                model_id = row["model_id"]
                self.logger.debug(f"获取/创建模型记录成功: platform={platform}, model={model}, model_id={model_id}")
                return model_id
            else:
                raise Exception(f"获取模型ID失败: platform={platform}, model={model}")

        except Exception as e:
            self.logger.error(f"创建或获取模型记录失败: {e}")
            raise e

    def get_model(self, model_id: int) -> Optional[Model]:
        """根据模型ID获取模型信息

        Args:
            model_id: 模型ID

        Returns:
            Optional[Model]: 模型对象，如果不存在则返回None
        """
        try:
            sql = """
                SELECT model_id, platform, model, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, request_count, success_count, error_count, avg_response_time, created_at, updated_at
                FROM models
                WHERE model_id = ?
            """
            row = self._fetch_one(sql, (model_id,))

            if row:
                model_data = self._row_to_dict(row)
                self.logger.debug(f"获取模型成功: model_id={model_id}")
                return Model.from_dict(model_data)
            else:
                self.logger.warning(f"模型不存在: model_id={model_id}")
                return None

        except Exception as e:
            self.logger.error(f"获取模型失败 (ID: {model_id}): {e}")
            raise e

    def get_model_by_platform_and_name(self, platform: str, model: str) -> Optional[Model]:
        """根据平台和模型名称获取模型信息

        Args:
            platform: 平台名称
            model: 模型名称

        Returns:
            Optional[Model]: 模型对象，如果不存在则返回None
        """
        try:
            sql = """
                SELECT model_id, platform, model, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, request_count, success_count, error_count, avg_response_time, created_at, updated_at
                FROM models
                WHERE platform = ? AND model = ?
            """
            row = self._fetch_one(sql, (platform, model))

            if row:
                model_data = self._row_to_dict(row)
                self.logger.debug(f"根据平台模型获取成功: platform={platform}, model={model}")
                return Model.from_dict(model_data)
            else:
                self.logger.warning(f"模型不存在: platform={platform}, model={model}")
                return None

        except Exception as e:
            self.logger.error(f"根据平台模型获取失败: platform={platform}, model={model}, 错误: {e}")
            raise e

    def add_tokens_to_model(self, platform: str, model: str, total_tokens: int, prompt_tokens: int = 0, completion_tokens: int = 0, reasoning_tokens: int = 0) -> None:
        """为指定模型累加Token数量

        Args:
            platform: 平台名称
            model: 模型名称
            total_tokens: 要累加的总Token数量
            prompt_tokens: 要累加的提示Token数量
            completion_tokens: 要累加的完成Token数量
            reasoning_tokens: 要累加的推理Token数量
        """
        try:
            now = datetime.datetime.now().isoformat()

            # 确保模型记录存在
            self.create_or_update_model(platform, model)

            # 累加Token数量并更新请求计数
            sql = """
                UPDATE models 
                SET total_tokens = total_tokens + ?, 
                    prompt_tokens = prompt_tokens + ?,
                    completion_tokens = completion_tokens + ?,
                    reasoning_tokens = reasoning_tokens + ?,
                    request_count = request_count + 1, 
                    updated_at = ?
                WHERE platform = ? AND model = ?
            """
            rows_affected = self._execute_update(sql, (total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, now, platform, model))

            if rows_affected > 0:
                self.logger.info(f"模型Token累加成功: platform={platform}, model={model}, total_tokens={total_tokens}, prompt_tokens={prompt_tokens}, completion_tokens={completion_tokens}, reasoning_tokens={reasoning_tokens}")
            else:
                self.logger.warning(f"模型Token累加失败: platform={platform}, model={model}")

        except Exception as e:
            self.logger.error(f"累加模型Token失败: {e}")
            raise e

    def update_model_stats(self, platform: str, model: str, success: bool = True, response_time: float = None) -> None:
        """更新模型统计信息

        Args:
            platform: 平台名称
            model: 模型名称
            success: 是否成功
            response_time: 响应时间（秒）
        """
        try:
            now = datetime.datetime.now().isoformat()

            # 确保模型记录存在
            self.create_or_update_model(platform, model)

            # 构建更新语句
            if success:
                if response_time is not None:
                    # 更新成功计数和平均响应时间
                    sql = """
                        UPDATE models 
                        SET success_count = success_count + 1,
                            avg_response_time = (avg_response_time * success_count + ?) / (success_count + 1),
                            updated_at = ?
                        WHERE platform = ? AND model = ?
                    """
                    params = (response_time, now, platform, model)
                else:
                    # 只更新成功计数
                    sql = """
                        UPDATE models 
                        SET success_count = success_count + 1, updated_at = ?
                        WHERE platform = ? AND model = ?
                    """
                    params = (now, platform, model)
            else:
                # 更新错误计数
                sql = """
                    UPDATE models 
                    SET error_count = error_count + 1, updated_at = ?
                    WHERE platform = ? AND model = ?
                """
                params = (now, platform, model)

            rows_affected = self._execute_update(sql, params)

            if rows_affected > 0:
                self.logger.info(f"模型统计更新成功: platform={platform}, model={model}, success={success}")
            else:
                self.logger.warning(f"模型统计更新失败: platform={platform}, model={model}")

        except Exception as e:
            self.logger.error(f"更新模型统计失败: {e}")
            raise e

    def get_model_statistics(self) -> List[Dict[str, Any]]:
        """获取所有模型的Token使用统计

        Returns:
            List[Dict[str, Any]]: 模型统计列表
        """
        try:
            sql = """
                SELECT model_id, platform, model, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, request_count, success_count, error_count, avg_response_time, created_at, updated_at
                FROM models
                ORDER BY total_tokens DESC
            """
            rows = self._fetch_all(sql)

            results = [self._row_to_dict(row) for row in rows]
            self.logger.debug(f"获取模型统计成功，共{len(results)}个模型")
            return results

        except Exception as e:
            self.logger.error(f"获取模型统计失败: {e}")
            raise e

    def get_platform_statistics(self) -> List[Dict[str, Any]]:
        """获取各平台的Token使用统计

        Returns:
            List[Dict[str, Any]]: 平台统计列表
        """
        try:
            sql = """
                SELECT 
                    platform, 
                    SUM(total_tokens) as total_tokens,
                    SUM(prompt_tokens) as total_prompt_tokens,
                    SUM(completion_tokens) as total_completion_tokens,
                    SUM(reasoning_tokens) as total_reasoning_tokens,
                    COUNT(*) as model_count,
                    SUM(request_count) as total_requests,
                    SUM(success_count) as total_success,
                    SUM(error_count) as total_errors,
                    AVG(avg_response_time) as avg_response_time
                FROM models
                GROUP BY platform
                ORDER BY total_tokens DESC
            """
            rows = self._fetch_all(sql)

            results = []
            for row in rows:
                data = self._row_to_dict(row)
                # 计算成功率
                total_requests = data["total_requests"] or 0
                total_success = data["total_success"] or 0
                success_rate = (total_success / total_requests * 100) if total_requests > 0 else 0
                data["success_rate"] = round(success_rate, 2)

                # 格式化平均响应时间
                avg_time = data["avg_response_time"] or 0
                data["avg_response_time"] = round(avg_time, 3)

                results.append(data)

            self.logger.debug(f"获取平台统计成功，共{len(results)}个平台")
            return results

        except Exception as e:
            self.logger.error(f"获取平台统计失败: {e}")
            raise e

    def get_model_statistics_by_platform(self, platform: str) -> List[Dict[str, Any]]:
        """获取指定平台的模型统计

        Args:
            platform: 平台名称

        Returns:
            List[Dict[str, Any]]: 平台下的模型统计列表
        """
        try:
            sql = """
                SELECT model_id, platform, model, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, request_count, success_count, error_count, avg_response_time, created_at, updated_at
                FROM models
                WHERE platform = ?
                ORDER BY total_tokens DESC
            """
            rows = self._fetch_all(sql, (platform,))

            results = [self._row_to_dict(row) for row in rows]
            self.logger.debug(f"获取平台模型统计成功: platform={platform}, 共{len(results)}个模型")
            return results

        except Exception as e:
            self.logger.error(f"获取平台模型统计失败: platform={platform}, 错误: {e}")
            raise e

    def get_top_models(self, limit: int = 10, by: str = "total_tokens") -> List[Dict[str, Any]]:
        """获取排名前N的模型

        Args:
            limit: 返回数量限制
            by: 排序字段 ('total_tokens', 'request_count', 'success_count')

        Returns:
            List[Dict[str, Any]]: 排名前N的模型列表
        """
        try:
            if by not in ["total_tokens", "request_count", "success_count"]:
                by = "total_tokens"

            sql = f"""
                SELECT model_id, platform, model, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, request_count, success_count, error_count, avg_response_time, created_at, updated_at
                FROM models
                ORDER BY {by} DESC
                LIMIT ?
            """
            rows = self._fetch_all(sql, (limit,))

            results = [self._row_to_dict(row) for row in rows]
            self.logger.debug(f"获取排名前{limit}模型成功，按{by}排序")
            return results

        except Exception as e:
            self.logger.error(f"获取排名前{limit}模型失败: {e}")
            raise e

    def get_token_usage_trends(self, platform: str = None, days: int = 30) -> List[Dict[str, Any]]:
        """获取Token使用趋势（基于模型的updated_at字段进行简单统计）

        Args:
            platform: 平台名称（可选）
            days: 统计天数

        Returns:
            List[Dict[str, Any]]: 使用趋势数据
        """
        try:
            # 这是一个简化的趋势统计，实际项目中可能需要专门的日统计表
            if platform:
                sql = """
                    SELECT 
                        DATE(updated_at) as date,
                        platform,
                        SUM(total_tokens) as daily_tokens,
                        SUM(request_count) as daily_requests
                    FROM models
                    WHERE platform = ? AND updated_at >= date('now', '-' || ? || ' days')
                    GROUP BY DATE(updated_at), platform
                    ORDER BY date DESC
                """
                params = (platform, days)
            else:
                sql = """
                    SELECT 
                        DATE(updated_at) as date,
                        'all' as platform,
                        SUM(total_tokens) as daily_tokens,
                        SUM(request_count) as daily_requests
                    FROM models
                    WHERE updated_at >= date('now', '-' || ? || ' days')
                    GROUP BY DATE(updated_at)
                    ORDER BY date DESC
                """
                params = (days,)

            rows = self._fetch_all(sql, params)

            results = [self._row_to_dict(row) for row in rows]
            self.logger.debug(f"获取Token使用趋势成功，{days}天数据，共{len(results)}条记录")
            return results

        except Exception as e:
            self.logger.error(f"获取Token使用趋势失败: {e}")
            raise e

    def delete_model(self, model_id: int) -> bool:
        """删除模型记录

        Args:
            model_id: 模型ID

        Returns:
            bool: 删除是否成功
        """
        try:
            sql = "DELETE FROM models WHERE model_id = ?"
            rows_affected = self._execute_update(sql, (model_id,))

            if rows_affected > 0:
                self.logger.info(f"模型删除成功: model_id={model_id}")
                return True
            else:
                self.logger.warning(f"模型不存在，删除失败: model_id={model_id}")
                return False

        except Exception as e:
            self.logger.error(f"删除模型失败 (ID: {model_id}): {e}")
            raise e

    def reset_model_stats(self, platform: str, model: str) -> None:
        """重置模型统计数据

        Args:
            platform: 平台名称
            model: 模型名称
        """
        try:
            now = datetime.datetime.now().isoformat()
            sql = """
                UPDATE models 
                SET total_tokens = 0, prompt_tokens = 0, completion_tokens = 0, reasoning_tokens = 0, request_count = 0, success_count = 0, error_count = 0, avg_response_time = 0, updated_at = ?
                WHERE platform = ? AND model = ?
            """
            rows_affected = self._execute_update(sql, (now, platform, model))

            if rows_affected > 0:
                self.logger.info(f"模型统计重置成功: platform={platform}, model={model}")
            else:
                self.logger.warning(f"模型不存在，统计重置失败: platform={platform}, model={model}")

        except Exception as e:
            self.logger.error(f"重置模型统计失败: {e}")
            raise e

    # ==================== 汇总统计 ====================

    def get_total_statistics(self) -> Dict[str, Any]:
        """获取总体统计信息

        Returns:
            Dict[str, Any]: 总体统计数据
        """
        try:
            sql = """
                SELECT 
                    COUNT(*) as total_models,
                    COUNT(DISTINCT platform) as total_platforms,
                    SUM(total_tokens) as total_tokens,
                    SUM(prompt_tokens) as total_prompt_tokens,
                    SUM(completion_tokens) as total_completion_tokens,
                    SUM(reasoning_tokens) as total_reasoning_tokens,
                    SUM(request_count) as total_requests,
                    SUM(success_count) as total_success,
                    SUM(error_count) as total_errors,
                    AVG(avg_response_time) as overall_avg_response_time
                FROM models
            """
            row = self._fetch_one(sql)

            if row:
                stats = self._row_to_dict(row)

                # 计算总体成功率
                total_requests = stats["total_requests"] or 0
                total_success = stats["total_success"] or 0
                success_rate = (total_success / total_requests * 100) if total_requests > 0 else 0
                stats["overall_success_rate"] = round(success_rate, 2)

                # 格式化平均响应时间
                avg_time = stats["overall_avg_response_time"] or 0
                stats["overall_avg_response_time"] = round(avg_time, 3)

                # 处理NULL值
                for key, value in stats.items():
                    if value is None:
                        stats[key] = 0

                self.logger.debug("获取总体统计成功")
                return stats
            else:
                return {}

        except Exception as e:
            self.logger.error(f"获取总体统计失败: {e}")
            raise e
