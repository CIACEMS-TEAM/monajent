<template>
  <div class="yt-app" :class="{ 'sidebar-open': sidebarOpen }">

    <!-- ===== WELCOME OVERLAY (first visit) ===== -->
    <WelcomeOverlay @closed="onWelcomeClosed" />

    <!-- ===== ONBOARDING TOUR ===== -->
    <OnboardingTour v-if="showOnboarding" @done="showOnboarding = false" />

    <!-- ===== HEADER ===== -->
    <header class="yt-header">
      <div class="yt-header__start">
        <button class="yt-icon-btn yt-hamburger-desktop" @click="sidebarOpen = !sidebarOpen" aria-label="Menu">
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path fill="currentColor" d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z" />
          </svg>
        </button>
        <router-link to="/home" class="yt-logo">
          <img src="@/assets/icons/logo_monajent_header.webp" alt="MonaJent" class="yt-logo__img" />
        </router-link>
      </div>

      <!-- Desktop search bar -->
      <div class="yt-header__center yt-desktop-search">
        <div class="yt-search">
          <input
            v-model="searchQuery"
            type="text"
            class="yt-search__input"
            placeholder="Rechercher un bien, une ville, un quartier..."
            @keyup.enter="handleSearch"
          />
          <button class="yt-search__btn" @click="handleSearch" aria-label="Rechercher">
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path
                fill="currentColor"
                d="M20.87 20.17l-5.59-5.59C16.35 13.35 17 11.75 17 10c0-3.87-3.13-7-7-7s-7 3.13-7 7 3.13 7 7 7c1.75 0 3.35-.65 4.58-1.71l5.59 5.59 1.7-1.71zM5 10c0-2.76 2.24-5 5-5s5 2.24 5 5-2.24 5-5 5-5-2.24-5-5z"
              />
            </svg>
          </button>
        </div>
      </div>

      <div class="yt-header__end">
        <!-- Mobile search icon -->
        <button class="yt-icon-btn yt-mobile-search-toggle" @click="mobileSearchOpen = true" aria-label="Rechercher">
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path
              fill="currentColor"
              d="M20.87 20.17l-5.59-5.59C16.35 13.35 17 11.75 17 10c0-3.87-3.13-7-7-7s-7 3.13-7 7 3.13 7 7 7c1.75 0 3.35-.65 4.58-1.71l5.59 5.59 1.7-1.71zM5 10c0-2.76 2.24-5 5-5s5 2.24 5 5-2.24 5-5 5-5-2.24-5-5z"
            />
          </svg>
        </button>
        <template v-if="auth.me">
          <!-- Keys indicators (masqué — mode standby paiement) -->
          <!--
          <div v-if="auth.me.role === 'CLIENT' && pub.keysLoaded" class="yt-keys">
            <router-link to="/home/packs" class="yt-keys__item yt-keys__item--virt" title="Clés virtuelles">
              <img :src="keyVirtImg" alt="" class="yt-keys__icon" />
              <span class="yt-keys__count">{{ pub.virtualKeys }}</span>
            </router-link>
            <router-link to="/home/packs" class="yt-keys__item yt-keys__item--phy" title="Clés physiques (visites gratuites)">
              <img :src="keyPhyImg" alt="" class="yt-keys__icon" />
              <span class="yt-keys__count">{{ pub.physicalKeys }}</span>
            </router-link>
          </div>
          -->

          <button class="yt-icon-btn yt-notif-btn" aria-label="Notifications">
            <svg viewBox="0 0 24 24" width="24" height="24">
              <path
                fill="currentColor"
                d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.63-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.64 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2zm-2 1H8v-6c0-2.48 1.51-4.5 4-4.5s4 2.02 4 4.5v6z"
              />
            </svg>
          </button>
          <div class="yt-usermenu-wrapper yt-header-avatar">
            <div class="yt-user-avatar" @click="handleBottomNavProfile">
              {{ userInitial }}
            </div>
            <Transition name="menu-fade">
              <div v-if="userMenuOpen" class="yt-usermenu" @click="userMenuOpen = false">
                <div class="yt-usermenu__header">
                  <div class="yt-usermenu__avatar">{{ userInitial }}</div>
                  <div class="yt-usermenu__info">
                    <span class="yt-usermenu__name">{{ auth.me.username || auth.me.phone }}</span>
                    <span class="yt-usermenu__phone">{{ auth.me.phone }}</span>
                  </div>
                </div>
                <div class="yt-usermenu__divider"></div>
                <a href="#" class="yt-usermenu__item" @click.prevent="navigateMenu('/home/profile')">
                  <svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/></svg>
                  <span>Mon profil</span>
                </a>
                <div class="yt-usermenu__divider"></div>
                <a href="#" class="yt-usermenu__item yt-usermenu__item--danger" @click.prevent="handleLogout">
                  <svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/></svg>
                  <span>Déconnexion</span>
                </a>
              </div>
            </Transition>
          </div>
        </template>
        <template v-else>
          <router-link to="/auth/login" class="yt-signin-btn">
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path
                d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zM7.07 18.28c.43-.9 3.05-1.78 4.93-1.78s4.51.88 4.93 1.78C15.57 19.36 13.86 20 12 20s-3.57-.64-4.93-1.72zm11.29-1.45c-1.43-1.74-4.9-2.33-6.36-2.33s-4.93.59-6.36 2.33A7.95 7.95 0 014 12c0-4.41 3.59-8 8-8s8 3.59 8 8c0 1.82-.62 3.49-1.64 4.83zM12 6c-1.94 0-3.5 1.56-3.5 3.5S10.06 13 12 13s3.5-1.56 3.5-3.5S13.94 6 12 6zm0 5c-.83 0-1.5-.67-1.5-1.5S11.17 8 12 8s1.5.67 1.5 1.5S12.83 11 12 11z"
              />
            </svg>
            <span>Se connecter</span>
          </router-link>
        </template>
      </div>
    </header>

    <!-- ===== MOBILE SEARCH OVERLAY ===== -->
    <div v-if="mobileSearchOpen" class="yt-mobile-search-overlay">
      <button class="yt-icon-btn" @click="mobileSearchOpen = false" aria-label="Retour">
        <svg viewBox="0 0 24 24" width="24" height="24">
          <path fill="currentColor" d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
        </svg>
      </button>
      <input
        ref="mobileSearchInput"
        v-model="searchQuery"
        type="text"
        class="yt-mobile-search-input"
        placeholder="Rechercher..."
        @keyup.enter="handleMobileSearch"
      />
      <button class="yt-icon-btn" @click="handleMobileSearch" aria-label="Rechercher">
        <svg viewBox="0 0 24 24" width="24" height="24">
          <path
            fill="currentColor"
            d="M20.87 20.17l-5.59-5.59C16.35 13.35 17 11.75 17 10c0-3.87-3.13-7-7-7s-7 3.13-7 7 3.13 7 7 7c1.75 0 3.35-.65 4.58-1.71l5.59 5.59 1.7-1.71zM5 10c0-2.76 2.24-5 5-5s5 2.24 5 5-2.24 5-5 5-5-2.24-5-5z"
          />
        </svg>
      </button>
    </div>

    <!-- ===== SIDEBAR ===== -->
    <aside class="yt-sidebar" data-tour="sidebar">
      <nav class="yt-sidebar__nav">
        <router-link to="/home" class="yt-sidebar__item active">
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path fill="currentColor" d="M4 21V10.08l8-6.96 8 6.96V21h-6v-6h-4v6H4z" />
          </svg>
          <span class="yt-sidebar__label">Accueil</span>
        </router-link>

        <!-- <a href="#" class="yt-sidebar__item yt-sidebar__item--soon" @click.prevent>
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path
              fill="currentColor"
              d="M17.53 11.2c-.23-.3-.51-.56-.84-.75-.24-.14-.36-.05-.24.14l.27.45c.19.32.3.68.3 1.06 0 1.1-.9 2-2 2-.34 0-.65-.09-.93-.25-.13-.07-.26.02-.23.16.16.84.76 1.55 1.56 1.84.45.17.93.2 1.4.08.47-.11.89-.36 1.2-.72.65-.74.82-1.82.43-2.73a2.07 2.07 0 00-.92-.28z"
            />
            <path
              fill="currentColor"
              d="M19 9l1.25-2.75L23 5l-2.75-1.25L19 1l-1.25 2.75L15 5l2.75 1.25zm-7.5.5L9 4 6.5 9.5 1 12l5.5 2.5L9 20l2.5-5.5L17 12l-5.5-2.5z"
            />
          </svg>
          <span class="yt-sidebar__label">Tendances</span>
          <span class="yt-badge-soon">Bientôt</span>
        </a> -->

        <div class="yt-sidebar__separator"></div>

        <div class="yt-sidebar__heading">Vous</div>

        <a href="#" class="yt-sidebar__item" :class="{ disabled: !auth.me }" @click.prevent="navigateAuth('/home/dashboard')">
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path fill="currentColor" d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/>
          </svg>
          <span class="yt-sidebar__label">Mon espace</span>
        </a>

        <a href="#" class="yt-sidebar__item" :class="{ disabled: !auth.me }" @click.prevent="navigateAuth('/home/history')">
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path
              fill="currentColor"
              d="M14.97 16.95L10 13.87V7h2v5.76l4.03 2.49-1.06 1.7zM22 12c0 5.51-4.49 10-10 10S2 17.51 2 12h2c0 4.41 3.59 8 8 8s8-3.59 8-8-3.59-8-8-8C8.56 4 5.85 5.56 4.31 8H8v2H2V4h2v2.69C5.72 4.04 8.64 2 12 2c5.51 0 10 4.49 10 10z"
            />
          </svg>
          <span class="yt-sidebar__label">Historique</span>
        </a>

        <a href="#" class="yt-sidebar__item" :class="{ disabled: !auth.me }" @click.prevent="navigateAuth('/home/favorites')">
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path
              fill="currentColor"
              d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3zm-4.4 15.55l-.1.1-.1-.1C7.14 14.24 4 11.39 4 8.5 4 6.5 5.5 5 7.5 5c1.54 0 3.04.99 3.57 2.36h1.87C13.46 5.99 14.96 5 16.5 5c2 0 3.5 1.5 3.5 3.5 0 2.89-3.14 5.74-7.9 10.05z"
            />
          </svg>
          <span class="yt-sidebar__label">Favoris</span>
        </a>

        <!-- Packs / Paiements masqués (mode freemium) -->

        <a href="#" class="yt-sidebar__item" :class="{ disabled: !auth.me }" @click.prevent="navigateAuth('/home/visits')">
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path
              fill="currentColor"
              d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"
            />
          </svg>
          <span class="yt-sidebar__label">Visites</span>
        </a>

        <a href="#" class="yt-sidebar__item" :class="{ disabled: !auth.me }" @click.prevent="navigateAuth('/home/reports')">
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path fill="currentColor" d="M14.4 6L14 4H5v17h2v-7h5.6l.4 2h7V6z"/>
          </svg>
          <span class="yt-sidebar__label">Signalements</span>
        </a>

        <a href="#" class="yt-sidebar__item" :class="{ disabled: !auth.me }" @click.prevent="navigateAuth('/home/support')">
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/>
          </svg>
          <span class="yt-sidebar__label">Aide & Support</span>
        </a>

        <div class="yt-sidebar__separator"></div>

        <!-- <div class="yt-sidebar__heading">Explorer</div>

        <a href="#" class="yt-sidebar__item yt-sidebar__item--soon" @click.prevent>
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path
              fill="currentColor"
              d="M12 7V3H2v18h20V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm10 12h-8v-2h2v-2h-2v-2h2v-2h-2V9h8v10zm-2-8h-2v2h2v-2zm0 4h-2v2h2v-2z"
            />
          </svg>
          <span class="yt-sidebar__label">Agents vérifiés</span>
          <span class="yt-badge-soon">Bientôt</span>
        </a>

        <a href="#" class="yt-sidebar__item yt-sidebar__item--soon" @click.prevent>
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path
              fill="currentColor"
              d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14zm-7-2h2V7h-4v2h2z"
            />
          </svg>
          <span class="yt-sidebar__label">Nouveautés</span>
          <span class="yt-badge-soon">Bientôt</span>
        </a> -->
      </nav>

      <!-- Footer expanded -->
      <div class="yt-sidebar__footer yt-sidebar__footer--expanded">
        <div class="yt-sidebar__links">
          <router-link to="/legal/cgu">Conditions d'utilisation</router-link>
          <router-link to="/legal/confidentialite">Confidentialité</router-link>
          <router-link to="/legal/conditions-agents">Conditions agents</router-link>
        </div>
        <p class="yt-sidebar__legal">&copy; 2026 MonaJent &mdash; CIACEMS</p>
      </div>

      <!-- Footer collapsed (icône) -->
      <div class="yt-sidebar__footer yt-sidebar__footer--collapsed">
        <router-link to="/legal/cgu" class="yt-sidebar__legal-icon" title="Mentions légales">
          <svg viewBox="0 0 24 24" width="20" height="20">
            <path fill="currentColor" d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-1 15h2v2h-2v-2zm0-8h2v6h-2V8z"/>
          </svg>
        </router-link>
      </div>
    </aside>

    <!-- Sidebar Overlay (mobile) -->
    <div
      v-if="sidebarOpen"
      class="yt-sidebar-overlay"
      @click="sidebarOpen = false"
    ></div>

    <!-- ===== MAIN CONTENT ===== -->
    <main class="yt-main">
      <router-view />
    </main>

    <!-- ===== LOGIN PROMPT MODAL ===== -->
    <div v-if="showLoginModal" class="yt-modal-overlay" @click.self="showLoginModal = false">
      <div class="yt-modal">
        <button class="yt-modal__close" @click="showLoginModal = false" aria-label="Fermer">
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path fill="#272727" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
          </svg>
        </button>
        <div class="yt-modal__icon">
          <svg viewBox="0 0 48 48" width="56" height="56">
            <circle cx="24" cy="24" r="22" fill="rgba(29,165,63,0.1)" stroke="#1DA53F" stroke-width="2" />
            <path fill="#1DA53F" d="M19 15l14 9-14 9V15z" />
          </svg>
        </div>
        <h2 class="yt-modal__title">Connectez-vous pour visionner</h2>
        <p class="yt-modal__subtitle">Regardez les vidéos des biens et trouvez votre logement idéal.</p>
        <div class="yt-modal__actions">
          <router-link to="/auth/login" class="yt-modal__btn yt-modal__btn--primary" @click="showLoginModal = false">Se connecter</router-link>
          <router-link to="/auth/join" class="yt-modal__btn yt-modal__btn--secondary" @click="showLoginModal = false">Créer un compte</router-link>
        </div>
      </div>
    </div>

    <!-- ===== MONA SEARCH (IA) ===== -->
    <MonaSearch ref="monaSearchRef" />

    <!-- ===== PWA INSTALL PROMPT ===== -->
    <PwaInstallPrompt />

    <!-- ===== MOBILE BOTTOM NAV ===== -->
    <nav class="yt-bottomnav" data-tour="nav">
      <router-link to="/home" class="yt-bottomnav__item" :class="{ active: activeBottomTab === 'home' }">
        <svg viewBox="0 0 24 24" width="22" height="22">
          <path fill="currentColor" d="M4 21V10.08l8-6.96 8 6.96V21h-6v-6h-4v6H4z" />
        </svg>
        <span>Accueil</span>
      </router-link>

      <button class="yt-bottomnav__mona" @click="openMonaSearch" aria-label="Mona — Recherche vocale IA">
        <div class="yt-bottomnav__mona-btn">
          <svg viewBox="0 0 24 24" width="26" height="26" fill="none">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" fill="#fff"/>
            <path d="M13.5 7.5l.9-1.9 1.9-.9-1.9-.9-.9-1.9-.9 1.9-1.9.9 1.9.9zm4.3 2.1l-.6 1.3-1.3.6 1.3.6.6 1.3.6-1.3 1.3-.6-1.3-.6zM9.2 7.6L8 10l-2.4 1.2L8 12.4 9.2 14.8l1.2-2.4 2.4-1.2-2.4-1.2z" fill="#1DA53F"/>
          </svg>
        </div>
        <span>Mona</span>
      </button>

      <a href="#" class="yt-bottomnav__item" :class="{ active: activeBottomTab === 'favorites' }" @click.prevent="navigateAuth('/home/favorites')">
        <svg viewBox="0 0 24 24" width="22" height="22">
          <path fill="currentColor" d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3zm-4.4 15.55l-.1.1-.1-.1C7.14 14.24 4 11.39 4 8.5 4 6.5 5.5 5 7.5 5c1.54 0 3.04.99 3.57 2.36h1.87C13.46 5.99 14.96 5 16.5 5c2 0 3.5 1.5 3.5 3.5 0 2.89-3.14 5.74-7.9 10.05z" />
        </svg>
        <span>Favoris</span>
      </a>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/Stores/auth'
