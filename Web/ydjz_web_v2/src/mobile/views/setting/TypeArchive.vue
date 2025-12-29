<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { typeApi, type TypeWithChildren } from '@shared/api/type'
import { useSmartBack } from '@shared/composables/useSmartBack'

const router = useRouter()
const { smartBack } = useSmartBack()

// 数据
const loading = ref(false)
const archiveList = ref<TypeWithChildren[]>([])
const activeNames = ref<number[]>([])

// 加载归档数据
async function fetchArchived() {
  loading.value = true
  try {
    const res = await typeApi.getArchived()
    archiveList.value = res.data.data || []
  } catch (err) {
    console.error('获取归档列表失败', err)
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

// 取出归档
async function onRestore(item: TypeWithChildren) {
  const isParent = item.parent === -1 || item.parent === 0
  const msg = isParent
    ? `该分类为：一级分类\n确定取出"${item.tname}"吗？\n一级分类取出后，下属二级分类会一同取出`
    : `该分类为：二级分类\n确定取出"${item.tname}"吗？\n二级分类取出后，会回到一级分类中`

  try {
    await showConfirmDialog({
      title: '提示',
      message: msg,
    })

    await typeApi.archive(item.id, false)
    showToast('取出成功')
    fetchArchived()
  } catch {
    // 取消
  }
}

function onBack() {
  smartBack('/setting/type')
}

onMounted(() => {
  fetchArchived()
})
</script>

<template>
  <div class="type-archive-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">管理归档</div>
      <div class="header-right"></div>
    </div>

    <!-- 页面内容 -->
    <div class="page-body">
      <!-- 归档列表 -->
      <div class="archive-list" v-if="archiveList.length">
        <div
          v-for="item in archiveList"
          :key="item.id"
          class="archive-group"
        >
          <!-- 一级分类头部 -->
          <div
            class="archive-parent"
            @click="activeNames.includes(item.id) ? activeNames = activeNames.filter(n => n !== item.id) : activeNames.push(item.id)"
          >
            <div class="parent-left">
              <van-icon
                :name="activeNames.includes(item.id) ? 'arrow-down' : 'arrow'"
                size="12"
                class="expand-icon"
              />
              <span class="parent-name">{{ item.tname }}</span>
              <span class="level-tag">
                {{ item.parent === -1 || item.parent === 0 ? '一级' : '二级' }}
              </span>
            </div>
            <div class="parent-right">
              <span
                v-if="item.action"
                class="action-tag"
                :class="getActionClass(item.action.handle)"
              >
                {{ item.action.hname }}
              </span>
            </div>
          </div>

          <!-- 操作区域 + 二级分类 -->
          <div
            v-show="activeNames.includes(item.id)"
            class="archive-content"
          >
            <!-- 取出按钮 -->
            <div class="restore-btn" @click="onRestore(item)">
              <van-icon name="revoke" size="16" />
              <span>取出归档</span>
            </div>

            <!-- 二级分类列表 -->
            <div
              v-for="child in item.childrenTypes"
              :key="child.id"
              class="archive-child"
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
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <van-empty v-if="!loading && !archiveList.length" description="暂无归档分类" />
    </div>
  </div>
</template>

<style scoped>
.type-archive-page {
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

.header-right {
  background: transparent;
}

.header-left:active {
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

/* 归档列表 */
.archive-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.archive-group {
  background: var(--color-bg-card);
  border-radius: 16px;
  overflow: hidden;
}

/* 一级分类 */
.archive-parent {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
}

.archive-parent:active {
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

.level-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--color-bg-page);
  color: var(--color-text-tertiary);
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

/* 内容区域 */
.archive-content {
  border-top: 1px solid var(--color-border-light);
  padding: 12px 16px 16px;
}

.restore-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 13px;
  color: var(--color-transfer);
  background: var(--color-transfer-bg);
  border-radius: 8px;
  margin-bottom: 12px;
}

.restore-btn:active {
  opacity: 0.7;
}

/* 二级分类 */
.archive-child {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  margin-top: 8px;
  background: var(--color-bg-page);
  border-radius: 10px;
}

.child-name {
  font-size: 14px;
  color: var(--color-text-primary);
}
</style>

<!-- 非 scoped 样式 -->
<style>
.type-archive-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .type-archive-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}
</style>
