import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/Stores/auth'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/home' },
  { path: '/home', name: 'home', component: () => import('@/views/HomePage.vue') },
  { path: '/auth/login', name: 'login', component: () => import('@/views/auth/LoginView.vue') },
  { path: '/auth/join', name: 'signup-choice', component: () => import('@/views/auth/SignupChoiceView.vue') },
  { path: '/auth/signup/client', name: 'signup-client', component: () => import('@/views/auth/SignupClientView.vue') },
  { path: '/auth/signup/agent', name: 'signup-agent', component: () => import('@/views/auth/SignupAgentView.vue') },
  { path: '/client', name: 'client-home', component: () => import('@/views/client/ClientHome.vue') },
  { path: '/agent', name: 'agent-home', component: () => import('@/views/agent/AgentHome.vue') },
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
  // Redirection post-login simple: si l'utilisateur va sur /home et est connecté, on peut suggérer sa home
  if (to.path === '/' || to.path === '/home') {
    if (auth.me?.role === 'AGENT') return { name: 'agent-home' }
    if (auth.me?.role === 'CLIENT') return { name: 'client-home' }
  }
  return true
})

export default router
