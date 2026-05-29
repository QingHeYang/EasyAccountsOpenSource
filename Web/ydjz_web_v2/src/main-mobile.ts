import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Vant, { showFailToast, showToast } from 'vant'
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
    const current = router.currentRoute.value

    // 已在登录页：不重复跳转。
    // 否则会话失效时首屏并发的多个 401 会把 /auth?redirect=... 整段
    // 再次当作 redirect 层层嵌套，产生畸形 URL（登录后回不去）。
    if (current.path.startsWith('/auth')) {
      return
    }

    // 仅记录“真实业务页面”作为登录后回跳目标
    const redirect = current.fullPath

    // 未注册 -> 注册模式（使用 replace，不留历史记录）
    if (code === ApiCode.NOT_REGISTERED) {
      router.replace({ path: '/auth', query: { redirect, mode: '0' } })
      return
    }

    // 未登录/过期 -> 登录模式（使用 replace，不留历史记录）
    router.replace({ path: '/auth', query: { redirect, mode: '1' } })
  },
  onError: (_code, msg) => {
    // bottom：跟操作位置更近，不挡顶部信息
    // 长文案（> 20 字）走 text 横条 toast，max-width 70% 能容纳；
    // 短文案走 fail 方形 toast，视觉强调失败语义
    const text = msg ?? ''
    if (text.length > 20) {
      showToast({
        message: text,
        type: 'fail',
        position: 'bottom',
        // 长文本时长按字数线性增加：每 10 字 +500ms，最多 5 秒
        duration: Math.min(2000 + Math.floor(text.length / 10) * 500, 5000),
        className: 'app-long-toast',
      })
    } else {
      showFailToast({ message: text, position: 'bottom' })
    }
  },
})

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(Vant)

app.mount('#app')
