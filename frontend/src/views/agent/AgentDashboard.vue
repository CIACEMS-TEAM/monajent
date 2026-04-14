<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useAgentStore } from '@/Stores/agent'
import { mediaUrl } from '@/services/http'

const agent = useAgentStore()

onMounted(async () => {
  try {
    await Promise.all([
      agent.fetchDashboard(),
      agent.listings.length ? Promise.resolve() : agent.fetchListings(),
    ])
  } catch (_) {}
})

const dash = computed(() => agent.dashboard)

function formatPrice(n: number | string): string {
  return Number(n).toLocaleString('fr-FR') + ' F'
}

function statusLabel(s: string) {
  const map: Record<string, string> = { ACTIF: 'Active', INACTIF: 'Inactive', EXPIRED: 'Expirée', SUSPENDED: 'Suspendue' }
  return map[s] || s
}

function statusClass(s: string) {
  return s === 'ACTIF' ? 'published' : s === 'INACTIF' ? 'draft' : 'expired'
}
</script>

<template>
  <div class="db">
    <h1 class="db-title">
      Tableau de bord
      <svg v-if="agent.isVerified" class="db-title__badge" viewBox="0 0 24 24" width="20" height="20" title="Agent vérifié"><circle cx="12" cy="12" r="11" fill="#1DA53F"/><path fill="#fff" d="M10 15.59l-3.29-3.3 1.41-1.41L10 12.76l5.88-5.88 1.41 1.41z"/></svg>
    </h1>

    <div v-if="agent.dashboardLoading && !dash" class="db-loading">Chargement...</div>

    <template v-else-if="dash">
      <!-- ===== TOP ROW: 3 cards ===== -->
      <div class="db-top">
        <!-- Performance -->
        <section class="db-card">
          <h2 class="db-card__title">Performance de la dernière annonce</h2>
          <div v-if="dash.latest_listing" class="db-perf">
            <div class="db-perf__thumb">
              <img v-if="dash.latest_listing.cover_image" :src="mediaUrl(dash.latest_listing.cover_image)!" :alt="dash.latest_listing.title" />
              <svg v-else viewBox="0 0 24 24" width="28" height="28"><path fill="#ccc" d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>
            </div>
            <div class="db-perf__name">{{ dash.latest_listing.title }}</div>
            <div class="db-perf__stats">
              <div class="db-perf__stat"><span class="db-perf__val">{{ dash.latest_listing.views_count }}</span><span class="db-perf__lbl">Vues</span></div>
              <div class="db-perf__stat"><span class="db-perf__val">{{ dash.latest_listing.favorites_count }}</span><span class="db-perf__lbl">Favoris</span></div>
              <div class="db-perf__stat"><span class="db-perf__val">{{ formatPrice(dash.latest_listing.price) }}</span><span class="db-perf__lbl">Prix</span></div>
            </div>
          </div>
          <p v-else class="db-empty">Aucune annonce publiée</p>
        </section>

        <!-- Analytiques -->
        <section class="db-card">
          <h2 class="db-card__title">Données analytiques</h2>
          <div class="db-analytics">
            <div class="db-analytics__row">
              <div class="db-analytics__item"><span class="db-analytics__val">{{ dash.listings.total_views }}</span><span class="db-analytics__lbl">Vues totales</span></div>
              <div class="db-analytics__item"><span class="db-analytics__val">{{ dash.listings.total_favorites }}</span><span class="db-analytics__lbl">Favoris</span></div>
              <div class="db-analytics__item"><span class="db-analytics__val">{{ dash.listings.published }}</span><span class="db-analytics__lbl">Publiées</span></div>
            </div>
            <div class="db-analytics__sub">28 derniers jours &middot; Vues : <strong>{{ dash.views_28d }}</strong></div>
          </div>
          <h3 class="db-card__subtitle">Annonces populaires</h3>
          <div class="db-popular">
            <div v-for="listing in dash.top_listings" :key="listing.id" class="db-popular__item">
              <div class="db-popular__thumb">
                <img v-if="listing.cover_image" :src="mediaUrl(listing.cover_image)!" :alt="listing.title" />
                <svg v-else viewBox="0 0 24 24" width="16" height="16"><path fill="#ccc" d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>
              </div>
              <div class="db-popular__info"><span class="db-popular__name">{{ listing.title }}</span><span class="db-popular__views">{{ listing.views_count }} vues</span></div>
            </div>
            <p v-if="!dash.top_listings.length" class="db-empty">Aucune annonce active</p>
          </div>
          <router-link to="/agent/analytics" class="db-link">Accéder aux statistiques</router-link>
        </section>

        <!-- Revenus — masqué (freemium) -->
      </div>

      <!-- ===== VISITES EN ATTENTE (prominent) ===== -->
      <section v-if="dash.pending_visits > 0" class="db-visits">
        <div class="db-visits__left">
          <div class="db-visits__icon"><i class="pi pi-calendar" style="font-size:22px;color:#fff"></i></div>
          <div class="db-visits__info">
            <span class="db-visits__count">{{ dash.pending_visits }}</span>
            <span class="db-visits__text">visite{{ dash.pending_visits > 1 ? 's' : '' }} en attente de confirmation</span>
          </div>
        </div>
        <router-link to="/agent/visits" class="db-visits__btn">Gérer les visites</router-link>
      </section>

      <!-- ===== VOS ANNONCES ===== -->
      <section class="db-card db-card--full">
        <div class="db-card__head">
          <h2 class="db-card__title">Vos annonces</h2>
          <router-link to="/agent/listings" class="db-link">Voir tout</router-link>
        </div>
        <div v-if="agent.listings.length > 0">
          <!-- Desktop table -->
          <div class="db-table db-table--desktop">
            <div class="db-table__head">
              <span class="db-table__col db-table__col--name">Annonce</span>
              <span class="db-table__col">Statut</span>
              <span class="db-table__col">Date</span>
              <span class="db-table__col">Vues</span>
              <span class="db-table__col">Vidéos</span>
            </div>
            <div v-for="l in agent.listings.slice(0, 5)" :key="l.id" class="db-table__row">
              <span class="db-table__col db-table__col--name">
                <div class="db-table__thumb">
                  <img v-if="l.cover_image" :src="mediaUrl(l.cover_image)!" :alt="l.title" />
                  <svg v-else viewBox="0 0 24 24" width="12" height="12"><path fill="#ccc" d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>
                </div>
                {{ l.title }}
              </span>
              <span class="db-table__col"><span class="db-badge" :class="statusClass(l.status)">{{ statusLabel(l.status) }}</span></span>
              <span class="db-table__col">{{ new Date(l.created_at).toLocaleDateString('fr-FR') }}</span>
              <span class="db-table__col">{{ l.views_count }}</span>
              <span class="db-table__col">{{ l.videos_count }}</span>
            </div>
          </div>
          <!-- Mobile cards -->
          <div class="db-mcards">
            <router-link
              v-for="l in agent.listings.slice(0, 5)"
              :key="l.id"
              :to="'/agent/listings'"
              class="db-mcard"
            >
              <div class="db-mcard__img">
                <img v-if="l.cover_image" :src="mediaUrl(l.cover_image)!" :alt="l.title" />
                <svg v-else viewBox="0 0 24 24" width="20" height="20"><path fill="#ccc" d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>
              </div>
              <div class="db-mcard__body">
                <span class="db-mcard__name">{{ l.title }}</span>
                <div class="db-mcard__row">
                  <span class="db-badge" :class="statusClass(l.status)">{{ statusLabel(l.status) }}</span>
                  <span class="db-mcard__stat"><i class="pi pi-eye" style="font-size:11px"></i> {{ l.views_count }}</span>
                  <span class="db-mcard__stat"><i class="pi pi-video" style="font-size:11px"></i> {{ l.videos_count }}</span>
                </div>
                <span class="db-mcard__date">{{ new Date(l.created_at).toLocaleDateString('fr-FR') }}</span>
              </div>
            </router-link>
          </div>
        </div>
        <p v-else class="db-empty">Aucune annonce</p>
      </section>
    </template>
  </div>
