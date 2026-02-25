<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/Stores/auth'
import { useAgentStore } from '@/Stores/agent'
import { useNotificationStore } from '@/Stores/notifications'
import logoIconUrl from '@/assets/icons/logo_icone_header.png'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const agent = useAgentStore()
const notifStore = useNotificationStore()

const sidebarOpen = ref(true)
const mobileMenuOpen = ref(false)
const profileOpen = ref(false)
const notifOpen = ref(false)
const isMobile = ref(false)
const searchQuery = ref('')

function checkMobile() {
  isMobile.value = window.innerWidth < 1024
  if (isMobile.value) sidebarOpen.value = false
  else mobileMenuOpen.value = false
}

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  if (!agent.profile) {
    try { await agent.fetchProfile() } catch (_) {}
  }
  notifStore.fetchUnreadCount()
  notifStore.startPolling()
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', checkMobile)
  notifStore.stopPolling()
})

function toggleSidebar() {
  if (isMobile.value) mobileMenuOpen.value = !mobileMenuOpen.value
  else sidebarOpen.value = !sidebarOpen.value
}

function closeMobile() { mobileMenuOpen.value = false }

const initials = computed(() => {
  const name = agent.agencyName || auth.me?.username || auth.me?.phone || '?'
  return name.charAt(0).toUpperCase()
})

const navItems = [
  { to: '/agent', icon: 'dashboard', label: 'Tableau de bord', exact: true },
  { to: '/agent/listings', icon: 'content', label: 'Mes annonces' },
  { to: '/agent/analytics', icon: 'analytics', label: 'Statistiques' },
  { to: '/agent/visits', icon: 'visits', label: 'Visites' },
  { to: '/agent/wallet', icon: 'wallet', label: 'Revenus' },
  { to: '/agent/settings', icon: 'settings', label: 'Paramètres' },
]

function isActive(item: typeof navItems[0]) {
  if (item.exact) return route.path === item.to
  return route.path.startsWith(item.to)
}

async function logout() {
  profileOpen.value = false
  agent.$resetAgent()
  await auth.logout()
  router.push('/home')
}

function formatNotifTime(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return "À l'instant"
  if (mins < 60) return `il y a ${mins} min`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `il y a ${hours}h`
  const days = Math.floor(hours / 24)
  if (days < 7) return `il y a ${days}j`
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })
}

function handleSearch() {
  const q = searchQuery.value.trim()
  if (q) router.push({ name: 'agent-listings', query: { q } })
}

function toggleNotif() {
  notifOpen.value = !notifOpen.value
  if (notifOpen.value) {
    profileOpen.value = false
    notifStore.fetchNotifications()
  }
}

async function markAllRead() {
  await notifStore.markAllRead()
}

function closePopupsOnClickOutside(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (profileOpen.value && !target.closest('.agt-profile-menu')) {
    profileOpen.value = false
  }
  if (notifOpen.value && !target.closest('.agt-notif-wrapper')) {
    notifOpen.value = false
  }
}
onMounted(() => document.addEventListener('click', closePopupsOnClickOutside))
onBeforeUnmount(() => document.removeEventListener('click', closePopupsOnClickOutside))
</script>

