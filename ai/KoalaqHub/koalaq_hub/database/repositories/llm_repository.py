"""
LLM配置Repository
负责 LLM 配置的 CRUD 操作
"""

import datetime
import uuid
from typing import Any, Dict, List, Optional

from ...core.logging_utils import ManagerLogger
from ...models.data_models import Model
from ..base.base_repository import BaseRepository
from ..base.database_connection import DatabaseConnection


def generate_llm_id() -> str:
    """生成 LLM ID（UUID 后8位）"""
    return uuid.uuid4().hex[-8:]


class LLMRepository(BaseRepository):
    """LLM配置数据访问对象"""

    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection)
        self.logger = ManagerLogger("LLMRepository")

    # ==================== 创建操作 ====================

    def create_llm(
        self,
        llm_config_name: str,
        platform: str,
        model: str,
        api_key: str = None,
        url: str = None,
        temperature: float = 0.7,
        top_p: float = 1.0,
        max_tokens: int = 4096,
        description: str = "",
    ) -> str:
        """创建 LLM 配置

        Args:
            llm_config_name: 配置名称（ini section 名）
            platform: 平台名称
            model: 模型名称
            api_key: API 密钥
            url: API URL
            temperature: 温度参数
            top_p: Top-p 参数
            max_tokens: 最大 token 数
            description: 描述

        Returns:
            str: 生成的 llm_id
        """
        try:
            llm_id = generate_llm_id()
            now = datetime.datetime.now().isoformat()

            sql = """
                INSERT INTO models (
                    llm_id, llm_config_name, platform, model, api_key, url,
                    temperature, top_p, max_tokens, description,
                    total_tokens, prompt_tokens, completion_tokens, reasoning_tokens,
                    request_count, success_count, error_count, avg_response_time,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, 0, 0, 0, 0, ?, ?)
            """
            self._execute_insert(
                sql,
                (
                    llm_id,
                    llm_config_name,
                    platform,
                    model,
                    api_key,
                    url,
                    temperature,
                    top_p,
                    max_tokens,
                    description,
                    now,
                    now,
                ),
            )

            self.logger.info(
                "创建 LLM 配置成功",
                {
                    "llm_id": llm_id,
                    "llm_config_name": llm_config_name,
                    "platform": platform,
                    "model": model,
                },
            )
            return llm_id

        except Exception as e:
            self.logger.error(f"创建 LLM 配置失败: {e}")
            raise e

    def create_if_not_exists(
        self,
        llm_config_name: str,
        platform: str,
        model: str,
        api_key: str = None,
        url: str = None,
        temperature: float = 0.7,
        top_p: float = 1.0,
        max_tokens: int = 4096,
        description: str = "",
    ) -> str:
        """创建 LLM 配置（如果不存在）

        Args:
            llm_config_name: 配置名称
            ...其他参数同 create_llm

        Returns:
            str: llm_id（新建或已存在的）
        """
        # 先检查是否存在
        existing = self.get_by_config_name(llm_config_name)
        if existing:
            self.logger.debug(
                f"LLM 配置已存在，跳过: {llm_config_name}, llm_id={existing.llm_id}"
            )
            return existing.llm_id

        # 不存在则创建
        return self.create_llm(
            llm_config_name=llm_config_name,
            platform=platform,
            model=model,
            api_key=api_key,
            url=url,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            description=description,
        )

    # ==================== 查询操作 ====================

    def get_by_id(self, llm_id: str) -> Optional[Model]:
        """根据 llm_id 获取 LLM 配置

        Args:
            llm_id: LLM ID

        Returns:
            Optional[Model]: LLM 配置对象
        """
        try:
            sql = """
                SELECT llm_id, llm_config_name, platform, model, api_key, url,
                       temperature, top_p, max_tokens, description,
                       total_tokens, prompt_tokens, completion_tokens, reasoning_tokens,
                       request_count, success_count, error_count, avg_response_time,
                       created_at, updated_at
                FROM models
                WHERE llm_id = ?
            """
            row = self._fetch_one(sql, (llm_id,))

            if row:
                model_data = self._row_to_dict(row)
                self.logger.debug(f"获取 LLM 配置成功: llm_id={llm_id}")
                return Model.from_dict(model_data)
            else:
                self.logger.debug(f"LLM 配置不存在: llm_id={llm_id}")
                return None

        except Exception as e:
            self.logger.error(f"获取 LLM 配置失败 (ID: {llm_id}): {e}")
            raise e

    def get_by_config_name(self, llm_config_name: str) -> Optional[Model]:
        """根据配置名称获取 LLM 配置

        Args:
            llm_config_name: 配置名称（ini section 名）

        Returns:
            Optional[Model]: LLM 配置对象
        """
        try:
            sql = """
                SELECT llm_id, llm_config_name, platform, model, api_key, url,
                       temperature, top_p, max_tokens, description,
                       total_tokens, prompt_tokens, completion_tokens, reasoning_tokens,
                       request_count, success_count, error_count, avg_response_time,
                       created_at, updated_at
                FROM models
                WHERE llm_config_name = ?
            """
            row = self._fetch_one(sql, (llm_config_name,))

            if row:
                model_data = self._row_to_dict(row)
                self.logger.debug(f"获取 LLM 配置成功: llm_config_name={llm_config_name}")
                return Model.from_dict(model_data)
            else:
                self.logger.debug(f"LLM 配置不存在: llm_config_name={llm_config_name}")
                return None

        except Exception as e:
            self.logger.error(
                f"获取 LLM 配置失败 (config_name: {llm_config_name}): {e}"
            )
            raise e

    def list_all(self) -> List[Model]:
        """获取所有 LLM 配置

        Returns:
            List[Model]: LLM 配置列表
        """
        try:
            sql = """
                SELECT llm_id, llm_config_name, platform, model, api_key, url,
                       temperature, top_p, max_tokens, description,
                       total_tokens, prompt_tokens, completion_tokens, reasoning_tokens,
                       request_count, success_count, error_count, avg_response_time,
                       created_at, updated_at
                FROM models
                ORDER BY created_at DESC
            """
            rows = self._fetch_all(sql)

            results = [Model.from_dict(self._row_to_dict(row)) for row in rows]
            self.logger.debug(f"获取所有 LLM 配置成功，共 {len(results)} 个")
            return results

        except Exception as e:
            self.logger.error(f"获取所有 LLM 配置失败: {e}")
            raise e

    def list_by_platform(self, platform: str) -> List[Model]:
        """根据平台获取 LLM 配置列表

        Args:
            platform: 平台名称

        Returns:
            List[Model]: LLM 配置列表
        """
        try:
            sql = """
                SELECT llm_id, llm_config_name, platform, model, api_key, url,
                       temperature, top_p, max_tokens, description,
                       total_tokens, prompt_tokens, completion_tokens, reasoning_tokens,
                       request_count, success_count, error_count, avg_response_time,
                       created_at, updated_at
                FROM models
                WHERE platform = ?
                ORDER BY created_at DESC
            """
            rows = self._fetch_all(sql, (platform,))

            results = [Model.from_dict(self._row_to_dict(row)) for row in rows]
            self.logger.debug(f"获取平台 {platform} 的 LLM 配置成功，共 {len(results)} 个")
            return results

        except Exception as e:
            self.logger.error(f"获取平台 LLM 配置失败 (platform: {platform}): {e}")
            raise e

    # ==================== 更新操作 ====================

    def update_llm(
        self,
        llm_id: str,
        platform: str = None,
        model: str = None,
        api_key: str = None,
        url: str = None,
        temperature: float = None,
        top_p: float = None,
        max_tokens: int = None,
        description: str = None,
    ) -> bool:
        """更新 LLM 配置

        Args:
            llm_id: LLM ID
            ...其他参数，None 表示不更新

        Returns:
            bool: 是否更新成功
        """
        try:
            # 构建更新字段
            updates = []
            params = []

            if platform is not None:
                updates.append("platform = ?")
                params.append(platform)
            if model is not None:
                updates.append("model = ?")
                params.append(model)
            if api_key is not None:
                updates.append("api_key = ?")
                params.append(api_key)
            if url is not None:
                updates.append("url = ?")
                params.append(url)
            if temperature is not None:
                updates.append("temperature = ?")
                params.append(temperature)
            if top_p is not None:
                updates.append("top_p = ?")
                params.append(top_p)
            if max_tokens is not None:
                updates.append("max_tokens = ?")
                params.append(max_tokens)
            if description is not None:
                updates.append("description = ?")
                params.append(description)

            if not updates:
                self.logger.warning(f"无字段需要更新: llm_id={llm_id}")
                return False

            # 添加 updated_at
            updates.append("updated_at = ?")
            params.append(datetime.datetime.now().isoformat())
            params.append(llm_id)

            sql = f"UPDATE models SET {', '.join(updates)} WHERE llm_id = ?"
            rows_affected = self._execute_update(sql, tuple(params))

            if rows_affected > 0:
                self.logger.info(f"更新 LLM 配置成功: llm_id={llm_id}")
                return True
            else:
                self.logger.warning(f"LLM 配置不存在: llm_id={llm_id}")
                return False

        except Exception as e:
            self.logger.error(f"更新 LLM 配置失败 (ID: {llm_id}): {e}")
            raise e

    # ==================== 删除操作 ====================

    def delete_by_id(self, llm_id: str) -> bool:
        """根据 llm_id 删除 LLM 配置

        Args:
            llm_id: LLM ID

        Returns:
            bool: 是否删除成功
        """
        try:
            sql = "DELETE FROM models WHERE llm_id = ?"
            rows_affected = self._execute_update(sql, (llm_id,))

            if rows_affected > 0:
                self.logger.info(f"删除 LLM 配置成功: llm_id={llm_id}")
                return True
            else:
                self.logger.warning(f"LLM 配置不存在: llm_id={llm_id}")
                return False

        except Exception as e:
            self.logger.error(f"删除 LLM 配置失败 (ID: {llm_id}): {e}")
            raise e

    def delete_by_config_name(self, llm_config_name: str) -> bool:
        """根据配置名称删除 LLM 配置

        Args:
            llm_config_name: 配置名称

        Returns:
            bool: 是否删除成功
        """
        try:
            sql = "DELETE FROM models WHERE llm_config_name = ?"
            rows_affected = self._execute_update(sql, (llm_config_name,))

            if rows_affected > 0:
                self.logger.info(f"删除 LLM 配置成功: llm_config_name={llm_config_name}")
                return True
            else:
                self.logger.warning(f"LLM 配置不存在: llm_config_name={llm_config_name}")
                return False

        except Exception as e:
            self.logger.error(
                f"删除 LLM 配置失败 (config_name: {llm_config_name}): {e}"
            )
            raise e

    # ==================== 检查操作 ====================

    def exists_by_config_name(self, llm_config_name: str) -> bool:
        """检查配置名称是否存在

        Args:
            llm_config_name: 配置名称

        Returns:
            bool: 是否存在
        """
        try:
            sql = "SELECT 1 FROM models WHERE llm_config_name = ? LIMIT 1"
            row = self._fetch_one(sql, (llm_config_name,))
            return row is not None

        except Exception as e:
            self.logger.error(f"检查 LLM 配置是否存在失败: {e}")
            raise e

    def count(self) -> int:
        """获取 LLM 配置总数

        Returns:
            int: 配置总数
        """
        try:
            sql = "SELECT COUNT(*) as count FROM models"
            row = self._fetch_one(sql)
            return row["count"] if row else 0

        except Exception as e:
            self.logger.error(f"获取 LLM 配置总数失败: {e}")
            raise e
