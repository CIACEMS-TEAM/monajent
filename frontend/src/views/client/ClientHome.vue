<script setup lang="ts">
import { useAuthStore } from '@/Stores/auth'
const auth = useAuthStore()
</script>

<template>
  <div class="wrap">
    <h1>Bienvenue, Client</h1>
    <p class="muted">Connecté en tant que: {{ auth.me?.username || auth.me?.phone }}</p>
    <div class="grid">
      <router-link class="card" to="/home#search">Rechercher un bien</router-link>
      <router-link class="card" to="/favorites">Mes favoris</router-link>
      <router-link class="card" to="/visits">Mes visites</router-link>
      <router-link class="card" to="/account">Mon compte</router-link>
    </div>
  </div>
</template>

<style scoped>
.wrap { max-width: 1080px; margin: 40px auto; padding: 0 16px; }
.muted { color: #666; margin-bottom: 16px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
.card { display:flex; align-items:center; justify-content:center; padding: 20px; border:1px solid #e5e5e5; border-radius: 12px; text-decoration:none; color:#1a1a1a; background:#fff; }
.card:hover { border-color:#ddd; box-shadow:0 6px 18px rgba(0,0,0,.08); }
</style>


