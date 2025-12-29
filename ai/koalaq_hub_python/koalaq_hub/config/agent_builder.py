import configparser
import json
from typing import Any, Dict, List, Optional

from .settings import config


class AgentConfig:
    """Agent配置类，用于管理单个Agent的配置"""

    def __init__(self, agent_id: str, agent_data: Dict[str, Any]):
        self.agent_id = agent_id
        self._data = agent_data
        self._use_think_llm = False  # 初始化use_think_llm属性
        self._agent_guide_context = ""  # 存储agent指南内容
        self._role_context = ""  # 存储角色文件内容

    @property
    def enable(self) -> bool:
        """是否启用"""
        return self._data.get("enable", "true").lower() == "true"

    # @property
    # def system_prompt_file(self) -> str:
    #     """获取系统提示词文件名（不读取内容）"""
    #     """已废弃：使用新的分层提示词拼接系统"""
    #     return self._data.get("system_prompt", "system.prompt")

    @property
    def llm_use(self) -> str:
        """获取LLM使用配置名称"""
        return self._data.get("llm_use", "")

    @property
    def llm_think_use(self) -> str:
        """获取LLM思考使用配置名称"""
        return self._data.get("llm_think_use", "")

    @property
    def summary_llm_use(self) -> str:
        """获取总结LLM使用配置名称"""
        return self._data.get("summary_llm_use", "")

    @property
    def mcp_servers(self) -> list:
        """获取MCP服务器名称列表"""
        # 新配置格式：mcp_servers = ["baidu-maps", "weather"]
        mcp_servers_str = self._data.get("mcp_servers", "[]")
        try:
            servers_list = json.loads(mcp_servers_str)
            return servers_list if isinstance(servers_list, list) else []
        except Exception as e:
            print(f"解析MCP服务器列表失败: {e}")
            return []

    @property
    def role_file(self) -> str:
        """获取角色配置文件名（不读取内容）"""
        return self._data.get("role", "")
    
    @property
    def agent_guide(self) -> str:
        """获取Agent指南文件名（不读取内容）"""
        return self._data.get("agent_guide", "")
    
    @property
    def agent_list(self) -> List[str]:
        """获取子Agent列表"""
        agent_list_str = self._data.get("agent_list", "[]")
        try:
            agent_list = json.loads(agent_list_str)
            return agent_list if isinstance(agent_list, list) else []
        except Exception as e:
            print(f"解析Agent列表失败: {e}")
            return []
    
    @property
    def agent_guide_context(self) -> str:
        """获取Agent指南内容"""
        if self._agent_guide_context:
            return f"```yaml\n{self._agent_guide_context}\n```"
    
    @property
    def role_context(self) -> str:
        """获取角色文件内容"""
        return self._role_context

    @property
    def name(self) -> str:
        """Agent名称"""
        return self._data.get("name", "")

    @property
    def description(self) -> str:
        """Agent描述"""
        return self._data.get("description", "")

    # 属性重复定义，移除这些重复项

    @property
    def enable_summary(self) -> bool:
        """是否启用总结"""
        return self._data.get("enable_summary", "true").lower() == "true"

    @property
    def enable_auto_question(self) -> bool:
        """是否启用自动生成问题"""
        return self._data.get("enable_auto_question", "true").lower() == "true"

    @enable_summary.setter
    def enable_summary(self, value: bool):
        self._data["enable_summary"] = str(value).lower()

    @property
    def enable_thinking(self) -> bool:
        """是否启用思考"""
        return self._data.get("enable_thinking", "true").lower() == "true"

    @property
    def llm_memory_window(self) -> int:
        """LLM记忆窗口大小"""
        return int(self._data.get("llm_memory_window", "10"))

    @property
    def tool_round(self) -> int:
        """工具调用轮次"""
        return int(self._data.get("tool_round", "5"))

    @property
    def mcp_tool_black_list(self) -> list:
        """MCP工具黑名单"""
        black_list_str = self._data.get("mcp_tool_black_list", "[]")
        try:
            return json.loads(black_list_str)
        except Exception as e:
            print(f"解析工具黑名单失败: {e}")
            return []

    @property
    def tool_tokens(self) -> Dict[str, str]:
        """工具Token配置，用于MCP鉴权"""
        tool_tokens_str = self._data.get("tool_tokens", "[]")
        try:
            # 支持两种格式：
            # 1. JSON格式: ["key1=value1", "key2=value2"]
            # 2. 直接字典格式: {"key1": "value1", "key2": "value2"}
            tokens_data = json.loads(tool_tokens_str)
            if isinstance(tokens_data, list):
                # 处理 ["key=value"] 格式
                result = {}
                for item in tokens_data:
                    if "=" in str(item):
                        key, value = str(item).split("=", 1)
                        result[key.strip()] = value.strip()
                return result
            elif isinstance(tokens_data, dict):
                # 直接返回字典格式
                return tokens_data
            else:
                return {}
        except Exception as e:
            print(f"解析工具Token配置失败: {e}")
            return {}
    
    @property
    def enable_react_mode(self) -> bool:
        """是否启用ReAct模式"""
        return self._data.get("enable_react_mode", "false").lower() == "true"
    
    @property
    def react_style(self) -> str:
        """ReAct模式风格：verbose, concise, hidden"""
        return self._data.get("react_style", "verbose")
    
    @property
    def base_modules(self) -> List[str]:
        """基础层模块列表"""
        modules_str = self._data.get("base_modules", '["format_rules", "communication_style"]')
        try:
            modules = json.loads(modules_str)
            return modules if isinstance(modules, list) else ["format_rules", "communication_style"]
        except Exception as e:
            print(f"解析基础模块列表失败: {e}")
            return ["format_rules", "communication_style"]
    
    @property
    def task_instructions_file(self) -> str:
        """任务指导文件名"""
        return self._data.get("task_instructions_file", "")

    @tool_tokens.setter
    def tool_tokens(self, value: Dict[str, str]):
        """设置工具Token配置"""
        # 将字典转换为JSON字符串存储
        self._data["tool_tokens"] = json.dumps(value, ensure_ascii=False)
    
    @property
    def use_think_llm(self) -> bool:
        """是否使用思考LLM"""
        return self._use_think_llm
    
    @use_think_llm.setter
    def use_think_llm(self, value: bool):
        self._use_think_llm = value


