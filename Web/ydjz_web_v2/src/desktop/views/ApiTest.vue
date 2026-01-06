<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  authApi, homeApi, accountApi, actionApi, typeApi,
  flowApi, screenApi, tagApi, templateApi, imageApi
} from '@shared/api'
import MD5 from 'crypto-js/md5'

// 响应数据
const responseData = ref<any>(null)
const loading = ref(false)
const error = ref('')

// Token 状态
const currentToken = ref(localStorage.getItem('token') || '')
const isLoggedIn = computed(() => !!currentToken.value)

// Auth 参数
const loginForm = ref({
  username: '',
  password: '',
})

// 请求参数
const yearInput = ref(new Date().getFullYear())

// Account 参数
const accountIdInput = ref(1)
const accountForm = ref({
  name: '',
  money: '',
  note: '',
})

// Action 参数
const actionIdInput = ref(1)
const actionForm = ref({
  hname: '',
  handle: 0,
  exempt: false,
})

// Type 参数
const typeIdInput = ref(1)
const typeActionIdInput = ref(1)
const typeParentIdInput = ref(0)
const typeForm = ref({
  tname: '',
  actionId: 1,
  parent: 0,
})

// Flow 参数
const flowIdInput = ref(1)
const flowHandleInput = ref(3)
const flowOrderInput = ref(0)
const flowMonthInput = ref(new Date().toISOString().slice(0, 7))
const flowForm = ref({
  money: '',
  fDate: new Date().toISOString().slice(0, 10),
  actionId: 1,
  accountId: 1,
  typeId: 1,
  note: '',
})

// Screen 参数
const screenForm = ref({
  startDate: '',
  endDate: '',
  chooseHandle: 3,
})

// Tag 参数
const tagIdInput = ref(1)
const tagForm = ref({
  name: '',
  color: '#409EFF',
})

// Template 参数
const templateIdInput = ref(1)
const templateTagIdInput = ref(1)
const templateForm = ref({
  name: '',
  money: '',
  actionId: 1,
  accountId: 1,
  typeId: 1,
})

// Image 参数
const imageFile = ref<File | null>(null)

// 通用请求处理
async function handleRequest(name: string, fn: () => Promise<any>) {
  loading.value = true
  error.value = ''
  responseData.value = null

  try {
    console.log(`[API Test] ${name} 请求开始`)
    const res = await fn()
    console.log(`[API Test] ${name} 响应:`, res.data)
    responseData.value = res.data
  } catch (e: any) {
    console.error(`[API Test] ${name} 错误:`, e)
    error.value = e.message || '请求失败'
  } finally {
    loading.value = false
  }
}

// Auth API
async function testLogin() {
  loading.value = true
  error.value = ''
  responseData.value = null

  try {
    console.log('[API Test] login 请求开始')
    const username = loginForm.value.username.trim()
    const password = loginForm.value.password.trim()
    const hashedPassword = MD5(password).toString()
    console.log('[API Test] 密码原文:', password, '哈希:', hashedPassword)
    const res = await authApi.login({
      username,
      password: hashedPassword,
    })
    console.log('[API Test] login 响应:', res.data)
    responseData.value = res.data

    // 保存 token
    if (res.data.code === 0 && res.data.data?.token) {
      localStorage.setItem('token', res.data.data.token)
      currentToken.value = res.data.data.token
    }
  } catch (e: any) {
    console.error('[API Test] login 错误:', e)
    error.value = e.message || '请求失败'
  } finally {
    loading.value = false
  }
}

async function testRegister() {
  const username = loginForm.value.username.trim()
  const password = loginForm.value.password.trim()
  const hashedPassword = MD5(password).toString()
  handleRequest('register', () => authApi.register({
    username,
    password: hashedPassword,
  }))
}

function clearToken() {
  localStorage.removeItem('token')
  currentToken.value = ''
}

// Home API
function testGetHomeInfo() {
  handleRequest('getHomeInfo', () => homeApi.getHomeInfo())
}

function testGetHomeInfoByYear() {
  handleRequest('getHomeInfoByYear', () => homeApi.getHomeInfoByYear(yearInput.value))
}

function testGetSystemConfig() {
  handleRequest('getSystemConfig', () => homeApi.getSystemConfig())
}

// Account API
function testGetAllAccounts() {
  handleRequest('account.getAll', () => accountApi.getAll())
}

function testGetAllAccountsNoLimit() {
  handleRequest('account.getAllNoLimit', () => accountApi.getAllNoLimit())
}

