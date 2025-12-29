"""
Token统计Repository
负责 Token 统计相关的数据库操作（基于 llm_config_name 查找）
"""

import datetime
from typing import Any, Dict, List, Optional

from ...core.logging_utils import ManagerLogger
from ...models.data_models import Model
from ..base.base_repository import BaseRepository
from ..base.database_connection import DatabaseConnection


# 标准字段列表（用于 SELECT 查询）
MODEL_FIELDS = """
    llm_id, llm_config_name, platform, model, api_key, url,
    temperature, top_p, max_tokens, description,
    total_tokens, prompt_tokens, completion_tokens, reasoning_tokens,
    request_count, success_count, error_count, avg_response_time,
    created_at, updated_at
"""


class TokenRepository(BaseRepository):
    """Token统计数据访问对象"""

    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection)
        self.logger = ManagerLogger("TokenRepository")

    # ==================== Token 累加操作 ====================

    def add_tokens_by_config_name(
        self,
        llm_config_name: str,
        total_tokens: int,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        reasoning_tokens: int = 0,
    ) -> bool:
        """为指定 LLM 配置累加 Token 数量

        Args:
            llm_config_name: LLM 配置名称
            total_tokens: 要累加的总 Token 数量
            prompt_tokens: 要累加的提示 Token 数量
            completion_tokens: 要累加的完成 Token 数量
            reasoning_tokens: 要累加的推理 Token 数量

        Returns:
            bool: 是否成功
        """
        try:
            now = datetime.datetime.now().isoformat()

            sql = """
                UPDATE models
                SET total_tokens = total_tokens + ?,
                    prompt_tokens = prompt_tokens + ?,
                    completion_tokens = completion_tokens + ?,
                    reasoning_tokens = reasoning_tokens + ?,
                    request_count = request_count + 1,
                    updated_at = ?
                WHERE llm_config_name = ?
            """
            rows_affected = self._execute_update(
                sql,
                (total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, now, llm_config_name),
            )

            if rows_affected > 0:
                self.logger.info(
                    f"Token累加成功: llm_config_name={llm_config_name}, "
                    f"total={total_tokens}, prompt={prompt_tokens}, "
                    f"completion={completion_tokens}, reasoning={reasoning_tokens}"
                )
                return True
            else:
                self.logger.warning(f"Token累加失败，配置不存在: llm_config_name={llm_config_name}")
                return False

        except Exception as e:
            self.logger.error(f"累加Token失败: {e}")
            raise e

    def update_model_stats_by_config_name(
        self, llm_config_name: str, success: bool = True, response_time: float = None
    ) -> bool:
        """更新模型统计信息

        Args:
            llm_config_name: LLM 配置名称
            success: 是否成功
            response_time: 响应时间（秒）

        Returns:
            bool: 是否成功
        """
        try:
            now = datetime.datetime.now().isoformat()

            if success:
                if response_time is not None:
                    sql = """
                        UPDATE models
                        SET success_count = success_count + 1,
                            avg_response_time = (avg_response_time * success_count + ?) / (success_count + 1),
                            updated_at = ?
                        WHERE llm_config_name = ?
                    """
                    params = (response_time, now, llm_config_name)
                else:
                    sql = """
                        UPDATE models
                        SET success_count = success_count + 1, updated_at = ?
                        WHERE llm_config_name = ?
                    """
                    params = (now, llm_config_name)
            else:
                sql = """
                    UPDATE models
                    SET error_count = error_count + 1, updated_at = ?
                    WHERE llm_config_name = ?
                """
                params = (now, llm_config_name)

            rows_affected = self._execute_update(sql, params)

            if rows_affected > 0:
                self.logger.info(f"模型统计更新成功: llm_config_name={llm_config_name}, success={success}")
                return True
            else:
                self.logger.warning(f"模型统计更新失败: llm_config_name={llm_config_name}")
                return False

        except Exception as e:
            self.logger.error(f"更新模型统计失败: {e}")
            raise e

    def reset_stats_by_config_name(self, llm_config_name: str) -> bool:
        """重置模型统计数据

        Args:
            llm_config_name: LLM 配置名称

        Returns:
            bool: 是否成功
        """
        try:
            now = datetime.datetime.now().isoformat()
            sql = """
                UPDATE models
                SET total_tokens = 0, prompt_tokens = 0, completion_tokens = 0,
                    reasoning_tokens = 0, request_count = 0, success_count = 0,
                    error_count = 0, avg_response_time = 0, updated_at = ?
                WHERE llm_config_name = ?
            """
            rows_affected = self._execute_update(sql, (now, llm_config_name))

            if rows_affected > 0:
                self.logger.info(f"模型统计重置成功: llm_config_name={llm_config_name}")
                return True
            else:
                self.logger.warning(f"模型统计重置失败: llm_config_name={llm_config_name}")
                return False

        except Exception as e:
            self.logger.error(f"重置模型统计失败: {e}")
            raise e

    # ==================== 统计查询操作 ====================

    def get_model_statistics(self) -> List[Dict[str, Any]]:
        """获取所有模型的 Token 使用统计

        Returns:
            List[Dict[str, Any]]: 模型统计列表
        """
        try:
            sql = f"SELECT {MODEL_FIELDS} FROM models ORDER BY total_tokens DESC"
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
            sql = f"""
                SELECT {MODEL_FIELDS}
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
        """获取排名前 N 的模型

        Args:
            limit: 返回数量限制
            by: 排序字段 ('total_tokens', 'request_count', 'success_count')

        Returns:
            List[Dict[str, Any]]: 排名前 N 的模型列表
        """
        try:
            if by not in ["total_tokens", "request_count", "success_count"]:
                by = "total_tokens"

            sql = f"""
                SELECT {MODEL_FIELDS}
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
