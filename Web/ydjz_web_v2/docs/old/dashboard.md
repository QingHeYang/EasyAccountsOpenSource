# 总览页面（首页）

## 页面功能描述
显示资产总览、年度收支概况和月度明细，是应用的主页面。

## 调用的 API 接口列表

1. **GET** `/home/getHomeInfoV2/{year}`
   - 用途：获取指定年份的首页信息
   - 参数：year（年份）
   - 返回：
     - 总资产、净资产
     - 年度收入、支出、结余
     - 月度明细列表
     - 账户列表

## 页面数据结构

### 资产信息
- homeInfo:
  - totalAsset: 总资产
  - netAsset: 净资产
  - yearIncome: 年度总收入
  - yearOutCome: 年度总支出
  - yearBalance: 年度结余

### 月度明细
- monthDetails: 月度明细列表
  - month: 月份
  - income: 收入
  - outcome: 支出
  - balance: 结余

### 账户信息
- accounts: 账户列表
  - accountName: 账户名称
  - accountAsset: 账户资产
  - exemptAsset: 豁免资产
  - realAsset: 净资产（计算得出）
  - note: 备注

### 年份选择
- chooseYear: 选择的年份
- yearList: 年份列表（2021年至今）

## 主要交互逻辑

### 年份切换
- 使用左右按钮切换年份
- 点击年份按钮弹出选择器
- 年份限制：最早2021年，最晚当前年份

### 账户详情
- 点击"账户详情"查看所有账户
- 显示账户余额和净资产
- 点击账户跳转到筛选页面查看该账户明细

### 月度明细
- 表格展示每月收支情况
- 点击月份跳转到流水页面
- 收入显示绿色，支出显示红色

### AI助手入口
- 浮动按钮"AI+"
- 点击跳转到AI助手页面
- 支持拖拽调整位置
