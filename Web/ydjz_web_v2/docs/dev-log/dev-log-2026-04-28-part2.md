# 开发日志 - 2026年4月28日（part2）

> 同日续篇。上一篇 `dev-log-2026-04-28.md` 是 v2.7.0 系统配置 UI 化的总结，本篇是当天后续，一波"普通用户能感知的小功能"的迭代。

## 今日开发概述

1. **登录页接入浏览器密码管理器**：双端 Auth 加 `autocomplete="username"` + `current-password`/`new-password`，让 Chrome / Edge / OS 钥匙串能识别表单 → 抛弃自研"记住密码"
2. **PC 端 FlowList 日趋势图**：右侧面板加 sparkline 折线 + 点击展开大图柱状弹窗，支持切月切年切类型
3. **趋势图收入支出同时显示**：扩展 chartType `outcome | income | both`
4. **PC 端右侧卡片可拖排序**：4 张卡片（统计 / 趋势 / 日历 / 筛选）用 sortablejs 拖动，月份卡固定不参与
5. **新增共享 storage 工具**：`shared/utils/storage.ts`，统一封装 localStorage（双端可用）
6. **移动端日趋势横屏 overlay**：顶部加柱状图按钮 → 全屏 rotate(90deg) 横屏看图，复用 `YearLineChartOverlay` 形式

---

## 文件变更统计

```
src/desktop/views/Auth.vue                                 | 改造表单（autocomplete + form submit）
src/mobile/views/Auth.vue                                  | 改造表单（autocomplete）
src/desktop/components/flow/DayTrendSparkline.vue          | 新建（~210 行）
src/desktop/components/flow/DayTrendDialog.vue             | 新建（~310 行）
src/desktop/views/flow/FlowList.vue                        | 集成 sparkline + dialog + 拖拽 + dayData
src/mobile/components/flow/DayTrendOverlay.vue             | 新建（~410 行）
src/mobile/views/Flow.vue                                  | 集成 overlay + 顶部柱状图按钮 + dayData
src/shared/utils/storage.ts                                | 新建（双端共享）
package.json                                               | + sortablejs / sortablejs-vue3 / @types/sortablejs
```

---

## 今日开发内容

### 1. 登录页接入浏览器密码管理器

#### 背景
用户提出"做记住密码功能"。讨论后达成共识：现代浏览器（Chrome / Edge / Safari）的密码管理器已经做得比自研版本更好（OS 级加密、跨站统一、跨设备同步），自研只能用 localStorage 存（明文/混淆），安全性反而更差。

最终方案：**不做自研记住密码，把表单改造成浏览器密码管理器能正确识别的形态**。

#### 改造点

桌面端 `desktop/views/Auth.vue`：
- `el-form` 改用 `@submit.prevent="onSubmit"`（取代手写 keydown Enter 处理）
- 登录按钮改为 `native-type="submit"`
- username 输入框加 `name="username"` + `autocomplete="username"`
- password 输入框加 `name="password"` + `:autocomplete="passwordAutocomplete"`
- `passwordAutocomplete` 跟随 `isLogin`：登录时 `current-password`，注册时 `new-password`

移动端 `mobile/views/Auth.vue`：
- `van-field` 加同样的 `autocomplete`（vant 4 透传到底层 input）
- van-form 已经是 native submit，不用改

#### 用户能感受到什么
- 首次登录/注册成功后，浏览器/系统钥匙串弹"是否保存这个网站的密码"
- 下次进登录页自动填账号 + 密码 → 点登录就行
- 注册时浏览器不会误填旧密码（new-password 语义）
- 整个流程密码不经过我们自己的 localStorage，安全性靠浏览器/OS 兜底

---

### 2. PC 端 FlowList 日支出/收入趋势图

#### 需求
用户："想对每日花销有严格管控，看单月日支出 + 变化趋势"。

