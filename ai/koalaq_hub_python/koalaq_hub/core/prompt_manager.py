import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from ..config.settings import config
from ..database.repository_adapter import RepositoryAdapter
from .logging_utils import ManagerLogger


class PromptManager:
    """提示词管理器 - 纯粹的模板引擎 + 专用系统提示词构建器

    职责：
    1. 通用模板引擎：加载.prompt文件并替换{占位符}
    2. 专用系统提示词构建：根据application_config构建系统提示词
    3. 专用系统消息构建：构建带历史总结的完整系统消息
    """

    def __init__(self, package_root: Path):
        """初始化提示词管理器

        Args:
            package_root: 包根目录路径
        """
        self.package_root = package_root
        # 使用全局配置获取路径
        self.role_dir = config.get_role_dir()
        self.prompts_dir = config.prompts_dir

        # 提示词缓存
        self._prompt_cache: Dict[str, str] = {}

        # 初始化日志记录器
        self.logger = ManagerLogger("PromptManager")

    def load_and_replace_prompt(self, prompt_filename: str, **kwargs) -> str:
        """通用模板引擎：加载.prompt文件并替换{占位符}

        Args:
            prompt_filename: 提示词文件名，如 "system.prompt", "conversation_summary.prompt"
            **kwargs: 用于替换文件中{占位符}的参数

        Returns:
            替换后的提示词内容

        Examples:
            prompt = load_and_replace_prompt("system.prompt",
                                           tools_description="工具列表...",
                                           role="智能助手")
        """
        # 生成缓存键
        cache_key = f"{prompt_filename}_{hash(str(sorted(kwargs.items())))}"

        # 检查缓存
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]

        # 构建文件路径
        prompt_path = self.prompts_dir / prompt_filename

        if not prompt_path.exists():
            self.logger.error(
                "提示词文件不存在",
                extra_data={
                    "prompt_filename": prompt_filename,
                    "prompt_path": str(prompt_path),
                }
            )
            return ""

        try:
            # 读取模板文件
            with open(prompt_path, "r", encoding="utf-8") as f:
                template = f.read()

            # 替换占位符
            result = template
            for key, value in kwargs.items():
                placeholder = f"{{{key}}}"
                result = result.replace(placeholder, str(value))

            # 缓存结果
            self._prompt_cache[cache_key] = result

            self.logger.debug(
                "成功加载并替换提示词模板",
                {
                    "prompt_filename": prompt_filename,
                    "placeholders_count": len(kwargs),
                    "result_length": len(result),
                }
            )

            return result

        except Exception as e:
            self.logger.error(
                "加载提示词文件失败",
                exception=e,
                extra_data={"prompt_filename": prompt_filename}
            )
            return ""

    def load_role_config(self, role_filename: str) -> Dict[str, str]:
        """加载角色配置文件（通用方法）

        Args:
            role_filename: 角色文件名，如 "assistant.role"

        Returns:
            角色配置字典，key:value格式
        """
        # 支持带扩展名和不带扩展名
        if not role_filename.endswith(".role"):
            role_filename += ".role"

        role_file_path = self.role_dir / role_filename

        if not role_file_path.exists():
            self.logger.warning(
                "角色配置文件不存在",
                {"role_filename": role_filename, "role_file_path": str(role_file_path)}
            )
            return {}

        try:
            role_config = {}
            with open(role_file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and ":" in line:
                        key, value = line.split(":", 1)
                        role_config[key.strip()] = value.strip()

            self.logger.debug(
                "成功加载角色配置",
                {
                    "role_filename": role_filename,
                    "config_keys": list(role_config.keys()),
                }
            )
            return role_config

        except Exception as e:
            self.logger.error(
                "加载角色配置文件失败",
                exception=e,
                extra_data={"role_filename": role_filename}
            )
            return {}

    def build_system_prompt(self, application_config, tools_description: str) -> str:
        """专用方法：构建系统提示词

        Args:
            application_config: 应用配置对象（包含system_prompt_file、role_file等）
            tools_description: 工具描述（从ToolManager获取）

        Returns:
            完整的系统提示词
        """
        # 获取系统提示词文件名
        system_prompt_file = application_config.system_prompt_file

        # 获取角色配置
        role_file = application_config.role_file
        role_config = {}
        if role_file:
            role_config = self.load_role_config(role_file)

        # 设置默认角色信息
        if not role_config:
            role_config = {
                "role": "智能助手",
                "capabilities": "回答问题、协助完成任务",
                "personality": "友善、专业、乐于助人",
                "user_scene": "日常对话",
                "location": "中国",
            }

        # 构建替换参数
        replace_params = {
            "tools_description": tools_description,
            **role_config,  # 展开角色配置中的所有键值对
        }

        # 使用通用模板引擎生成系统提示词
        system_prompt = self.load_and_replace_prompt(system_prompt_file, **replace_params)

        self.logger.info(
            "构建系统提示词完成",
            {
                "application_id": application_config.app_id,
                "system_prompt_file": system_prompt_file,
                "role_file": role_file,
                "prompt_length": len(system_prompt),
            }
        )

        return system_prompt

    # 旧的服务器管理方法已移除，现在PromptManager专注于提示词管理
    # 服务器管理职责已转移到ServerManager
    # 工具管理职责已转移到ToolManager

    # 角色配置加载已统一到 load_role_config() 方法

    def _replace_placeholders(self, template: str, role_config: Dict[str, str], tools_description: str) -> str:
        """替换模板中的占位符

        Args:
            template: 原始模板
            role_config: 角色配置
            tools_description: 工具描述

        Returns:
            替换后的模板
        """
        # 替换工具描述
        result = template.replace("{tools_description}", tools_description)

        # 替换角色相关的占位符
        placeholders = {
            "{{role}}": role_config.get("role", ""),
            "{{cos_role}}": role_config.get("cos_role", ""),
            "{{name}}": role_config.get("name", ""),
            "{{character}}": role_config.get("character", ""),
            "{{user_role}}": role_config.get("user_role", ""),
            "{{user_role_description}}": role_config.get("user_role_description", ""),
            "{{user_scene}}": role_config.get("user_scene", ""),
            "{{location}}": role_config.get("location", ""),
        }
        if "{{current_time}}" in result:
            placeholders["{{current_time}}"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        for placeholder, value in placeholders.items():
            result = result.replace(placeholder, value)

        return result

    def load_system_prompt(self, tools_description: str) -> str:
        """加载并生成系统提示词

        Args:
            tools_description: 工具描述字符串

        Returns:
            完整的系统提示词
        """
        # 从环境变量读取角色配置
        role_name = os.getenv("ROLE", "default")

        # 加载角色配置
        role_config = self._load_role_config(role_name)
        if not role_config:
            self.logger.warning("未找到角色配置，使用默认配置", {"role_name": role_name})
            role_config = {
                "role": "智能助手",
                "cos_role": "AI助手",
                "name": "助手",
                "character": "友好、专业、乐于助人",
                "user_role": "用户",
                "user_role_description": "用户",
                "user_scene": "日常对话",
                "location": "中国",
            }

        # 加载提示词模板
        system_prompt_path = self.prompts_dir / "system.prompt"
        if not system_prompt_path.exists():
            raise FileNotFoundError(f"系统提示词模板文件不存在: {system_prompt_path}")
        try:
            with open(system_prompt_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except Exception as e:
            raise Exception(f"读取系统提示词模板失败: {e}")

        # 替换占位符
        system_prompt = self._replace_placeholders(prompt_template, role_config, tools_description)
        return system_prompt

    def load_prompt_template(self, template_name: str, **kwargs) -> str:
        """加载prompts文件夹下的提示词模板

        Args:
            template_name: 模板名称（不带.prompt后缀）
            **kwargs: 模板中的占位符参数

        Returns:
            渲染后的提示词内容
        """
        # 检查缓存
        cache_key = f"{template_name}_{hash(str(sorted(kwargs.items())))}"
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]

        # 构建模板文件路径
        template_path = self.prompts_dir / f"{template_name}.prompt"

        if not template_path.exists():
            raise FileNotFoundError(f"提示词模板文件不存在: {template_path}")

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()
        except Exception as e:
            raise Exception(f"读取提示词模板失败: {e}")

        # 替换占位符
        try:
            rendered_content = template_content.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"模板 {template_name} 中缺少必需的参数: {e}")
        except Exception as e:
            raise Exception(f"渲染模板失败: {e}")

        # 缓存结果
        self._prompt_cache[cache_key] = rendered_content
        return rendered_content

    def get_available_templates(self) -> List[str]:
        """获取所有可用的提示词模板名称

        Returns:
            模板名称列表，不包含.prompt后缀
        """
        if not self.prompts_dir.exists():
            return []

        templates = []
        for template_file in self.prompts_dir.glob("*.prompt"):
            if template_file.name != "system.prompt":  # 排除系统提示词
                templates.append(template_file.stem)
        return templates

    def get_available_roles(self) -> List[str]:
        """获取所有可用的角色列表

        Returns:
            角色名称列表
        """
        if not self.role_dir.exists():
            return []

        roles = []
        for role_file in self.role_dir.glob("*.role"):
            roles.append(role_file.stem)
        return roles

    def build_system_message(
        self,
        application_config,
        user_id: str,
        conversation_id: str,
        tools_description: str,
        sqlite_storage: RepositoryAdapter=None,
    ) -> str:
        """专用方法：构建带历史总结的完整系统消息（三层历史结构）

        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            application_config: 应用配置对象
            tools_description: 工具描述（从ToolManager获取）
            sqlite_storage: 数据库实例

        Returns:
            完整的系统消息（系统提示词 + 历史总结）
        """
        # 1. 构建基础系统提示词
        base_prompt = self.build_system_prompt(application_config, tools_description)
        parts = [base_prompt]
        
        # 初始化变量
        conversation = None
        recent_snapshots = []
        
        if sqlite_storage: # 如果sqlite_storage不为空，则获取历史总结
            # 2. 获取当前会话的历史总结（三层结构）
            conversation = sqlite_storage.get_conversation_recorder(user_id, conversation_id)
            # 3. 第一层：当前会话的对话总结（最重要的上下文）
            if conversation and conversation.summary:
                parts.append(f"\n【当前会话总结】\n{conversation.summary}")

            # 4. 第二层：最近两个快照（补充详细的近期上下文）
            recent_snapshots = sqlite_storage.get_recent_snapshots(conversation_id, limit=2)
            if recent_snapshots:
                for i, snapshot in enumerate(recent_snapshots, 1):
                    parts.append(f"\n【快照{i}】\n{snapshot['context_summary']}")

            # # 5. 第三层：历史会话总结（用户整体行为模式）
            # user_history = sqlite_storage.get_summary_logs_by_conversation(conversation_id, limit=3)
            # if user_history:
            #     history_parts = []
            #     for history in user_history:
            #         if history["conversation_id"] != conversation_id:  # 排除当前会话
            #             history_parts.append(f"- {history['summary']}")
            #     if history_parts:
            #         parts.append(f"\n【用户历史行为模式】\n" + "\n".join(history_parts))

        # 构建最终结果
        result = "\n".join(parts)

        self.logger.info(
            "构建系统消息完成",
            {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "application_id": getattr(application_config, "app_id", "unknown"),
                "system_message_length": len(result),
                "has_conversation_summary": bool(conversation and conversation.summary),
                "snapshots_count": len(recent_snapshots) if recent_snapshots else 0,
            }
        )

        return result

    def clear_cache(self, pattern: str = None):
        """清空提示词缓存

        Args:
            pattern: 可选的模式匹配，只清除匹配的缓存项
        """
        if pattern:
            keys_to_remove = [k for k in self._prompt_cache.keys() if pattern in k]
            for key in keys_to_remove:
                self._prompt_cache.pop(key, None)
            self.logger.debug("清除匹配缓存", {"pattern": pattern, "count": len(keys_to_remove)})
        else:
            self._prompt_cache.clear()
            self.logger.debug("清除所有缓存")

    # 向后兼容的方法
    def get_prompt_template_path(self):
        """获取系统提示词模板路径（向后兼容）"""
        return self.prompts_dir / "system.prompt"

    def load_round_summary_prompt(self) -> str:
        """加载round_summary.prompt模板"""
        max_length = config.round_summary_max_length
        return self.load_prompt_template("round_summary", max_length=max_length)

    def load_snapshot_summary_prompt(self) -> str:
        """加载snapshot_summary.prompt模板"""
        max_length = config.snapshot_summary_max_length
        return self.load_prompt_template("snapshot_summary", max_length=max_length)

    def load_conversation_summary_prompt(self) -> str:
        """加载conversation_summary.prompt模板"""
        max_length = config.conversation_summary_max_length
        return self.load_prompt_template("conversation_summary", max_length=max_length)

    def load_title_summary_prompt(self) -> str:
        """加载title_summary.prompt模板"""
        return self.load_prompt_template("title_summary")
    
    def load_auto_question_prompt(self, agent_system_prompt: str) -> str:
        """加载auto_question.prompt模板"""
        return self.load_prompt_template("auto_question", agent_system_prompt=agent_system_prompt)
