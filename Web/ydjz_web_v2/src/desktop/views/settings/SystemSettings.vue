<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  systemConfigApi,
  type SystemConfigOverview,
} from '@shared/api/systemConfig'
import { isHandledError } from '@shared/api/request'
import type { VersionInfo } from '@shared/api/home'

import './system-settings/styles.css'
import AppearanceSection from './system-settings/AppearanceSection.vue'
import AuthSection from './system-settings/AuthSection.vue'
import MailSection from './system-settings/MailSection.vue'
import ReminderSection from './system-settings/ReminderSection.vue'
import BackupSection from './system-settings/BackupSection.vue'
import AutoExcelSection from './system-settings/AutoExcelSection.vue'
import VersionSection from './system-settings/VersionSection.vue'

const props = defineProps<{
  visible: boolean
  versions: VersionInfo
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
}>()

/* ============================================================
 * 数据加载：用 /system/config/overview 一次拿全 5 域。
 *
 * - 抽屉每次打开都重新拉，确保数据最新（"不费流量"，admin 配置不频繁打开）
 * - 子组件单项更新成功后 emit('updated')，主容器重新拉 overview
 * - 子组件 props 自动回填新值（解决"修改后页面没跟着变"的问题）
 * ============================================================ */

const overview = ref<SystemConfigOverview | null>(null)
const loading = ref(false)

async function loadOverview() {
  loading.value = true
  try {
    const res = await systemConfigApi.getOverview()
    overview.value = res.data.data
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('加载系统设置失败')
  } finally {
    loading.value = false
  }
}

watch(
  () => props.visible,
  (v) => {
    if (v) loadOverview()
  },
)

function onSectionUpdated() {
  loadOverview()
}
</script>

<template>
  <el-drawer
    :model-value="visible"
    title="系统设置"
    direction="rtl"
    size="540px"
    class="setting-drawer system-settings-drawer"
    @update:model-value="emit('update:visible', $event)"
  >
    <div class="system-settings-content" v-loading="loading && !overview">
      <!-- 1. 外观（前端本地状态，不依赖 overview） -->
      <AppearanceSection />

      <!-- 2-6. 五大基础设施域：依赖 overview 数据 -->
      <template v-if="overview">
        <AuthSection
          :data="overview.auth"
          @updated="onSectionUpdated"
        />
        <MailSection
          :data="overview.mail"
          @updated="onSectionUpdated"
        />
        <ReminderSection
          :scheduled="overview.scheduledFlow"
          :auto-excel="overview.autoExcel"
          @updated="onSectionUpdated"
        />
        <BackupSection
          :data="overview.backup"
          @updated="onSectionUpdated"
        />
        <AutoExcelSection
          :data="overview.autoExcel"
          @updated="onSectionUpdated"
        />
      </template>

      <!-- 7. 版本信息（来自 props，不依赖 overview） -->
      <VersionSection :versions="versions" />
    </div>
  </el-drawer>
</template>

<style scoped>
.system-settings-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 200px;
}
</style>
