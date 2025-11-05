<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/Stores/auth'

const auth = useAuthStore()
onMounted(() => {
  // tente un refresh silencieux au démarrage
  if (!auth.bootstrapped) auth.bootstrap()
})
</script>

<template>
  <router-view />
</template>

<style scoped>
/* conteneur minimal */
:host { display: block; }
</style>
