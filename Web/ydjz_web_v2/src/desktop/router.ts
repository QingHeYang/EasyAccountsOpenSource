import { createRouter, createWebHistory } from 'vue-router'

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

export default router
