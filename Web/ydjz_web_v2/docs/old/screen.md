# 筛选页面

## 页面功能描述
高级筛选功能，支持按账户、时间、收支类型、操作、分类等多维度筛选流水，并可生成Excel报表。

## 调用的 API 接口列表

1. **POST** `/screen/getFlowByScreen`
   - 用途：根据条件筛选流水
   - 参数：
     - chooseHandle: 收支类型
     - accountId: 账户ID
     - startDate: 开始日期
     - endDate: 结束日期
     - singleMonth: 是否整月
     - collect: 是否只看收藏
     - types: 分类ID数组
     - actions: 操作ID数组
     - note: 备注关键词
   - 返回：流水列表及统计数据

2. **POST** `/screen/makeExcel?excelName={name}`
   - 用途：生成Excel报表
   - 参数：excelName + 筛选条件
   - 返回：报表生成结果

3. **GET** `/type/getType/noLimit`
   - 用途：获取所有分类（包括停用）
   - 返回：分类树形结构

4. **GET** `/action/getAction`
   - 用途：获取所有操作
   - 返回：操作列表

5. **GET** `/account/getAccountNoLimit`
   - 用途：获取所有账户（包括停用）
   - 返回：账户列表

## 页面数据结构

### 筛选条件
- accountId: 账户ID（-1表示全部）
- accountName: 账户名称
- startDate: 开始日期
- endDate: 结束日期
- singleMonth: 是否整月
- handle: 收支类型（0流入/1流出/2转账/3全部）
- collect: 是否只看收藏
- chooseTypes: 选择的分类ID数组
- chooseActions: 选择的操作ID数组
- note: 备注关键词

### 统计数据
- totalIn: 总收入
- totalOut: 总支出
- totalEarn: 结余

### 流水列表
- flows: 流水数组（结构同flow.md）

### 分类明细
- allTypesMoney: 分类金额列表
  - typeId: 分类ID
  - typeName: 分类名称
  - money: 金额
  - children: 子分类列表

## 主要交互逻辑

### 快速切换
- 单选框快速选择：当月/上月/全年/上年
- 自动设置开始和结束日期
- 自动设置整月标志

### 备注搜索
- 输入关键词
- 点击搜索按钮
- 模糊匹配流水备注

### 详细筛选
- 点击"更多条件"打开详细筛选面板
- 包含以下筛选项：
  - 账户选择
  - 时间选择（开始/结束日期）
  - 是否整月
  - 是否只看收藏
  - 资金流向（全部/流入/流出/转账）
  - 操作选择（多选）
  - 资金分类（树形选择）

### 分类明细
- 点击"查看分类明细"
- 弹出分类汇总数据
- 分一级和二级分类展示
- 显示每个分类的金额合计

### Excel生成
- 点击"生成EXCEL"
- 输入Excel标题
- 确认后根据当前筛选条件生成报表
- 显示生成结果日志

### 流水展示
- 列表展示筛选结果
- 点击流水跳转到编辑页面
- 左滑查看完整备注
- 显示统计信息：总收入/总支出/结余

### 返回顶部
- 滚动时显示返回顶部按钮
- 点击平滑滚动到顶部