import { usePublicStore } from '@/Stores/public'
import WelcomeOverlay from '@/components/WelcomeOverlay.vue'
import OnboardingTour from '@/components/OnboardingTour.vue'
import MonaSearch from '@/components/MonaSearch.vue'
import PwaInstallPrompt from '@/components/PwaInstallPrompt.vue'
// Clés masquées (mode freemium)
// import keyVirtImg from '@/assets/icons/key_virt.png'
// import keyPhyImg from '@/assets/icons/key_phy.png'

const auth = useAuthStore()
const pub = usePublicStore()
const router = useRouter()
const route = useRoute()
const sidebarOpen = ref(false)
const mobileSearchOpen = ref(false)
const mobileSearchInput = ref<HTMLInputElement | null>(null)
const searchQuery = ref((route.query.q as string) || '')
const monaSearchRef = ref<InstanceType<typeof MonaSearch> | null>(null)
const showLoginModal = ref(false)
const userMenuOpen = ref(false)
const showOnboarding = ref(false)

function fetchClientData() {
  if (auth.me?.role === 'CLIENT') {
    pub.fetchKeyCounts()
    pub.fetchFavoriteIds()
  }
}

watch(mobileSearchOpen, (open) => {
  if (open) nextTick(() => mobileSearchInput.value?.focus())
})

