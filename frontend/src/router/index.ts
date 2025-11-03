import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/Stores/auth'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/auth/join' },
  { path: '/auth/login', name: 'login', component: () => import('@/views/auth/LoginView.vue') },
  { path: '/auth/join', name: 'signup-choice', component: () => import('@/views/auth/SignupChoiceView.vue') },
  { path: '/auth/signup/client', name: 'signup-client', component: () => import('@/views/auth/SignupClientView.vue') },
  { path: '/auth/signup/agent', name: 'signup-agent', component: () => import('@/views/auth/SignupAgentView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  // Exemple de route protégée plus tard: if (to.meta.requiresAuth)
  const auth = useAuthStore()
  if (!auth.bootstrapped) {
    try { await auth.bootstrap() } catch (_) { /* noop */ }
  }
  return true
})

export default router
