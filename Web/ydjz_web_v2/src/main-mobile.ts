import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Vant, { showNotify } from 'vant'
import 'vant/lib/index.css'
import '@shared/styles/theme.css'
import './mobile/styles/base.css'

import App from './mobile/App.vue'
import router from './mobile/router'
import { setupRequest } from '@shared/api'
import { ApiCode } from '@shared/types'

// 初始化请求（使用运行时配置 window.config）
setupRequest({
  baseURL: window.config?.apiBaseUrl || '/api',
  onUnauthorized: (code) => {
    const redirect = router.currentRoute.value.fullPath

    // 未注册 -> 注册模式（使用 replace，不留历史记录）
    if (code === ApiCode.NOT_REGISTERED) {
      router.replace({ path: '/auth', query: { redirect, mode: '0' } })
      return
    }

    // 未登录/过期 -> 登录模式（使用 replace，不留历史记录）
    router.replace({ path: '/auth', query: { redirect, mode: '1' } })
  },
  onError: (_code, msg) => {
    // Mobile 使用 Vant 通知（只显示消息，不显示错误码）
    showNotify({ type: 'warning', message: msg })
  },
})

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(Vant)

app.mount('#app')
