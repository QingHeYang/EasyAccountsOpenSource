import { createRouter, createWebHistory } from 'vue-router'
import { useRouteHistoryStore } from '@shared/stores/routeHistory'

const routes = [
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
]

const router = createRouter({
  history: createWebHistory('/m'),
  routes,
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
