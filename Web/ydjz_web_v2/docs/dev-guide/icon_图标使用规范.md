# Icon 图标使用规范

> v2.7.0+ 起，项目逐步统一到 **Lucide** 图标库（`lucide-vue-next`）。本文是双端图标使用的事实标准，新增 / 替换图标都按此规范来。

---

## 一、图标库选型

| 类别 | 库 | 用途 |
|---|---|---|
| **业务图标**（首选） | **`lucide-vue-next`**（Lucide） | 一切语义化图标：导航、菜单、提示、状态、说明、动作 |
| **状态符号** | `@element-plus/icons-vue` | 仅 `CircleCheckFilled` / `CircleCloseFilled` / `WarnFilled` 这种"实心圆+勾/叉"语义符号，Lucide 没有等价物 |
| **导航箭头** | Vant 内置（`arrow-left` / `arrow` / `cross`）/ Element Plus（`ArrowRight` / `Close`） | 两端原生组件附带的导航类小图标，跟所在 UI 库视觉统一最稳，**不强制切 Lucide** |

—— 规则总结：**线性、语义化的图标都用 Lucide；填充态状态符号保留 Element Plus；UI 库自带的导航小图标不动**。

---

## 二、为什么是 Lucide

- **跟 Vant / Element Plus 同源 SVG + currentColor 机制**：颜色继承父级 `color`，主题切换 / 暗黑模式零成本无缝
- **全线性 stroke** 风格，**跟两端 UI 库的 outlined 图标视觉一致**（Vant `-o` 后缀系列、Element Plus 默认 outlined 图标都是线性）
- **GitHub 30k+ star** + 1600+ 图标，社区事实标准
- **tree-shake 友好**：`import { Home } from 'lucide-vue-next'` 只打包用到的，体积可控
- **支持 `:size` / `:stroke-width` / `:color` props**，单组件可调

---

## 三、统一参数

```vue
<Home :size="20" :stroke-width="1.75" />
```

### `size`（按容器大小选）

| 容器场景 | size |
|---|---|
| 顶部 / 底部 Tab 大胶囊 | 20 |
| 顶部右侧按钮（铃铛 / 筛选 / 搜索） | 20 |
| 卡片大图标（设置主页大方块） | 24 |
| Cell 行内图标 | 18 |
| Section header（模块标题旁） | 18 |
| 提示 / 帮助 / 警告 inline 图标 | 14 |
| 空状态大图标 | 28 ~ 40 |

### `stroke-width`（按重量需求选）

- **`1.75`**：默认推荐值。比 Lucide 默认 `2` 略细，跟 Vant 字体图标视觉重量更平衡，跟两端 UI 库混用最和谐
- **`2`**：原生 Lucide 默认。需要"重一档"时用（极少）
- **`1.5`**：空状态等"弱化装饰"场景

### 颜色

**永远不要**给 Lucide 组件硬编码 `:color="..."`。一律用 CSS `color` 属性继承（svg `stroke="currentColor"`）：

```css
.cell-icon {
  color: var(--color-text-secondary); /* 默认灰 */
}
.cell-icon.active {
  color: var(--color-transfer); /* 选中蓝 */
}
html.dark .cell-icon-danger {
  color: #ff9999; /* 暗黑下的危险红 */
}
```

跟随主题、暗黑、active 状态都靠 CSS 切换 `color`，零 Vue 代码。

---

## 四、命名约定

Lucide 组件用 **PascalCase**，跟官方一致：

```vue
<script setup lang="ts">
import { Home, Settings, AlarmClock, FolderOpen, Calendars } from 'lucide-vue-next'
</script>
```

去 https://lucide.dev/icons 搜图标，hover 看名字，整段大写驼峰直接用。

---

## 五、双端通用语义对照表

EasyAccounts 内"语义 → 图标名"的事实标准。新增功能复用这套，避免每个开发者各挑各的：

### 主导航（双端 4 大胶囊）
| 语义 | Lucide | 备注 |
|---|---|---|
| 总览 / 首页 | `Home` | |
| 明细 / 列表 | `List` | |
| 统计 | `BarChart3` | 柱状图，跟"分类统计"语义贴 |
| 设置 | `Settings` | （注意是复数 Settings 不是 Setting） |

### 通知系统
| 语义 | Lucide |
|---|---|
| 通知铃铛（顶部按钮 / 设置 cell） | `Bell` |
| 暂无通知 / 静默（空状态） | `BellOff` |
| 公告 / 系统消息 | `Newspaper` |

### 设置主页 cell（双端共用语义）
| 语义 | Lucide |
|---|---|
| 收支管理（收入 / 支出双向） | `ArrowLeftRight` |
| 账户管理（钱包） | `Wallet` |
| 分类管理（标签） | `Tags` |
| 快记模板 | `Layers2` |
| 定时记账 | `AlarmClock` |
| AI / 智能 | `Sparkles` |
| 系统设置 | `Settings` |
| 数据备份 / 文件夹 | `FolderOpen` |
| 关于 | `Info` |
| 退出登录 | `LogOut`（配 `cell-icon-danger` 淡红色） |

### 系统设置子 section（双端共用）
| 语义 | Lucide |
|---|---|
| 鉴权 / 安全 | `Lock` |
| 邮件 | `Mail` |
| 提醒 | `Bell` |
| 备份 | `FolderOpen` |
| 月度报表 | `Calendars` |
| 版本信息 | `Info` |

### 主题选择
| 语义 | Lucide |
|---|---|
| 浅色 | `Sun` |
| 深色 | `Moon` |
| 跟随系统 | `Monitor` |

