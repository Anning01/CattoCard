<script setup lang="ts">
import { useAppStore } from '@/stores/app'
import { CheckCircleIcon, XCircleIcon, ExclamationTriangleIcon, InformationCircleIcon } from '@heroicons/vue/24/solid'

const appStore = useAppStore()

const iconMap = {
  success: CheckCircleIcon,
  error: XCircleIcon,
  warning: ExclamationTriangleIcon,
  info: InformationCircleIcon,
}

const colorMap = {
  success: 'text-green-500',
  error: 'text-red-500',
  warning: 'text-amber-500',
  info: 'text-blue-500',
}
</script>

<template>
  <div class="fixed top-20 left-1/2 -translate-x-1/2 z-[100] flex flex-col gap-2 items-center">
    <TransitionGroup name="toast">
      <div
        v-for="toast in appStore.toasts"
        :key="toast.id"
        class="flex items-center gap-3 px-4 py-3 bg-white rounded-xl shadow-lg border border-gray-100 min-w-[280px] max-w-sm"

      >
        <component :is="iconMap[toast.type]" class="w-5 h-5 shrink-0" :class="colorMap[toast.type]" />
        <span class="text-sm text-gray-700">{{ toast.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-enter-active {
  animation: slideDown 0.3s ease-out;
}

.toast-leave-active {
  animation: slideUp 0.2s ease-in forwards;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideUp {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-10px);
  }
}
</style>