watch(() => route.query.q, (q) => {
  searchQuery.value = (q as string) || ''
})

function closeUserMenu(e: MouseEvent) {
  const wrapper = (e.target as HTMLElement).closest('.yt-usermenu-wrapper')
  if (!wrapper) userMenuOpen.value = false
}

function onWelcomeClosed() {
  if (!localStorage.getItem('monajent_onboarding_done')) {
    setTimeout(() => { showOnboarding.value = true }, 400)
  }
}

onMounted(() => {
  document.addEventListener('click', closeUserMenu)
  fetchClientData()
  const welcomeSeen = localStorage.getItem('monajent_welcome_dismissed') || sessionStorage.getItem('monajent_welcome_seen')
  const onboardingDone = localStorage.getItem('monajent_onboarding_done')
  if (welcomeSeen && !onboardingDone) {
    setTimeout(() => { showOnboarding.value = true }, 800)
  }
})
onUnmounted(() => document.removeEventListener('click', closeUserMenu))

watch(() => auth.me, () => fetchClientData())

const userInitial = computed(() => {
  if (!auth.me) return ''
  return (auth.me.username?.[0] ?? auth.me.phone?.[0] ?? 'U').toUpperCase()
})

const activeBottomTab = computed(() => {
  const path = route.path
  if (path === '/home/favorites') return 'favorites'
  if (path.startsWith('/home/dashboard') || path.startsWith('/home/profile') ||
      path.startsWith('/home/history') || path.startsWith('/home/visits') ||
      path.startsWith('/home/reports') || path.startsWith('/home/support')) return 'you'
  return 'home'
})

