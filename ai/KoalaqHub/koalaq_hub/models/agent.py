"""
Agent 模型类
定义了一个完整的智能体实例，包含配置、能力和运行时状态
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .llm import LLM


@dataclass
class Agent:
    """Agent 实例模型
    
    代表一个完整的智能体，包含：
    - 基础配置信息（从 AgentConfig 复制）
    - LLM 对象实例
    - 运行时状态
    - 可动态修改的参数
    """
    
    # 基础信息
    agent_id: str
    name: str
    description: str
    
    # 从 AgentConfig 复制的配置值
    enable: bool = True
    # system_prompt_file: str = "system.prompt"  # 已废弃：使用新的分层提示词拼接系统
    role_file: str = ""
    role_context: str = ""  # 角色文件内容
    llm_use: str = ""
    llm_think_use: str = ""
    summary_llm_use: str = ""
    
    # 功能开关
    enable_summary: bool = True
    enable_thinking: bool = True
    enable_auto_question: bool = True
    
    # 参数配置
    llm_memory_window: int = 10
    tool_round: int = 5
    
    # MCP 相关配置
    mcp_servers: List[str] = field(default_factory=list)
    mcp_tool_black_list: List[str] = field(default_factory=list)
    
    # 系统提示词（运行时组装）
    system_prompt: str = ""
    tool_tokens: Dict[str, str] = field(default_factory=dict)
    
    # Function Calling 工具列表（运行时构建）
    tool_list: List[Dict[str, Any]] = field(default_factory=list)
    
    # Agent 相关配置
    agent_guide: str = ""  # 自己的guide文件名（给别人看的）
    agent_list: List[str] = field(default_factory=list)  # 可以调用的子Agent列表
    agent_sub_prompt: str = ""  # 动态构建的子Agent使用指南

    # 内部工具列表（配置该Agent可用的内部工具）
    inner_tools: List[str] = field(default_factory=list)

    # 任务指导文件（核心配置，包含详细的工具使用指南）
    task_instructions_file: str = ""
    
    # LLM 对象（从 llm_builder 获取）
    main_llm: Optional[LLM] = None
    think_llm: Optional[LLM] = None
    summary_llm: Optional[LLM] = None
    
    # 运行时状态
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    
    # 运行时参数（可被请求覆盖）
    use_think_llm: bool = False
    
    # 子agent模式
    sub_agent_mode: bool = False
    current_conversation_id: str = ""
    parent_conversation_id: str = ""
    
    websocket_mode: bool = False
    
    def __post_init__(self):
        """初始化后处理"""
        # 可以在这里添加初始化逻辑
        pass
    
    def get_llm_for_mode(self, use_think: Optional[bool] = None) -> Optional[LLM]:
        """根据模式获取对应的 LLM 对象
        
        Args:
            use_think: 是否使用思考模式，为None时使用实例属性
            
        Returns:
            对应的 LLM 对象
        """
        # 优先使用参数，其次使用实例属性
        should_use_think = use_think if use_think is not None else self.use_think_llm
        
        if should_use_think and self.think_llm:
            return self.think_llm
        return self.main_llm
    
    def get_llm_config_for_mode(self, use_think: Optional[bool] = None) -> Dict[str, Any]:
        """根据模式获取对应的 LLM 配置
        
        Args:
            use_think: 是否使用思考模式，为None时使用实例属性
            
        Returns:
            对应的 LLM 配置
        """
        llm = self.get_llm_for_mode(use_think)
        if llm:
            return llm.to_llm_config()
        return {}
    
    @property
    def memory_window(self) -> int:
        """获取记忆窗口大小"""
        return self.llm_memory_window
    
    @property
    def tool_round_limit(self) -> int:
        """获取工具调用轮次限制"""
        return self.tool_round
    
    def update_usage(self):
        """更新使用统计"""
        self.last_used_at = datetime.now()
        self.usage_count += 1
    
    
    def get_info(self) -> Dict[str, Any]:
        """获取 Agent 信息摘要"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "usage_count": self.usage_count,
            "has_think_llm": self.think_llm is not None,
            "has_summary_llm": self.summary_llm is not None,
            "memory_window": self.memory_window,
            "tool_round_limit": self.tool_round_limit,
            "enable_summary": self.enable_summary,
            "enable_thinking": self.enable_thinking,
            "enable_auto_question": self.enable_auto_question,
        }
    
    def validate(self) -> bool:
        """验证 Agent 是否配置完整
        
        Returns:
            bool: 配置是否有效
        """
        # 必须有主 LLM 对象
        if not self.main_llm:
            return False
        
        # 必须有基础信息
        if not self.agent_id or not self.name:
            return False
        
        return True
    
    def is_ready(self) -> bool:
        """检查Agent是否就绪（validate的别名）"""
        return self.validate()
    
    def __repr__(self) -> str:
        return (
            f"Agent(id='{self.agent_id}', name='{self.name}', "
            f"active={self.is_active})"
        )