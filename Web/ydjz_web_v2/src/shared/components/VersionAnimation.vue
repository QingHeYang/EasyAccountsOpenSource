<script setup lang="ts">
import { ref, watch, nextTick, onUnmounted } from 'vue'
import confetti from 'canvas-confetti'
import logoUrl from '@shared/assets/logo.png'

const props = defineProps<{
  /** 是否触发动画，从 false → true 时触发一次，自动归零 */
  show: boolean
  /** 显示的版本号，如 'v2.7.0'（一般来源 SystemConfig.versions.release） */
  version: string
  /** 动画总时长（ms），默认 3500ms */
  duration?: number
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
}>()

const visible = ref(false)
let hideTimer: number | null = null

function fireConfetti() {
  const total = (props.duration ?? 3500) - 800
  const end = Date.now() + Math.min(total, 1800)

  ;(function frame() {
    confetti({
      particleCount: 4,
      angle: 60,
      spread: 65,
      origin: { x: 0, y: 0.6 },
      colors: ['#52C41A', '#F5222D', '#1890FF', '#FAAD14', '#722ED1'],
      zIndex: 99999,
    })
    confetti({
      particleCount: 4,
      angle: 120,
      spread: 65,
      origin: { x: 1, y: 0.6 },
      colors: ['#52C41A', '#F5222D', '#1890FF', '#FAAD14', '#722ED1'],
      zIndex: 99999,
    })
    if (Date.now() < end) {
      requestAnimationFrame(frame)
    }
  })()
}

watch(
  () => props.show,
  (val) => {
    if (val) {
      visible.value = true
      nextTick(fireConfetti)
      if (hideTimer) clearTimeout(hideTimer)
      hideTimer = window.setTimeout(() => {
        visible.value = false
        emit('update:show', false)
      }, props.duration ?? 3500)
    } else {
      visible.value = false
    }
  }
)

onUnmounted(() => {
  if (hideTimer) clearTimeout(hideTimer)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="va-fade">
      <div v-if="visible" class="va-overlay">
        <div class="va-content">
          <img :src="logoUrl" alt="EasyAccounts" class="va-logo" />
          <div class="va-app-name">EasyAccounts</div>
          <div class="va-version-chip">{{ version }}</div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.va-overlay {
  position: fixed;
  inset: 0;
  z-index: 9998;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(3px);
  -webkit-backdrop-filter: blur(3px);
}

.va-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  user-select: none;
  padding: 36px 56px;
  border-radius: 24px;
  background: var(--color-bg-card);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.25);
  /* 卡片跟随整体 va-fade 一起淡入，再叠一个 scale 进入更有"弹出"感 */
  transform: scale(0.92);
  animation: va-card-in 0.4s ease forwards;
}

@keyframes va-card-in {
  to {
    transform: scale(1);
  }
}

.va-logo {
  width: 88px;
  height: 88px;
  border-radius: 22px;
  box-shadow: 0 12px 36px rgba(24, 144, 255, 0.25);
  opacity: 0;
  transform: scale(0.4) rotate(-12deg);
  animation: va-logo-in 0.6s 0.05s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

.va-app-name {
  font-size: 30px;
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: 1px;
  opacity: 0;
  transform: translateY(12px);
  animation: va-fade-up 0.5s 0.35s ease forwards;
}

.va-version-chip {
  padding: 6px 18px;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--color-transfer) 0%, #5b9cf8 100%);
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.5px;
  box-shadow: 0 6px 18px rgba(24, 144, 255, 0.35);
  opacity: 0;
  transform: scale(0.6);
  animation: va-chip-in 0.55s 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

@keyframes va-logo-in {
  to {
    opacity: 1;
    transform: scale(1) rotate(0);
  }
}

@keyframes va-fade-up {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes va-chip-in {
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* 整体淡入淡出 */
.va-fade-enter-active,
.va-fade-leave-active {
  transition: opacity 0.4s ease;
}

.va-fade-enter-from,
.va-fade-leave-to {
  opacity: 0;
}

/* 移动端略小 */
@media (max-width: 600px) {
  .va-content {
    padding: 32px 40px;
  }

  .va-logo {
    width: 76px;
    height: 76px;
    border-radius: 20px;
  }

  .va-app-name {
    font-size: 26px;
  }

  .va-version-chip {
    font-size: 16px;
    padding: 5px 16px;
  }
}
</style>

<style>
/* 暗黑模式：卡片用 #1e1e1e（跟项目其他暗黑弹窗一致） */
html.dark .va-content {
  background: #1e1e1e;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.5);
}
</style>