function handleSearch() {
  if (!searchQuery.value.trim()) return
  router.push({ path: '/home', query: { q: searchQuery.value } })
}

function handleMobileSearch() {
  handleSearch()
  mobileSearchOpen.value = false
}

function openMonaSearch() {
  monaSearchRef.value?.toggle()
}

function navigateAuth(path: string) {
  if (!auth.me) {
    showLoginModal.value = true
    return
  }
  router.push(path)
  sidebarOpen.value = false
}

function navigateMenu(path: string) {
  userMenuOpen.value = false
  router.push(path)
}

async function handleLogout() {
  userMenuOpen.value = false
  await auth.logout()
  router.push({ name: 'home' })
}

function handleBottomNavProfile() {
  if (!auth.me) {
    router.push({ name: 'login' })
    return
  }
  if (window.innerWidth <= 768) {
    router.push({ name: 'client-dashboard' })
    return
  }
  userMenuOpen.value = !userMenuOpen.value
}
</script>

<style scoped>
/* ===== RESET & VARIABLES ===== */
*,
*::before,
*::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.yt-app {
  --header-h: 56px;
  --sidebar-w: 240px;
  --sidebar-collapsed-w: 72px;
  --bottomnav-h: 0px;
  --green: #1DA53F;
  --green-dark: #178A33;
  --green-light: rgba(29, 165, 63, 0.08);
  --green-ring: rgba(29, 165, 63, 0.15);
  --bg: #FFFFFF;
  --text-primary: #0F0F0F;
  --text-secondary: #272727;
  --chip-bg: #f2f2f2;
  --chip-bg-active: #0F0F0F;
  --chip-text-active: #FFFFFF;
  --border: #E0E0E0;
  --card-hover: #f2f2f2;

  font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
  background: var(--bg);
  color: var(--text-primary);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ===== HEADER ===== */
.yt-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: var(--header-h);
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  z-index: 100;
  border-bottom: 1px solid var(--border);
}

