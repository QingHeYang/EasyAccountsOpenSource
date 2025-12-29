<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { tagApi, type Tag } from '@shared/api/tag'
import { useSmartBack } from '@shared/composables/useSmartBack'

const router = useRouter()
const { smartBack } = useSmartBack()

// 数据
const tags = ref<Tag[]>([])
const showPopup = ref(false)
const isEdit = ref(false)
const editingTag = ref<Tag | null>(null)

// 表单数据
const tagName = ref('')
const tagColor = ref('')

// 预设颜色列表
const colorOptions = [
  '#FFEA00', '#ECD540', '#B8860B',
  '#90EE90', '#3CB371', '#008000', '#006400', '#013220',
  '#FFCCB6', '#FFB6C1', '#FF1493',
  '#FFA500', '#FF4500',
  '#D2B48C', '#8B4513',
  '#ADD8E6', '#48D1CC', '#120A8F', '#000080',
  '#B57EDC', '#800080', '#4B0082',
  '#FFA07A', '#FF0000', '#8B0000', '#800020', '#600000',
  '#A9A9A9', '#607B8B', '#000000',
]

// 加载标签列表
async function fetchTags() {
  try {
    const res = await tagApi.getAll()
    tags.value = res.data.data || []
  } catch (err) {
    console.error('获取标签列表失败', err)
  }
}

// 打开新建弹窗
function openAddPopup() {
  isEdit.value = false
  editingTag.value = null
  tagName.value = ''
  tagColor.value = ''
  showPopup.value = true
}

// 打开编辑弹窗
function openEditPopup(tag: Tag) {
  isEdit.value = true
  editingTag.value = tag
  tagName.value = tag.name
  tagColor.value = tag.color
  showPopup.value = true
}

// 关闭弹窗
function closePopup() {
  showPopup.value = false
  tagName.value = ''
  tagColor.value = ''
}

// 选择颜色
function selectColor(color: string) {
  tagColor.value = color
}

// 验证表单
function validateForm(): boolean {
  if (!tagName.value.trim()) {
    showToast('请输入标签名称')
    return false
  }
  if (!tagColor.value) {
    showToast('请选择标签颜色')
    return false
  }
  return true
}

// 新建标签
async function addTag() {
  if (!validateForm()) return

  try {
    await tagApi.add({
      name: tagName.value.trim(),
      color: tagColor.value,
    })
    showToast('添加成功')
    closePopup()
    fetchTags()
  } catch (err) {
    showToast('添加失败')
    console.error(err)
  }
}

// 更新标签
async function updateTag() {
  if (!validateForm() || !editingTag.value) return

  try {
    await tagApi.update({
      id: editingTag.value.id,
      name: tagName.value.trim(),
      color: tagColor.value,
    })
    showToast('修改成功')
    closePopup()
    fetchTags()
  } catch (err) {
    showToast('修改失败')
    console.error(err)
  }
}

// 删除标签
async function deleteTag() {
  if (!editingTag.value) return

  try {
    await showConfirmDialog({
      title: '删除',
      message: '确定删除此标签吗？\n删除后模板中的标签将一并删除',
    })

    await tagApi.delete(editingTag.value.id)
    showToast('已删除')
    closePopup()
    fetchTags()
  } catch {
    // 取消
  }
}

// 提交
function onSubmit() {
  if (isEdit.value) {
    updateTag()
  } else {
    addTag()
  }
}

function onBack() {
  smartBack('/setting/template')
}

onMounted(() => {
  fetchTags()
})
</script>