### 提示 / 帮助 / 警告（inline / 顶部右侧问号）
| 语义 | Lucide |
|---|---|
| 帮助 / 问号 | `CircleHelp` |
| 信息提示 | `Info` |
| 警告 | `TriangleAlert` |

### 时间 / 计划
| 语义 | Lucide |
|---|---|
| 时钟 | `Clock` |
| 闹钟（带"提醒"语义） | `AlarmClock` |
| 执行记录 / 日志 | `ClipboardClock` |

---

## 六、新增页面接入清单

```vue
<script setup lang="ts">
// 1) 从 lucide-vue-next 引入需要的图标（PascalCase 名）
import { Home, Bell, Info } from 'lucide-vue-next'
</script>

<template>
  <!-- 2) 用组件标签直接渲染，不需要包 <el-icon> 或 <van-icon> -->
  <Home :size="20" :stroke-width="1.75" />

  <!-- 3) 颜色靠父级 CSS color 继承，不传 :color prop -->
  <div class="cell-icon">
    <Bell :size="18" :stroke-width="1.75" />
  </div>
</template>

<style scoped>
.cell-icon {
  color: var(--color-text-secondary);  /* 默认灰，自动跟主题/暗黑切换 */
}
</style>
```

---

## 七、特殊场景

### 1. Element Plus `el-button :icon="..."` 不能直接传 Lucide

Element Plus 的 `el-button` 的 `:icon` prop 期望是 EP 的 IconProps 类型，**不能直接传 Lucide 组件**。改用 slot 写法：

```vue
<!-- ❌ 错（类型不兼容） -->
<el-button :icon="ClipboardClock" circle />

<!-- ✅ 对（用 slot） -->
<el-button circle>
  <ClipboardClock :size="16" :stroke-width="1.75" />
</el-button>
```

EP 默认的 `[class*="el-icon"] + span { margin-left: 6px }` 规则也不会作用到 Lucide，需要手动加 `.btn-icon { margin-right: 6px }` 之类的 css。

### 2. Vant `van-cell icon="xxx"` prop 不能传 Lucide

Vant 的 `van-cell` `icon` prop 接收字符串名（Vant 内置图标）。要用 Lucide 必须用 `<template #icon>` slot：

```vue
<!-- ❌ 错（不识别） -->
<van-cell title="收支" icon="ArrowLeftRight" />

<!-- ✅ 对（slot） -->
<van-cell title="收支">
  <template #icon>
    <ArrowLeftRight :size="18" :stroke-width="1.75" class="cell-icon" />
  </template>
</van-cell>
```

### 3. 解决"垂直对齐偏上"

Lucide 是 SVG 元素，默认 `display: inline`，会按文字 baseline 对齐 → 在 flex 容器里跟文字一起放时往往看起来"偏上"。

```css
.cell-icon {
  display: block;       /* 关键：脱离 inline baseline */
  align-self: center;   /* 双保险，flex 中严格垂直居中 */
}
```

### 4. `:has()` 选择器要求

如果想用"群组卡 hover/active 时整张变色"这种现代选择器（如 TypePicker / StatTypePicker 的群组卡），最低 Chrome 105 / Safari 15.4 / iOS 16.4 才支持。EasyAccounts 浏览器目标足够新，但要心里有数。

---

## 八、不该用 Lucide 的场景（保留原生）

| 场景 | 用什么 | 为什么 |
|---|---|---|
| 顶部 / 抽屉返回箭头 | Vant `arrow-left` / Element Plus `ArrowLeft` | 跟所在 UI 库的导航惯性一致，用户不会困惑 |
| 弹窗关闭 X | Vant `cross` / Element Plus `Close` | 同上 |
| 列表行右侧 ">"  | Vant `arrow` / Element Plus `ArrowRight` | 同上 |
| 状态符号（成功 / 失败 / 警告填充态） | Element Plus `CircleCheckFilled` / `CircleCloseFilled` / `WarnFilled` | Lucide 全是线性，没有"填充实心圆 + 勾 / 叉" 的等价物 |
| Vant 默认 toast / dialog 内置图标 | Vant 自带（不需要管） | 库内部约定 |

---

## 九、进度跟踪（截至 v2.7.0）

| 模块 | 状态 |
|---|---|
| 双端 HomeLayout 主导航 4 胶囊 | ✅ 已切 Lucide |
| 双端 NotificationCenter 铃铛 + 空状态 | ✅ |
| 双端 Setting 主页 cell（11 项） | ✅ |
| 双端 SystemSettings 主入口 cell（5 项） | ✅ |
| PC 端 SystemSettings 抽屉 6 个 Section header | ✅ |
| 双端外观三选项（Sun / Moon / Monitor） | ✅ |
| 双端 ScheduledFlow 执行记录按钮 | ✅ |
| 双端 SystemSettings 子页面提示图标（info / 问号 / 警告） | ✅ |
| 通知卡片内类型 icon（CircleCheckFilled 等状态符号） | ⏳ 保留 EP，下版本视情况评估 |
| 流水编辑器 / 账户管理 / 分类管理 / 模板管理等业务子页面内图标 | ⏳ 后续版本逐步切 |

---

## 十、引用 / 资源

- 图标查找：https://lucide.dev/icons
- 包：`lucide-vue-next`（已装）
- TypeScript 类型：组件自带，无需 `@types/`
- 颜色变量参考：`shared/styles/theme.css`（语义色 + 暗黑自动切换）
