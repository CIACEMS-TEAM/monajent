<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useClientStore } from '@/Stores/client'

const client = useClientStore()
const receiptPayment = ref<any>(null)

onMounted(() => {
  client.fetchPayments()
})

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('fr-FR', {
    day: 'numeric', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function formatDateFull(iso: string) {
  return new Date(iso).toLocaleDateString('fr-FR', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function formatPrice(val: string | number) {
  return Number(val).toLocaleString('fr-FR') + ' F CFA'
}

function statusSeverity(s: string): string {
  const map: Record<string, string> = {
    PAID: 'pay--paid', PENDING: 'pay--pending',
    FAILED: 'pay--failed', REFUNDED: 'pay--refunded',
  }
  return map[s] || ''
}

function providerIcon(p: string): string {
  const map: Record<string, string> = {
    ORANGE_MONEY: 'pi-mobile', WAVE: 'pi-bolt',
    MTN: 'pi-phone', CARD: 'pi-credit-card',
    PAYSTACK: 'pi-wallet',
  }
  return map[p] || 'pi-wallet'
}

function openReceipt(p: any) {
  receiptPayment.value = p
}

function closeReceipt() {
  receiptPayment.value = null
}

function printReceipt() {
  window.print()
}
</script>

<template>
  <div class="pay">
    <h1 class="pay__title">
      <i class="pi pi-credit-card"></i>
      Historique des paiements
    </h1>

    <div v-if="client.paymentsLoading && client.payments.length === 0" class="pay__loading">
      <div class="pay__spinner"></div>
    </div>

    <div v-else-if="client.payments.length === 0" class="pay__empty">
      <svg viewBox="0 0 24 24" width="56" height="56"><path fill="#E0E0E0" d="M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z"/></svg>
      <p>Aucun paiement pour l'instant.</p>
      <p class="pay__hint">Vos achats de packs apparaîtront ici.</p>
      <router-link to="/home/packs" class="pay__btn">Voir mes packs</router-link>
    </div>

    <div v-else class="pay__list">
      <div
        v-for="p in client.payments"
        :key="p.id"
        class="pay__card"
        :class="statusSeverity(p.status)"
        @click="openReceipt(p)"
      >
        <div class="pay__card-icon">
          <i :class="'pi ' + providerIcon(p.provider)"></i>
        </div>
        <div class="pay__card-body">
          <div class="pay__card-top">
            <span class="pay__provider">{{ p.provider_label }}</span>
            <span class="pay__badge" :class="'pay__badge--' + p.status.toLowerCase()">
              {{ p.status_label }}
            </span>
          </div>
          <div class="pay__card-mid">
            <span class="pay__amount">{{ formatPrice(p.amount) }}</span>
          </div>
          <div class="pay__card-bottom">
            <span class="pay__date">{{ formatDate(p.created_at) }}</span>
            <span class="pay__ref">Réf: {{ p.tx_ref.slice(0, 12) }}...</span>
          </div>
        </div>
        <div class="pay__card-actions">
          <button
            class="pay__receipt-btn"
            title="Voir le reçu"
            @click.stop="openReceipt(p)"
          >
            <i class="pi pi-file-pdf"></i>
          </button>
          <router-link
            v-if="p.has_pack && p.pack_id"
            :to="'/home/packs'"
            class="pay__pack-link"
            title="Voir le pack associé"
            @click.stop
          >
            <i class="pi pi-shopping-bag"></i>
          </router-link>
        </div>
      </div>
    </div>

    <!-- Receipt modal -->
    <Teleport to="body">
      <div v-if="receiptPayment" class="rcpt-overlay" @click.self="closeReceipt">
        <div class="rcpt no-print-hide" id="receipt-content">
          <div class="rcpt__header">
            <div class="rcpt__logo">
              <svg viewBox="0 0 24 24" width="28" height="28"><path fill="#1DA53F" d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
              <span class="rcpt__brand">MonaJent</span>
            </div>
            <h2 class="rcpt__title">Reçu de paiement</h2>
          </div>

          <div class="rcpt__badge-row">
            <span
              class="rcpt__status"
              :class="'rcpt__status--' + receiptPayment.status.toLowerCase()"
            >
              {{ receiptPayment.status_label }}
            </span>
          </div>

          <div class="rcpt__amount-row">
            <span class="rcpt__amount">{{ formatPrice(receiptPayment.amount) }}</span>
          </div>

          <div class="rcpt__divider"></div>

          <table class="rcpt__details">
            <tr>
              <td class="rcpt__label">Référence</td>
              <td class="rcpt__value rcpt__mono">{{ receiptPayment.tx_ref }}</td>
            </tr>
            <tr>
              <td class="rcpt__label">Méthode</td>
              <td class="rcpt__value">{{ receiptPayment.provider_label }}</td>
            </tr>
            <tr>
              <td class="rcpt__label">Date</td>
              <td class="rcpt__value">{{ formatDateFull(receiptPayment.created_at) }}</td>
            </tr>
            <tr>
              <td class="rcpt__label">Devise</td>
              <td class="rcpt__value">{{ receiptPayment.currency }}</td>
            </tr>
            <tr v-if="receiptPayment.has_pack">
              <td class="rcpt__label">Pack associé</td>
              <td class="rcpt__value">Pack Visites #{{ receiptPayment.pack_id }}</td>
            </tr>
          </table>

          <div class="rcpt__divider"></div>

          <p class="rcpt__footer-note">
            Ce reçu confirme votre transaction sur MonaJent.<br>
            Conservez-le comme preuve de paiement.
          </p>

          <div class="rcpt__actions no-print">
            <button class="rcpt__btn rcpt__btn--print" @click="printReceipt">
              <i class="pi pi-print"></i> Imprimer
            </button>
            <button class="rcpt__btn rcpt__btn--close" @click="closeReceipt">
              Fermer
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.pay { max-width: 700px; margin: 0 auto; padding: 0 16px; }
.pay__title {
  font-size: 22px; font-weight: 700; color: #0F0F0F;
  margin-bottom: 20px; display: flex; align-items: center; gap: 8px;
}
.pay__title i { color: #1DA53F; }

.pay__loading { display: flex; justify-content: center; padding: 64px 0; }
.pay__spinner {
  width: 32px; height: 32px; border: 3px solid #E0E0E0;
  border-top-color: #1DA53F; border-radius: 50%;
  animation: pay-spin 0.7s linear infinite;
}
@keyframes pay-spin { to { transform: rotate(360deg); } }

.pay__empty { text-align: center; padding: 64px 16px; color: #606060; }
.pay__empty p { margin: 8px 0; }
.pay__hint { font-size: 14px; color: #888; }
.pay__btn {
  display: inline-block; padding: 10px 24px; margin-top: 8px;
  background: #1DA53F; color: #fff; border-radius: 8px;
  text-decoration: none; font-weight: 600;
}
.pay__btn:hover { background: #168a34; }

.pay__list { display: flex; flex-direction: column; gap: 10px; }

.pay__card {
  display: flex; align-items: center; gap: 14px;
  padding: 14px 18px; border-radius: 12px;
  background: #fff; border: 1px solid #e0e0e0;
  transition: box-shadow 0.15s;
  cursor: pointer;
}
.pay__card:hover { box-shadow: 0 2px 10px rgba(0,0,0,0.05); }

.pay__card-icon {
  width: 42px; height: 42px; border-radius: 10px;
  background: #f2f2f2; display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.pay__card-icon i { font-size: 20px; color: #1DA53F; }

.pay__card-body { flex: 1; min-width: 0; }

.pay__card-top {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 4px;
}
.pay__provider { font-size: 14px; font-weight: 600; color: #0f0f0f; }

.pay__badge {
  font-size: 11px; font-weight: 600; padding: 2px 8px;
  border-radius: 4px; text-transform: uppercase;
}
.pay__badge--paid { background: #dcfce7; color: #16a34a; }
.pay__badge--pending { background: #fef3c7; color: #d97706; }
.pay__badge--failed { background: #fef2f2; color: #dc2626; }
.pay__badge--refunded { background: #ede9fe; color: #7c3aed; }

.pay__card-mid { margin-bottom: 4px; }
.pay__amount { font-size: 16px; font-weight: 700; color: #1DA53F; }

.pay__card-bottom {
  display: flex; align-items: center; gap: 12px;
  font-size: 12px; color: #888;
}
.pay__ref { font-family: monospace; font-size: 11px; }

.pay__card-actions {
  display: flex; flex-direction: column; gap: 6px;
  flex-shrink: 0;
}

.pay__receipt-btn {
  width: 36px; height: 36px; border-radius: 8px;
  background: #fff7ed; border: 1px solid #fed7aa;
  display: flex; align-items: center; justify-content: center;
  color: #ea580c; cursor: pointer; transition: background 0.15s;
}
.pay__receipt-btn:hover { background: #ffedd5; }

.pay__pack-link {
  width: 36px; height: 36px; border-radius: 8px;
  background: #f0fdf4; border: 1px solid #bbf7d0;
  display: flex; align-items: center; justify-content: center;
  color: #1DA53F; text-decoration: none; flex-shrink: 0;
  transition: background 0.15s;
}
.pay__pack-link:hover { background: #dcfce7; }

/* ── Receipt modal ──────────────────────── */
.rcpt-overlay {
  position: fixed; inset: 0; z-index: 9000;
  background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center;
  padding: 16px;
}

.rcpt {
  background: #fff; border-radius: 14px; width: 100%; max-width: 440px;
  padding: 32px 28px; box-shadow: 0 12px 48px rgba(0,0,0,0.18);
  position: relative;
}

.rcpt__header { text-align: center; margin-bottom: 16px; }
.rcpt__logo {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  margin-bottom: 8px;
}
.rcpt__brand { font-size: 20px; font-weight: 800; color: #1DA53F; }
.rcpt__title { font-size: 16px; font-weight: 600; color: #444; margin: 0; }

.rcpt__badge-row { text-align: center; margin-bottom: 8px; }
.rcpt__status {
  display: inline-block; padding: 4px 14px; border-radius: 6px;
  font-size: 12px; font-weight: 700; text-transform: uppercase;
}
.rcpt__status--paid { background: #dcfce7; color: #16a34a; }
.rcpt__status--pending { background: #fef3c7; color: #d97706; }
.rcpt__status--failed { background: #fef2f2; color: #dc2626; }
.rcpt__status--refunded { background: #ede9fe; color: #7c3aed; }

.rcpt__amount-row { text-align: center; margin-bottom: 16px; }
.rcpt__amount { font-size: 28px; font-weight: 800; color: #0f0f0f; }

.rcpt__divider {
  border: none; border-top: 1px dashed #d0d0d0;
  margin: 16px 0; height: 0;
}

.rcpt__details {
  width: 100%; border-collapse: collapse;
  font-size: 14px;
}
.rcpt__details tr { border-bottom: 1px solid #f0f0f0; }
.rcpt__details tr:last-child { border-bottom: none; }
.rcpt__details td { padding: 8px 0; }
.rcpt__label { color: #888; font-weight: 500; width: 130px; }
.rcpt__value { color: #0f0f0f; font-weight: 600; word-break: break-all; }
.rcpt__mono { font-family: monospace; font-size: 12px; }

.rcpt__footer-note {
  text-align: center; font-size: 12px; color: #999;
  margin: 16px 0 0; line-height: 1.5;
}

.rcpt__actions {
  display: flex; gap: 10px; margin-top: 20px;
  justify-content: center;
}
.rcpt__btn {
  padding: 10px 24px; border-radius: 8px; font-size: 14px;
  font-weight: 600; cursor: pointer; border: none;
  display: flex; align-items: center; gap: 6px;
  transition: background 0.15s;
}
.rcpt__btn--print { background: #1DA53F; color: #fff; }
.rcpt__btn--print:hover { background: #168a34; }
.rcpt__btn--close { background: #f5f5f5; color: #444; }
.rcpt__btn--close:hover { background: #e5e5e5; }

@media (max-width: 480px) {
  .pay__card { padding: 12px 14px; }
  .pay__card-bottom { flex-direction: column; align-items: flex-start; gap: 2px; }
  .rcpt { padding: 24px 18px; }
  .rcpt__amount { font-size: 24px; }
}
</style>

<!-- Print styles (global, not scoped) -->
<style>
@media print {
  body * { visibility: hidden !important; }
  #receipt-content, #receipt-content * { visibility: visible !important; }
  #receipt-content {
    position: fixed !important; top: 0; left: 0;
    width: 100% !important; max-width: 100% !important;
    padding: 40px !important; box-shadow: none !important;
    border-radius: 0 !important;
  }
  .rcpt-overlay { background: #fff !important; }
  .no-print { display: none !important; }
}
</style>