function testGetAccountById() {
  handleRequest('account.getById', () => accountApi.getById(accountIdInput.value))
}

function testAddAccount() {
  handleRequest('account.add', () => accountApi.add(accountForm.value))
}

function testUpdateAccount() {
  handleRequest('account.update', () => accountApi.update(accountIdInput.value, accountForm.value))
}

function testDeleteAccount() {
  handleRequest('account.delete', () => accountApi.delete(accountIdInput.value))
}

// Action API
function testGetAllActions() {
  handleRequest('action.getAll', () => actionApi.getAll())
}
function testGetActionById() {
  handleRequest('action.getById', () => actionApi.getById(actionIdInput.value))
}
function testAddAction() {
  handleRequest('action.add', () => actionApi.add(actionForm.value))
}
function testUpdateAction() {
  handleRequest('action.update', () => actionApi.update(actionIdInput.value, actionForm.value))
}

// Type API
function testGetAllTypes() {
  handleRequest('type.getAll', () => typeApi.getAll())
}
function testGetAllTypesNoLimit() {
  handleRequest('type.getAllNoLimit', () => typeApi.getAllNoLimit())
}
function testGetArchivedTypes() {
  handleRequest('type.getArchived', () => typeApi.getArchived())
}
function testGetTypesByActionId() {
  handleRequest('type.getByActionId', () => typeApi.getByActionId(typeActionIdInput.value))
}
function testGetTypesByParent() {
  handleRequest('type.getByParent', () => typeApi.getByParent(typeParentIdInput.value))
}
function testGetTypeById() {
  handleRequest('type.getById', () => typeApi.getById(typeIdInput.value))
}
function testAddType() {
  handleRequest('type.add', () => typeApi.add(typeForm.value))
}
function testUpdateType() {
  handleRequest('type.update', () => typeApi.update(typeIdInput.value, typeForm.value))
}
function testArchiveType() {
  handleRequest('type.archive', () => typeApi.archive(typeIdInput.value, true))
}
function testDeleteType() {
  handleRequest('type.delete', () => typeApi.delete(typeIdInput.value))
}

// Flow API
function testGetFlowMonthList() {
  handleRequest('flow.getMonthList', () => flowApi.getMonthList(flowHandleInput.value, flowOrderInput.value, flowMonthInput.value))
}
function testGetFlowById() {
  handleRequest('flow.getById', () => flowApi.getById(flowIdInput.value))
}
function testAddFlow() {
  handleRequest('flow.add', () => flowApi.add(flowForm.value))
}
function testUpdateFlow() {
  handleRequest('flow.update', () => flowApi.update(flowIdInput.value, flowForm.value))
}
function testDeleteFlow() {
  handleRequest('flow.delete', () => flowApi.delete(flowIdInput.value))
}
function testToggleCollectFlow() {
  handleRequest('flow.toggleCollect', () => flowApi.toggleCollect(flowIdInput.value, true))
}
function testMakeFlowExcel() {
  handleRequest('flow.makeExcel', () => flowApi.makeExcel(flowMonthInput.value))
}

// Screen API
function testGetFlowByScreen() {
  handleRequest('screen.getFlowByScreen', () => screenApi.getFlowByScreen(screenForm.value))
}
function testMakeScreenExcel() {
  handleRequest('screen.makeExcel', () => screenApi.makeExcel('test', screenForm.value))
}

// Tag API
function testGetAllTags() {
  handleRequest('tag.getAll', () => tagApi.getAll())
}
function testGetTagById() {
  handleRequest('tag.getById', () => tagApi.getById(tagIdInput.value))
}
function testAddTag() {
  handleRequest('tag.add', () => tagApi.add(tagForm.value))
}
function testUpdateTag() {
  handleRequest('tag.update', () => tagApi.update({ ...tagForm.value, id: tagIdInput.value }))
}
function testDeleteTag() {
  handleRequest('tag.delete', () => tagApi.delete(tagIdInput.value))
}

// Template API
function testGetAllTemplates() {
  handleRequest('template.getAll', () => templateApi.getAll())
}
function testGetTemplatesByTagId() {
  handleRequest('template.getByTagId', () => templateApi.getByTagId(templateTagIdInput.value))
}
function testGetTemplateById() {
  handleRequest('template.getById', () => templateApi.getById(templateIdInput.value))
}
function testAddTemplate() {
  handleRequest('template.add', () => templateApi.add(templateForm.value))
}
function testUpdateTemplate() {
  handleRequest('template.update', () => templateApi.update({ ...templateForm.value, id: templateIdInput.value }))
}
function testDeleteTemplate() {
  handleRequest('template.delete', () => templateApi.delete(templateIdInput.value))
}

