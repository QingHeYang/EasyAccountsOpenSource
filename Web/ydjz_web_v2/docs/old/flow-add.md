# 账单新增/编辑页面

## 页面功能描述
新增或编辑账单流水，支持图片上传、快记模板、追加分账单等功能。

## 调用的 API 接口列表

### 流水相关
1. **GET** `/flow/getFlow/{flowId}`
   - 用途：获取流水详情（编辑时）
   - 参数：flowId
   - 返回：流水完整信息

2. **POST** `/flow/addFlow`
   - 用途：新增流水
   - 参数：流水完整信息
   - 返回：操作结果

3. **PUT** `/flow/updateFlow/{flowId}`
   - 用途：更新流水
   - 参数：flowId + 流水信息
   - 返回：操作结果

### 基础数据
4. **GET** `/action/getAction`
   - 用途：获取所有收支类型
   - 返回：收支类型列表

5. **GET** `/account/getAccount`
   - 用途：获取所有账户
   - 返回：账户列表

6. **GET** `/type/getTypeByActionId/{actionId}`
   - 用途：根据收支类型获取分类
   - 参数：actionId
   - 返回：分类树形结构

### 模板相关
7. **GET** `/tag/getTags`
   - 用途：获取所有标签
   - 返回：标签列表

8. **GET** `/template/getAllTemplates`
   - 用途：获取所有模板
   - 返回：模板列表

9. **GET** `/template/getAllTemplatesByTag/{tagId}`
   - 用途：根据标签获取模板
   - 参数：tagId
   - 返回：模板列表

### 图片相关
10. **POST** `/image/upload`
    - 用途：上传图片
    - 参数：FormData（file）
    - 返回：文件名

## 页面数据结构

### 账单基本信息
- money: 账单金额
- chooseAction: 选择的收支类型
- chooseAccount: 选择的账户
- chooseToAccount: 目标账户（转账时）
- chooseType: 选择的分类
- chooseDate: 账单日期
- isCollect: 是否收藏
- note: 备注

### 追加账单
- childMoneyItem: 追加账单列表
  - index: 索引
  - money: 金额
  - note: 备注

### 图片上传
- fileList: 图片文件列表
  - url: 图片URL
  - status: 状态（uploading/done/failed）
  - serverFileName: 服务器文件名

### 快记模板
- allTemplates: 模板列表
- allTags: 标签列表
- chooseTag: 选择的标签
- chooseTemplate: 选择的模板

## 主要交互逻辑

### 表单填写
- 金额输入：自动格式化为两位小数
- 收支类型选择：弹出操作列表
- 账户选择：弹出账户列表
- 分类选择：级联选择器
- 日期选择：日历组件
- 备注输入：多行文本域

### 追加分账单
- 点击"追加分账单"添加新项
- 每项独立设置金额和备注
- 左滑删除追加项
- 提交时自动计算总金额

### 图片上传
- 支持多图上传（最多3张）
- 上传前压缩图片：
  - 最大尺寸：1920x1920
  - 质量：80%
  - 最大大小：2MB
- 显示上传进度
- 点击预览大图
- 长按删除图片
- 编辑时加载已有图片

### 快记模板
- 点击"快记模板"打开模板面板
- 标签筛选：按标签过滤模板
- 模板列表：网格展示
- 点击模板：自动填充表单
- 模板详情：查看完整信息
- 跳转模板管理页面

### 数据验证
- 金额必填
- 收支类型必选
- 账户必选
- 转账时目标账户必选
- 分类必选
- 日期必选

### 提交确认
- 分类收支类型不匹配时弹出确认
- 追加账单时显示总金额确认
- 确认后提交数据
- 成功后返回上一页