.yt-header__start {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 200px;
}

.yt-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  background: none;
  border-radius: 50%;
  cursor: pointer;
  color: var(--text-primary);
  transition: background 0.15s;
}

.yt-icon-btn:hover {
  background: var(--chip-bg);
}

.yt-logo {
  display: flex;
  align-items: center;
  text-decoration: none;
}

.yt-logo__img {
  height: 36px;
  width: auto;
}

/* Search */
.yt-header__center {
  flex: 1;
  max-width: 640px;
  margin: 0 32px;
}

.yt-search {
  display: flex;
  width: 100%;
}

.yt-search__input {
  flex: 1;
  height: 40px;
  padding: 0 16px;
  border: 1px solid var(--border);
  border-right: none;
  border-radius: 20px 0 0 20px;
  font-size: 16px;
  color: var(--text-primary);
  background: #fff;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.yt-search__input:focus {
  border-color: var(--green);
  box-shadow: inset 0 1px 2px var(--green-ring);
}

.yt-search__input::placeholder {
  color: #999;
}

.yt-search__btn {
  width: 64px;
  height: 40px;
  border: 1px solid var(--border);
  border-left: none;
  border-radius: 0 20px 20px 0;
  background: var(--chip-bg);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
  transition: background 0.15s;
}

.yt-search__btn:hover {
  background: #e0e0e0;
}

