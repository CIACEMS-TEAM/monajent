import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/Stores/auth'
import { useAgentStore } from '@/Stores/agent'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/home' },

  {
    path: '/home',
    component: () => import('@/views/HomePage.vue'),
    children: [
      { path: '', name: 'home', component: () => import('@/views/HomeListings.vue') },
      { path: 'annonce/:slug', name: 'public-listing', component: () => import('@/views/public/PublicListingView.vue'), props: true },
      { path: 'dashboard', name: 'client-dashboard', component: () => import('@/views/client/ClientDashboard.vue'), meta: { requiresClient: true } },
      { path: 'favorites', name: 'client-favorites', component: () => import('@/views/client/ClientFavorites.vue'), meta: { requiresClient: true } },
      { path: 'history', name: 'client-history', component: () => import('@/views/client/ClientHistory.vue'), meta: { requiresClient: true } },
      { path: 'packs', name: 'client-packs', component: () => import('@/views/client/ClientPacks.vue'), meta: { requiresClient: true } },
      { path: 'payments', name: 'client-payments', component: () => import('@/views/client/ClientPayments.vue'), meta: { requiresClient: true } },
      { path: 'visits', name: 'client-visits', component: () => import('@/views/client/ClientVisits.vue'), meta: { requiresClient: true } },
      { path: 'reports', name: 'client-reports', component: () => import('@/views/client/ClientReports.vue'), meta: { requiresClient: true } },
      { path: 'profile', name: 'client-profile', component: () => import('@/views/client/ClientProfile.vue'), meta: { requiresClient: true } },
      { path: 'support', name: 'client-support', component: () => import('@/views/support/SupportListView.vue'), meta: { requiresAuth: true } },
      { path: 'support/new', name: 'client-support-new', component: () => import('@/views/support/SupportCreateView.vue'), meta: { requiresAuth: true } },
      { path: 'support/:id', name: 'client-support-detail', component: () => import('@/views/support/SupportDetailView.vue'), meta: { requiresAuth: true }, props: true },
    ],
  },

  { path: '/annonces/:slug', redirect: to => ({ name: 'public-listing', params: { slug: to.params.slug } }) },

  // Legal
  { path: '/legal/cgu', name: 'legal-cgu', component: () => import('@/views/legal/LegalCGU.vue') },
  { path: '/legal/confidentialite', name: 'legal-privacy', component: () => import('@/views/legal/LegalPrivacy.vue') },
  { path: '/legal/conditions-agents', name: 'legal-agent', component: () => import('@/views/legal/LegalAgentConditions.vue') },

  // Auth
  { path: '/auth/login', name: 'login', component: () => import('@/views/auth/LoginView.vue') },
  { path: '/auth/join', name: 'signup-choice', component: () => import('@/views/auth/SignupChoiceView.vue') },
  { path: '/auth/signup/client', name: 'signup-client', component: () => import('@/views/auth/SignupClientView.vue') },
  { path: '/auth/signup/agent', name: 'signup-agent', component: () => import('@/views/auth/SignupAgentView.vue') },

  // Agent
  {
    path: '/agent/onboarding',
    name: 'agent-onboarding',
    component: () => import('@/views/agent/AgentOnboarding.vue'),
    meta: { requiresAgent: true },
  },
  {
    path: '/agent',
    component: () => import('@/layouts/AgentLayout.vue'),
    meta: { requiresAgent: true },
    children: [
      { path: '', name: 'agent-home', component: () => import('@/views/agent/AgentDashboard.vue') },
      { path: 'listings', name: 'agent-listings', component: () => import('@/views/agent/AgentListings.vue') },
      { path: 'analytics', name: 'agent-analytics', component: () => import('@/views/agent/AgentAnalytics.vue') },
      { path: 'visits', name: 'agent-visits', component: () => import('@/views/agent/AgentVisits.vue') },
      { path: 'wallet', name: 'agent-wallet', component: () => import('@/views/agent/AgentWallet.vue') },
      { path: 'settings', name: 'agent-settings', component: () => import('@/views/agent/AgentSettings.vue') },
      { path: 'support', name: 'agent-support', component: () => import('@/views/support/SupportListView.vue') },
      { path: 'support/new', name: 'agent-support-new', component: () => import('@/views/support/SupportCreateView.vue') },
      { path: 'support/:id', name: 'agent-support-detail', component: () => import('@/views/support/SupportDetailView.vue'), props: true },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) return savedPosition
    return { top: 0 }
  },
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.bootstrapped) {
    try { await auth.bootstrap() } catch (_) { /* noop */ }
  }

  if (to.path === '/' || to.path === '/home') {
    if (auth.me?.role === 'AGENT') return { name: 'agent-home' }
  }

  if (to.meta.requiresAuth) {
    if (!auth.me) return { name: 'home', query: { redirect: to.fullPath } }
  }

  if (to.meta.requiresAgent) {
    if (!auth.me) return { name: 'login', query: { redirect: to.fullPath } }
    if (auth.me.role !== 'AGENT') return { name: 'home' }

    if (to.name !== 'agent-onboarding') {
      const agentStore = useAgentStore()
      if (!agentStore.profile) {
        try { await agentStore.fetchProfile() } catch (_) { /* noop */ }
      }
      if (!agentStore.isProfileComplete) {
        return { name: 'agent-onboarding' }
      }
    }
  }

  if (to.meta.requiresClient) {
    if (!auth.me) return { name: 'login', query: { redirect: to.fullPath } }
    if (auth.me.role !== 'CLIENT') return { name: 'home' }
  }

  return true
})

export default router
