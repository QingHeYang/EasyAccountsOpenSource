<script setup lang="ts">
defineProps<{
  visible?: boolean
}>()

const emit = defineEmits<{
  click: []
}>()
</script>

<template>
  <Transition name="scale">
    <button
      v-show="visible"
      class="ai-trigger-btn"
      @click="emit('click')"
    >
      <span class="ai-text">AI+</span>
    </button>
  </Transition>
</template>

<style scoped>
.ai-trigger-btn {
  position: fixed;
  right: 24px;
  bottom: 24px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: none;
  background: var(--color-transfer);
  color: #fff;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.4);
  transition: transform 0.2s, box-shadow 0.2s;
  z-index: 150;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-trigger-btn:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 24px rgba(24, 144, 255, 0.5);
}

.ai-text {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

/* 缩放动画 */
.scale-enter-active,
.scale-leave-active {
  transition: transform 0.2s, opacity 0.2s;
}

.scale-enter-from,
.scale-leave-to {
  transform: scale(0.5);
  opacity: 0;
}
</style>