/* Header End */
.yt-header__end {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 200px;
  justify-content: flex-end;
}

/* Keys indicators */
.yt-keys {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-right: 2px;
}
.yt-keys__item {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 4px 8px;
  border-radius: 16px;
  text-decoration: none;
  transition: all 0.15s;
  cursor: pointer;
}
.yt-keys__item--virt { background: rgba(37,99,235,.08); }
.yt-keys__item--virt:hover { background: rgba(37,99,235,.15); }
.yt-keys__item--phy { background: rgba(234,160,12,.08); }
.yt-keys__item--phy:hover { background: rgba(234,160,12,.15); }
.yt-keys__icon {
  width: 20px;
  height: 20px;
  object-fit: contain;
}
.yt-keys__count {
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
}
.yt-keys__item--virt .yt-keys__count { color: #2563eb; }
.yt-keys__item--phy .yt-keys__count { color: #d97706; }

.yt-notif-btn {
  position: relative;
}

.yt-user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--green);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  user-select: none;
}

.yt-signin-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 15px;
  border: 1px solid var(--green);
  border-radius: 18px;
  text-decoration: none;
  color: var(--green);
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  transition: background 0.15s, border-color 0.15s;
}

.yt-signin-btn svg {
  color: var(--green);
  fill: var(--green);
}

.yt-signin-btn:hover {
  background: var(--green-light);
  border-color: var(--green-dark);
}

/* ===== USER DROPDOWN MENU ===== */
.yt-usermenu-wrapper {
  position: relative;
}

.yt-usermenu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 260px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.14), 0 0 0 1px rgba(0, 0, 0, 0.04);
  z-index: 200;
  padding: 8px 0;
  overflow: hidden;
}

.yt-usermenu__header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 16px 12px;
}

.yt-usermenu__avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--green);
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.yt-usermenu__info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.yt-usermenu__name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.yt-usermenu__phone {
  font-size: 12px;
  color: var(--text-secondary);
}

.yt-usermenu__divider {
  height: 1px;
  background: var(--border);
  margin: 4px 0;
}

.yt-usermenu__item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 16px;
  text-decoration: none;
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.12s;
}

.yt-usermenu__item:hover {
  background: var(--chip-bg);
}

.yt-usermenu__item svg {
  flex-shrink: 0;
  color: var(--text-secondary);
}

.yt-usermenu__item--danger {
  color: #d32f2f;
}

.yt-usermenu__item--danger svg {
  color: #d32f2f;
}

.yt-usermenu__item--danger:hover {
  background: rgba(211, 47, 47, 0.06);
}

/* Transition */
.menu-fade-enter-active,
.menu-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.menu-fade-enter-from,
.menu-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.96);
}

/* Mobile search toggle — hidden on desktop */
.yt-mobile-search-toggle {
  display: none;
}

/* ===== MOBILE SEARCH OVERLAY ===== */
.yt-mobile-search-overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: var(--header-h);
  background: #fff;
  z-index: 110;
  align-items: center;
  gap: 4px;
  padding: 0 8px;
}

.yt-mobile-search-input {
  flex: 1;
  height: 36px;
  padding: 0 12px;
  border: none;
  border-bottom: 2px solid var(--text-primary);
  font-size: 16px;
  color: var(--text-primary);
  background: transparent;
  outline: none;
}

.yt-mobile-search-input::placeholder {
  color: #999;
}

/* ===== SIDEBAR ===== */
.yt-sidebar {
  position: fixed;
  top: var(--header-h);
  left: 0;
  bottom: 0;
  width: var(--sidebar-collapsed-w);
  background: #fff;
  overflow-y: auto;
  overflow-x: hidden;
  z-index: 90;
  transition: width 0.2s ease;
  display: flex;
  flex-direction: column;
}

