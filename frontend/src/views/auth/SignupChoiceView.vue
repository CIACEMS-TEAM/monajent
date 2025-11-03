<script setup lang="ts">
import { useRouter } from 'vue-router'
import logoUrl from '@/assets/icons/logo_monajent_sf.png'
import clientIcon from '@/assets/icons/client.png'
import agentIcon from '@/assets/icons/icone_agent_sf.png'

const router = useRouter()
</script>

<template>
  <div class="page">
    <header class="header">
      <div class="container">
        <img :src="logoUrl" alt="MonaJent" class="logo" />
      </div>
    </header>

    <div class="join">
      <h1 class="title">Rejoindre MonaJent</h1>
      <div class="cards">
        <button class="card" @click="router.push('/auth/signup/client')">
          <img :src="clientIcon" alt="Client" class="icon-img client" />
          <div class="h">Je suis client, je cherche un logement</div>
          <p class="p">Créez votre compte pour explorer avec des clés virtuelles et réserver des visites.</p>
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
.header { padding: 0; }
.container { width: min(1128px, 92vw); margin: -50px auto; padding: 0 24px; display:flex; align-items:center; }
.logo { height: 220px; width: auto; }

.join { max-width: 1040px; margin: 48px auto 64px; padding: 0 16px; text-align: center; }
.title { font-size: 36px; font-weight: 700; margin-bottom: 28px; }
.cards { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.card { text-align: left; background: #fff; border: 1px solid #e5e5e5; border-radius: 14px; padding: 32px; cursor: pointer; transition: box-shadow .15s ease, border-color .15s ease; min-height: 200px; }
.card:hover { box-shadow: 0 10px 26px rgba(0,0,0,.09); border-color: #e0e0e0; }
.icon-img { width: 40px; height: 40px; object-fit: contain; }
.icon-img.client { width: 70px; height: 70px; }
.h { font-weight: 700; margin: 10px 0 6px; font-size: 20px; }
.p { color: #555; font-size: 15px; }
.footer { margin-top: 22px; }
@media (max-width: 860px) { .cards { grid-template-columns: 1fr; } }
@media (max-width: 600px) { .logo { height: 72px; } }
</style>


