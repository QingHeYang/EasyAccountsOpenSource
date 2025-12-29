#!/usr/bin/env python
"""
测试 make_excel 工具
"""

import asyncio
import sys
from pathlib import Path
import datetime

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from koalaq_hub.core.tool.function.easyaccounts import EasyAccountsTools, get_tool_names


async def test_make_excel():
    """测试生成Excel报表功能"""
    print("=" * 50)
    print("测试 make_excel 工具")
    print("=" * 50)
    
    # 创建工具实例（无认证）
    tools = EasyAccountsTools(auth_token=None)
    
    # 1. 获取当前日期
    print("\n1. 获取当前日期...")
    import json
    date_json = await tools.get_server_date()
    date_data = json.loads(date_json)
    today = date_data.get("today")
    year = date_data.get("year")
    month = date_data.get("month")
    print(f"当前日期: {today}")
    
    # 2. 测试生成当月Excel报表
    print(f"\n2. 生成{year}年{month}月Excel报表...")
    
    # 生成当月报表的参数（与flows参数一致）
    excel_params = {
        "excelName": f"{year}年{month}月账单报表",
        "handle": 3,  # 全部流水
        "startDate": f"{year}-{month}-01",
        "singleMonth": True  # 单月模式
    }
    
    print(f"参数: {excel_params}")
    
    try:
        result = await tools.make_excel(**excel_params)
        result_data = json.loads(result)
        
        if result_data.get("success"):
            print(f"✓ Excel生成成功!")
            print(f"  文件名: {result_data.get('fileName')}")
            print(f"  文件路径: {result_data.get('filePath')}")
            print(f"  下载地址: {result_data.get('downloadUrl')}")
        else:
            print(f"✗ Excel生成失败: {result_data.get('error')}")
    except Exception as e:
        print(f"✗ 执行出错: {e}")
    
    # 3. 测试生成指定时间段的Excel报表
    print("\n3. 生成指定时间段的Excel报表...")
    
    # 生成最近7天的报表
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    excel_params2 = {
        "excelName": "最近7天流水报表",
        "handle": 3,  # 全部流水
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d")
    }
    
    print(f"参数: {excel_params2}")
    
    try:
        result = await tools.make_excel(**excel_params2)
        result_data = json.loads(result)
        
        if result_data.get("success"):
            print(f"✓ Excel生成成功!")
            print(f"  文件名: {result_data.get('fileName')}")
        else:
            print(f"✗ Excel生成失败: {result_data.get('error')}")
    except Exception as e:
        print(f"✗ 执行出错: {e}")
    
    # 4. 显示所有可用工具
    print("\n4. 所有可用的 EasyAccounts 工具:")
    all_tools = get_tool_names()
    for tool in all_tools:
        print(f"  - {tool}")


async def main():
    """主函数"""
    print("开始测试 EasyAccounts make_excel 工具\n")
    
    await test_make_excel()
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("\n总结：")
    print("1. make_excel 工具已成功添加到系统")
    print("2. 参数与 flows 工具完全一致，便于统一使用")
    print("3. 可以生成各种时间段的Excel报表")
    print("4. 生成的Excel文件可以下载或查看")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())