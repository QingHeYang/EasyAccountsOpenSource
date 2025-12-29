import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import '@shared/styles/theme.css'
import '@desktop/styles/base.css'

import App from './desktop/App.vue'
import router from './desktop/router'
import { setupRequest } from '@shared/api'
import { ApiCode } from '@shared/types'

// 初始化请求
setupRequest({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  onUnauthorized: (code) => {
    const currentPath = router.currentRoute.value.fullPath

    // API 测试页面不跳转
    if (currentPath.startsWith('/api-test')) {
      console.warn('[Auth] 未授权，当前在测试页面，不跳转')
      return
    }

    // 已在登录页，不重复跳转
    if (currentPath.startsWith('/auth')) {
      return
    }

    // 未注册 -> 注册页 (mode=0)
    if (code === ApiCode.NOT_REGISTERED) {
      router.push({ path: '/auth', query: { redirect: currentPath, mode: '0' } })
      return
    }

    // 未登录/过期 -> 登录页 (mode=1)
    router.push({ path: '/auth', query: { redirect: currentPath, mode: '1' } })
  },
  onError: (code, msg) => {
    // Desktop 使用 Element Plus 消息提示
    import('element-plus').then(({ ElMessage }) => {
      ElMessage.error(`${code}: ${msg}`)
    })
  },
})

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')