<template>
  <div class="agt-app" :class="{ 'sidebar-open': sidebarOpen && !isMobile, 'sidebar-collapsed': !sidebarOpen && !isMobile }">
    <!-- HEADER -->
    <header class="agt-header">
      <div class="agt-header__start">
        <button class="agt-header__hamburger" @click="toggleSidebar" aria-label="Menu">
          <svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>
        </button>
        <router-link to="/agent" class="agt-header__logo">
          <img :src="logoIconUrl" alt="MonaJent" class="agt-header__icon" />
          <span class="agt-header__studio">Studio</span>
        </router-link>
      </div>

      <div class="agt-header__center">
        <form class="agt-header__search" @submit.prevent="handleSearch">
          <svg viewBox="0 0 24 24" width="20" height="20"><path fill="#606060" d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
          <input v-model="searchQuery" type="text" placeholder="Rechercher dans vos annonces" />
        </form>
      </div>

      <div class="agt-header__end">
        <router-link to="/agent/listings" class="agt-header__create" title="Nouvelle annonce">
          <svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
          <span class="agt-header__create-text">Nouvelle annonce</span>
        </router-link>

        <!-- Notifications Bell -->
        <div class="agt-notif-wrapper">
          <button class="agt-header__bell" @click.stop="toggleNotif" title="Notifications">
            <svg viewBox="0 0 24 24" width="22" height="22"><path fill="currentColor" d="M12 22c1.1 0 2-.9 2-2h-4a2 2 0 002 2zm6-6v-5c0-3.07-1.63-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.64 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/></svg>
            <span v-if="notifStore.unreadCount > 0" class="agt-header__bell-badge">{{ notifStore.unreadCount > 9 ? '9+' : notifStore.unreadCount }}</span>
          </button>
          <div v-if="notifOpen" class="agt-notif-panel">
            <div class="agt-notif-panel__header">
              <span class="agt-notif-panel__title">Notifications</span>
              <button v-if="notifStore.unreadCount > 0" class="agt-notif-panel__mark-all" @click="markAllRead">Tout lire</button>
            </div>
            <div v-if="notifStore.loading" class="agt-notif-panel__loading">Chargement...</div>
            <div v-else-if="notifStore.notifications.length === 0" class="agt-notif-panel__empty">Aucune notification</div>
            <div v-else class="agt-notif-panel__list">
              <div
                v-for="n in notifStore.notifications"
                :key="n.id"
                class="agt-notif-item"
                :class="{ unread: !n.is_read }"
                @click="notifStore.markRead([n.id]); notifOpen = false"
              >
                <div class="agt-notif-item__icon" :class="'cat-' + n.category.toLowerCase()">
                  <svg v-if="n.category === 'KYC'" viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/></svg>
                  <svg v-else-if="n.category === 'VISIT'" viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-2 .9-2 2v14a2 2 0 002 2h14a2 2 0 002-2V5a2 2 0 00-2-2zm0 16H5V8h14v11z"/></svg>
                  <svg v-else-if="n.category === 'WALLET'" viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M21 18v1c0 1.1-.9 2-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h14c1.1 0 2 .9 2 2v1h-9a2 2 0 00-2 2v8a2 2 0 002 2h9zm-9-2h10V8H12v8zm4-2.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/></svg>
                  <svg v-else viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M12 22c1.1 0 2-.9 2-2h-4a2 2 0 002 2zm6-6v-5c0-3.07-1.63-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.64 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/></svg>
                </div>
                <div class="agt-notif-item__body">
                  <div class="agt-notif-item__title">{{ n.title }}</div>
                  <div class="agt-notif-item__msg">{{ n.message }}</div>
                  <div class="agt-notif-item__time">{{ formatNotifTime(n.created_at) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="agt-profile-menu">
          <div class="agt-avatar-wrap">
            <button class="agt-header__avatar" :class="{ 'has-photo': agent.profilePhoto }" @click.stop="profileOpen = !profileOpen">
              <img v-if="agent.profilePhoto" :src="agent.profilePhoto" alt="" />
              <span v-else>{{ initials }}</span>
            </button>
            <svg v-if="agent.isVerified" class="agt-avatar-badge agt-avatar-badge--sm" viewBox="0 0 24 24" width="14" height="14"><circle cx="12" cy="12" r="11" fill="#1DA53F"/><path fill="#fff" d="M10 15.59l-3.29-3.3 1.41-1.41L10 12.76l5.88-5.88 1.41 1.41z"/></svg>
          </div>
          <div v-if="profileOpen" class="agt-profile-dropdown">
            <div class="agt-profile-dropdown__header">
              <div class="agt-avatar-wrap">
                <div class="agt-profile-dropdown__avatar" :class="{ 'has-photo': agent.profilePhoto }">
                  <img v-if="agent.profilePhoto" :src="agent.profilePhoto" alt="" />
                  <span v-else>{{ initials }}</span>
                </div>
                <svg v-if="agent.isVerified" class="agt-avatar-badge" viewBox="0 0 24 24" width="16" height="16"><circle cx="12" cy="12" r="11" fill="#1DA53F"/><path fill="#fff" d="M10 15.59l-3.29-3.3 1.41-1.41L10 12.76l5.88-5.88 1.41 1.41z"/></svg>
              </div>
              <div>
                <div class="agt-profile-dropdown__name">
                  {{ agent.agencyName || 'Agent' }}
                  <svg v-if="agent.isVerified" viewBox="0 0 24 24" width="14" height="14" style="vertical-align:middle;margin-left:3px"><circle cx="12" cy="12" r="11" fill="#1DA53F"/><path fill="#fff" d="M10 15.59l-3.29-3.3 1.41-1.41L10 12.76l5.88-5.88 1.41 1.41z"/></svg>
                </div>
                <div class="agt-profile-dropdown__phone">{{ auth.me?.phone }}</div>
              </div>
            </div>
            <div class="agt-profile-dropdown__sep"></div>
            <router-link to="/agent/settings" class="agt-profile-dropdown__item" @click="profileOpen = false">
              <svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
              Mon profil
            </router-link>
            <div class="agt-profile-dropdown__sep"></div>
            <button class="agt-profile-dropdown__item" @click="logout">
              <svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5-5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/></svg>
              Se déconnecter
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- MOBILE OVERLAY -->
    <div v-if="mobileMenuOpen" class="agt-overlay" @click="closeMobile"></div>

    <!-- SIDEBAR -->
    <aside class="agt-sidebar" :class="{ 'mobile-open': mobileMenuOpen }">
      <div class="agt-sidebar__profile" v-if="sidebarOpen || mobileMenuOpen">
        <div class="agt-avatar-wrap">
          <div class="agt-sidebar__avatar" :class="{ 'has-photo': agent.profilePhoto }">
            <img v-if="agent.profilePhoto" :src="agent.profilePhoto" alt="" />
            <span v-else>{{ initials }}</span>
          </div>
          <svg v-if="agent.isVerified" class="agt-avatar-badge" viewBox="0 0 24 24" width="16" height="16"><circle cx="12" cy="12" r="11" fill="#1DA53F"/><path fill="#fff" d="M10 15.59l-3.29-3.3 1.41-1.41L10 12.76l5.88-5.88 1.41 1.41z"/></svg>
        </div>
        <div class="agt-sidebar__info">
          <div class="agt-sidebar__agency">{{ agent.agencyName || 'Mon agence' }}</div>
          <div class="agt-sidebar__sub">{{ auth.me?.phone }}</div>
        </div>
      </div>
      <div class="agt-sidebar__profile agt-sidebar__profile--mini" v-else>
        <div class="agt-avatar-wrap">
          <div class="agt-sidebar__avatar agt-sidebar__avatar--sm" :class="{ 'has-photo': agent.profilePhoto }">
            <img v-if="agent.profilePhoto" :src="agent.profilePhoto" alt="" />
            <span v-else>{{ initials }}</span>
          </div>
          <svg v-if="agent.isVerified" class="agt-avatar-badge agt-avatar-badge--sm" viewBox="0 0 24 24" width="12" height="12"><circle cx="12" cy="12" r="11" fill="#1DA53F"/><path fill="#fff" d="M10 15.59l-3.29-3.3 1.41-1.41L10 12.76l5.88-5.88 1.41 1.41z"/></svg>
        </div>
      </div>

      <nav class="agt-sidebar__nav">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="agt-sidebar__item"
          :class="{ active: isActive(item) }"
          @click="closeMobile"
        >
          <!-- Dashboard -->
          <svg v-if="item.icon === 'dashboard'" viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/></svg>
          <!-- Content -->
          <svg v-else-if="item.icon === 'content'" viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8 12.5v-9l6 4.5-6 4.5z"/></svg>
          <!-- Analytics -->
          <svg v-else-if="item.icon === 'analytics'" viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg>
          <!-- Visits -->
          <svg v-else-if="item.icon === 'visits'" viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-2 .9-2 2v14a2 2 0 002 2h14a2 2 0 002-2V5a2 2 0 00-2-2zm0 16H5V8h14v11zM9 10H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2z"/></svg>
          <!-- Wallet -->
          <svg v-else-if="item.icon === 'wallet'" viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z"/></svg>
          <!-- Settings -->
          <svg v-else-if="item.icon === 'settings'" viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 00.12-.61l-1.92-3.32a.49.49 0 00-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.48.48 0 00-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96a.49.49 0 00-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.07.62-.07.94s.02.64.07.94l-2.03 1.58a.49.49 0 00-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6A3.6 3.6 0 1115.6 12 3.6 3.6 0 0112 15.6z"/></svg>
          <span class="agt-sidebar__label">{{ item.label }}</span>
        </router-link>
      </nav>

    </aside>

    <!-- MAIN -->
    <main class="agt-main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.agt-app {
  --header-h: 56px;
  --sidebar-w: 240px;
  --sidebar-collapsed-w: 72px;
  --green: #1DA53F;
  --green-dark: #178A33;
  --green-light: rgba(29, 165, 63, 0.08);
  --bg: #f8f8f8;
  --text: #0F0F0F;
  --text2: #272727;
  --text3: #606060;
  --border: #E0E0E0;
  --card: #fff;
  min-height: 100vh;
  background: var(--bg);
}

/* ====== HEADER ====== */
.agt-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: var(--header-h);
  background: var(--card);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 16px;
  z-index: 100;
  gap: 16px;
}

