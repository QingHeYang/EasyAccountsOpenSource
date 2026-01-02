# 页面状态恢复指南

本文档说明移动端页面跳转后如何保持筛选条件等状态。

---

## 一、问题场景

移动端常见的状态丢失场景：

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  页面 A      │────▶│  页面 B      │────▶│  页面 C      │
│  (有筛选)    │     │  (有筛选)    │     │  (编辑/新增) │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                    │
                           │◀───────────────────┘
                           │  返回后状态丢失！
```

**具体例子：**

| 流程 | 问题 |
|------|------|
| 统计(上月) → 分类统计 → 返回 | 时间重置为当月 |
| 明细(3月) → FlowAdd → 返回 | 月份重置为当月 |
| 分类统计 → popup → FlowEdit → 返回 | popup 关闭，筛选重置 |

---

## 二、解决方案

使用 **Pinia Store** 保存页面状态，在离开页面时保存，返回时恢复。

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        状态恢复架构                               │
│                                                                 │
│   ┌─────────────┐         ┌─────────────────────────────────┐   │
│   │  页面组件    │◀───────▶│         Pinia Store             │   │
│   │             │         │                                 │   │
│   │ onMounted   │  恢复    │  ┌─────────────────────────┐   │   │
│   │    ↓        │◀────────│  │ selectedTypeId          │   │   │
│   │ 检查 store  │         │  │ startDate / endDate     │   │   │
│   │ initialized │         │  │ showFlowPopup           │   │   │
│   │    ↓        │         │  │ ...其他状态              │   │   │
│   │ 恢复或初始化 │         │  │ initialized (标记)      │   │   │
│   │             │         │  └─────────────────────────┘   │   │
│   │             │         │                                 │   │
│   │ onBeforeUnmount  保存  │  save()   保存状态             │   │
│   │    ↓        │────────▶│  reset()  重置状态             │   │
│   │ 保存状态    │         │                                 │   │
│   └─────────────┘         └─────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Store 文件结构

```
src/shared/stores/
├── analysisFilter.ts      # Analysis 页面状态
├── flowFilter.ts          # Flow 页面状态
├── analysisTypeFilter.ts  # AnalysisType 页面状态
├── routeHistory.ts        # 路由历史（智能返回）
└── theme.ts               # 主题设置
```

---

## 三、实现步骤

### Step 1: 创建状态 Store

```typescript
// src/shared/stores/xxxFilter.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useXxxFilterStore = defineStore('xxxFilter', () => {
  // 1. 定义需要保存的状态
  const selectedId = ref<number | null>(null)
  const startDate = ref('')
  const endDate = ref('')

  // 2. 初始化标记
  const initialized = ref(false)

  // 3. 保存方法
  function save(state: {
    selectedId: number | null
    startDate: string
    endDate: string
  }) {
    selectedId.value = state.selectedId
    startDate.value = state.startDate
    endDate.value = state.endDate
    initialized.value = true
  }

  // 4. 重置方法
  function reset() {
    selectedId.value = null
    startDate.value = ''
    endDate.value = ''
    initialized.value = false
  }

  return {
    selectedId,
    startDate,
    endDate,
    initialized,
    save,
    reset,
  }
})
```

### Step 2: 页面中使用 Store

```vue
<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useXxxFilterStore } from '@shared/stores/xxxFilter'

const filterStore = useXxxFilterStore()

// 页面状态
const selectedId = ref<number | null>(null)
const startDate = ref('')
const endDate = ref('')

onMounted(() => {
  // 检查是否有保存的状态
  if (filterStore.initialized) {
    // 恢复状态
    selectedId.value = filterStore.selectedId
    startDate.value = filterStore.startDate
    endDate.value = filterStore.endDate
  } else {
    // 首次进入，初始化默认值
    initDefaultValues()
  }
})

onBeforeUnmount(() => {
  // 离开页面时保存状态
  filterStore.save({
    selectedId: selectedId.value,
    startDate: startDate.value,
    endDate: endDate.value,
  })
})
</script>
```

---

## 四、跨页面来源判断

当需要区分 "从 A 页面进入" 还是 "从 B 页面返回" 时，使用 `sessionStorage` 标记。

### 4.1 问题场景

```
Analysis ──(带参数)──▶ AnalysisType ──▶ FlowEdit ──(返回)──▶ AnalysisType
   │                        │                                    │
   │  typeId=5              │                                    │
   │  start=2024-01         │  用户修改了筛选                      │  应该用哪个？
   │  end=2024-06           │  start=2024-03                     │  - 路由参数？
   │                        │  end=2024-06                       │  - store 状态？
```

### 4.2 解决方案

```typescript
// 来源页面：设置标记
function toTargetPage() {
  sessionStorage.setItem('targetPageFrom', 'sourcePage')
  router.push({ path: '/target', query: {...} })
}

