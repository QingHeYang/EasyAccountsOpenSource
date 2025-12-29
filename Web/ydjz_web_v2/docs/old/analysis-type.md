# 单项分类统计页面

## 页面功能描述
查看单个分类的详细统计信息，按年份和月份展示收支明细。

## 调用的 API 接口列表

1. **GET** `/type/getType`
   - 用途：获取所有分类列表
   - 返回：分类树形结构

2. **POST** `/analysis/v2/getAnalysisTypeMonthData`
   - 用途：获取指定分类的月度数据
   - 参数：
     - typeId: 分类ID
     - start: 开始日期
     - end: 结束日期
   - 返回：按年份和月份组织的收支数据

3. **POST** `/screen/getFlowByScreen`
   - 用途：获取指定月份的流水明细
   - 参数：
     - accountId: 账户ID
     - chooseHandle: 收支类型
     - startDate: 开始日期
     - singleMonth: 是否单月
     - types: 分类ID列表
   - 返回：流水列表

## 页面数据结构

### 分类信息
- chooseType: 选择的分类
  - id: 分类ID
  - tname: 分类名称
  - action: 收支类型

### 统计数据
- typeData: 分类统计数据
  - totalIncome: 总收入
  - totalOutcome: 总支出
  - yearData: 年度数据列表
    - year: 年份
    - income: 年收入
    - outcome: 年支出
    - monthData: 月度数据列表

### 流水数据
- flows: 流水列表
- clickTitle: 点击的月份标题

## 主要交互逻辑

### 分类选择
- 点击"选择分类"弹出级联选择器
- 支持一级和二级分类选择
- 选择后显示分类名称和收支类型标签

### 时间筛选
- 快速选择：近一年、今年、上年
- 自定义：选择时间段
- 时间范围验证

### 数据展示
- 按年份折叠展示
- 每年显示总收入和总支出
- 月份数据显示当月收入或支出
- 空数据时显示提示

### 明细查看
- 点击月份数据查看该月流水明细
- 弹出流水列表对话框
- 显示流水的日期、分类、金额、备注等信息
- 支持图片标识和AI来源标识