.agt-header__start {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.agt-header__hamburger {
  width: 40px;
  height: 40px;
  border: none;
  background: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text3);
  transition: background .15s;
}
.agt-header__hamburger:hover { background: #f2f2f2; }

.agt-header__logo {
  display: flex;
  align-items: center;
  gap: 4px;
  text-decoration: none;
}
.agt-header__icon {
  height: 36px;
  width: auto;
}
.agt-header__studio {
  font-family: Roboto, 'Noto Sans', sans-serif;
  font-size: 20px;
  font-weight: 500;
  font-style: normal;
  color: #272727;
  line-height: normal;
  margin-left: 4px;
  letter-spacing: -0.2px;
}

.agt-header__center {
  flex: 1;
  max-width: 540px;
  margin: 0 auto;
}

.agt-header__search {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 40px;
  padding: 0 16px;
  height: 36px;
  transition: border-color .15s, box-shadow .15s;
}
.agt-header__search:focus-within {
  border-color: var(--green);
  box-shadow: 0 0 0 3px rgba(29,165,63,.12);
}
.agt-header__search input {
  border: none;
  background: none;
  outline: none;
  flex: 1;
  font-size: 14px;
  color: var(--text);
}

.agt-header__end {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.agt-header__create {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 16px;
  height: 36px;
  border-radius: 20px;
  background: var(--green-light);
  border: none;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  color: var(--green);
  cursor: pointer;
  transition: background .15s;
  white-space: nowrap;
}
.agt-header__create:hover {
  background: rgba(29, 165, 63, 0.15);
}

.agt-avatar-wrap { position: relative; display: inline-flex; }
.agt-avatar-badge {
  position: absolute; bottom: -1px; right: -2px;
  filter: drop-shadow(0 1px 2px rgba(0,0,0,.25));
}
.agt-avatar-badge--sm { bottom: -1px; right: -3px; }

.agt-header__avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--green);
  color: #fff;
  border: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.agt-header__avatar.has-photo { background: none; }
.agt-header__avatar img { width: 100%; height: 100%; object-fit: cover; }

.agt-profile-menu { position: relative; }

.agt-profile-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 280px;
  background: var(--card);
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0,0,0,.15);
  border: 1px solid var(--border);
  z-index: 200;
  overflow: hidden;
}