// 目标页面：判断来源
onMounted(() => {
  const isFromSourcePage = sessionStorage.getItem('targetPageFrom') === 'sourcePage'
  sessionStorage.removeItem('targetPageFrom')  // 立即清除！

  if (isFromSourcePage) {
    // 从来源页面进入，使用路由参数
    filterStore.reset()
    initFromRouteParams()
  } else if (filterStore.initialized) {
    // 从其他页面返回，恢复 store 状态
    restoreFromStore()
  }
})
```

### 4.3 为什么不用 URL 参数？

最初尝试在 URL 中添加 `from=analysis`，然后用 `router.replace` 删除：

```typescript
// ❌ 不推荐：会产生多余历史记录
router.replace({
  path: route.path,
  query: { ...route.query, from: undefined },
})
```

问题：`router.replace` 在 `onMounted` 中执行会产生额外的历史记录，导致点击返回需要点两次。

---

## 五、特殊场景处理

### 5.1 弹窗状态恢复

如果页面有弹窗（如流水列表 popup），跳转时需要保持弹窗打开状态：

```typescript
// 1. 跳转时不关闭弹窗
function onItemClick(item: Item) {
  // 不要：showPopup.value = false
  router.push({ path: `/edit/${item.id}` })
}

// 2. 在 store 中保存弹窗状态
const showPopup = ref(false)
const popupData = ref<Data | null>(null)

// 3. 返回时恢复并刷新数据
if (filterStore.showPopup) {
  showPopup.value = true
  // 重新请求数据（可能有修改）
  fetchPopupData()
}
```

### 5.2 数据刷新

返回页面时，某些数据可能已被修改，需要重新请求：

```typescript
onMounted(async () => {
  if (filterStore.initialized) {
    // 恢复状态
    restoreFromStore()

    // 如果弹窗是打开的，重新请求数据
    if (filterStore.showFlowPopup && filterStore.flowMonth) {
      const match = filterStore.flowMonth.match(/(\d+)年(\d+)月/)
      if (match) {
        await fetchFlowList(match[1], match[2])
      }
    }
  }
})
```

---

## 六、现有 Store 参考

### 6.1 analysisFilter.ts

```typescript
// Analysis 页面状态
{
  fastChoose: number,      // 快捷时间选项 0-6
  startDate: string,       // 开始日期 YYYY-MM
  endDate: string,         // 结束日期 YYYY-MM
  tabIndex: number,        // 0=收入, 1=支出
  combineSubType: boolean, // 合并子分类
  showDisableAnalysisType: boolean, // 显示全部分类
}
```

### 6.2 flowFilter.ts

```typescript
// Flow 页面状态
{
  chooseMonth: string,  // 当前月份 YYYY-MM
  handleType: number,   // 3=全部, 0=流入, 1=流出, 2=转账
  orderType: number,    // 0=按时间, 1=按金额
}
```

### 6.3 analysisTypeFilter.ts

```typescript
// AnalysisType 页面状态
{
  selectedTypeId: number | null,  // 选中的分类 ID
  selectedTypeName: string,       // 选中的分类名称
  fastChoose: string,             // 快捷时间选项 '1'-'4'
  startDate: string,              // 开始日期
  endDate: string,                // 结束日期
  showFlowPopup: boolean,         // 流水弹窗是否打开
  flowMonth: string,              // 流水弹窗的月份
  flowChooseHandle: number,       // 0=收入, 1=支出
  flowList: Flow[],               // 流水列表（临时缓存）
  result: AnalysisTypeMonthResult | null, // 查询结果
}
```

---

## 七、最佳实践

### 7.1 何时需要状态恢复？

| 场景 | 需要恢复 | 说明 |
|------|----------|------|
| 列表页 → 详情页 → 返回 | ✅ 是 | 筛选条件、滚动位置 |
| 列表页 → 新增页 → 返回 | ✅ 是 | 筛选条件 |
| Tab 切换 | ❌ 否 | 同一页面内 |
| 弹窗开关 | ❌ 否 | 同一页面内 |
| 底部导航切换 | ⚠️ 可选 | 看业务需求 |

### 7.2 Store 命名规范

```
use + 页面名 + Filter + Store
```

例如：
- `useAnalysisFilterStore`
- `useFlowFilterStore`
- `useAnalysisTypeFilterStore`

### 7.3 状态分类

| 类型 | 应该保存 | 例子 |
|------|----------|------|
| 筛选条件 | ✅ 是 | 日期、类型、排序 |
| 选中项 | ✅ 是 | 选中的分类、账户 |
| 弹窗状态 | ✅ 是 | 是否打开、弹窗数据 |
| 查询结果 | ⚠️ 可选 | 列表数据（可重新请求） |
| 临时输入 | ❌ 否 | 表单输入中的内容 |
| 加载状态 | ❌ 否 | loading、error |

---

## 八、相关文件

| 文件 | 说明 |
|------|------|
| `src/shared/stores/analysisFilter.ts` | Analysis 状态 Store |
| `src/shared/stores/flowFilter.ts` | Flow 状态 Store |
| `src/shared/stores/analysisTypeFilter.ts` | AnalysisType 状态 Store |
| `src/mobile/views/Analysis.vue` | 统计页面 |
| `src/mobile/views/Flow.vue` | 明细页面 |
| `src/mobile/views/analysis/AnalysisType.vue` | 分类统计页面 |
