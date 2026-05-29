import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useRouteHistoryStore } from '@shared/stores/routeHistory'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('./layouts/HomeLayout.vue'),
    children: [
      {
        path: '',
        redirect: '/board',
      },
      {
        path: 'board',
        name: 'Board',
        component: () => import('./views/Board.vue'),
        meta: { title: '总览' },
      },
      {
        path: 'flow',
        name: 'Flow',
        component: () => import('./views/Flow.vue'),
        meta: { title: '明细' },
      },
      {
        path: 'analysis',
        name: 'Analysis',
        component: () => import('./views/Analysis.vue'),
        meta: { title: '统计' },
      },
      {
        path: 'setting',
        name: 'Setting',
        component: () => import('./views/Setting.vue'),
        meta: { title: '设置' },
      },
    ],
  },
  {
    path: '/auth',
    name: 'Auth',
    component: () => import('./views/Auth.vue'),
    meta: { title: '登录' },
  },
  // 设置子页面
  {
    path: '/setting/action',
    name: 'SettingAction',
    component: () => import('./views/setting/Action.vue'),
    meta: { title: '收支管理' },
  },
  {
    path: '/setting/action/add',
    name: 'SettingActionAdd',
    component: () => import('./views/setting/ActionAdd.vue'),
    meta: { title: '添加收支' },
  },
  {
    path: '/setting/action/edit/:id',
    name: 'SettingActionEdit',
    component: () => import('./views/setting/ActionAdd.vue'),
    meta: { title: '编辑收支' },
  },
  {
    path: '/setting/account',
    name: 'SettingAccount',
    component: () => import('./views/setting/Account.vue'),
    meta: { title: '账户管理' },
  },
  {
    path: '/setting/account/add',
    name: 'SettingAccountAdd',
    component: () => import('./views/setting/AccountAdd.vue'),
    meta: { title: '添加账户' },
  },
  {
    path: '/setting/account/edit/:id',
    name: 'SettingAccountEdit',
    component: () => import('./views/setting/AccountAdd.vue'),
    meta: { title: '编辑账户' },
  },
  // 分类管理
  {
    path: '/setting/type',
    name: 'SettingType',
    component: () => import('./views/setting/Type.vue'),
    meta: { title: '分类管理' },
  },
  {
    path: '/setting/type/add',
    name: 'SettingTypeAdd',
    component: () => import('./views/setting/TypeAdd.vue'),
    meta: { title: '添加分类' },
  },
  {
    path: '/setting/type/edit/:id',
    name: 'SettingTypeEdit',
    component: () => import('./views/setting/TypeAdd.vue'),
    meta: { title: '编辑分类' },
  },
  {
    path: '/setting/type/archive',
    name: 'SettingTypeArchive',
    component: () => import('./views/setting/TypeArchive.vue'),
    meta: { title: '管理归档' },
  },
  // 快记模板
  {
    path: '/setting/template',
    name: 'SettingTemplate',
    component: () => import('./views/setting/template/Template.vue'),
    meta: { title: '快记模板' },
  },
  {
    path: '/setting/template/add',
    name: 'SettingTemplateAdd',
    component: () => import('./views/setting/template/TemplateAdd.vue'),
    meta: { title: '添加模板' },
  },
  {
    path: '/setting/template/edit/:id',
    name: 'SettingTemplateEdit',
    component: () => import('./views/setting/template/TemplateAdd.vue'),
    meta: { title: '编辑模板' },
  },
  {
    path: '/setting/template/tag',
    name: 'SettingTemplateTag',
    component: () => import('./views/setting/template/TemplateTag.vue'),
    meta: { title: '标签管理' },
  },
  // AI 设置
  {
    path: '/setting/ai',
    name: 'SettingAi',
    component: () => import('./views/setting/AiSettings.vue'),
    meta: { title: 'AI+ 设置' },
  },
  // 定时记账
  {
    path: '/setting/scheduled-flow',
    name: 'SettingScheduledFlow',
    component: () => import('./views/setting/ScheduledFlow.vue'),
    meta: { title: '定时记账' },
  },
  {
    path: '/setting/scheduled-flow/add',
    name: 'SettingScheduledFlowAdd',
    component: () => import('./views/setting/ScheduledFlowAdd.vue'),
    meta: { title: '新建规则' },
  },
  {
    path: '/setting/scheduled-flow/edit/:id',
    name: 'SettingScheduledFlowEdit',
    component: () => import('./views/setting/ScheduledFlowAdd.vue'),
    meta: { title: '编辑规则' },
  },
  {
    path: '/setting/scheduled-flow/logs',
    name: 'SettingScheduledFlowLogs',
    component: () => import('./views/setting/ScheduledFlowLogs.vue'),
    meta: { title: '执行记录' },
  },
  // 系统设置（主页 + 5 个子域）
  {
    path: '/setting/system',
    name: 'SettingSystem',
    component: () => import('./views/setting/SystemSettings.vue'),
    meta: { title: '系统设置' },
  },
  {
    path: '/setting/system/auth',
    name: 'SettingSystemAuth',
    component: () => import('./views/setting/system/AuthSettings.vue'),
    meta: { title: '鉴权设置' },
  },
  {
    path: '/setting/system/mail',
    name: 'SettingSystemMail',
    component: () => import('./views/setting/system/MailSettings.vue'),
    meta: { title: '邮件设置' },
  },
  {
    path: '/setting/system/reminder',
    name: 'SettingSystemReminder',
    component: () => import('./views/setting/system/ReminderSettings.vue'),
    meta: { title: '提醒设置' },
  },
  {
    path: '/setting/system/backup',
    name: 'SettingSystemBackup',
    component: () => import('./views/setting/system/BackupSettings.vue'),
    meta: { title: '备份设置' },
  },
  {
    path: '/setting/system/auto-excel',
    name: 'SettingSystemAutoExcel',
    component: () => import('./views/setting/system/AutoExcelSettings.vue'),
    meta: { title: '月度报表' },
  },
  // 流水记账
  {
    path: '/flow/add',
    name: 'FlowAdd',
    component: () => import('./views/flow/FlowAdd.vue'),
    meta: { title: '新增账单' },
  },
  {
    path: '/flow/edit/:id',
    name: 'FlowEdit',
    component: () => import('./views/flow/FlowAdd.vue'),
    meta: { title: '修改账单' },
  },
  // 筛选
  {
    path: '/screen',
    name: 'Screen',
    component: () => import('./views/Screen.vue'),
    meta: { title: '筛选' },
  },
  // 统计分析
  {
    path: '/analysis/type',
    name: 'AnalysisType',
    component: () => import('./views/analysis/AnalysisType.vue'),
    meta: { title: '分类统计' },
  },
  // AI 助手
  {
    path: '/ai',
    name: 'AI',
    component: () => import('./views/AI.vue'),
    meta: { title: 'AI 助手' },
  },
  // 通知中心（顶层入口：Board 铃铛 + Setting 「消息通知」cell）
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('./views/NotificationCenter.vue'),
    meta: { title: '消息通知' },
  },
]

