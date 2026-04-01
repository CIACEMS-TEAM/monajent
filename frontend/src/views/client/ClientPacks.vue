<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useToast } from 'vue-toastification'
import http from '@/services/http'
import { usePublicStore } from '@/Stores/public'
import keyVirtImg from '@/assets/icons/key_virt.png'
import keyPhyImg from '@/assets/icons/key_phy.png'

declare const PaystackPop: any

let paystackLoaded = false
function loadPaystackSDK(retries = 3, delay = 2000): Promise<void> {
  if (paystackLoaded || typeof PaystackPop !== 'undefined') {
    paystackLoaded = true
    return Promise.resolve()
  }
  return new Promise((resolve, reject) => {
    const existing = document.querySelector('script[src*="paystack"]')
    if (existing) existing.remove()
    const s = document.createElement('script')
    s.src = 'https://js.paystack.co/v2/inline.js'
    s.onload = () => { paystackLoaded = true; resolve() }
    s.onerror = () => {
      s.remove()
      if (retries > 0) {
        setTimeout(() => loadPaystackSDK(retries - 1, delay * 1.5).then(resolve, reject), delay)
      } else {
        reject(new Error('Paystack SDK unreachable'))
      }
    }
    document.head.appendChild(s)
  })
}

const toast = useToast()
const route = useRoute()
const pub = usePublicStore()

interface Pack {
  id: number
  virtual_total: number
  virtual_used: number
  has_physical_key: boolean
  is_locked_by_visit: boolean
  created_at: string
}

const packs = ref<Pack[]>([])
const loading = ref(true)
const buying = ref(false)

const PACK_PRICE = 500
const PACK_VIRTUAL_KEYS = 33

const totalVirtual = computed(() => packs.value.reduce((s, p) => s + remaining(p), 0))
const totalPhysical = computed(() => packs.value.filter(p => p.has_physical_key && !p.is_locked_by_visit).length)

function remaining(p: Pack) { return Math.max(p.virtual_total - p.virtual_used, 0) }

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })
}

async function fetchPacks() {
  loading.value = true
  try {
    const { data } = await http.get<Pack[]>('/api/client/packs/')
    packs.value = Array.isArray(data) ? data : (data as any).results ?? []
  } catch { /* empty state handles this */ }
  finally { loading.value = false }
}

async function handleBuyPack() {
  if (buying.value) return
  try { await loadPaystackSDK() } catch {}
  if (typeof PaystackPop === 'undefined') {
    toast.error('Le serveur de paiement Paystack est temporairement injoignable. Réessayez dans quelques minutes.')
    return
  }

  buying.value = true

  try {
    const { data } = await http.post<{
      payment_id: number
      tx_ref: string
      checkout_url: string
      access_code: string
      status: string
      amount: string
      currency: string
      provider: string
    }>('/api/client/packs/buy/', {
      provider: 'PAYSTACK',
      return_url: `${window.location.origin}/home/packs`,
    })

    const txRef = data.tx_ref

    const popup = new PaystackPop()
    popup.resumeTransaction(data.access_code, {
      onSuccess: async (transaction: any) => {
        toast.success('Paiement réussi ! Activation de votre pack...')
        buying.value = false

        try {
          await http.post(`/api/payments/verify/${txRef}/`)
          pub.fetchKeyCounts()
          await fetchPacks()
          toast.success('Votre pack est actif !')
        } catch {
          toast.warning('Pack en cours d\'activation. Actualisez dans quelques instants.')
          await fetchPacks()
        }
      },
      onCancel: () => {
        buying.value = false
        toast.info('Paiement annulé.')
      },
      onError: (error: any) => {
        buying.value = false
        toast.error('Erreur de paiement. Veuillez réessayer.')
        console.error('[Paystack Error]', error)
      },
    })
  } catch (err: any) {
    buying.value = false
    const msg = err?.response?.data?.detail || 'Erreur lors de l\'initiation du paiement.'
    toast.error(msg)
  }
}

