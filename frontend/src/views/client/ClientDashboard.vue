<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useClientStore } from '@/Stores/client'
import { useAuthStore } from '@/Stores/auth'
import keyVirtImg from '@/assets/icons/key_virt.png'
import keyPhyImg from '@/assets/icons/key_phy.png'

const client = useClientStore()
const auth = useAuthStore()
const router = useRouter()

onMounted(() => {
  client.fetchDashboard()
})

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
}

async function handleLogout() {
  await auth.logout()
  router.push({ name: 'home' })
}
</script>

<template>
  <div class="cd">
    <div v-if="client.dashboardLoading && !client.dashboard" class="cd__loading">
      <div class="cd__spinner"></div>
      <span>Chargement...</span>
    </div>

    <template v-else-if="client.dashboard">
      <!-- Welcome -->
      <div class="cd__welcome">
        <router-link to="/home/profile" class="cd__welcome-avatar">
          {{ (client.dashboard.username || client.dashboard.phone).charAt(0).toUpperCase() }}
        </router-link>
        <div class="cd__welcome-text">
          <h1 class="cd__welcome-name">
            Bonjour {{ client.dashboard.username || client.dashboard.phone }}
          </h1>
          <p class="cd__welcome-since">Membre depuis le {{ formatDate(client.dashboard.member_since) }}</p>
        </div>
        <router-link to="/home/profile" class="cd__welcome-edit" title="Mon profil">
          <svg viewBox="0 0 24 24" width="20" height="20"><path fill="#fff" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
        </router-link>
      </div>

      <!-- KPI Cards -->
      <div class="cd__kpis">
        <router-link to="/home/packs" class="cd__kpi cd__kpi--keys">
          <div class="cd__kpi-icon">
            <img :src="keyVirtImg" alt="" />
          </div>
          <div class="cd__kpi-data">
            <span class="cd__kpi-val">{{ client.dashboard.total_virtual_remaining }}</span>
            <span class="cd__kpi-label">Clés virtuelles</span>
          </div>
        </router-link>

        <router-link to="/home/packs" class="cd__kpi cd__kpi--phy">
          <div class="cd__kpi-icon">
            <img :src="keyPhyImg" alt="" />
          </div>
          <div class="cd__kpi-data">
            <span class="cd__kpi-val">{{ client.dashboard.total_physical_available }}</span>
            <span class="cd__kpi-label">Clés physiques</span>
          </div>
        </router-link>

        <router-link to="/home/visits" class="cd__kpi cd__kpi--visits">
          <div class="cd__kpi-icon cd__kpi-icon--svg">
            <svg viewBox="0 0 24 24" width="28" height="28"><path fill="#ea580c" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 010-5 2.5 2.5 0 010 5z"/></svg>
          </div>
          <div class="cd__kpi-data">
            <span class="cd__kpi-val">{{ client.dashboard.visits_in_progress }}</span>
            <span class="cd__kpi-label">Visites en cours</span>
          </div>
        </router-link>

        <router-link to="/home/favorites" class="cd__kpi cd__kpi--favs">
          <div class="cd__kpi-icon cd__kpi-icon--svg">
            <svg viewBox="0 0 24 24" width="28" height="28"><path fill="#ef4444" d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3z"/></svg>
          </div>
          <div class="cd__kpi-data">
            <span class="cd__kpi-val">{{ client.dashboard.favorites_count }}</span>
            <span class="cd__kpi-label">Favoris</span>
          </div>
        </router-link>

        <router-link to="/home/history" class="cd__kpi cd__kpi--videos">
          <div class="cd__kpi-icon cd__kpi-icon--svg">
            <svg viewBox="0 0 24 24" width="28" height="28"><path fill="#2563eb" d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8 12.5v-9l6 4.5-6 4.5z"/></svg>
          </div>
          <div class="cd__kpi-data">
            <span class="cd__kpi-val">{{ client.dashboard.total_videos_watched }}</span>
            <span class="cd__kpi-label">Vidéos visionnées</span>
          </div>
        </router-link>

        <div class="cd__kpi cd__kpi--packs">
          <div class="cd__kpi-icon cd__kpi-icon--svg">
            <svg viewBox="0 0 24 24" width="28" height="28"><path fill="#1DA53F" d="M18 6h-2c0-2.21-1.79-4-4-4S8 3.79 8 6H6c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-6-2c1.1 0 2 .9 2 2h-4c0-1.1.9-2 2-2zm6 16H6V8h2v2c0 .55.45 1 1 1s1-.45 1-1V8h4v2c0 .55.45 1 1 1s1-.45 1-1V8h2v12z"/></svg>
          </div>
          <div class="cd__kpi-data">
            <span class="cd__kpi-val">{{ client.dashboard.active_packs_count }}</span>
            <span class="cd__kpi-label">Packs actifs</span>
          </div>
        </div>
      </div>

      <!-- Quick links -->
      <div class="cd__quick">
        <h2 class="cd__section-title">Accès rapide</h2>
        <div class="cd__quick-grid">
          <router-link to="/home/packs" class="cd__quick-link">
            <i class="pi pi-shopping-bag"></i>
            <span>Mes packs</span>
          </router-link>
          <router-link to="/home/visits" class="cd__quick-link">
            <i class="pi pi-map-marker"></i>
            <span>Mes visites</span>
          </router-link>
          <router-link to="/home/favorites" class="cd__quick-link">
            <i class="pi pi-heart"></i>
            <span>Mes favoris</span>
          </router-link>
          <router-link to="/home/history" class="cd__quick-link">
            <i class="pi pi-history"></i>
            <span>Historique vidéos</span>
          </router-link>
          <router-link to="/home/payments" class="cd__quick-link">
            <i class="pi pi-credit-card"></i>
            <span>Paiements</span>
          </router-link>
          <router-link to="/home/reports" class="cd__quick-link">
            <i class="pi pi-flag"></i>
            <span>Signalements</span>
          </router-link>
          <router-link to="/home/profile" class="cd__quick-link">
            <i class="pi pi-user"></i>
            <span>Mon profil</span>
          </router-link>
          <router-link to="/home/support" class="cd__quick-link">
            <i class="pi pi-question-circle"></i>
            <span>Aide & Support</span>
          </router-link>
        </div>
      </div>

      <!-- Stats summary -->
      <div class="cd__stats">
        <h2 class="cd__section-title">Activité</h2>
        <div class="cd__stats-row">
          <div class="cd__stat-item">
            <span class="cd__stat-val">{{ client.dashboard.total_visits_requested }}</span>
            <span class="cd__stat-label">Visites demandées</span>
          </div>
          <div class="cd__stat-item">
            <span class="cd__stat-val">{{ client.dashboard.total_videos_watched }}</span>
            <span class="cd__stat-label">Vidéos vues</span>
          </div>
          <div class="cd__stat-item">
            <span class="cd__stat-val">{{ client.dashboard.favorites_count }}</span>
            <span class="cd__stat-label">Biens en favoris</span>
          </div>
        </div>
      </div>

      <!-- Logout (visible surtout sur mobile comme point d'accès principal) -->
      <button class="cd__logout" @click="handleLogout">
        <svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/></svg>
        <span>Se déconnecter</span>
      </button>
    </template>
  </div>
</template>

<style scoped>
.cd { max-width: 900px; margin: 0 auto; padding: 0 16px; }

.cd__loading {
  display: flex; align-items: center; justify-content: center;
  gap: 12px; padding: 80px 0; color: #606060;
}
.cd__spinner {
  width: 28px; height: 28px; border: 3px solid #e0e0e0;
  border-top-color: #1DA53F; border-radius: 50%;
  animation: cd-spin 0.7s linear infinite;
}
@keyframes cd-spin { to { transform: rotate(360deg); } }

/* Welcome */
.cd__welcome {
  display: flex; align-items: center; gap: 14px;
  margin-bottom: 24px; padding: 20px;
  background: linear-gradient(135deg, #1DA53F 0%, #168a34 100%);
  border-radius: 16px; color: #fff;
}
.cd__welcome-avatar {
  width: 52px; height: 52px; border-radius: 50%;
  background: rgba(255,255,255,0.2);
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 700; flex-shrink: 0;
  text-decoration: none; color: #fff;
  transition: background 0.15s;
}
.cd__welcome-avatar:hover { background: rgba(255,255,255,0.3); }
.cd__welcome-text { flex: 1; min-width: 0; }
.cd__welcome-name { font-size: 20px; font-weight: 700; margin: 0; }
.cd__welcome-since { font-size: 13px; opacity: 0.85; margin: 2px 0 0; }
.cd__welcome-edit {
  display: flex; align-items: center; justify-content: center;
  width: 36px; height: 36px; border-radius: 50%;
  background: rgba(255,255,255,0.15);
  flex-shrink: 0; transition: background 0.15s;
}
.cd__welcome-edit:hover { background: rgba(255,255,255,0.3); }

/* KPI */
.cd__kpis {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 28px;
}
.cd__kpi {
  display: flex; align-items: center; gap: 12px;
  padding: 16px; border-radius: 12px;
  background: #fff; border: 1px solid #e0e0e0;
  text-decoration: none; color: inherit;
  transition: box-shadow 0.15s, transform 0.15s;
}
.cd__kpi:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.07); transform: translateY(-1px); }
.cd__kpi-icon { flex-shrink: 0; }
.cd__kpi-icon img { width: 36px; height: 36px; }
.cd__kpi-icon--svg { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; }
.cd__kpi-data { display: flex; flex-direction: column; }
.cd__kpi-val { font-size: 24px; font-weight: 700; color: #0f0f0f; line-height: 1; }
.cd__kpi-label { font-size: 12px; color: #888; margin-top: 2px; }

/* Section title */
.cd__section-title {
  font-size: 16px; font-weight: 600; color: #0f0f0f;
  margin: 0 0 14px;
}

/* Quick links */
.cd__quick { margin-bottom: 28px; }
.cd__quick-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.cd__quick-link {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 16px; border-radius: 10px;
  background: #fafafa; border: 1px solid #eee;
  text-decoration: none; color: #333;
  font-size: 14px; font-weight: 500;
  transition: background 0.15s, border-color 0.15s;
}
.cd__quick-link:hover { background: #f0f0f0; border-color: #ccc; }
.cd__quick-link i { font-size: 18px; color: #1DA53F; }

/* Stats */
.cd__stats { margin-bottom: 28px; }
.cd__stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.cd__stat-item {
  text-align: center; padding: 18px 12px;
  background: #fff; border: 1px solid #e0e0e0;
  border-radius: 12px;
}
.cd__stat-val {
  display: block; font-size: 28px; font-weight: 700; color: #1DA53F;
}
.cd__stat-label {
  display: block; font-size: 12px; color: #888; margin-top: 4px;
}

/* Logout */
.cd__logout {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  width: 100%; padding: 14px; margin-bottom: 32px;
  border: 1px solid #e5e5e5; border-radius: 12px;
  background: #fff; color: #d32f2f;
  font-size: 15px; font-weight: 500;
  cursor: pointer; transition: background 0.15s, border-color 0.15s;
}
.cd__logout:hover { background: #fef2f2; border-color: #fecaca; }

@media (max-width: 768px) {
  .cd__kpis { grid-template-columns: repeat(2, 1fr); }
  .cd__quick-grid { grid-template-columns: repeat(2, 1fr); }
  .cd__stats-row { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 480px) {
  .cd { padding: 0 12px; }
  .cd__kpis { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .cd__kpi { padding: 12px 10px; gap: 8px; }
  .cd__kpi-val { font-size: 20px; }
  .cd__kpi-icon img { width: 28px; height: 28px; }
  .cd__kpi-icon--svg { width: 28px; height: 28px; }
  .cd__kpi-icon--svg svg { width: 22px; height: 22px; }
  .cd__quick-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .cd__quick-link { padding: 12px; font-size: 13px; }
  .cd__stats-row { grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .cd__stat-item { padding: 12px 6px; }
  .cd__stat-val { font-size: 22px; }
  .cd__welcome { padding: 16px; }
  .cd__welcome-name { font-size: 17px; }
}
</style>
