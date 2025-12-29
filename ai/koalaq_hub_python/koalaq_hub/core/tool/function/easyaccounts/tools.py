"""
EasyAccounts 工具实现
从 MCP server.py 迁移的工具函数
"""

import json
import datetime
from typing import Any, Dict, List, Optional
import httpx
from .....config.settings import config
from ....logging_utils import ManagerLogger


class EasyAccountsTools:
    """EasyAccounts 内部工具实现类"""
    
    # EasyAccounts API 基础URL（从配置文件读取）
    BASE_URL = config.easyaccounts_url
    # API 端点
    ACCOUNTS_URL = f"{BASE_URL}/account/getAccount"
    TYPES_URL = f"{BASE_URL}/type/getType"
    HOME_INFO_URL = f"{BASE_URL}/home/getHomeInfoV2/"
    FLOW_URL = f"{BASE_URL}/screen/getFlowByScreen"
    ADD_FLOW_URL = f"{BASE_URL}/flow/addFlow"
    UPDATE_FLOW_URL = f"{BASE_URL}/flow/updateFlow"
    MAKE_EXCEL_URL = f"{BASE_URL}/screen/makeExcel"
    
    def __init__(self, auth_token: Optional[str] = None):
        """初始化工具类
        
        Args:
            auth_token: 可选的认证token，如果为None则不添加认证头
        """
        self.logger = ManagerLogger("EasyAccountsTools")
        self.auth_token = auth_token
    
    async def get_accounts(self) -> str:
        """
        查询用户资金账户
        
        Returns:
            JSON字符串，包含账户列表
        """
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient() as client:
                response = await client.get(self.ACCOUNTS_URL, headers=headers)
                
                # 检查401错误
                if response.status_code == 401:
                    self.logger.warning("获取账户列表遇到401认证错误")
                    return self._handle_auth_error(response.text)
                
                accounts = response.json()
                self.logger.info(f"获取账户列表成功: {len(accounts) if isinstance(accounts, list) else 0}个账户")
                return json.dumps(accounts, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"获取账户列表失败: {e}")
            return json.dumps({"error": f"获取账户失败: {str(e)}"}, ensure_ascii=False)
    
    async def get_categories(self) -> str:
        """
        获取所有账单分类（标签）信息
        
        Returns:
            JSON字符串，包含分类层级结构
        """
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient() as client:
                response = await client.get(self.TYPES_URL, headers=headers)
                
                # 检查401错误
                if response.status_code == 401:
                    self.logger.warning("获取分类列表遇到401认证错误")
                    return self._handle_auth_error(response.text)
                
                raw = response.json()
                
                # 处理标准响应格式 {"code": 0, "msg": "Success", "data": [...]}
                if isinstance(raw, dict) and "data" in raw:
                    data = raw.get("data", [])
                else:
                    # 兼容直接返回数组的情况
                    data = raw if isinstance(raw, list) else []
                
                def format_desc(cat):
                    action = cat.get("action")
                    if action:
                        # 明确显示actionId，避免混淆
                        return (f"id={cat.get('id')},name={cat.get('tname')},"
                               f"actionId={action.get('id')},handle={action.get('handle')},handleName={action.get('hname')}")
                    else:
                        # 当action为null时（如父分类），不包含action信息
                        return f"id={cat.get('id')},name={cat.get('tname')},actionId=null"
                
                result = []
                for cat in data:
                    desc = format_desc(cat)
                    children = []
                    for child in cat.get("childrenTypes") or []:
                        children.append(format_desc(child))
                    result.append({
                        "description": desc,
                        "children": children
                    })
                
                self.logger.info(f"获取分类成功: {len(result)}个顶级分类")
                return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"获取分类失败: {e}")
            return json.dumps({"error": f"获取分类失败: {str(e)}"}, ensure_ascii=False)
    
    async def get_server_date(self) -> str:
        """
        获取当前服务器时间
        
        Returns:
            JSON字符串，包含日期信息
        """
        try:
            now = datetime.datetime.now()
            today = now.strftime("%Y-%m-%d")
            year = now.strftime("%Y")
            month = now.strftime("%m")
            day = now.strftime("%d")
            week = now.strftime("%w")
            
            json_data = {
                "today": today,
                "year": year,
                "month": month,
                "day": day,
                "week": week
            }
            
            self.logger.info(f"获取当前日期: {today}")
            return json.dumps(json_data, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"获取日期失败: {e}")
            return json.dumps({"error": f"获取日期失败: {str(e)}"}, ensure_ascii=False)
    
    async def get_home_info_v2(self, year: int) -> str:
        """
        获取年度统计信息
        
        Args:
            year: 年份
            
        Returns:
            JSON字符串，包含年度统计数据
        """
        try:
            url = f"{self.HOME_INFO_URL}{year}"
            headers = self._build_headers()
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                
                # 检查401错误
                if response.status_code == 401:
                    self.logger.warning(f"获取{year}年统计信息遇到401认证错误")
                    return self._handle_auth_error(response.text)
                
                home_info = response.json()
                self.logger.info(f"获取{year}年统计信息成功")
                return json.dumps(home_info, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"获取年度统计失败: {e}")
            return json.dumps({"error": f"获取年度统计失败: {str(e)}"}, ensure_ascii=False)
    
    async def get_flows_by_screen(
        self,
        accountId: Optional[int] = None,
        handle: Optional[int] = None,
        endDate: Optional[str] = None,
        note: Optional[str] = None,
        singleMonth: Optional[bool] = None,
        analysis: Optional[bool] = None,
        startDate: Optional[str] = None,
        typeList: Optional[List[int]] = None,
        orderBy: Optional[int] = None
    ) -> str:
        """
        根据条件查询流水
        
        Args:
            accountId: 账户ID
            handle: 收支类型 (0收入,1支出,2内部转账,3全部)
            endDate: 结束日期
            note: 备注关键字
            singleMonth: 是否单月查询
            analysis: 是否分析占比
            startDate: 开始日期
            typeList: 分类ID列表
            orderBy: 排序方式 (0金额升序,1金额降序,2时间排序)
            
        Returns:
            JSON字符串，包含流水列表和汇总信息
        """
        try:
            # 参数验证
            if handle is not None and (int(handle) > 3 or int(handle) < 0):
                raise ValueError("handle 参数错误，请传入0-3之间的整数")
            
            # 构建请求头
            headers = self._build_headers(content_type="application/json")
            
            # 构建请求体
            payload = {
                "accountId": accountId,
                "actions": [],
                "chooseHandle": handle,
                "collect": "false",
                "endDate": endDate,
                "note": note,
                "singleMonth": singleMonth,
                "startDate": startDate,
                "types": typeList,
            }
            
            # 移除为None的字段
            payload = {k: v for k, v in payload.items() if v is not None}
            
            async with httpx.AsyncClient() as client:
                self.logger.info(f"查询流水，参数: {payload}")
                response = await client.post(self.FLOW_URL, headers=headers, json=payload)
                
                # 检查401错误
                if response.status_code == 401:
                    self.logger.warning("查询流水遇到401认证错误")
                    return self._handle_auth_error(response.text)
                
                flows_data = response.json()
                
                # 提取数据
                data = flows_data.get("data", {})
                totalIn = data.get("totalIn", "0")
                totalOut = data.get("totalOut", "0")
                totalEarn = data.get("totalEarn", "0")
                flows = data.get("flows", [])
                total_count = len(flows)
                
                flows_description = f"当期：收入={totalIn},支出={totalOut},盈余={totalEarn}"
                self.logger.info(f"流水查询成功: {flows_description}, 共{total_count}条")
                
                # 排序处理
                if orderBy == 0:
                    flows.sort(key=lambda x: float(x.get("money", 0)))
                elif orderBy == 1:
                    flows.sort(key=lambda x: float(x.get("money", 0)), reverse=True)
                
                # 限制返回数量
                MAX_FLOWS = 100
                is_truncated = False
                truncation_message = ""
                
                if total_count > MAX_FLOWS:
                    is_truncated = True
                    flows = flows[:MAX_FLOWS]
                    truncation_message = (
                        f"\n\n⚠️ 注意：查询结果共有 {total_count} 条流水记录，"
                        f"由于上下文限制，仅返回前 {MAX_FLOWS} 条。\n"
                        f"建议您使用 make_excel 工具生成完整的Excel报表进行查看。\n"
                        f"非常抱歉给您带来不便。"
                    )
                    self.logger.warning(f"流水数量超过限制，截断至{MAX_FLOWS}条（总计{total_count}条）")
                
                flows_list = []
                
                # 处理每条流水
                for flow in flows:
                    percentStr = ""
                    if analysis:
                        # 计算百分比
                        moneyFloat = float(flow.get("money", 0))
                        if handle == 0 and float(totalIn) > 0:
                            percent = moneyFloat / float(totalIn) * 100
                            percentStr = f"收入占比:{percent:.2f}%"
                        elif handle == 1 and float(totalOut) > 0:
                            percent = moneyFloat / float(totalOut) * 100
                            percentStr = f"支出占比:{percent:.2f}%"
                    
                    parts = [
                        f"流水ID:{flow.get('id')}",
                        f"流水收支:{flow.get('hname')}",
                        f"流水金额:{flow.get('money')}",
                        f"流水账户:{flow.get('aname')}",
                        f"流水分类:{flow.get('tname')}",
                        f"流水时间:{flow.get('fdate')}",
                        percentStr
                    ]
                    
                    toAName = flow.get('toAName')
                    if toAName:
                        parts.append(f"转到账户:{toAName}")
                    
                    note = flow.get('note')
                    parts.append(f"备注:{note}")
                    flows_list.append(";".join(parts))
                
                result = {
                    "flows_description": flows_description,
                    "flows": flows_list,
                    "total_count": total_count,
                    "returned_count": len(flows_list),
                    "is_truncated": is_truncated
                }
                
                # 如果有截断，添加提示信息
                if truncation_message:
                    result["notice"] = truncation_message
                
                return json.dumps(result, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"查询流水失败: {e}")
            return json.dumps({"error": f"查询流水失败: {str(e)}"}, ensure_ascii=False)
    
    def _build_headers(self, content_type: Optional[str] = None) -> Dict[str, str]:
        """
        构建请求头
        
        Args:
            content_type: 可选的Content-Type
            
        Returns:
            请求头字典
        """
        headers = {}
        
        # 如果有auth_token，添加authorization头（小写，无Bearer前缀）
        if self.auth_token:
            headers["authorization"] = self.auth_token
            self.logger.debug(f"使用认证token: {self.auth_token[:20]}..." if len(self.auth_token) > 20 else f"使用认证token: {self.auth_token}")
        else:
            self.logger.debug("未配置认证token，使用无鉴权模式")
        
        # 如果指定了Content-Type，添加
        if content_type:
            headers["Content-Type"] = content_type
        
        return headers
    
    def _handle_auth_error(self, response_text: str) -> str:
        """
        处理401认证错误
        
        Args:
            response_text: 响应内容
            
        Returns:
            包含错误信息和指导的JSON字符串
        """
        auth_error_msg = {
            "error": "认证失败",
            "status": 401,
            "message": "EasyAccounts系统已开启登录鉴权",
            "guidance": "请先在EasyAccounts网页端登录，然后重新连接AI对话",
            "steps": [
                "1. 访问EasyAccounts网页端",
                "2. 使用用户名和密码登录",
                "3. 登录成功后，重新开始AI对话",
                "4. 系统会自动获取您的认证token"
            ],
            "original_response": response_text
        }
        return json.dumps(auth_error_msg, ensure_ascii=False)
    
    async def add_flow(
        self,
        accountId: int,
        typeId: int,
        actionId: int,
        money: str,
        fDate: str,
        note: Optional[str] = None,
        accountToId: Optional[int] = None,
        collect: bool = False
    ) -> str:
        """
        添加流水记录
        
        Args:
            accountId: 账户ID
            typeId: 分类ID
            actionId: 收支类型ID
            money: 金额
            fDate: 流水日期 (yyyy-MM-dd)
            note: 备注
            accountToId: 转入账户ID（转账时使用）
            collect: 是否收藏
            
        Returns:
            JSON字符串，包含操作结果
        """
        try:
            # 构建请求体
            payload = {
                "accountId": accountId,
                "typeId": typeId,
                "actionId": actionId,
                "money": money,
                "fDate": fDate,
                "collect": collect
            }
            
            # 添加可选字段
            if note:
                payload["note"] = note
            if accountToId is not None:
                payload["accountToId"] = accountToId
            
            # 获取当前时间作为创建时间
            payload["createDate"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 添加来源标记，表示这是AI创建的流水
            payload["from"] = "ai"
            
            # 构建请求头
            headers = self._build_headers(content_type="application/json")
            
            async with httpx.AsyncClient() as client:
                self.logger.info(f"添加流水，参数: {payload}")
                response = await client.post(self.ADD_FLOW_URL, headers=headers, json=payload)
                
                # 检查响应状态
                if response.status_code == 200:
                    result = response.json()
                    self.logger.info(f"流水添加成功")
                    return json.dumps({
                        "success": True,
                        "message": "流水添加成功",
                        "data": result
                    }, ensure_ascii=False)
                elif response.status_code == 401:
                    self.logger.warning("添加流水遇到401认证错误")
                    return self._handle_auth_error(response.text)
                else:
                    try:
                        result = response.json()
                        error_msg = result.get('msg', '未知错误')
                    except:
                        error_msg = response.text
                    self.logger.error(f"添加流水失败: {response.status_code} - {error_msg}")
                    return json.dumps({
                        "success": False,
                        "error": f"添加流水失败: {error_msg}"
                    }, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"添加流水出错: {e}")
            return json.dumps({"error": f"添加流水失败: {str(e)}"}, ensure_ascii=False)
    
    async def update_flow(
        self,
        flowId: int,
        accountId: int,
        typeId: int,
        actionId: int,
        money: str,
        fDate: str,
        note: Optional[str] = None,
        accountToId: Optional[int] = None,
        collect: bool = False
    ) -> str:
        """
        更新流水记录
        
        Args:
            flowId: 流水ID
            accountId: 账户ID
            typeId: 分类ID
            actionId: 收支类型ID
            money: 金额
            fDate: 流水日期 (yyyy-MM-dd)
            note: 备注
            accountToId: 转入账户ID（转账时使用）
            collect: 是否收藏
            
        Returns:
            JSON字符串，包含操作结果
        """
        try:
            # 构建请求体
            payload = {
                "accountId": accountId,
                "typeId": typeId,
                "actionId": actionId,
                "money": money,
                "fDate": fDate,
                "collect": collect
            }
            
            # 添加可选字段
            if note:
                payload["note"] = note
            if accountToId is not None:
                payload["accountToId"] = accountToId
            
            # 获取当前时间作为创建时间
            payload["createDate"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 添加来源标记，表示这是AI更新的流水
            payload["from"] = "ai"
            
            # 构建请求URL
            url = f"{self.UPDATE_FLOW_URL}/{flowId}"
            
            # 构建请求头
            headers = self._build_headers(content_type="application/json")
            
            async with httpx.AsyncClient() as client:
                self.logger.info(f"更新流水ID={flowId}，参数: {payload}")
                response = await client.put(url, headers=headers, json=payload)
                
                # 检查响应状态
                if response.status_code == 200:
                    result = response.json()
                    self.logger.info(f"流水更新成功: ID={flowId}")
                    return json.dumps({
                        "success": True,
                        "message": f"流水ID={flowId}更新成功",
                        "data": result
                    }, ensure_ascii=False)
                elif response.status_code == 401:
                    self.logger.warning(f"更新流水ID={flowId}遇到401认证错误")
                    return self._handle_auth_error(response.text)
                else:
                    try:
                        result = response.json()
                        error_msg = result.get('msg', '未知错误')
                    except:
                        error_msg = response.text
                    self.logger.error(f"更新流水失败: {response.status_code} - {error_msg}")
                    return json.dumps({
                        "success": False,
                        "error": f"更新流水失败: {error_msg}"
                    }, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"更新流水出错: {e}")
            return json.dumps({"error": f"更新流水失败: {str(e)}"}, ensure_ascii=False)
    
    async def make_excel(
        self,
        excelName: str,
        accountId: Optional[int] = None,
        handle: Optional[int] = 3,
        endDate: Optional[str] = None,
        note: Optional[str] = None,
        singleMonth: Optional[bool] = None,
        startDate: Optional[str] = None,
        typeList: Optional[List[int]] = None,
        collect: Optional[bool] = None
    ) -> str:
        """
        根据条件生成Excel报表
        参数与get_flows_by_screen完全一致，只是输出为Excel文件
        
        Args:
            excelName: Excel文件名称（不含扩展名）
            accountId: 账户ID
            handle: 收支类型 (0收入,1支出,2内部转账,3全部)
            endDate: 结束日期
            note: 备注关键字
            singleMonth: 是否单月查询
            startDate: 开始日期
            typeList: 分类ID列表
            collect: 是否只导出收藏的流水
            
        Returns:
            JSON字符串，包含Excel文件信息
        """
        try:
            # 参数验证
            if handle is not None and (int(handle) > 3 or int(handle) < 0):
                raise ValueError("handle 参数错误，请传入0-3之间的整数")
            
            # 构建请求头
            headers = self._build_headers(content_type="application/json")
            
            # 构建请求体（与flows查询参数一致）
            payload = {
                "accountId": accountId,
                "actions": [],
                "chooseHandle": handle,
                "endDate": endDate,
                "note": note,
                "singleMonth": singleMonth,
                "startDate": startDate,
                "types": typeList,
            }
            
            # 添加collect参数（如果指定）
            if collect is not None:
                payload["collect"] = str(collect).lower()
            else:
                payload["collect"] = "false"
            
            # 移除为None的字段
            payload = {k: v for k, v in payload.items() if v is not None}
            
            # 构建请求URL，添加excelName查询参数
            url = f"{self.MAKE_EXCEL_URL}?excelName={excelName}"
            
            async with httpx.AsyncClient() as client:
                self.logger.info(f"生成Excel，文件名: {excelName}, 参数: {payload}")
                response = await client.post(url, headers=headers, json=payload)
                
                # 检查响应状态
                if response.status_code == 200:
                    result = response.json()
                    # 提取Excel文件信息
                    data = result.get("data", {})
                    file_name = data.get("fileName", f"{excelName}.xlsx")
                    file_path = data.get("filePath", "")
                    download_url = data.get("downloadUrl", "")
                    
                    self.logger.info(f"Excel生成成功: {file_name}")
                    
                    return json.dumps({
                        "success": True,
                        "message": f"Excel报表生成成功",
                        "fileName": file_name,
                        "filePath": file_path,
                        "downloadUrl": download_url,
                        "data": result
                    }, ensure_ascii=False)
                elif response.status_code == 401:
                    self.logger.warning("生成Excel遇到401认证错误")
                    return self._handle_auth_error(response.text)
                else:
                    try:
                        result = response.json()
                        error_msg = result.get('msg', '未知错误')
                    except:
                        error_msg = response.text
                    self.logger.error(f"生成Excel失败: {response.status_code} - {error_msg}")
                    return json.dumps({
                        "success": False,
                        "error": f"生成Excel失败: {error_msg}"
                    }, ensure_ascii=False)
                    
        except Exception as e:
            self.logger.error(f"生成Excel出错: {e}")
            return json.dumps({"error": f"生成Excel失败: {str(e)}"}, ensure_ascii=False)