#### 关键设计决策（用户拍板）
| 维度 | 决策 |
|---|---|
| 端 | 仅 PC 端（移动端单独做横屏 overlay） |
| 放置 | FlowList 右侧面板，日历卡上方 |
| 外面 sparkline | 纯线条 + 浅色填充，无 X 轴标签 / grid，tooltip 极简 |
| 弹窗大图 | 800px 居中 dialog，参考 YearLineChartDialog |
| 大图图形 | **柱状图**（产品讨论后从折线改成柱状：每日支出本质是离散事件，柱状更主流） |
| 切月/年联动 | **甲方案** — 触发整页 FlowList 切月（数据重拉、列表/日历/汇总全变） |
| 切收入/支出联动 | **乙方案** — 仅图表本身，不动列表 handleType 筛选 |
| 没记账的天 | null（柱状图自然空白，无视觉负担） |
| 未来日期 | 横轴只到今天，不画 |
| 转账 + exempt | 不计入（与后端 totalIn/Out 对齐） |

#### 数据流
```
FlowList.flowData (受 handleType 筛选)
        ↘
FlowList.chartFlowData (始终 handleType=3 全量) ← 关键独立数据源
        ↓ (computed)
dayData = [{ day, date, income | null, outcome | null }]
        ↓ (props)
        ├── DayTrendSparkline (右侧面板，常驻)
        └── DayTrendDialog (点击 sparkline 弹出)
                ↓ emit
                ├── update:month → FlowList.chooseMonth → fetchFlows + 整页联动
                └── update:chartType → 双向绑定（sparkline / dialog 同步）
```

**性能优化**：handleType=3 时 `chartFlowData` 直接复用 `flowData`（0 额外请求）；其它 handleType 时并行多发一次 `getMonthList(3, ...)` 拉全量给图表。这样列表筛选期间图表也能保持完整数据。

#### 暗黑模式
- 两个组件都用 `themeStore.effectiveTheme` 触发 watch 重绘图表
- ECharts 配色根据 `isDark()` 切换（红 #FF6B6B / #F5222D，绿 #69DB7C / #52C41A）

#### 一个 tooltip 配色坑
sparkline 的 series 我只给了 `lineStyle.color`（线对了），但 tooltip 的圆点 marker 取的是 `itemStyle.color`，没设就 fallback 到 ECharts 默认色板（蓝 #5470c6 / 绿 #91cc75）。所以 hover 时 tooltip 出现"蓝色 + 绿色"的小圆点（跟支出红 / 收入绿不符）。

修复：buildLineSeries 加 `itemStyle: { color }`，跟 lineStyle 同色。柱状图因为 itemStyle.color 是渐变对象，ECharts 自动取 colorStops[0]，没这个问题。

---

### 3. 收入支出同时显示（both 模式）

#### 改动
- `chartType` 类型从 `'outcome' | 'income'` 扩展为 `'outcome' | 'income' | 'both'`
- Sparkline 在 both 模式下生成两条 series（双折线，红 + 绿，tooltip 同时显示两个值）
- Dialog 在 both 模式下生成两组柱状（每天双柱并排）+ 底部 legend（点击可单显某条）
- Dialog segmented 多了"全部"选项

both 模式下两个组件标题都改成"日收支趋势"，单选时是"日支出趋势" / "日收入趋势"。

---

### 4. PC 端右侧卡片可拖排序

#### 用户决策
- **触发方式 B**：始终可拖（每张卡片右上角拖拽手柄，不要编辑模式按钮）
- **可拖范围**：4 张（统计 / 趋势 / 日历 / 筛选） —— 月份卡作为核心交互固定在顶部
- **持久化**：localStorage，不动后端
- **库**：sortablejs（事实标准，比原生 drag API 体验好太多）