.agt-profile-dropdown__header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
}

.agt-profile-dropdown__avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--green);
  color: #fff;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}
.agt-profile-dropdown__avatar.has-photo { background: none; }
.agt-profile-dropdown__avatar img { width: 100%; height: 100%; object-fit: cover; }

.agt-profile-dropdown__name {
  font-weight: 600;
  font-size: 14px;
  color: var(--text);
}
.agt-profile-dropdown__phone {
  font-size: 13px;
  color: var(--text3);
}

.agt-profile-dropdown__sep {
  height: 1px;
  background: var(--border);
}

.agt-profile-dropdown__item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  font-size: 14px;
  color: var(--text);
  text-decoration: none;
  cursor: pointer;
  border: none;
  background: none;
  width: 100%;
  text-align: left;
  transition: background .1s;
}
.agt-profile-dropdown__item:hover { background: #f2f2f2; }

/* ====== OVERLAY ====== */
.agt-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.4);
  z-index: 149;
}

/* ====== SIDEBAR ====== */
.agt-sidebar {
  position: fixed;
  top: var(--header-h);
  left: 0;
  bottom: 0;
  width: var(--sidebar-collapsed-w);
  background: var(--card);
  border-right: 1px solid var(--border);
  overflow-y: auto;
  overflow-x: hidden;
  z-index: 150;
  transition: width .2s ease;
  display: flex;
  flex-direction: column;
}

.sidebar-open .agt-sidebar { width: var(--sidebar-w); }

.agt-sidebar__profile {
  padding: 20px 16px 12px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.agt-sidebar__profile--mini {
  justify-content: center;
  padding: 16px 0;
}

.agt-sidebar__avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--green);
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}
.agt-sidebar__avatar.has-photo { background: none; }
.agt-sidebar__avatar img { width: 100%; height: 100%; object-fit: cover; }
.agt-sidebar__avatar--sm {
  width: 32px;
  height: 32px;
  font-size: 14px;
}

