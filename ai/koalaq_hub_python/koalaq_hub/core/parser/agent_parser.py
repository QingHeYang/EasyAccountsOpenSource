"""
Agent解析器 - 解析Agent调用指令，支持多种格式
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .base_parser import BaseParser, CallType, ParseResult


@dataclass
class AgentCall(ParseResult):
    """Agent调用"""
    agent_id: str
    task: str
    context: Dict[str, Any] = field(default_factory=dict)
    require_reasoning: bool = False
    
    def __init__(self, agent_id: str, task: str, context: Optional[Dict[str, Any]] = None,
                 require_reasoning: bool = False, raw_content: str = "", 
                 position: Tuple[int, int] = (0, 0)):
        super().__init__(
            call_type=CallType.AGENT,
            raw_content=raw_content,
            position=position
        )
        self.agent_id = agent_id
        self.task = task
        self.context = context or {}
        self.require_reasoning = require_reasoning
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            "agent": self.agent_id,
            "task": self.task,
            "context": self.context,
            "require_reasoning": self.require_reasoning
        })
        return base_dict


class AgentParser(BaseParser):
    """Agent调用解析器"""
    
    def __init__(self):
        super().__init__()
        # 预编译正则表达式
        self._agent_block_pattern = re.compile(r"```agent\s*\n(.*?)\n```", re.DOTALL)
        self._mention_pattern = re.compile(r"@([\w-]+-agent)\s+([^@\n]+)")
        self._json_agent_pattern = re.compile(r'\{[^{}]*"agent"[^{}]*"task"[^{}]*\}')
    
    def parse(self, content: str) -> Tuple[str, List[ParseResult], bool]:
        """
        解析Agent调用
        
        Args:
            content: 需要解析的内容
            
        Returns:
            Tuple[str, List[ParseResult], bool]: 
            - 清理后的内容
            - 解析结果列表（所有AgentCall）
            - 是否包含Agent调用
        """
        all_results = []
        
        # 1. 解析```agent代码块
        agent_block_results = self._parse_agent_blocks(content)
        all_results.extend(agent_block_results)
        
        # 2. 解析@mention格式
        mention_results = self._parse_mentions(content)
        all_results.extend(mention_results)
        
        # 3. 解析JSON格式
        json_results = self._parse_json_agents(content)
        all_results.extend(json_results)
        
        # 清理内容
        cleaned_content = self.remove_parsed_content(content, all_results)
        
        return cleaned_content, all_results, len(all_results) > 0
    
    def can_parse(self, content: str) -> bool:
        """快速检查是否包含Agent调用"""
        return bool(
            self._agent_block_pattern.search(content) or
            self._mention_pattern.search(content) or
            ('"agent"' in content and '"task"' in content)
        )
    
    def _parse_agent_blocks(self, content: str) -> List[AgentCall]:
        """解析```agent代码块"""
        results = []
        
        for match in self._agent_block_pattern.finditer(content):
            try:
                block_content = match.group(1).strip()
                agent_data = json.loads(block_content)
                
                if isinstance(agent_data, list):
                    # 多个agent调用
                    for item in agent_data:
                        if isinstance(item, dict) and "agent" in item and "task" in item:
                            results.append(AgentCall(
                                agent_id=item["agent"],
                                task=item["task"],
                                context=item.get("context", {}),
                                require_reasoning=item.get("require_reasoning", False),
                                raw_content=match.group(0),
                                position=(match.start(), match.end())
                            ))
                elif isinstance(agent_data, dict) and "agent" in agent_data and "task" in agent_data:
                    # 单个agent调用
                    results.append(AgentCall(
                        agent_id=agent_data["agent"],
                        task=agent_data["task"],
                        context=agent_data.get("context", {}),
                        require_reasoning=agent_data.get("require_reasoning", False),
                        raw_content=match.group(0),
                        position=(match.start(), match.end())
                    ))
                    
            except json.JSONDecodeError:
                self.logger.debug("Agent代码块解析失败", {"content": block_content})
                
        return results
    
    def _parse_mentions(self, content: str) -> List[AgentCall]:
        """解析@mention格式"""
        results = []
        
        for match in self._mention_pattern.finditer(content):
            agent_id = match.group(1)
            task = match.group(2).strip()
            
            results.append(AgentCall(
                agent_id=agent_id,
                task=task,
                raw_content=match.group(0),
                position=(match.start(), match.end())
            ))
            
        return results
    
    def _parse_json_agents(self, content: str) -> List[AgentCall]:
        """解析JSON格式的Agent调用"""
        results = []
        
        for match in self._json_agent_pattern.finditer(content):
            try:
                agent_data = json.loads(match.group(0))
                if "agent" in agent_data and "task" in agent_data:
                    results.append(AgentCall(
                        agent_id=agent_data["agent"],
                        task=agent_data["task"],
                        context=agent_data.get("context", {}),
                        require_reasoning=agent_data.get("require_reasoning", False),
                        raw_content=match.group(0),
                        position=(match.start(), match.end())
                    ))
            except json.JSONDecodeError:
                self.logger.debug("JSON Agent解析失败", {"content": match.group(0)})
                
        return results