// Image API
function handleFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  imageFile.value = target.files?.[0] || null
}
function testUploadImage() {
  if (!imageFile.value) {
    error.value = '请先选择图片'
    return
  }
  handleRequest('image.upload', () => imageApi.upload(imageFile.value!))
}
</script>

<template>
  <div class="api-test">
    <h1>API 测试面板</h1>

    <!-- Token 状态 -->
    <el-card class="api-section">
      <template #header>
        <span class="section-title">Token 状态</span>
      </template>
      <div class="token-status">
        <el-tag :type="isLoggedIn ? 'success' : 'danger'">
          {{ isLoggedIn ? '已登录' : '未登录' }}
        </el-tag>
        <span v-if="isLoggedIn" class="token-preview">
          {{ currentToken.slice(0, 20) }}...
        </span>
        <el-button v-if="isLoggedIn" type="danger" size="small" @click="clearToken">
          清除 Token
        </el-button>
      </div>
    </el-card>

    <!-- Auth API -->
    <el-card class="api-section">
      <template #header>
        <span class="section-title">Auth API (登录注册)</span>
      </template>

      <div class="button-group">
        <div class="inline-input">
          <el-input v-model="loginForm.username" placeholder="用户名" style="width: 150px" />
          <el-input v-model="loginForm.password" placeholder="密码" type="password" style="width: 150px" />
          <el-button type="success" @click="testLogin" :loading="loading">
            login - 登录
          </el-button>
          <el-button type="warning" @click="testRegister" :loading="loading">
            register - 注册
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- Home API -->
    <el-card class="api-section">
      <template #header>
        <span class="section-title">Home API (首页信息)</span>
      </template>

      <div class="button-group">
        <el-button type="primary" @click="testGetHomeInfo" :loading="loading">
          getHomeInfo - 获取首页信息
        </el-button>

        <div class="inline-input">
          <el-input-number v-model="yearInput" :min="2020" :max="2030" />
          <el-button type="primary" @click="testGetHomeInfoByYear" :loading="loading">
            getHomeInfoByYear - 获取指定年份首页信息
          </el-button>
        </div>

        <el-button type="primary" @click="testGetSystemConfig" :loading="loading">
          getSystemConfig - 获取系统配置
        </el-button>
      </div>
    </el-card>

    <!-- Account API -->
    <el-card class="api-section">
      <template #header>
        <span class="section-title">Account API (账户管理)</span>
      </template>

      <div class="button-group">
        <el-button type="primary" @click="testGetAllAccounts" :loading="loading">
          getAll - 获取全部账户
        </el-button>

        <el-button type="primary" @click="testGetAllAccountsNoLimit" :loading="loading">
          getAllNoLimit - 获取全部账户(无限制)
        </el-button>

        <div class="inline-input">
          <span>ID:</span>
          <el-input-number v-model="accountIdInput" :min="1" />
          <el-button type="primary" @click="testGetAccountById" :loading="loading">
            getById - 获取指定账户
          </el-button>
        </div>

        <div class="inline-input">
          <el-input v-model="accountForm.name" placeholder="账户名" style="width: 120px" />
          <el-input-number v-model="accountForm.money" placeholder="金额" :precision="2" />
          <el-input v-model="accountForm.note" placeholder="备注" style="width: 120px" />
          <el-button type="success" @click="testAddAccount" :loading="loading">
            add - 添加账户
          </el-button>
        </div>

        <div class="inline-input">
          <span>ID:</span>
          <el-input-number v-model="accountIdInput" :min="1" />
          <el-button type="warning" @click="testUpdateAccount" :loading="loading">
            update - 更新账户
          </el-button>
          <el-button type="danger" @click="testDeleteAccount" :loading="loading">
            delete - 停用账户
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- Action API -->
    <el-card class="api-section">
      <template #header>
        <span class="section-title">Action API (收支管理)</span>
      </template>
      <div class="button-group">
        <el-button type="primary" @click="testGetAllActions" :loading="loading">getAll - 获取全部收支</el-button>
        <div class="inline-input">
          <span>ID:</span>
          <el-input-number v-model="actionIdInput" :min="1" />
          <el-button type="primary" @click="testGetActionById" :loading="loading">getById</el-button>
        </div>
        <div class="inline-input">
          <el-input v-model="actionForm.hname" placeholder="收支名称" style="width: 120px" />
          <el-select v-model="actionForm.handle" style="width: 100px">
            <el-option label="流入" :value="0" />
            <el-option label="流出" :value="1" />
            <el-option label="转账" :value="2" />
          </el-select>
          <el-checkbox v-model="actionForm.exempt">不计入</el-checkbox>
          <el-button type="success" @click="testAddAction" :loading="loading">add</el-button>
          <el-button type="warning" @click="testUpdateAction" :loading="loading">update</el-button>
        </div>
      </div>
    </el-card>

    <!-- Type API -->
    <el-card class="api-section">
      <template #header>
        <span class="section-title">Type API (分类管理)</span>
      </template>
      <div class="button-group">
        <div class="inline-input">
          <el-button type="primary" @click="testGetAllTypes" :loading="loading">getAll</el-button>
          <el-button type="primary" @click="testGetAllTypesNoLimit" :loading="loading">getAllNoLimit</el-button>
          <el-button type="primary" @click="testGetArchivedTypes" :loading="loading">getArchived</el-button>
        </div>
        <div class="inline-input">
          <span>ActionID:</span>
          <el-input-number v-model="typeActionIdInput" :min="1" />
          <el-button type="primary" @click="testGetTypesByActionId" :loading="loading">getByActionId</el-button>
        </div>
        <div class="inline-input">
          <span>ParentID:</span>
          <el-input-number v-model="typeParentIdInput" :min="0" />
          <el-button type="primary" @click="testGetTypesByParent" :loading="loading">getByParent</el-button>
        </div>
        <div class="inline-input">
          <span>ID:</span>
          <el-input-number v-model="typeIdInput" :min="1" />
          <el-button type="primary" @click="testGetTypeById" :loading="loading">getById</el-button>
          <el-button type="info" @click="testArchiveType" :loading="loading">archive</el-button>
          <el-button type="danger" @click="testDeleteType" :loading="loading">delete</el-button>
        </div>
        <div class="inline-input">
          <el-input v-model="typeForm.tname" placeholder="分类名" style="width: 120px" />
          <el-input-number v-model="typeForm.actionId" :min="1" placeholder="ActionID" />
          <el-input-number v-model="typeForm.parent" :min="0" placeholder="ParentID" />
          <el-button type="success" @click="testAddType" :loading="loading">add</el-button>
          <el-button type="warning" @click="testUpdateType" :loading="loading">update</el-button>
        </div>
      </div>
    </el-card>

    <!-- Flow API -->
    <el-card class="api-section">
      <template #header>
        <span class="section-title">Flow API (流水管理)</span>
      </template>
      <div class="button-group">
        <div class="inline-input">
          <el-select v-model="flowHandleInput" style="width: 100px">
            <el-option label="全部" :value="3" />
            <el-option label="流入" :value="0" />
            <el-option label="流出" :value="1" />
            <el-option label="转账" :value="2" />
          </el-select>
          <el-input v-model="flowMonthInput" placeholder="月份 YYYY-MM" style="width: 120px" />
          <el-button type="primary" @click="testGetFlowMonthList" :loading="loading">getMonthList</el-button>
          <el-button type="info" @click="testMakeFlowExcel" :loading="loading">makeExcel</el-button>
        </div>
        <div class="inline-input">
          <span>ID:</span>
          <el-input-number v-model="flowIdInput" :min="1" />
          <el-button type="primary" @click="testGetFlowById" :loading="loading">getById</el-button>
          <el-button type="info" @click="testToggleCollectFlow" :loading="loading">toggleCollect</el-button>
          <el-button type="danger" @click="testDeleteFlow" :loading="loading">delete</el-button>
        </div>
        <div class="inline-input">
          <el-input v-model="flowForm.money" placeholder="金额" style="width: 80px" />
          <el-input v-model="flowForm.fDate" placeholder="日期" style="width: 120px" />
          <el-input-number v-model="flowForm.actionId" :min="1" placeholder="ActionID" />
          <el-input-number v-model="flowForm.accountId" :min="1" placeholder="AccountID" />
          <el-input-number v-model="flowForm.typeId" :min="1" placeholder="TypeID" />
          <el-button type="success" @click="testAddFlow" :loading="loading">add</el-button>
          <el-button type="warning" @click="testUpdateFlow" :loading="loading">update</el-button>
        </div>
      </div>
    </el-card>

    <!-- Screen API -->
    <el-card class="api-section">
      <template #header>
        <span class="section-title">Screen API (筛选功能)</span>
      </template>
      <div class="button-group">
        <div class="inline-input">
          <el-input v-model="screenForm.startDate" placeholder="开始日期" style="width: 120px" />
          <el-input v-model="screenForm.endDate" placeholder="结束日期" style="width: 120px" />
          <el-select v-model="screenForm.chooseHandle" style="width: 100px">
            <el-option label="全部" :value="3" />
            <el-option label="流入" :value="0" />
            <el-option label="流出" :value="1" />
            <el-option label="转账" :value="2" />
          </el-select>
          <el-button type="primary" @click="testGetFlowByScreen" :loading="loading">getFlowByScreen</el-button>
          <el-button type="info" @click="testMakeScreenExcel" :loading="loading">makeExcel</el-button>
        </div>
      </div>
    </el-card>

    <!-- Tag API -->
    <el-card class="api-section">
      <template #header>
        <span class="section-title">Tag API (标签管理)</span>
      </template>
      <div class="button-group">
        <el-button type="primary" @click="testGetAllTags" :loading="loading">getAll - 获取全部标签</el-button>
        <div class="inline-input">
          <span>ID:</span>
          <el-input-number v-model="tagIdInput" :min="1" />
          <el-button type="primary" @click="testGetTagById" :loading="loading">getById</el-button>
          <el-button type="danger" @click="testDeleteTag" :loading="loading">delete</el-button>
        </div>
        <div class="inline-input">
          <el-input v-model="tagForm.name" placeholder="标签名" style="width: 120px" />
          <el-color-picker v-model="tagForm.color" />
          <el-button type="success" @click="testAddTag" :loading="loading">add</el-button>
          <el-button type="warning" @click="testUpdateTag" :loading="loading">update</el-button>
        </div>
      </div>
    </el-card>

    <!-- Template API -->
    <el-card class="api-section">
      <template #header>
        <span class="section-title">Template API (快记模板)</span>
      </template>
      <div class="button-group">
        <el-button type="primary" @click="testGetAllTemplates" :loading="loading">getAll - 获取全部模板</el-button>
        <div class="inline-input">
          <span>TagID:</span>
          <el-input-number v-model="templateTagIdInput" :min="1" />
          <el-button type="primary" @click="testGetTemplatesByTagId" :loading="loading">getByTagId</el-button>
        </div>
        <div class="inline-input">
          <span>ID:</span>
          <el-input-number v-model="templateIdInput" :min="1" />
          <el-button type="primary" @click="testGetTemplateById" :loading="loading">getById</el-button>
          <el-button type="danger" @click="testDeleteTemplate" :loading="loading">delete</el-button>
        </div>
        <div class="inline-input">
          <el-input v-model="templateForm.name" placeholder="模板名" style="width: 100px" />
          <el-input v-model="templateForm.money" placeholder="金额" style="width: 80px" />
          <el-button type="success" @click="testAddTemplate" :loading="loading">add</el-button>
          <el-button type="warning" @click="testUpdateTemplate" :loading="loading">update</el-button>
        </div>
      </div>
    </el-card>

    <!-- Image API -->
    <el-card class="api-section">
      <template #header>
        <span class="section-title">Image API (图片管理)</span>
      </template>
      <div class="button-group">
        <div class="inline-input">
          <input type="file" accept="image/*" @change="handleFileChange" />
          <el-button type="primary" @click="testUploadImage" :loading="loading">upload - 上传图片</el-button>
        </div>
      </div>
    </el-card>

    <!-- 响应结果 -->
    <el-card class="response-section">
      <template #header>
        <span class="section-title">响应结果</span>
      </template>

      <el-alert v-if="error" :title="error" type="error" show-icon />

      <el-skeleton v-if="loading" :rows="5" animated />

      <pre v-else-if="responseData" class="response-json">{{ JSON.stringify(responseData, null, 2) }}</pre>

      <el-empty v-else description="点击按钮测试 API" />
    </el-card>
  </div>
</template>

<style scoped>
.api-test {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.api-test h1 {
  margin-bottom: 20px;
}

.api-section {
  margin-bottom: 20px;
}

.section-title {
  font-weight: bold;
  font-size: 16px;
}

.button-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.inline-input {
  display: flex;
  gap: 12px;
  align-items: center;
}

.token-status {
  display: flex;
  align-items: center;
  gap: 12px;
}

.token-preview {
  font-family: monospace;
  color: #666;
  font-size: 13px;
}

.response-section {
  margin-top: 20px;
}

.response-json {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  overflow: auto;
  max-height: 500px;
  font-size: 13px;
  line-height: 1.5;
}
</style>