#### 实施
- 装依赖：`sortablejs`、`sortablejs-vue3`、`@types/sortablejs`（dev）
- `ALL_CARDS = ['stats', 'trend', 'calendar', 'filter'] as const`
- `loadCardOrder()` 读 localStorage 并校验：合法 cardId 保留 + 缺失的自动追加（向前兼容旧顺序）
- `<Sortable>` 包裹 5 个 `<template #item>` 槽，每张卡片右上角加 `<DCaret>` 拖拽手柄
- `forceFallback: true` 用 sortable 自带 ghost，避免原生 drag 丑陋样式
- 拖完写入 `flowList.cardOrder` 持久化
- handle 颜色：默认半透明灰色，hover 加深；月份卡（蓝色背景）原本要白色 handle —— 但月份卡后来移出可拖范围，这段 `:has()` 选择器也清理掉了

#### 月份卡为什么不拖
最初设计 5 张全可拖，月份卡参与。用户测试后说："月份选择不应在拖动范围内" —— 因为月份是核心交互（切月联动整页），固定在顶部更符合"操作 vs 配置"的分层。

#### 拖拽手感参数曾经踩过坑
最初为了"避免误触" + "避免轻擦即抖动"，加了 `delay: 120` + `swapThreshold: 0.65` + `invertSwap: true`。用户测后说"不好用，改回去"。回滚到 sortable 默认手感。

—— 经验：用户对手感的偏好可能跟"业界推荐参数"不一致，先用默认，让用户主动反馈调整方向。

---

### 5. 共享 storage 工具

#### 起源
做拖拽时用户说"用统一的工具类"。一翻发现项目里**没有** —— 所有 localStorage 用法都是 `localStorage.getItem/setItem` + 各自的 `const KEY`（theme.ts、Auth.vue、request.ts 等）。

用户决定："抽取工具，后面我会统一使用这个的，移动端也用的。"

#### 设计
`src/shared/utils/storage.ts`：
```ts
export const storage: StorageApi = {
  getJSON<T>(key, defaultValue): T   // JSON.parse 失败/缺失返回 default
  setJSON<T>(key, value): void       // 自动 stringify
  getString(key): string | null      // 重载：可选 default
  getString(key, default): string
  setString(key, value): void
  remove(key): void
}
```

为什么用 `interface` 提供重载签名 + 实现里用宽签名？因为 **esbuild 不支持 object 字面量方法的重载语法**。第一版直接在 object 里写两个同名方法签名 + 实现，esbuild 报 `Expected "{" but found "getString"`。

修复方案：interface 提供两个签名（TypeScript 支持），实现用 `getString(key, defaultValue?): any` 一个签名。从调用方看类型推导仍然完整：
- `storage.getString('token')` → `string | null`
- `storage.getString('token', '')` → `string`

#### 后续
后续可以把 theme.ts 的 `localStorage.getItem(THEME_KEY)` 等迁过来。本次任务只新建工具，没动现有调用点（避免改动面扩大）。

---

### 6. 移动端日趋势横屏 overlay

#### 用户决策
- 移动端**不要 sparkline**（屏幕太小，给个按钮就完事）
- 顶部 header-actions 的筛选按钮**左侧**加柱状图按钮
- 大图弹窗形式：**参考 `mobile/components/YearLineChartOverlay`** 的横屏全屏 overlay 模式
- 不做拖拽排序

#### 实施
新建 `mobile/components/flow/DayTrendOverlay.vue`：

- **横屏**：竖屏设备用 `transform: rotate(90deg)` 把 overlay 旋转成横屏；横屏设备 `@media (orientation: landscape)` 不旋转 —— 完全照搬 YearLineChartOverlay 模式
- **左侧**：柱状图（跟桌面 dialog 一致的双柱 + 渐变 + 圆角顶 + 暗黑适配）
- **右侧 130px 信息面板**：
  - 顶部年份显示 + 上下年箭头（边界禁用：< 2021 / > 当年）
  - 中间月份 + 类型副标题 + 上下月箭头（同样边界禁用）
  - 类型 chips 垂直 3 个：支出 / 收入 / 全部
  - 底部 close 按钮

