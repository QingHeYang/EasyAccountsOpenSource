"""
系统提示词组装器
负责按照分层架构组装完整的系统提示词

简化版：只包含任务层和角色层
- 任务层：每个Agent的详细任务指导（含工具使用指南）
- 角色层：身份定位
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ...config.settings import config
from ...database.repository_adapter import RepositoryAdapter
from ...models.agent import Agent
from ..logging_utils import ManagerLogger


class SystemPromptAssembler:
    """系统提示词组装器（简化版）"""

    def __init__(self, repository_adapter: RepositoryAdapter, tool_manager=None):
        """初始化

        Args:
            repository_adapter: 数据库适配器，用于获取历史上下文
            tool_manager: 工具管理器（保留参数兼容，未使用）
        """
        self.repository_adapter = repository_adapter
        self.logger = ManagerLogger("SystemPromptAssembler")

        # 提示词目录
        self.prompts_dir = config.prompts_dir
        self.layers_dir = self.prompts_dir / "layers"

    def assemble(self, agent: Agent, user_id: str, conversation_id: str) -> str:
        """组装完整的系统提示词

        简化架构：
        1. 任务层 - Agent专属指导（含工具使用指南）
        2. 角色层 - 身份定位
        3. 上下文层 - 历史信息（可选）

        Args:
            agent: Agent实例
            user_id: 用户ID
            conversation_id: 会话ID

        Returns:
            组装好的系统提示词
        """
        sections = []

        # 1. 任务层（最高优先级）- 每个Agent的详细任务指导
        if agent.task_instructions_file:
            task_content = self._load_task_layer(agent)
            if task_content:
                sections.append(f"<task>\n{task_content}\n</task>")

        # 2. 角色层（身份定位）
        role_content = self._build_role_layer(agent)
        if role_content:
            sections.append(f"<role>\n{role_content}\n</role>")

        # 3. 上下文层（历史信息）
        context_content = self._build_context_layer(user_id, conversation_id)
        if context_content:
            sections.append(f"<context>\n{context_content}\n</context>")

        # 组装最终结果
        result = "\n\n".join(filter(None, sections))

        self.logger.info("系统提示词组装完成", {
            "agent_id": agent.agent_id,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "prompt_length": len(result),
            "sections_count": len(sections)
        })

        return result

    def _load_task_layer(self, agent: Agent) -> str:
        """加载任务层提示词

        任务层是每个Agent的核心指导，包含：
        - 具体业务规则
        - 工具使用指南（什么情况用什么工具）
        - 回复规范
        """
        task_path = self.layers_dir / "task" / agent.task_instructions_file
        if task_path.exists():
            try:
                with open(task_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                self.logger.error(f"加载任务指导文件失败: {e}")
        return ""

    def _build_role_layer(self, agent: Agent) -> str:
        """构建角色层提示词"""
        if not agent.role_context:
            return ""

        # 解析role_context (JSON格式)
        try:
            role_dict = json.loads(agent.role_context)
        except:
            self.logger.error("解析角色配置失败")
            return ""

        # 查找合适的角色模板
        role_template_path = None

        # 1. 尝试特定角色文件
        if agent.role_file:
            role_name = agent.role_file.replace('.role', '')
            specific_path = self.layers_dir / "role" / f"{role_name}.prompt"
            if specific_path.exists():
                role_template_path = specific_path

        # 2. 使用通用模板
        if not role_template_path:
            default_path = self.layers_dir / "role" / "default.prompt"
            if default_path.exists():
                role_template_path = default_path

        if not role_template_path:
            return ""

        # 读取模板并替换占位符
        try:
            with open(role_template_path, 'r', encoding='utf-8') as f:
                template = f.read()

            # 替换占位符
            result = template
            for key, value in role_dict.items():
                result = result.replace(f"{{{key}}}", str(value))

            return result
        except Exception as e:
            self.logger.error(f"构建角色层失败: {e}")
            return ""

    def _build_context_layer(self, user_id: str, conversation_id: str) -> str:
        """构建上下文层（历史信息）"""
        if not self.repository_adapter:
            return ""

        parts = []

        try:
            # 获取会话信息
            conversation = self.repository_adapter.get_conversation_recorder(user_id, conversation_id)

            # 1. 当前会话总结
            if conversation and conversation.summary:
                parts.append(f"【当前会话总结】\n{conversation.summary}")

            # 2. 最近快照
            recent_snapshots = self.repository_adapter.get_recent_snapshots(conversation_id, limit=2)
            if recent_snapshots:
                for i, snapshot in enumerate(recent_snapshots, 1):
                    parts.append(f"【快照{i}】\n{snapshot['context_summary']}")

        except Exception as e:
            self.logger.error(f"获取历史上下文失败: {e}")

        return "\n\n".join(parts) if parts else ""