.agt-sidebar__info { min-width: 0; }
.agt-sidebar__agency {
  font-weight: 600;
  font-size: 14px;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.agt-sidebar__sub {
  font-size: 12px;
  color: var(--text3);
}

.agt-sidebar__nav {
  flex: 1;
  padding: 4px 8px;
}

.agt-sidebar__item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 12px;
  height: 40px;
  border-radius: 10px;
  text-decoration: none;
  color: var(--text);
  font-size: 14px;
  white-space: nowrap;
  transition: background .1s;
  cursor: pointer;
}
.agt-sidebar__item:hover { background: #f2f2f2; }
.agt-sidebar__item.active {
  background: var(--green-light);
  color: var(--green);
  font-weight: 600;
}
.agt-sidebar__item.active svg { color: var(--green); }

.sidebar-collapsed .agt-sidebar__item {
  justify-content: center;
  padding: 0;
}
.sidebar-collapsed .agt-sidebar__label { display: none; }


/* ====== NOTIFICATIONS ====== */
.agt-notif-wrapper { position: relative; }
.agt-header__bell {
  background: none; border: none; cursor: pointer; position: relative;
  display: flex; align-items: center; justify-content: center;
  width: 40px; height: 40px; border-radius: 50%;
  color: #606060; transition: background .15s;
}
.agt-header__bell:hover { background: #f2f2f2; }
.agt-header__bell-badge {
  position: absolute; top: 2px; right: 2px;
  min-width: 18px; height: 18px; padding: 0 5px;
  background: #e53e3e; color: #fff; font-size: 11px; font-weight: 700;
  border-radius: 9px; display: flex; align-items: center; justify-content: center;
  line-height: 1;
}
.agt-notif-panel {
  position: absolute; top: calc(100% + 8px); right: 0; z-index: 200;
  width: 380px; max-height: 460px; background: #fff;
  border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,.15);
  overflow: hidden; display: flex; flex-direction: column;
}
.agt-notif-panel__header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px; border-bottom: 1px solid #eee;
}
.agt-notif-panel__title { font-weight: 700; font-size: .95rem; }
.agt-notif-panel__mark-all {
  background: none; border: none; color: var(--green); font-size: .82rem;
  cursor: pointer; font-weight: 600;
}
.agt-notif-panel__loading, .agt-notif-panel__empty {
  padding: 2rem; text-align: center; color: #888; font-size: .9rem;
}
.agt-notif-panel__list { overflow-y: auto; flex: 1; }
.agt-notif-item {
  display: flex; gap: 12px; padding: 12px 16px;
  cursor: pointer; transition: background .12s; border-bottom: 1px solid #f5f5f5;
}
.agt-notif-item:hover { background: #f9f9f9; }
.agt-notif-item.unread { background: #f0fdf4; }
.agt-notif-item__icon {
  flex-shrink: 0; width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
}
.agt-notif-item__icon.cat-kyc { background: #dcfce7; color: #16a34a; }
.agt-notif-item__icon.cat-visit { background: #dbeafe; color: #2563eb; }
.agt-notif-item__icon.cat-wallet { background: #fef3c7; color: #d97706; }
.agt-notif-item__icon.cat-system { background: #f3f4f6; color: #6b7280; }
.agt-notif-item__body { flex: 1; min-width: 0; }
.agt-notif-item__title { font-weight: 600; font-size: .85rem; margin-bottom: 2px; }
.agt-notif-item__msg { font-size: .8rem; color: #555; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.agt-notif-item__time { font-size: .72rem; color: #999; margin-top: 4px; }

@media (max-width: 480px) {
  .agt-notif-panel { width: calc(100vw - 16px); right: -60px; }
}

/* ====== MAIN ====== */
.agt-main {
  margin-top: var(--header-h);
  margin-left: var(--sidebar-collapsed-w);
  padding: 24px;
  min-height: calc(100vh - var(--header-h));
  transition: margin-left .2s ease;
}
.sidebar-open .agt-main { margin-left: var(--sidebar-w); }

/* ====== MOBILE ====== */
@media (max-width: 1023px) {
  .agt-header__center { display: none; }
  .agt-header__create-text { display: none; }
  .agt-header__create { padding: 0 10px; }
  .agt-header__studio { font-size: 18px; }
  .agt-header__icon { height: 30px; }

  .agt-sidebar {
    width: var(--sidebar-w);
    transform: translateX(-100%);
    transition: transform .25s ease;
    z-index: 151;
  }
  .agt-sidebar.mobile-open { transform: translateX(0); }

  .agt-main {
    margin-left: 0;
    padding: 16px;
  }
}
</style>
