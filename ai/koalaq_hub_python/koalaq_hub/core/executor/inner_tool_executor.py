"""
内部工具执行器 - 负责执行系统内部工具
"""

import json
from typing import Any, Dict, List

from ..parser import AgentCall
from ..tool.function.easyaccounts import EasyAccountsTools, get_tool_names
from .base_executor import BaseExecutor, ExecutionResult


class InnerToolExecutor(BaseExecutor):
    """内部工具执行器 - 处理内部Function Calling工具"""
    
    def __init__(self, sub_agent_executor=None):
        """
        初始化内部工具执行器
        
        Args:
            sub_agent_executor: 子Agent执行器（用于处理ask_agent调用，可选）
        """
        super().__init__()
        self.sub_agent_executor = sub_agent_executor
        # 注意：EasyAccounts 工具实例需要在执行时根据Agent的token创建
        self.easyaccounts_tools = None  # 将在执行时初始化
        # 获取所有 EasyAccounts 工具名称
        self.easyaccounts_tool_names = get_tool_names()
    
    async def execute(self, call: Any, context: Dict[str, Any]) -> ExecutionResult:
        """
        执行单个内部工具调用
        
        Args:
            call: 工具调用对象
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        # 从call中提取工具名称
        tool_name = call.get("tool_name") or call.get("function", {}).get("name")
        
        # 目前没有其他内部工具需要处理
        # call_agent 已经在 BaseChatProcessor 中直接路由到 agent_executor
        return self._create_error_result(f"未知的内部工具: {tool_name}")
    
    async def execute_batch(self, tool_calls: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        批量执行内部工具调用
        
        Args:
            tool_calls: 工具调用列表
            context: 执行上下文
            
        Returns:
            执行结果列表
        """
        # 检查递归深度（工具调用额度）
        recursion_depth = context.get("recursion_depth", 0)
        if recursion_depth <= 0:
            self.logger.warning("工具调用额度耗尽，拒绝执行内部工具调用", {
                "conversation_id": context.get("conversation_id"),
                "tool_calls_count": len(tool_calls)
            })
            # 为所有工具调用返回额度用尽的错误
            return [{
                "tool_call_id": tc.get("tool_call_id"),
                "tool_name": tc.get("tool_name"),
                "result": "工具调用额度已用完：本轮对话的工具调用次数已达上限。请根据已有信息完成任务，或告知用户需要分步执行。",
                "success": False
            } for tc in tool_calls]
        
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("tool_name")
            
            # 执行 EasyAccounts 工具
            if tool_name in self.easyaccounts_tool_names:
                result = await self._execute_easyaccounts_tool(tool_call, context)
                results.append(result)
            else:
                # 未知工具
                results.append({
                    "tool_call_id": tool_call.get("tool_call_id"),
                    "tool_name": tool_name,
                    "result": f"未知的内部工具: {tool_name}",
                    "success": False
                })
        
        return results
    
    async def _execute_ask_agent(self, call: Dict[str, Any], context: Dict[str, Any]) -> ExecutionResult:
        """
        执行ask_agent工具调用
        
        Args:
            call: 工具调用信息
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        try:
            # 提取参数
            arguments = call.get("arguments", {})
            agent_id = arguments.get("agent_id")
            task = arguments.get("task")
            agent_context = arguments.get("context", {})
            
            if not agent_id or not task:
                return self._create_error_result("ask_agent缺少必要参数: agent_id 或 task")
            
            # 构建AgentCall对象
            agent_call = AgentCall(
                agent_id=agent_id,
                task=task,
                context=agent_context
            )
            
            # 调用子Agent执行器
            result = await self.sub_agent_executor.execute(agent_call, context)
            
            # 返回执行结果
            return result
            
        except Exception as e:
            self.logger.error("执行ask_agent失败", {
                "error": str(e),
                "call": call
            })
            return self._create_error_result(f"ask_agent执行失败: {str(e)}")
    
    def is_inner_tool(self, tool_name: str) -> bool:
        """
        判断是否为内部工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            是否为内部工具
        """
        # 检查是否为 EasyAccounts 工具
        return tool_name in self.easyaccounts_tool_names
    
    async def _execute_easyaccounts_tool(self, tool_call: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行 EasyAccounts 工具
        
        Args:
            tool_call: 工具调用信息
            context: 执行上下文，包含Agent等信息
            
        Returns:
            执行结果
        """
        tool_name = tool_call.get("tool_name")
        tool_call_id = tool_call.get("tool_call_id")
        arguments = tool_call.get("arguments", {})
        
        # 解析参数（如果是字符串）
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except:
                arguments = {}
        
        try:
            # 从上下文获取Agent和token
            agent = context.get("agent") if context else None
            auth_token = None
            
            if agent and hasattr(agent, 'tool_tokens') and agent.tool_tokens:
                # 从 tool_tokens 中获取 authorization 或其他可能的key
                # 优先使用小写的 authorization
                auth_token = agent.tool_tokens.get("authorization") or \
                           agent.tool_tokens.get("Authorization") or \
                           agent.tool_tokens.get("auth_token") or \
                           agent.tool_tokens.get("token")
                
                if auth_token:
                    self.logger.info(f"EasyAccounts 使用认证token: {auth_token[:20]}..." if len(auth_token) > 20 else f"使用认证token")
            else:
                self.logger.info("EasyAccounts 使用无鉴权模式")
            
            # 创建或更新 EasyAccountsTools 实例
            if not self.easyaccounts_tools or self.easyaccounts_tools.auth_token != auth_token:
                self.easyaccounts_tools = EasyAccountsTools(auth_token=auth_token)
            
            result = None
            
            # 根据工具名称调用对应方法
            if tool_name == "accounts":
                result = await self.easyaccounts_tools.get_accounts()
            elif tool_name == "types":
                result = await self.easyaccounts_tools.get_categories()
            elif tool_name == "current_date":
                result = await self.easyaccounts_tools.get_server_date()
            elif tool_name == "year_statistics":
                year = arguments.get("year")
                if not year:
                    raise ValueError("year_statistics 缺少必要参数: year")
                result = await self.easyaccounts_tools.get_home_info_v2(year)
            elif tool_name == "flows":
                # 提取流水查询参数
                result = await self.easyaccounts_tools.get_flows_by_screen(
                    accountId=arguments.get("accountId"),
                    handle=arguments.get("handle", 3),
                    startDate=arguments.get("startDate"),
                    endDate=arguments.get("endDate"),
                    note=arguments.get("note"),
                    singleMonth=arguments.get("singleMonth"),
                    analysis=arguments.get("analysis"),
                    typeList=arguments.get("types"),
                    orderBy=arguments.get("orderBy")
                )
            elif tool_name == "add_flow":
                # 添加流水记录
                # 检查必填参数
                required = ["accountId", "typeId", "actionId", "money", "fDate"]
                missing = [field for field in required if field not in arguments]
                if missing:
                    raise ValueError(f"add_flow 缺少必要参数: {', '.join(missing)}")
                
                result = await self.easyaccounts_tools.add_flow(
                    accountId=arguments.get("accountId"),
                    typeId=arguments.get("typeId"),
                    actionId=arguments.get("actionId"),
                    money=arguments.get("money"),
                    fDate=arguments.get("fDate"),
                    note=arguments.get("note"),
                    accountToId=arguments.get("accountToId"),
                    collect=arguments.get("collect", False)
                )
            elif tool_name == "update_flow":
                # 更新流水记录
                # 检查必填参数
                required = ["flowId", "accountId", "typeId", "actionId", "money", "fDate"]
                missing = [field for field in required if field not in arguments]
                if missing:
                    raise ValueError(f"update_flow 缺少必要参数: {', '.join(missing)}")
                
                result = await self.easyaccounts_tools.update_flow(
                    flowId=arguments.get("flowId"),
                    accountId=arguments.get("accountId"),
                    typeId=arguments.get("typeId"),
                    actionId=arguments.get("actionId"),
                    money=arguments.get("money"),
                    fDate=arguments.get("fDate"),
                    note=arguments.get("note"),
                    accountToId=arguments.get("accountToId"),
                    collect=arguments.get("collect", False)
                )
            elif tool_name == "make_excel":
                # 生成Excel报表
                # 检查必填参数
                required = ["excelName", "handle"]
                missing = [field for field in required if field not in arguments]
                if missing:
                    raise ValueError(f"make_excel 缺少必要参数: {', '.join(missing)}")
                
                # 与flows参数完全一致，只是多了excelName
                result = await self.easyaccounts_tools.make_excel(
                    excelName=arguments.get("excelName"),
                    accountId=arguments.get("accountId"),
                    handle=arguments.get("handle", 3),
                    startDate=arguments.get("startDate"),
                    endDate=arguments.get("endDate"),
                    note=arguments.get("note"),
                    singleMonth=arguments.get("singleMonth"),
                    typeList=arguments.get("types"),  # 注意：参数名是types
                    collect=arguments.get("collect")
                )
            else:
                result = f"未知的 EasyAccounts 工具: {tool_name}"
                return {
                    "tool_call_id": tool_call_id,
                    "tool_name": tool_name,
                    "result": result,
                    "success": False
                }
            
            self.logger.info(f"EasyAccounts 工具执行成功: {tool_name}")
            return {
                "tool_call_id": tool_call_id,
                "tool_name": tool_name,
                "result": result,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"执行 EasyAccounts 工具失败: {tool_name}", {
                "error": str(e),
                "arguments": arguments
            })
            return {
                "tool_call_id": tool_call_id,
                "tool_name": tool_name,
                "result": f"工具执行失败: {str(e)}",
                "success": False
            }