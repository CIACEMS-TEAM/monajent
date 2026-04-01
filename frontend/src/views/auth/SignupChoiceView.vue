<script setup lang="ts">
import { useRouter } from 'vue-router'
import logoUrl from '@/assets/icons/logo_monajent_header.webp'
import clientIcon from '@/assets/icons/client.png'
import agentIcon from '@/assets/icons/icone_agent_sf.png'

const router = useRouter()
</script>

<template>
  <div class="page">
    <header class="header">
      <div class="container">
        <router-link to="/home" class="back-btn" aria-label="Retour à l'accueil">
          <svg viewBox="0 0 24 24" width="22" height="22"><path fill="currentColor" d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
        </router-link>
        <router-link to="/home">
          <img :src="logoUrl" alt="MonaJent" class="logo" />
        </router-link>
      </div>
    </header>

    <div class="join">
      <h1 class="title">Rejoindre MonaJent</h1>
      <div class="cards">
        <button class="card" @click="router.push('/auth/signup/client')">
          <img :src="clientIcon" alt="Client" class="icon-img client" />
          <div class="h">Je suis client, je cherche un logement</div>
          <p class="p">Créez votre compte pour explorer avec des clés virtuelles et réserver des visites gratuites.</p>
        </button>
        <button class="card" @click="router.push('/auth/signup/agent')">
          <img :src="agentIcon" alt="Agent" class="icon-img agent" />
          <div class="h">Je suis agent, je propose des biens</div>
          <p class="p">Inscrivez‑vous pour publier des annonces et vérifier votre identité (KYC).</p>
        </button>
      </div>
      <div class="footer">
        <router-link to="/auth/login">Déjà un compte ? Se connecter</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { min-height: 100vh; background: #fff; }
.header { padding: 16px 0; border-bottom: 1px solid #E0E0E0; }
.container { width: min(1128px, 92vw); margin: 0 auto; padding: 0 24px; display: flex; align-items: center; gap: 12px; }
.logo { height: 32px; width: auto; }
.back-btn { display: flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; color: #272727; transition: background .15s; text-decoration: none; }
.back-btn:hover { background: #f2f2f2; }
.join { max-width: 1040px; margin: 48px auto 64px; padding: 0 16px; text-align: center; }
.title { font-size: 36px; font-weight: 700; margin-bottom: 28px; color: #0F0F0F; }
.cards { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.card { text-align: left; background: #fff; border: 1px solid #E0E0E0; border-radius: 14px; padding: 32px; cursor: pointer; transition: box-shadow .15s ease, border-color .15s ease; min-height: 200px; }
.card:hover { box-shadow: 0 10px 26px rgba(0,0,0,.09); border-color: #1DA53F; }
.icon-img { width: 40px; height: 40px; object-fit: contain; }
.icon-img.client { width: 70px; height: 70px; }
.h { font-weight: 700; margin: 10px 0 6px; font-size: 20px; color: #0F0F0F; }
.p { color: #272727; font-size: 15px; }
.footer { margin-top: 22px; }
.footer a { color: #1DA53F; font-weight: 500; }
@media (max-width: 860px) { .cards { grid-template-columns: 1fr; } }
@media (max-width: 600px) { .logo { height: 26px; } }
</style>