.sidebar-open .yt-sidebar {
  width: var(--sidebar-w);
  box-shadow: 4px 0 12px rgba(0, 0, 0, 0.08);
}

.yt-sidebar::-webkit-scrollbar {
  width: 8px;
}

.yt-sidebar::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 4px;
}

.yt-sidebar:hover::-webkit-scrollbar-thumb {
  background: #c1c1c1;
}

.yt-sidebar__nav {
  padding: 12px 0;
  flex: 1;
}

.yt-sidebar__item {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 0 12px;
  height: 40px;
  border-radius: 10px;
  margin: 1px 12px;
  text-decoration: none;
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
  white-space: nowrap;
  overflow: hidden;
}

.yt-sidebar__item:hover {
  background: var(--chip-bg);
}

.yt-sidebar__item.active {
  background: var(--chip-bg);
  font-weight: 600;
}

.yt-sidebar__item svg {
  flex-shrink: 0;
}

.yt-sidebar__item.disabled {
  opacity: 0.45;
  cursor: default;
}

.yt-sidebar__item.disabled:hover {
  background: transparent;
}

.yt-sidebar__item--soon {
  opacity: 0.5;
  cursor: default;
  position: relative;
}

.yt-sidebar__item--soon:hover {
  background: transparent;
}

.yt-badge-soon {
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  background: var(--green-light);
  color: var(--green);
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
}

.yt-app:not(.sidebar-open) .yt-badge-soon {
  display: none;
}

.yt-sidebar__label {
  opacity: 0;
  transition: opacity 0.15s;
}

.sidebar-open .yt-sidebar__label {
  opacity: 1;
}

/* Collapsed: center icons, hide text */
.yt-app:not(.sidebar-open) .yt-sidebar__item {
  flex-direction: column;
  gap: 4px;
  height: auto;
  padding: 12px 0 10px;
  margin: 0;
  border-radius: 10px;
  justify-content: center;
  align-items: center;
}

.yt-app:not(.sidebar-open) .yt-sidebar__label {
  opacity: 1;
  font-size: 10px;
  line-height: 1.2;
  text-align: center;
}

.yt-app:not(.sidebar-open) .yt-sidebar__heading,
.yt-app:not(.sidebar-open) .yt-sidebar__separator,
.yt-app:not(.sidebar-open) .yt-sidebar__footer--expanded {
  display: none;
}

.yt-sidebar__footer--collapsed {
  display: none;
}

.yt-app:not(.sidebar-open) .yt-sidebar__footer--collapsed {
  display: flex;
  justify-content: center;
  padding: 12px 0;
  border-top: 1px solid var(--border);
}

.yt-sidebar__legal-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  color: var(--text-secondary);
  transition: background 0.15s, color 0.15s;
}

.yt-sidebar__legal-icon:hover {
  background: var(--chip-bg);
  color: var(--text-primary);
}

.yt-sidebar__separator {
  height: 1px;
  background: var(--border);
  margin: 12px 16px;
}

.yt-sidebar__heading {
  padding: 8px 24px 4px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
}

.yt-sidebar__footer {
  padding: 16px;
  border-top: 1px solid var(--border);
}

.yt-sidebar__links {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 12px;
  margin-bottom: 10px;
}

.yt-sidebar__links a {
  font-size: 12px;
  color: var(--text-secondary);
  text-decoration: none;
  line-height: 1.6;
}

.yt-sidebar__links a:hover {
  color: var(--text-primary);
}

.yt-sidebar__legal {
  font-size: 11px;
  color: #909090;
  white-space: nowrap;
  overflow: hidden;
}

.yt-sidebar-overlay {
  position: fixed;
  top: var(--header-h);
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 85;
  display: none;
}

/* ===== MAIN CONTENT ===== */
.yt-main {
  margin-top: var(--header-h);
  margin-left: var(--sidebar-collapsed-w);
  padding: 0 24px 32px;
  transition: margin-left 0.2s ease;
}

.sidebar-open .yt-main {
  margin-left: var(--sidebar-w);
}