<template>
  <div class="template-tag-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">标签管理</div>
      <div class="header-right"></div>
    </div>

    <!-- 页面内容 -->
    <div class="page-body">
      <!-- 标签列表 -->
      <div class="section-title">全部标签</div>

      <div v-if="tags.length" class="tag-grid">
        <div
          v-for="tag in tags"
          :key="tag.id"
          class="tag-card"
          :style="{ background: tag.color }"
          @click="openEditPopup(tag)"
        >
          {{ tag.name }}
        </div>
      </div>

      <van-empty v-else description="当前无标签" />

      <!-- 新建按钮 -->
      <button class="add-btn" @click="openAddPopup">
        新建标签
      </button>
    </div>

    <!-- 新建/编辑弹窗 -->
    <van-popup
      v-model:show="showPopup"
      round
      closeable
      position="bottom"
      teleport="body"
      :style="{ height: '70%' }"
      @close="closePopup"
    >
      <div class="popup-content">
        <div class="popup-title">{{ isEdit ? '修改标签' : '新建标签' }}</div>

        <!-- 名称输入 -->
        <div class="form-card">
          <div class="form-item">
            <label class="form-label">名称</label>
            <input
              v-model="tagName"
              type="text"
              class="form-input"
              placeholder="请输入标签名"
              maxlength="4"
            />
          </div>
        </div>

        <!-- 颜色选择 -->
        <div class="form-card">
          <div class="form-item">
            <div class="color-header">
              <label class="form-label">颜色</label>
              <div
                v-if="tagName && tagColor"
                class="preview-tag"
                :style="{ background: tagColor }"
              >
                {{ tagName }}
              </div>
            </div>
            <div class="color-grid">
              <div
                v-for="color in colorOptions"
                :key="color"
                class="color-item"
                :class="{ selected: tagColor === color }"
                :style="{ background: color }"
                @click="selectColor(color)"
              >
                <van-icon v-if="tagColor === color" name="success" size="16" color="#fff" />
              </div>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="popup-actions">
          <button class="submit-btn" @click="onSubmit">
            {{ isEdit ? '修改' : '新建' }}
          </button>
          <button v-if="isEdit" class="delete-btn" @click="deleteTag">
            删除
          </button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<style scoped>
.template-tag-page {
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

/* 区块标题 */
.section-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-transfer);
  padding: 0 4px 16px;
  border-bottom: 1px solid var(--color-transfer);
  margin-bottom: 20px;
}

/* 标签网格 */
.tag-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 30px;
}

.tag-card {
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #fff;
}

.tag-card:active {
  opacity: 0.8;
}

/* 新建按钮 */
.add-btn {
  width: 100%;
  padding: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  background: var(--color-income);
  border: none;
  border-radius: 14px;
  cursor: pointer;
}

.add-btn:active {
  opacity: 0.9;
}

/* 弹窗内容 */
.popup-content {
  padding: 20px 16px;
}

.popup-title {
  text-align: center;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 20px;
}

/* 表单卡片 */
.form-card {
  background: var(--color-bg-card);
  border-radius: 16px;
  padding: 8px 0;
  margin-bottom: 16px;
}

.form-item {
  padding: 16px 20px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: 12px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  font-size: 16px;
  color: var(--color-text-primary);
  background: var(--color-bg-page);
  border: none;
  border-radius: 12px;
  outline: none;
  box-sizing: border-box;
}

.form-input::placeholder {
  color: var(--color-text-tertiary);
}

/* 颜色选择 */
.color-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.color-header .form-label {
  margin-bottom: 0;
}

.preview-tag {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  color: #fff;
}

.color-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
}

.color-item {
  aspect-ratio: 1;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.color-item:active {
  opacity: 0.8;
}

.color-item.selected {
  box-shadow: 0 0 0 3px var(--color-bg-page), 0 0 0 5px var(--color-text-primary);
}

/* 弹窗操作按钮 */
.popup-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

.submit-btn {
  width: 100%;
  padding: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  background: var(--color-transfer);
  border: none;
  border-radius: 14px;
  cursor: pointer;
}

.submit-btn:active {
  opacity: 0.9;
}

.delete-btn {
  width: 100%;
  padding: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  background: var(--color-expense);
  border: none;
  border-radius: 14px;
  cursor: pointer;
}

.delete-btn:active {
  opacity: 0.9;
}
</style>

<!-- 非 scoped 样式 -->
<style>
.template-tag-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .template-tag-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}

/* 弹窗暗黑模式 */
html.dark .template-tag-page .van-popup {
  background: var(--color-bg-page) !important;
}
</style>