async function verifyPaymentFromCallback() {
  const trxref = route.query.trxref as string || route.query.reference as string
  if (!trxref) return

  toast.info('Vérification de votre paiement en cours...')

  try {
    const { data } = await http.post<{ tx_ref: string; status: string; pack: any }>(
      `/api/payments/verify/${trxref}/`,
    )

    if (data.status === 'PAID') {
      toast.success('Paiement confirmé ! Votre pack est actif.')
      pub.fetchKeyCounts()
      await fetchPacks()
    } else if (data.status === 'PENDING') {
      toast.warning('Paiement en cours de traitement. Actualisez dans quelques instants.')
    } else {
      toast.error('Le paiement a échoué. Veuillez réessayer.')
    }
  } catch {
    toast.warning('Impossible de vérifier le paiement. Actualisez la page.')
  }

  const url = new URL(window.location.href)
  url.searchParams.delete('trxref')
  url.searchParams.delete('reference')
  window.history.replaceState({}, '', url.toString())
}

onMounted(async () => {
  await fetchPacks()
  loadPaystackSDK().catch(() => {})
  await verifyPaymentFromCallback()
})
</script>

<template>
  <div class="pk">
    <!-- ── Hero offer ────────────────────────────────── -->
    <div class="pk__hero">
      <div class="pk__hero-badge">
        <img :src="keyPhyImg" alt="" class="pk__hero-badge-icon" />
        <span class="pk__hero-free">GRATUIT</span>
      </div>
      <h1 class="pk__hero-title">
        Visites <span class="pk__hero-hl">Gratuites</span>
      </h1>
      <p class="pk__hero-sub">
        avec seulement <strong>{{ PACK_PRICE }} F</strong> le pack de visionnage
      </p>
    </div>

    <div class="pk__offer">
      <div class="pk__offer-left">
        <h2 class="pk__offer-title">Pack Visites</h2>

        <div class="pk__offer-star">
          <img :src="keyPhyImg" alt="" class="pk__offer-star-icon" />
          <div>
            <span class="pk__offer-star-label">1 visite physique</span>
            <span class="pk__offer-star-free">OFFERTE</span>
          </div>
        </div>

        <div class="pk__offer-plus">
          <img :src="keyVirtImg" alt="" class="pk__offer-plus-icon" />
          <span class="pk__offer-plus-num">{{ PACK_VIRTUAL_KEYS }}</span>
          <span class="pk__offer-plus-label">visites virtuelles (vidéos exclusives)</span>
        </div>

        <ul class="pk__offer-perks">
          <li>Visitez un bien <strong>gratuitement</strong> avec un agent certifié</li>
          <li>Visionnez {{ PACK_VIRTUAL_KEYS }} vidéos immobilières avant de vous déplacer</li>
          <li>Paiement sécurisé : carte ou mobile money</li>
        </ul>
      </div>
      <div class="pk__offer-right">
        <div class="pk__price">
          <span class="pk__price-only">seulement</span>
          <span class="pk__price-amount">{{ PACK_PRICE.toLocaleString('fr-FR') }}</span>
          <span class="pk__price-currency">F CFA</span>
        </div>
        <button
          class="pk__buy-btn"
          :disabled="buying"
          @click="handleBuyPack"
        >
          <svg v-if="buying" class="pk__buy-spinner" viewBox="0 0 24 24" width="18" height="18">
            <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="3" stroke-dasharray="30 70" />
          </svg>
          <svg v-else viewBox="0 0 24 24" width="18" height="18">
            <path fill="currentColor" d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49A1.003 1.003 0 0 0 20 4H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z"/>
          </svg>
          {{ buying ? 'Paiement en cours...' : 'Acheter mon pack' }}
        </button>
        <div class="pk__payment-methods">
          <span>Orange Money</span>
          <span>MTN</span>
          <span>Wave</span>
          <span>Visa / MC</span>
        </div>
      </div>
    </div>

    <!-- ── Summary strip ─────────────────────────────── -->
    <div v-if="!loading && packs.length > 0" class="pk__summary">
      <div class="pk__summary-item">
        <img :src="keyVirtImg" alt="" class="pk__summary-icon" />
        <span class="pk__summary-val">{{ totalVirtual }}</span>
        <span class="pk__summary-lbl">clés virtuelles disponibles</span>
      </div>
      <div class="pk__summary-item">
        <img :src="keyPhyImg" alt="" class="pk__summary-icon" />
        <span class="pk__summary-val">{{ totalPhysical }}</span>
        <span class="pk__summary-lbl">visites physiques disponibles</span>
      </div>
      <div class="pk__summary-item">
        <span class="pk__summary-val pk__summary-val--count">{{ packs.length }}</span>
        <span class="pk__summary-lbl">packs achetés</span>
      </div>
    </div>

    <!-- ── My packs ──────────────────────────────────── -->
    <h2 v-if="!loading" class="pk__section-title">Mes packs</h2>

    <div v-if="loading" class="pk__loading">
      <div class="pk__spinner"></div>
    </div>

    <div v-else-if="packs.length === 0" class="pk__empty">
      <svg viewBox="0 0 24 24" width="48" height="48"><path fill="#E0E0E0" d="M18 6h-2c0-2.21-1.79-4-4-4S8 3.79 8 6H6c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-6-2c1.1 0 2 .9 2 2h-4c0-1.1.9-2 2-2zm6 16H6V8h2v2c0 .55.45 1 1 1s1-.45 1-1V8h4v2c0 .55.45 1 1 1s1-.45 1-1V8h2v12z"/></svg>
      <p>Aucun pack pour le moment.</p>
      <p class="pk__empty-hint">Achetez votre premier pack pour commencer les visites.</p>
    </div>

    <div v-else class="pk__grid">
      <div v-for="pack in packs" :key="pack.id" class="pk__card">
        <div class="pk__card-top">
          <span class="pk__badge" :class="{
            'pk__badge--locked': pack.is_locked_by_visit,
            'pk__badge--exhausted': remaining(pack) === 0 && !pack.has_physical_key,
          }">
            {{ pack.is_locked_by_visit ? 'Visite en cours' : remaining(pack) === 0 && !pack.has_physical_key ? 'Épuisé' : 'Actif' }}
          </span>
          <span class="pk__date">{{ formatDate(pack.created_at) }}</span>
        </div>
        <div class="pk__keys">
          <div class="pk__key">
            <img :src="keyVirtImg" alt="" class="pk__key-icon" />
            <div>
              <div class="pk__key-value">{{ remaining(pack) }}</div>
              <div class="pk__key-label">clés virtuelles</div>
            </div>
          </div>
          <div class="pk__key">
            <img :src="keyPhyImg" alt="" class="pk__key-icon" />
            <div>
              <div class="pk__key-value">{{ pack.has_physical_key ? '1' : '0' }}</div>
              <div class="pk__key-label">visite physique</div>
            </div>
          </div>
        </div>
        <div class="pk__bar">
          <div class="pk__bar-fill" :style="{ width: (pack.virtual_used / pack.virtual_total * 100) + '%' }"></div>
        </div>
        <div class="pk__bar-label">{{ pack.virtual_used }}/{{ pack.virtual_total }} clés utilisées</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pk { max-width: 860px; margin: 0 auto; padding: 0 16px; }

