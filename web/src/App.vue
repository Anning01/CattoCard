<script setup lang="ts">
import { onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { useCartStore } from '@/stores/cart'
import ToastContainer from '@/components/common/ToastContainer.vue'

const appStore = useAppStore()
const cartStore = useCartStore()

onMounted(() => {
  appStore.initTheme()
  cartStore.initialize()
})
</script>

<template>
  <router-view />
  <ToastContainer />
</template>