class AgentBuilder:
    """Agent构建器 - 从配置文件构建Agent"""

    def __init__(self):
        # 使用 config 中的路径配置
        self.agent_config_path = config.agent_config_path
        self._agents = {}
        self._load_agents()

    def _load_agents(self) -> None:
        """加载Agent配置"""
        if not self.agent_config_path.exists():
            print(f"Agent配置文件不存在: {self.agent_config_path}")
            return

        try:
            config_parser = configparser.ConfigParser()
            config_parser.read(self.agent_config_path, encoding="utf-8")

            for section_name in config_parser.sections():
                section = config_parser[section_name]
                agent_data = {key: value for key, value in section.items()}
                agent_config = AgentConfig(section_name, agent_data)
                
                # 读取agent_guide文件内容
                if agent_config.agent_guide:
                    guide_file_path = config.agent_guide_dir / agent_config.agent_guide
                    try:
                        if guide_file_path.exists():
                            with open(guide_file_path, 'r', encoding='utf-8') as f:
                                agent_config._agent_guide_context = f.read()
                    except Exception as e:
                        print(f"读取Agent指南文件失败 {guide_file_path}: {e}")
                
                # 读取role文件内容
                if agent_config.role_file:
                    role_file_path = config.role_dir / agent_config.role_file
                    try:
                        if role_file_path.exists():
                            # 读取role文件，解析key:value格式
                            role_dict = {}
                            with open(role_file_path, 'r', encoding='utf-8') as f:
                                for line in f:
                                    line = line.strip()
                                    if line and ':' in line:
                                        key, value = line.split(':', 1)
                                        role_dict[key.strip()] = value.strip()
                            
                            # 转换为JSON字符串存储
                            agent_config._role_context = json.dumps(role_dict, ensure_ascii=False)
                    except Exception as e:
                        print(f"读取角色文件失败 {role_file_path}: {e}")
                
                self._agents[section_name] = agent_config

            print(f"成功加载Agent配置，共 {len(self._agents)} 个Agent: {list(self._agents.keys())}")

        except Exception as e:
            print(f"加载Agent配置失败: {e}")

    def print_agent_info(self, agent_id: str) -> None:
        """打印Agent配置信息（用于调试）"""
        agent = self.get_agent(agent_id)
        if not agent:
            print(f"Agent不存在: {agent_id}")
            return

        print(f"=== Agent配置信息: {agent_id} ===")
        print(f"启用: {agent.enable}")
        print(f"Agent名称: {agent.name}")
        print(f"描述: {agent.description}")
        print(f"主LLM: {agent.llm_use}")
        print(f"思考LLM: {agent.llm_think_use}")
        print(f"总结LLM: {agent.summary_llm_use}")
        print(f"启用总结: {agent.enable_summary}")
        print(f"启用自动生成问题: {agent.enable_auto_question}")
        print(f"使用思考LLM: {agent.use_think_llm}")
        print(f"记忆窗口: {agent.llm_memory_window}")
        print(f"工具轮次: {agent.tool_round}")
        print(f"MCP服务器: {agent._data.get('mcp_servers', '')}")
        print(f"工具黑名单: {agent.mcp_tool_black_list}")
        print(f"角色文件: {agent._data.get('role', '无')}")
        # print(f"提示词文件: {agent._data.get('system_prompt', '无')}")  # 已废弃
        print(f"ReAct模式: {agent.enable_react_mode} ({agent.react_style})")
        print(f"基础模块: {agent.base_modules}")
        print(f"任务指导文件: {agent.task_instructions_file}")

    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """获取指定Agent配置"""
        return self._agents.get(agent_id)

    def build_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """构建指定的Agent（同get_agent，更语义化）"""
        return self.get_agent(agent_id)

    def __getitem__(self, agent_id: str) -> AgentConfig:
        """支持 agent_builder[agent_id] 语法"""
        agent = self.get_agent(agent_id)
        if agent is None:
            raise KeyError(f"Agent配置不存在: {agent_id}")
        return agent

    def get_all_agents(self) -> Dict[str, AgentConfig]:
        """获取所有Agent配置"""
        return self._agents

    def get_available_agents(self) -> list:
        """获取可用Agent列表"""
        return list(self._agents.keys())


# 创建全局Agent构建器实例
agent_builder = AgentBuilder()