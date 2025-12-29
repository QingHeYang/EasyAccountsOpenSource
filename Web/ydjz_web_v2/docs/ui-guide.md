# UI 设计指南

本文档定义了 EasyAccounts 的 UI 规范，包括颜色系统、主题切换、CSS 变量使用方法。

## 颜色系统

### 业务语义色

| 语义 | CSS 变量 | 亮色模式 | 暗色模式 | 用途 |
|------|----------|----------|----------|------|
| 收入 | `--color-income` | #52C41A | #69DB7C | 收入金额、收入图标 |
| 支出 | `--color-expense` | #F5222D | #FF6B6B | 支出金额、支出图标 |
| 转账 | `--color-transfer` | #1890FF | #74C0FC | 转账金额、主色调 |
| 备注 | `--color-note` | #FAAD14 | #FFD43B | 备注标签、警告提示 |

### 文本色

| 层级 | CSS 变量 | 亮色模式 | 暗色模式 | 用途 |
|------|----------|----------|----------|------|
| 主文本 | `--color-text-primary` | #262626 | #F5F5F5 | 标题、重要文本 |
| 次文本 | `--color-text-secondary` | #595959 | #A3A3A3 | 正文、描述 |
| 辅助文本 | `--color-text-tertiary` | #8C8C8C | #737373 | 提示、禁用文本 |
| 占位符 | `--color-text-placeholder` | #BFBFBF | #525252 | 输入框占位符 |

### 背景色

| 层级 | CSS 变量 | 亮色模式 | 暗色模式 | 用途 |
|------|----------|----------|----------|------|
| 页面背景 | `--color-bg-page` | #F5F5F5 | #141414 | 页面底层背景 |
| 卡片背景 | `--color-bg-card` | #FFFFFF | #1F1F1F | 卡片、列表项 |
| 悬浮背景 | `--color-bg-elevated` | #FFFFFF | #262626 | 弹窗、下拉菜单 |

### 边框色

| 层级 | CSS 变量 | 亮色模式 | 暗色模式 | 用途 |
|------|----------|----------|----------|------|
| 默认边框 | `--color-border` | #E8E8E8 | #303030 | 分割线、卡片边框 |
| 浅色边框 | `--color-border-light` | #F0F0F0 | #262626 | 次要分割线 |

---

## 主题切换

### 主题模式

支持三种模式：
- `light` - 亮色模式
- `dark` - 暗色模式
- `system` - 跟随系统（默认）

### 使用 Theme Store

```typescript
import { useThemeStore } from '@shared/stores/theme'

const themeStore = useThemeStore()

// 读取状态
themeStore.mode           // 'light' | 'dark' | 'system'
themeStore.effectiveTheme // 'light' | 'dark' (实际显示的主题)
themeStore.isDark         // boolean

// 设置主题
themeStore.set('dark')    // 切换到暗色
themeStore.set('light')   // 切换到亮色
themeStore.set('system')  // 跟随系统

// 快速切换
themeStore.toggle()       // 亮 <-> 暗
```

### 使用工具函数

```typescript
import {
  getStoredTheme,    // 获取存储的主题设置
  getEffectiveTheme, // 获取实际显示的主题
  setTheme,          // 设置主题
  toggleTheme,       // 切换主题
} from '@shared/utils/theme'
```

---

## CSS 变量使用

### 在 Vue 组件中使用

```vue
<template>
  <div class="amount income">+100.00</div>
  <div class="amount expense">-50.00</div>
</template>

<style scoped>
.amount {
  font-size: 16px;
}

.income {
  color: var(--color-income);
}

.expense {
  color: var(--color-expense);
}
</style>
```

### 在 TypeScript 中获取 CSS 变量值

```typescript
function getCssVar(name: string): string {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim()
}

const incomeColor = getCssVar('--color-income')
```

### 完整变量列表

```css
/* 业务色 */
--color-income
--color-expense
--color-transfer
--color-note

/* 文本色 */
--color-text-primary
--color-text-secondary
--color-text-tertiary
--color-text-placeholder

/* 背景色 */
--color-bg-page
--color-bg-card
--color-bg-elevated

/* 边框色 */
--color-border
--color-border-light
```

---

## 框架主题

### Element Plus (PC 端)

Element Plus 的暗色模式通过 `html.dark` 类自动激活。

已导入的样式：
```typescript
// main-desktop.ts
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
```

### Vant (移动端)

Vant 的暗色模式通过 `html.van-theme-dark` 类自动激活。

已导入的样式：
```typescript
// main-mobile.ts
import 'vant/lib/index.css'
```

### 暗色模式生效条件

| 端 | HTML 类 | 自动添加位置 |
|----|---------|--------------|
| PC | `dark` | `index.html` 初始化脚本 |
| Mobile | `dark`, `van-theme-dark` | `mobile.html` 初始化脚本 |

---

## 设计原则

### 暗色模式色彩调整

暗色模式下颜色需要降低饱和度约 20%，避免刺眼：

| 亮色 | 暗色 | 调整 |
|------|------|------|
| #52C41A (收入) | #69DB7C | 饱和度 ↓, 亮度 ↑ |
| #F5222D (支出) | #FF6B6B | 饱和度 ↓, 亮度 ↑ |
| #1890FF (转账) | #74C0FC | 饱和度 ↓, 亮度 ↑ |

### 对比度要求

- 正文文本与背景对比度 ≥ 4.5:1
- 大字标题与背景对比度 ≥ 3:1
- 遵循 WCAG 2.1 AA 标准

### 间距规范

使用 4px 基准网格：
- 小间距: 4px, 8px
- 中间距: 12px, 16px
- 大间距: 24px, 32px

---

## 示例：主题切换组件

### PC 端 (Element Plus)

```vue
<template>
  <el-dropdown @command="handleTheme">
    <el-button>
      {{ themeLabel }}
      <el-icon><arrow-down /></el-icon>
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="light">亮色</el-dropdown-item>
        <el-dropdown-item command="dark">暗色</el-dropdown-item>
        <el-dropdown-item command="system">跟随系统</el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useThemeStore } from '@shared/stores/theme'

const themeStore = useThemeStore()

const themeLabel = computed(() => {
  const labels = { light: '亮色', dark: '暗色', system: '跟随系统' }
  return labels[themeStore.mode]
})

function handleTheme(mode: 'light' | 'dark' | 'system') {
  themeStore.set(mode)
}
</script>
```

### 移动端 (Vant)

```vue
<template>
  <van-cell title="主题模式" :value="themeLabel" is-link @click="showPicker = true" />

  <van-action-sheet
    v-model:show="showPicker"
    :actions="actions"
    @select="handleSelect"
  />
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useThemeStore } from '@shared/stores/theme'

const themeStore = useThemeStore()
const showPicker = ref(false)

const themeLabel = computed(() => {
  const labels = { light: '亮色', dark: '暗色', system: '跟随系统' }
  return labels[themeStore.mode]
})

const actions = [
  { name: '亮色', value: 'light' },
  { name: '暗色', value: 'dark' },
  { name: '跟随系统', value: 'system' },
]

function handleSelect(action: { value: string }) {
  themeStore.set(action.value as 'light' | 'dark' | 'system')
  showPicker.value = false
}
</script>
```