/* ── Hero banner ─────────────────────────── */
.pk__hero {
  text-align: center; padding: 32px 20px 20px;
  background: linear-gradient(135deg, #065f46 0%, #047857 40%, #059669 100%);
  border-radius: 18px 18px 0 0; margin-bottom: 0;
  position: relative; overflow: hidden;
}
.pk__hero::after {
  content: ''; position: absolute; inset: 0;
  background: radial-gradient(ellipse at 30% 20%, rgba(255,255,255,.08) 0%, transparent 60%);
  pointer-events: none;
}
.pk__hero-badge {
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(255,255,255,.15); backdrop-filter: blur(4px);
  border: 1px solid rgba(255,255,255,.25); border-radius: 30px;
  padding: 6px 18px 6px 10px; margin-bottom: 10px;
}
.pk__hero-badge-icon { width: 28px; height: 28px; object-fit: contain; }
.pk__hero-free {
  font-size: 14px; font-weight: 900; color: #fbbf24;
  letter-spacing: 2px; text-transform: uppercase;
}
.pk__hero-title {
  font-size: 32px; font-weight: 900; color: #fff; margin: 0 0 6px;
  line-height: 1.15;
}
.pk__hero-hl {
  color: #fbbf24; position: relative;
}
.pk__hero-hl::after {
  content: ''; position: absolute; left: 0; bottom: -2px;
  width: 100%; height: 4px; border-radius: 2px;
  background: rgba(251,191,36,.4);
}
.pk__hero-sub {
  font-size: 15px; color: rgba(255,255,255,.85); margin: 0;
}
.pk__hero-sub strong { color: #fff; font-weight: 800; font-size: 17px; }

/* ── Offer card ──────────────────────────── */
.pk__offer {
  display: flex; gap: 24px; align-items: stretch;
  background: #fff;
  border: 1px solid #d1fae5; border-top: none;
  border-radius: 0 0 18px 18px;
  padding: 24px 28px 28px; margin-bottom: 24px;
  box-shadow: 0 4px 20px rgba(0,0,0,.05);
}
.pk__offer-left { flex: 1; }
.pk__offer-right {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-width: 200px; gap: 12px;
}
.pk__offer-title {
  font-size: 20px; font-weight: 800; color: #0F0F0F; margin: 0 0 16px;
}

/* Star feature — FREE physical visit */
.pk__offer-star {
  display: flex; align-items: center; gap: 12px;
  background: linear-gradient(90deg, #fef9c3, #fef3c7);
  border: 2px solid #fbbf24; border-radius: 12px;
  padding: 12px 16px; margin-bottom: 14px;
}
.pk__offer-star-icon { width: 36px; height: 36px; object-fit: contain; }
.pk__offer-star-label { font-size: 15px; font-weight: 700; color: #0F0F0F; display: block; }
.pk__offer-star-free {
  display: inline-block; font-size: 12px; font-weight: 900; color: #fff;
  background: #f59e0b; padding: 2px 10px; border-radius: 6px;
  letter-spacing: 1.5px; text-transform: uppercase; margin-top: 2px;
}

/* Plus feature — virtual keys */
.pk__offer-plus {
  display: flex; align-items: center; gap: 10px; margin-bottom: 14px;
  padding: 8px 0;
}
.pk__offer-plus-icon { width: 28px; height: 28px; object-fit: contain; }
.pk__offer-plus-num { font-size: 24px; font-weight: 900; color: #1DA53F; }
.pk__offer-plus-label { font-size: 13px; color: #606060; }

.pk__offer-perks { list-style: none; padding: 0; margin: 0; }
.pk__offer-perks li {
  font-size: 13px; color: #444; padding: 3px 0; padding-left: 20px;
  position: relative;
}
.pk__offer-perks li::before {
  content: '✓'; position: absolute; left: 0; color: #1DA53F; font-weight: 700;
}

.pk__price { text-align: center; }
.pk__price-only {
  display: block; font-size: 11px; color: #909090; text-transform: uppercase;
  letter-spacing: 1px; font-weight: 600; margin-bottom: 2px;
}
.pk__price-amount { font-size: 40px; font-weight: 900; color: #1DA53F; line-height: 1; }
.pk__price-currency { font-size: 14px; font-weight: 600; color: #1DA53F; display: block; margin-top: 2px; }

.pk__buy-btn {
  display: flex; align-items: center; gap: 8px; justify-content: center;
  width: 100%; padding: 14px 24px;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #fff; border: none; border-radius: 12px;
  font-size: 16px; font-weight: 800; cursor: pointer;
  transition: background .2s, transform .1s, box-shadow .2s;
  box-shadow: 0 4px 14px rgba(245,158,11,.3);
}
.pk__buy-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #d97706, #b45309);
  transform: translateY(-2px); box-shadow: 0 6px 20px rgba(245,158,11,.4);
}
.pk__buy-btn:active:not(:disabled) { transform: translateY(0); }
.pk__buy-btn:disabled { opacity: .7; cursor: wait; }

.pk__buy-spinner { animation: spin .7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.pk__payment-methods {
  display: flex; gap: 6px; flex-wrap: wrap; justify-content: center;
}
.pk__payment-methods span {
  font-size: 10px; color: #909090; padding: 2px 8px;
  background: rgba(0,0,0,.04); border-radius: 4px;
}

/* ── Summary strip ───────────────────────── */
.pk__summary {
  display: flex; gap: 16px; margin-bottom: 24px;
  background: #fff; border: 1px solid #E0E0E0; border-radius: 12px; padding: 16px 20px;
}
.pk__summary-item { display: flex; align-items: center; gap: 8px; flex: 1; }
.pk__summary-icon { width: 24px; height: 24px; object-fit: contain; }
.pk__summary-val { font-size: 22px; font-weight: 800; color: #0F0F0F; }
.pk__summary-val--count { color: #606060; }
.pk__summary-lbl { font-size: 12px; color: #606060; }

/* ── Section title ───────────────────────── */
.pk__section-title { font-size: 18px; font-weight: 700; color: #0F0F0F; margin: 0 0 16px; }

/* ── Loading / Empty ─────────────────────── */
.pk__loading { display: flex; justify-content: center; padding: 64px 0; }
.pk__spinner { width: 32px; height: 32px; border: 3px solid #E0E0E0; border-top-color: #1DA53F; border-radius: 50%; animation: spin .7s linear infinite; }
.pk__empty { text-align: center; padding: 48px 16px; color: #606060; }
.pk__empty p { margin: 8px 0; }
.pk__empty-hint { font-size: 13px; color: #909090; }

/* ── Pack cards ──────────────────────────── */
.pk__grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.pk__card { background: #fff; border: 1px solid #E0E0E0; border-radius: 12px; padding: 20px; }
.pk__card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.pk__badge { padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; background: rgba(29,165,63,.1); color: #1DA53F; }
.pk__badge--locked { background: rgba(245,158,11,.1); color: #d97706; }
.pk__badge--exhausted { background: rgba(239,68,68,.08); color: #dc2626; }
.pk__date { font-size: 12px; color: #909090; }
.pk__keys { display: flex; gap: 24px; margin-bottom: 14px; }
.pk__key { display: flex; align-items: center; gap: 8px; }
.pk__key-icon { width: 28px; height: 28px; object-fit: contain; }
.pk__key-value { font-size: 26px; font-weight: 800; color: #0F0F0F; }
.pk__key-label { font-size: 12px; color: #606060; }
.pk__bar { height: 6px; background: #f0f0f0; border-radius: 3px; overflow: hidden; }
.pk__bar-fill { height: 100%; background: #1DA53F; border-radius: 3px; transition: width .3s; }
.pk__bar-label { font-size: 11px; color: #909090; margin-top: 4px; }

/* ── Responsive ──────────────────────────── */
@media (max-width: 640px) {
  .pk__hero { padding: 24px 16px 16px; }
  .pk__hero-title { font-size: 26px; }
  .pk__offer { flex-direction: column; padding: 20px 16px; }
  .pk__offer-right { min-width: auto; }
  .pk__summary { flex-direction: column; gap: 10px; }
  .pk__grid { grid-template-columns: 1fr; }
}
</style>