修改 `mobile/views/Flow.vue`：
- `header-actions` 最左侧加 `<van-icon name="bar-chart-o">` 柱状图按钮
- 加 `chartType` / `chartFlowData` / `showTrendOverlay` 状态（跟桌面端策略对齐）
- `fetchFlows` 改造：handleType=3 时复用 flowData，否则并行多拉一份 handleType=3 给图表
- 加 `dayData` computed：剔除 exempt 和转账，按日聚合，未到日期截断
- overlay 切月份 → `onTrendMonthChange` 更新 `chooseMonth` + `fetchFlows()`，整页（明细列表 + 月统计）跟着切

---

## 遇到的坑 / 注意事项

### 1. ECharts tooltip marker 用 itemStyle.color，不是 lineStyle.color
线条配色对了但 tooltip 圆点是默认蓝绿 —— 要给 series 显式补 `itemStyle: { color }`。柱状图（itemStyle 是渐变对象）会自动取 colorStops[0]，所以柱状图没这个问题。

### 2. esbuild 不支持 object 字面量方法的 TypeScript 重载语法
报错：`Expected "{" but found "getString"`。修复：用 `interface` 声明重载，object 实现用一个宽签名（返回 `any`）。

### 3. sortable 的"灵敏度优化参数"不能想当然
delay + swapThreshold + invertSwap 三件套是 stack overflow 上"标准答案"，但实际用户体验后说"不好用"。回滚到默认。**手感是体感问题，先用默认让用户反馈方向。**

### 4. handleType=1 时图表会拿不到完整数据
列表的 `flowData.flows` 受 handleType 筛选影响（只有支出/只有收入/只有转账），但图表要的是全量。
解决：独立 `chartFlowData`，handleType=3 时复用，否则并行多拉一次。代价是非"全部"模式下每次切月多 1 个请求 —— 个人记账数据量级可控，能扛。

### 5. 月份卡能不能拖是产品决策
最初做 5 张全可拖，用户测试后排除月份卡。原因：月份是**核心交互**（切月联动整页），不是配置项，不应跟统计/筛选这类"配置卡"放在一组拖排里。
**经验**：可拖的应该是"配置/视图"这类语义同等的项；操作类、强语义的固定不动。

### 6. 移动端 overlay 横屏旋转模式很值得收藏
`rotate(90deg)` 把竖屏当横屏用 —— 看图体验秒杀小屏吃力的全屏弹窗。

### 7. Element Plus 的 `el-input` 默认 `autocomplete="off"`
要显式覆盖才能让浏览器密码管理器识别表单。van-field 同理。

---

## 后续 TODO

1. **storage 工具迁移**：theme.ts、Auth.vue 等现有 localStorage 调用点未来可统一到 storage.ts，本次没改避免影响面扩大
2. **拖拽手感如果还想调**：sortable 的 fallbackTolerance / swapThreshold 还可以试，但要用户主动反馈想调哪个方向再动
3. **趋势图分类钻取**：当前是月度 1-31 天聚合，未来可考虑按一级分类堆叠柱状图（信息密度更高，但视觉更挤）
4. **暗黑模式截图整理**：本次新增 sparkline / dialog / overlay 三个组件全做了暗黑适配，但没对截图归档

---

## 工程化遗产

| 资产 | 路径 | 用途 |
|---|---|---|
| `storage` 共享工具 | `src/shared/utils/storage.ts` | 双端 localStorage 统一封装 |
| 日聚合算法（dayData） | FlowList.vue / Flow.vue 内 computed | 流水按 fdate group + exempt/转账剔除 + 月内填充 |
| 桌面 sparkline + dialog 双向绑定模式 | DayTrendSparkline + DayTrendDialog | 概览 sparkline + 详情大图，同 chartType / month 联动 |
| 移动横屏 overlay 模式 | DayTrendOverlay | rotate(90deg) 全屏看图 + 右侧 130px 控件面板 |
| sortablejs-vue3 集成模板 | FlowList.vue | handle + forceFallback + storage 持久化 |
