<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { typeApi, type TypeWithChildren } from '@shared/api/type'
import { useSmartBack } from '@shared/composables/useSmartBack'

const router = useRouter()
const { smartBack } = useSmartBack()

// 数据
const loading = ref(false)
const typeList = ref<TypeWithChildren[]>([])
const activeNames = ref<number[]>([])

// 加载数据
async function fetchTypes() {
  loading.value = true
  try {
    const res = await typeApi.getAll()
    typeList.value = res.data.data || []
  } catch (err) {
    console.error('获取分类列表失败', err)
  } finally {
    loading.value = false
  }
}

// 获取收支样式类
function getActionClass(handle: number | undefined): string {
  if (handle === 0) return 'income'
  if (handle === 1) return 'expense'
  if (handle === 2) return 'transfer'
  return ''
}

// 导航
function onBack() {
  smartBack('/setting')
}

function onAdd() {
  router.push('/setting/type/add')
}

function onArchive() {
  router.push('/setting/type/archive')
}

function onEdit(id: number) {
  router.push(`/setting/type/edit/${id}`)
}

onMounted(() => {
  fetchTypes()
})
</script>

<template>
  <div class="type-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">分类管理</div>
      <div class="header-right" @click="onAdd">
        <van-icon name="plus" size="20" />
      </div>
    </div>

    <!-- 页面内容 -->
    <div class="page-body">
      <!-- 归档入口 -->
      <div class="archive-entry" @click="onArchive">
        <div class="archive-left">
          <van-icon name="tosend" size="18" />
          <span>管理归档</span>
        </div>
        <van-icon name="arrow" size="16" class="archive-arrow" />
      </div>

      <!-- 分类列表 -->
      <div class="type-list" v-if="typeList.length">
        <div
          v-for="item in typeList"
          :key="item.id"
          class="type-group"
        >
          <!-- 一级分类头部 -->
          <div
            class="type-parent"
            @click="activeNames.includes(item.id) ? activeNames = activeNames.filter(n => n !== item.id) : activeNames.push(item.id)"
          >
            <div class="parent-left">
              <van-icon
                :name="activeNames.includes(item.id) ? 'arrow-down' : 'arrow'"
                size="12"
                class="expand-icon"
              />
              <span class="parent-name">{{ item.tname }}</span>
            </div>
            <div class="parent-right">
              <span
                v-if="item.action"
                class="action-tag"
                :class="getActionClass(item.action.handle)"
              >
                {{ item.action.hname }}
              </span>
              <div class="edit-btn" @click.stop="onEdit(item.id)">
                <van-icon name="edit" size="16" />
              </div>
            </div>
          </div>

          <!-- 二级分类列表 -->
          <div
            v-show="activeNames.includes(item.id)"
            class="type-children"
          >
            <div
              v-for="child in item.childrenTypes"
              :key="child.id"
              class="type-child"
              @click="onEdit(child.id)"
            >
              <span class="child-name">{{ child.tname }}</span>
              <span
                v-if="child.action"
                class="action-tag small"
                :class="getActionClass(child.action.handle)"
              >
                {{ child.action.hname }}
              </span>
            </div>
            <div
              v-if="!item.childrenTypes?.length"
              class="no-children"
            >
              暂无二级分类
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <van-empty v-if="!loading && !typeList.length" description="暂无分类" />
    </div>
  </div>
</template>

<style scoped>
.type-page {
  min-height: 100vh;
  background: var(--color-bg-page);
}

/* 顶部导航 */
.page-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.header-left,
.header-right {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: var(--color-bg-card);
  color: var(--color-text-primary);
}

.header-left:active,
.header-right:active {
  opacity: 0.7;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.page-body {
  padding: 76px 16px 24px;
}

/* 归档入口 */
.archive-entry {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--color-bg-card);
  border-radius: 12px;
  margin-bottom: 16px;
}

.archive-entry:active {
  opacity: 0.8;
}

.archive-left {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  color: var(--color-text-primary);
}

.archive-arrow {
  color: var(--color-text-tertiary);
}

/* 分类列表 */
.type-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.type-group {
  background: var(--color-bg-card);
  border-radius: 16px;
  overflow: hidden;
}

/* 一级分类 */
.type-parent {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
}

.type-parent:active {
  background: var(--color-bg-page);
}

.parent-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.expand-icon {
  color: var(--color-text-tertiary);
  transition: transform 0.2s;
}

.parent-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.parent-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 收支标签 */
.action-tag {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 500;
}

.action-tag.income {
  background: var(--color-income-bg);
  color: var(--color-income);
}

.action-tag.expense {
  background: var(--color-expense-bg);
  color: var(--color-expense);
}

.action-tag.transfer {
  background: var(--color-transfer-bg);
  color: var(--color-transfer);
}

.action-tag.small {
  font-size: 11px;
  padding: 2px 8px;
}

.edit-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: var(--color-bg-page);
  color: var(--color-text-secondary);
}

.edit-btn:active {
  opacity: 0.7;
}

/* 二级分类 */
.type-children {
  border-top: 1px solid var(--color-border-light);
  padding: 8px 16px 16px;
}

.type-child {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  margin-top: 8px;
  background: var(--color-bg-page);
  border-radius: 10px;
}

.type-child:active {
  opacity: 0.8;
}

.child-name {
  font-size: 14px;
  color: var(--color-text-primary);
}

.no-children {
  padding: 16px;
  text-align: center;
  font-size: 13px;
  color: var(--color-text-tertiary);
}
</style>

<!-- 非 scoped 样式 -->
<style>
.type-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .type-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}
</style>
