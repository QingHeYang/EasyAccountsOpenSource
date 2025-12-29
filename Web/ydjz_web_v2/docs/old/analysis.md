# 财务分析页面

## 页面功能描述
财务数据同比和环比分析，展示不同周期的收支增长情况。

## 调用的 API 接口列表

1. **GET** `/analysis/doAnalysis`
   - 用途：获取分析数据
   - 参数：start（开始日期），end（结束日期）
   - 返回：同比、环比数据列表

2. **GET** `/analysis/exportExcel`
   - 用途：生成财务分析报表
   - 参数：start（开始日期），end（结束日期）
   - 返回：报表生成结果

## 页面数据结构

### 选择条件
- fastChoose: 快速选择（当月/上月/全年/上年/自定义）
- startChooseMonth: 开始月份
- endChooseMonth: 结束月份

### 分析数据
- yoyList: 同比数据列表
  - name: 分类名称
  - money: 当期金额
  - compareMoney: 同比金额
  - compareIncrease: 同比增量
  - compareRate: 增长率
- momList: 环比数据列表（结构同上）
- currentCircle: 当前周期
- yoyCircle: 同比周期
- momCircle: 环比周期

## 主要交互逻辑

### 时间选择
- 快速选择：当月、上月、全年、上年
- 自定义：选择开始和结束月份
- 日期范围限制：结束日期不能早于开始日期

### 数据展示
- 分别展示同比和环比数据
- 表格形式展示分类、金额、增量、增速
- 空数据时显示提示

### 报表生成
- 点击生成当期报表
- 确认后调用接口生成 Excel
- 生成失败时显示错误提示
