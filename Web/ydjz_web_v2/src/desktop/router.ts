import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

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
        component: () => import('./views/analysis/index.vue'),
        meta: { title: '统计' },
      },
      {
        path: 'setting',
        name: 'Setting',
        component: () => import('./views/settings/index.vue'),
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
  {
    path: '/api-test',
    name: 'ApiTest',
    component: () => import('./views/ApiTest.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 无需登录即可访问的白名单路由
const PUBLIC_PATHS = ['/auth', '/api-test']

/**
 * 路由前置守卫：鉴权
 *
 * 解决“恢复上次路由”首屏卡死的问题：
 * - 重新打开网页会恢复到上次的深层路由（浏览器原生 URL 恢复）
 * - 若此时本地没有 token（会话已失效），不应先渲染陈旧页面再等接口 401 才跳转，
 *   而是直接、干净地跳到 /auth —— 避免“看得见但点不动、必须刷新+重登”的卡死态。
 *
 * 关键：守卫只负责“无 token 时干净跳到 /auth”，**不决定 登录/注册 模式**。
 * 模式只能由后端判定（secret.key 是否存在 → 401 登录 / 418 注册），
 * 因此这里不带 mode，交由 Auth.vue 挂载时探测后端信号再定。
 * （旧实现写死 mode=1 会让全新部署的首装用户错误地看到登录页而非注册页。）
 */
router.beforeEach((to) => {
  // 整段匹配，避免 /authorize、/api-test-xxx 这类需登录路由被前缀误放行
  const isPublic = PUBLIC_PATHS.some((p) => to.path === p || to.path.startsWith(p + '/'))
  const hasToken = !!localStorage.getItem('token')

  // 需要登录但没有 token -> 跳 /auth（携带原始目标，登录后回跳；mode 由 Auth.vue 探测决定）
  if (!isPublic && !hasToken) {
    return { path: '/auth', query: { redirect: to.fullPath }, replace: true }
  }

  return true
})

export default router
