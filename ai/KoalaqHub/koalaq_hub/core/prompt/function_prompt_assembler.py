"""
功能型提示词组装器
负责处理独立的功能型提示词，主要用于模板替换
"""

from typing import Dict, Optional

from ...config.settings import config
from ..logging_utils import ManagerLogger


class FunctionPromptAssembler:
    """功能型提示词组装器 - 用于替代PromptManager的部分功能"""
    
    def __init__(self):
        """初始化"""
        self.logger = ManagerLogger("FunctionPromptAssembler")
        
        # 功能型提示词目录
        self.functions_dir = config.prompts_dir / "functions"
        
        # 缓存
        self._cache: Dict[str, str] = {}
        
    def load_and_format(self, function_name: str, **kwargs) -> str:
        """加载并格式化功能提示词
        
        Args:
            function_name: 功能名称（不带.prompt后缀）
            **kwargs: 用于替换的参数
            
        Returns:
            格式化后的提示词
        """
        # 生成缓存键
        cache_key = f"{function_name}_{hash(str(sorted(kwargs.items())))}"
        
        # 检查缓存
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 加载模板
        template = self._load_template(function_name)
        if not template:
            return ""
        
        # 替换占位符
        result = self._replace_placeholders(template, **kwargs)
        
        # 缓存结果
        self._cache[cache_key] = result
        
        return result
    
    def _load_template(self, function_name: str) -> str:
        """加载模板文件"""
        template_path = self.functions_dir / f"{function_name}.prompt"
        
        if not template_path.exists():
            self.logger.error(f"功能提示词文件不存在: {template_path}")
            return ""
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"读取功能提示词文件失败: {e}", extra_data={
                "function_name": function_name,
                "path": str(template_path)
            })
            return ""
    
    def _replace_placeholders(self, template: str, **kwargs) -> str:
        """替换模板中的占位符
        
        支持三种格式：
        1. {{placeholder}} - 双花括号格式（旧版提示词）
        2. {placeholder} - 单花括号格式
        3. Python format风格 - 用于复杂格式化
        """
        result = template
        
        # 首先处理双花括号格式 {{placeholder}}
        for key, value in kwargs.items():
            double_placeholder = f"{{{{{key}}}}}"
            result = result.replace(double_placeholder, str(value))
        
        # 然后尝试使用format方法处理单花括号格式
        try:
            result = result.format(**kwargs)
        except:
            # 如果format失败，使用简单替换处理剩余的单花括号
            for key, value in kwargs.items():
                single_placeholder = f"{{{key}}}"
                result = result.replace(single_placeholder, str(value))
        
        return result
    
    # 便捷方法 - 直接对应PromptManager中的方法
    
    def load_round_summary_prompt(self) -> str:
        """加载单轮总结提示词"""
        max_length = config.round_summary_max_length
        return self.load_and_format("round_summary", max_length=max_length)
    
    def load_snapshot_summary_prompt(self) -> str:
        """加载快照总结提示词"""
        max_length = config.snapshot_summary_max_length
        return self.load_and_format("snapshot_summary", max_length=max_length)
    
    def load_conversation_summary_prompt(self) -> str:
        """加载会话总结提示词"""
        max_length = config.conversation_summary_max_length
        return self.load_and_format("conversation_summary", max_length=max_length)
    
    def load_title_summary_prompt(self) -> str:
        """加载标题生成提示词"""
        return self.load_and_format("title_summary")
    
    def load_auto_question_prompt(self, agent_system_prompt: str) -> str:
        """加载自动追问提示词"""
        return self.load_and_format("auto_question", agent_system_prompt=agent_system_prompt)
    
    def clear_cache(self, pattern: Optional[str] = None):
        """清空缓存
        
        Args:
            pattern: 可选的模式匹配，只清除匹配的缓存项
        """
        if pattern:
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                self._cache.pop(key, None)
            self.logger.debug(f"清除匹配缓存: {pattern}, 数量: {len(keys_to_remove)}")
        else:
            self._cache.clear()
            self.logger.debug("清除所有缓存")