const router = createRouter({
  history: createWebHistory('/m'),
  routes,
})

// 无需登录即可访问的白名单路由
const PUBLIC_PATHS = ['/auth']

/**
 * 路由前置守卫：鉴权
 *
 * 解决“恢复上次路由”首屏卡死的问题：
 * - 重新打开网页会恢复到上次的深层路由（浏览器原生 URL 恢复）
 * - 若此时本地没有 token（会话已失效），不应先渲染陈旧页面再等接口 401 才跳转，
 *   而是直接、干净地跳到登录页 —— 避免“看得见但点不动、必须刷新+重登”的卡死态，
 *   也避免首屏并发 401 把 /auth?redirect=... 层层嵌套成畸形 URL。
 */
router.beforeEach((to) => {
  const isPublic = PUBLIC_PATHS.some((p) => to.path.startsWith(p))
  const hasToken = !!localStorage.getItem('token')

  // 需要登录但没有 token -> 跳登录页（携带原始目标，登录后回跳）
  if (!isPublic && !hasToken) {
    return { path: '/auth', query: { redirect: to.fullPath, mode: '1' }, replace: true }
  }

  return true
})

// 路由后置守卫：记录路由历史
router.afterEach((to) => {
  // 延迟获取 store，确保 pinia 已初始化
  try {
    const routeHistory = useRouteHistoryStore()
    routeHistory.push(to)
  } catch {
    // pinia 未初始化时忽略
  }
})

export default router