/* ===== LOGIN MODAL ===== */
.yt-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.yt-modal {
  background: #fff;
  border-radius: 16px;
  padding: 40px 32px 32px;
  max-width: 420px;
  width: 100%;
  text-align: center;
  position: relative;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.yt-modal__close {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 36px;
  height: 36px;
  border: none;
  background: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #272727;
  transition: background 0.15s;
}

.yt-modal__close:hover {
  background: #f2f2f2;
}

.yt-modal__icon {
  margin-bottom: 20px;
}

.yt-modal__title {
  font-size: 20px;
  font-weight: 700;
  color: #0F0F0F;
  margin-bottom: 8px;
}

.yt-modal__subtitle {
  font-size: 14px;
  color: #272727;
  line-height: 1.5;
  margin-bottom: 28px;
}

.yt-modal__actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.yt-modal__btn {
  display: block;
  padding: 12px 24px;
  border-radius: 24px;
  font-size: 15px;
  font-weight: 600;
  text-decoration: none;
  text-align: center;
  cursor: pointer;
  transition: background 0.15s, box-shadow 0.15s;
}

.yt-modal__btn--primary {
  background: #1DA53F;
  color: #fff;
  border: none;
}

.yt-modal__btn--primary:hover {
  background: #178A33;
  box-shadow: 0 4px 12px rgba(29, 165, 63, 0.3);
}

.yt-modal__btn--secondary {
  background: #fff;
  color: #1DA53F;
  border: 1.5px solid #1DA53F;
}

.yt-modal__btn--secondary:hover {
  background: rgba(29, 165, 63, 0.08);
}

/* ===== BOTTOM NAV (mobile only) ===== */
.yt-bottomnav {
  display: none;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: var(--bottomnav-h);
  background: #fff;
  border-top: 1px solid var(--border);
  z-index: 100;
  align-items: center;
  justify-content: space-around;
}

.yt-bottomnav__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  flex: 1;
  padding: 6px 0 4px;
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 10px;
  font-weight: 500;
  transition: color 0.15s;
  -webkit-tap-highlight-color: transparent;
}

.yt-bottomnav__item.active {
  color: var(--text-primary);
}

.yt-bottomnav__item:active {
  opacity: 0.7;
}

.yt-bottomnav__mona {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  margin-top: -22px;
  position: relative;
  -webkit-tap-highlight-color: transparent;
}
.yt-bottomnav__mona-btn {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1DA53F 0%, #16913A 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(29,165,63,.35);
  transition: transform .15s, box-shadow .15s;
}
.yt-bottomnav__mona-btn:active {
  transform: scale(0.92);
}
.yt-bottomnav__mona span {
  font-size: 10px;
  font-weight: 600;
  color: var(--green);
  line-height: 1;
}

.yt-bottomnav__avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: box-shadow 0.15s;
}
.yt-bottomnav__avatar--active {
  box-shadow: 0 0 0 2px var(--text-primary);
}

/* ===== RESPONSIVE ===== */

/* Tablette */
@media (max-width: 1100px) {
  .sidebar-open .yt-main {
    margin-left: var(--sidebar-collapsed-w);
  }

  .sidebar-open .yt-sidebar {
    position: fixed;
    width: var(--sidebar-w);
    z-index: 95;
  }

  .sidebar-open .yt-sidebar-overlay {
    display: block;
  }
}

/* Mobile (<= 768px) */
@media (max-width: 768px) {
  .yt-app {
    --bottomnav-h: 52px;
  }

  /* Header: hide hamburger, show mobile search icon */
  .yt-hamburger-desktop {
    display: none;
  }

  .yt-desktop-search {
    display: none;
  }

  .yt-mobile-search-toggle {
    display: flex;
  }

  .yt-mobile-search-overlay {
    display: flex;
  }

  .yt-signin-btn span {
    display: none;
  }

  .yt-signin-btn {
    padding: 5px;
    border: none;
  }

  /* Sidebar completely hidden on mobile */
  .yt-sidebar {
    width: 0;
    overflow: hidden;
  }

  .sidebar-open .yt-sidebar {
    width: var(--sidebar-w);
  }

  .sidebar-open .yt-sidebar-overlay {
    display: block;
  }

  /* Main content */
  .yt-main {
    margin-left: 0;
    padding: 0 12px calc(var(--bottomnav-h) + 12px);
  }

  .sidebar-open .yt-main {
    margin-left: 0;
  }

  .yt-header__start {
    min-width: auto;
  }

  .yt-header__end {
    min-width: auto;
    gap: 4px;
  }

  .yt-logo__img {
    height: 28px;
  }

  /* Show bottom nav */
  .yt-bottomnav {
    display: flex;
  }
}

/* Petit mobile (<= 480px) */
@media (max-width: 480px) {
  .yt-main {
    padding: 0 0 calc(var(--bottomnav-h) + 12px);
  }
  .yt-bottomnav__item { min-width: 48px; font-size: 9px; }
  .yt-bottomnav__mona-btn { width: 48px; height: 48px; }
}
</style>