</template>

<style scoped>
.db { width: 100%; max-width: 100%; overflow-x: hidden; box-sizing: border-box; }
.db-title { font-size: 22px; font-weight: 700; color: #0f0f0f; margin: 0 0 20px; display: flex; align-items: center; gap: 8px; }
.db-title__badge { flex-shrink: 0; }
.db-loading { padding: 48px 0; text-align: center; color: #606060; }
.db-empty { color: #606060; font-size: 13px; margin: 0; }
.db-link { font-size: 13px; color: #1DA53F; text-decoration: none; font-weight: 500; flex-shrink: 0; }
.db-link:hover { text-decoration: underline; }

/* ===== TOP 3 CARDS ===== */
.db-top {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

/* Card */
.db-card {
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  padding: 18px;
}
.db-card--full { margin-bottom: 16px; }
.db-card__title { font-size: 15px; font-weight: 600; color: #0f0f0f; margin: 0 0 14px; }
.db-card__subtitle { font-size: 13px; font-weight: 600; color: #0f0f0f; margin: 16px 0 8px; }
.db-card__head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.db-card__head .db-card__title { margin: 0; }

/* Perf */
.db-perf__thumb {
  width: 100%; height: 120px; background: #f5f5f5; border-radius: 8px;
  display: flex; align-items: center; justify-content: center; margin-bottom: 8px;
  overflow: hidden;
}
.db-perf__thumb img {
  width: 100%; height: 100%; object-fit: cover;
}
.db-perf__name { font-size: 13px; font-weight: 500; color: #0f0f0f; margin-bottom: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.db-perf__stats { display: flex; gap: 20px; }
.db-perf__stat { display: flex; flex-direction: column; }
.db-perf__val { font-size: 16px; font-weight: 700; color: #0f0f0f; }
.db-perf__lbl { font-size: 11px; color: #606060; }

/* Analytics */
.db-analytics__row { display: flex; gap: 20px; margin-bottom: 8px; }
.db-analytics__item { display: flex; flex-direction: column; }
.db-analytics__val { font-size: 20px; font-weight: 700; color: #0f0f0f; }
.db-analytics__lbl { font-size: 11px; color: #606060; }
.db-analytics__sub { font-size: 12px; color: #606060; padding-bottom: 2px; }

/* Popular */
.db-popular { display: flex; flex-direction: column; gap: 4px; margin-bottom: 10px; }
.db-popular__item { display: flex; align-items: center; gap: 8px; padding: 5px; border-radius: 6px; transition: background 0.1s; }
.db-popular__item:hover { background: #f8f8f8; }
.db-popular__thumb {
  width: 36px; height: 26px; background: #f2f2f2; border-radius: 4px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  overflow: hidden;
}
.db-popular__thumb img {
  width: 100%; height: 100%; object-fit: cover;
}
.db-popular__info { display: flex; flex-direction: column; min-width: 0; }
.db-popular__name { font-size: 12px; color: #0f0f0f; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.db-popular__views { font-size: 11px; color: #606060; }

/* Wallet — masqué (freemium) */

/* ===== VISITES EN ATTENTE ===== */
.db-visits {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%);
  border: 2px solid #1DA53F;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 16px;
  gap: 16px;
}
.db-visits__left { display: flex; align-items: center; gap: 14px; }
.db-visits__icon {
  width: 44px; height: 44px; border-radius: 50%;
  background: #1DA53F; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.db-visits__info { display: flex; align-items: baseline; gap: 6px; flex-wrap: wrap; }
.db-visits__count { font-size: 28px; font-weight: 700; color: #1DA53F; }
.db-visits__text { font-size: 15px; color: #272727; font-weight: 500; }
.db-visits__btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 20px; border-radius: 20px;
  background: #1DA53F; color: #fff; font-size: 13px; font-weight: 600;
  text-decoration: none; flex-shrink: 0; transition: background 0.15s;
}
.db-visits__btn:hover { background: #178a33; }

/* ===== TABLE ===== */
.db-table__head,
.db-table__row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 0.7fr 0.7fr;
  gap: 10px;
  padding: 8px 0;
  align-items: center;
}
.db-table__head { border-bottom: 1px solid #e5e5e5; font-size: 12px; color: #606060; font-weight: 500; }
.db-table__row { border-bottom: 1px solid #f5f5f5; font-size: 13px; color: #0f0f0f; }
.db-table__col--name {
  display: flex; align-items: center; gap: 8px; min-width: 0;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.db-table__thumb {
  width: 32px; height: 22px; background: #f2f2f2; border-radius: 3px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  overflow: hidden;
}
.db-table__thumb img {
  width: 100%; height: 100%; object-fit: cover;
}

.db-badge {
  display: inline-block; padding: 2px 8px; border-radius: 10px;
  font-size: 11px; font-weight: 500;
}
.db-badge.published { background: rgba(29,165,63,.1); color: #1DA53F; }
.db-badge.draft { background: #f2f2f2; color: #606060; }
.db-badge.expired { background: #fef2f2; color: #dc2626; }

/* ===== MOBILE CARDS for listings ===== */
.db-mcards { display: none; }

.db-mcard {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid #f2f2f2;
  text-decoration: none;
  color: inherit;
  transition: background .1s;
}
.db-mcard:last-child { border-bottom: none; }
.db-mcard:active { background: #f8f8f8; }

.db-mcard__img {
  width: 56px;
  height: 56px;
  border-radius: 10px;
  background: #f2f2f2;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}
.db-mcard__img img { width: 100%; height: 100%; object-fit: cover; }

.db-mcard__body { flex: 1; min-width: 0; }
.db-mcard__name {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #0f0f0f;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}
.db-mcard__row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}
.db-mcard__stat {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  color: #606060;
}
.db-mcard__date {
  font-size: 11px;
  color: #909090;
}

/* ===== RESPONSIVE ===== */
@media (max-width: 1024px) {
  .db-top { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 768px) {
  .db-top { grid-template-columns: 1fr; gap: 12px; }
  .db-title { font-size: 18px; margin-bottom: 16px; }
  .db-visits { flex-direction: column; text-align: center; padding: 14px; }
  .db-visits__left { flex-direction: column; align-items: center; }
  .db-visits__count { font-size: 22px; }
  .db-visits__text { font-size: 13px; }
  .db-visits__btn { font-size: 12px; padding: 8px 16px; }

  .db-card {
    padding: 14px;
    overflow: hidden;
  }
  .db-card--full { margin-bottom: 12px; }
  .db-card__title { font-size: 14px; margin-bottom: 10px; }

  .db-perf__thumb { height: 140px; border-radius: 10px; }
  .db-perf__stats { gap: 0; justify-content: space-between; }
  .db-perf__val { font-size: 14px; }
  .db-perf__lbl { font-size: 10px; }

  .db-analytics__row { gap: 0; justify-content: space-between; }
  .db-analytics__val { font-size: 18px; }
  .db-analytics__lbl { font-size: 10px; }

  .db-table--desktop { display: none; }
  .db-mcards { display: flex; flex-direction: column; }

  .db-popular__name { font-size: 11px; }
  .db-popular__thumb { width: 32px; height: 22px; }
}

@media (max-width: 400px) {
  .db-card { padding: 12px; }
  .db-perf__thumb { height: 120px; }
  .db-perf__stats { flex-wrap: wrap; gap: 8px; }
}
</style>
