<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'vue-toastification'
import { useAgentStore } from '@/Stores/agent'

const agent = useAgentStore()
const toast = useToast()

const showWithdraw = ref(false)
const withdrawForm = ref({ amount: '', method: 'ORANGE_MONEY', phone_number: '', pin: '' })
const withdrawLoading = ref(false)

const filterSource = ref('')
const filterType = ref('')

onMounted(async () => {
  try { await Promise.all([agent.fetchWallet(), agent.fetchWalletEntries(), agent.fetchWithdrawals()]) }
  catch (_) { /* handled by store */ }
})

async function applyFilters() {
  const params: Record<string, string> = {}
  if (filterSource.value) params.source = filterSource.value
  if (filterType.value) params.entry_type = filterType.value
  await agent.fetchWalletEntries(params)
}

function clearFilters() {
  filterSource.value = ''
  filterType.value = ''
  agent.fetchWalletEntries()
}

function formatPrice(n: number | string): string {
  return Number(n).toLocaleString('fr-FR') + ' F'
}

async function requestWithdraw() {
  const amount = parseInt(withdrawForm.value.amount)
  if (!amount || amount <= 0) { toast.error('Montant invalide'); return }
  if (!withdrawForm.value.pin) { toast.error('Code PIN requis'); return }
  if (!withdrawForm.value.phone_number) { toast.error('Numéro de téléphone requis'); return }

  withdrawLoading.value = true
  try {
    await agent.requestWithdrawal({
      pin: withdrawForm.value.pin,
      amount,
      method: withdrawForm.value.method,
      phone_number: withdrawForm.value.phone_number,
    })
    toast.success('Demande de retrait envoyée')
    withdrawForm.value = { amount: '', method: 'ORANGE_MONEY', phone_number: '', pin: '' }
    showWithdraw.value = false
    await agent.fetchWalletEntries()
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    if (e?.response?.data?.pin_required) {
      toast.error('Vous devez d\'abord configurer votre code PIN dans les paramètres.')
    } else {
      toast.error(detail || 'Échec du retrait')
    }
  } finally {
    withdrawLoading.value = false
  }
}

function statusLabel(s: string) {
  const map: Record<string, string> = { PENDING: 'En cours', COMPLETED: 'Effectué', REJECTED: 'Rejeté' }
  return map[s] || s
}
function statusClass(s: string) { return s.toLowerCase() }

const methods = [
  { value: 'ORANGE_MONEY', label: 'Orange Money' },
  { value: 'WAVE', label: 'Wave' },
  { value: 'MTN', label: 'MTN Money' },
]
</script>

<template>
  <div class="wlt">
    <h1 class="wlt__title">Revenus</h1>

    <!-- Loading -->
    <div v-if="agent.walletLoading && !agent.wallet" class="wlt__loading">
      <p>Chargement du portefeuille...</p>
    </div>

    <template v-else>
      <!-- KPI Cards -->
      <div class="wlt__kpi-row">
        <div class="wlt__kpi wlt__kpi--balance">
          <div class="wlt__kpi-icon">
            <svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M21 18v1c0 1.1-.9 2-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h14c1.1 0 2 .9 2 2v1h-9a2 2 0 00-2 2v8a2 2 0 002 2h9zm-9-2h10V8H12v8zm4-2.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/></svg>
          </div>
          <div class="wlt__kpi-body">
            <span class="wlt__kpi-label">Solde disponible</span>
            <span class="wlt__kpi-value wlt__kpi-value--balance">{{ formatPrice(agent.walletBalance) }}</span>
          </div>
          <button
            class="wlt__withdraw-btn"
            :disabled="!agent.walletCanWithdraw"
            @click="showWithdraw = true"
            :title="!agent.walletHasPin ? 'Configurez votre PIN dans les paramètres' : !agent.walletCanWithdraw ? 'Solde insuffisant (min. 2 000 F)' : ''"
          >
            <svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M9 16h6v-6h4l-7-7-7 7h4v6zm-4 2h14v2H5v-2z" transform="rotate(180 12 12)"/></svg>
            Retirer
          </button>
        </div>
        <div class="wlt__kpi wlt__kpi--earned">
          <div class="wlt__kpi-icon">
            <svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M7 14l5-5 5 5H7z"/></svg>
          </div>
          <div class="wlt__kpi-body">
            <span class="wlt__kpi-label">Total gagné</span>
            <span class="wlt__kpi-value wlt__kpi-value--earned">{{ formatPrice(agent.walletTotalEarned) }}</span>
            <span class="wlt__kpi-sub">Cumul de tous vos revenus</span>
          </div>
        </div>
        <div class="wlt__kpi wlt__kpi--withdrawn">
          <div class="wlt__kpi-icon">
            <svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M7 10l5 5 5-5H7z"/></svg>
          </div>
          <div class="wlt__kpi-body">
            <span class="wlt__kpi-label">Total retiré</span>
            <span class="wlt__kpi-value wlt__kpi-value--withdrawn">{{ formatPrice(agent.walletTotalWithdrawn) }}</span>
            <span class="wlt__kpi-sub">Cumul de tous vos retraits</span>
          </div>
        </div>
      </div>

      <!-- Pending withdrawal alert -->
      <div v-if="agent.wallet?.pending_withdrawal" class="wlt__pending-alert">
        <svg viewBox="0 0 24 24" width="20" height="20"><path fill="#d97706" d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>
        <span>Retrait en attente de <strong>{{ formatPrice(agent.wallet.pending_withdrawal.amount) }}</strong> via {{ agent.wallet.pending_withdrawal.method }}</span>
      </div>

      <div class="wlt__grid">
        <!-- Historique mouvements -->
        <section class="wlt__section">
          <h2 class="wlt__section-title">Historique des mouvements</h2>
          <div class="wlt__filters">
            <select v-model="filterType" @change="applyFilters" class="wlt__filter-select">
              <option value="">Tous les types</option>
              <option value="CREDIT">Crédits</option>
              <option value="DEBIT">Débits</option>
            </select>
            <select v-model="filterSource" @change="applyFilters" class="wlt__filter-select">
              <option value="">Toutes les sources</option>
              <option value="VIDEO_VIEW">Visionnage vidéo</option>
              <option value="PHYSICAL_VISIT">Visite physique</option>
              <option value="WITHDRAWAL">Retrait</option>
              <option value="ADJUSTMENT">Ajustement</option>
            </select>
            <button v-if="filterType || filterSource" class="wlt__filter-clear" @click="clearFilters">&times; Effacer</button>
          </div>
          <div v-if="agent.walletEntriesLoading" class="wlt__empty">Chargement...</div>
          <div v-else-if="agent.walletEntries.length === 0" class="wlt__empty">Aucun mouvement pour le moment</div>
          <div v-else class="wlt__entries">
            <div v-for="entry in agent.walletEntries" :key="entry.id" class="wlt__entry">
              <div class="wlt__entry-icon" :class="(entry.entry_type || '').toLowerCase()">
                <svg v-if="entry.entry_type === 'CREDIT'" viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M7 14l5-5 5 5H7z"/></svg>
                <svg v-else viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M7 10l5 5 5-5H7z"/></svg>
              </div>
              <div class="wlt__entry-info">
                <span class="wlt__entry-label">{{ entry.label || entry.source_label }}</span>
                <span class="wlt__entry-date">{{ new Date(entry.created_at).toLocaleDateString('fr-FR') }}</span>
              </div>
              <span class="wlt__entry-amount" :class="(entry.entry_type || '').toLowerCase()">
                {{ entry.entry_type === 'CREDIT' ? '+' : '-' }}{{ formatPrice(entry.amount) }}
              </span>
            </div>
          </div>
        </section>

        <!-- Historique retraits -->
        <section class="wlt__section">
          <h2 class="wlt__section-title">Demandes de retrait</h2>
          <div v-if="agent.withdrawalsLoading" class="wlt__empty">Chargement...</div>
          <div v-else-if="agent.withdrawals.length === 0" class="wlt__empty">Aucune demande de retrait</div>
          <div v-else class="wlt__withdrawals">
            <div v-for="w in agent.withdrawals" :key="w.id" class="wlt__withdrawal">
              <div class="wlt__withdrawal-info">
                <span class="wlt__withdrawal-amount">{{ formatPrice(w.amount) }}</span>
                <span class="wlt__withdrawal-method">{{ w.method_label }} — {{ w.phone_number }}</span>
                <span class="wlt__withdrawal-date">{{ new Date(w.created_at).toLocaleDateString('fr-FR') }}</span>
              </div>
              <span class="wlt__withdrawal-badge" :class="statusClass(w.status)">{{ statusLabel(w.status) }}</span>
            </div>
          </div>
        </section>
      </div>
    </template>

    <!-- Withdraw modal -->
    <div v-if="showWithdraw" class="wlt__modal-overlay" @click.self="showWithdraw = false">
      <div class="wlt__modal">
        <h3 class="wlt__modal-title">Demander un retrait</h3>
        <p class="wlt__modal-sub">
          Solde : <strong>{{ formatPrice(agent.walletBalance) }}</strong>
          &middot; Minimum : <strong>{{ formatPrice(agent.walletMinWithdrawal) }}</strong>
        </p>

        <div class="wlt__modal-field">
          <label>Montant (FCFA)</label>
          <input v-model="withdrawForm.amount" type="number" :max="agent.walletBalance" placeholder="Ex: 10000" />
        </div>

        <div class="wlt__modal-field">
          <label>Méthode de retrait</label>
          <div class="wlt__modal-methods">
            <label
              v-for="m in methods"
              :key="m.value"
              class="wlt__method"
              :class="{ active: withdrawForm.method === m.value }"
            >
              <input type="radio" v-model="withdrawForm.method" :value="m.value" />
              <span>{{ m.label }}</span>
            </label>
          </div>
        </div>

        <div class="wlt__modal-field">
          <label>Numéro de téléphone</label>
          <input v-model="withdrawForm.phone_number" type="tel" placeholder="+2250700..." />
        </div>

        <div class="wlt__modal-field">
          <label>Code PIN de retrait</label>
          <input v-model="withdrawForm.pin" type="password" maxlength="4" placeholder="••••" />
        </div>

        <div class="wlt__modal-actions">
          <button class="wlt__modal-btn cancel" @click="showWithdraw = false" :disabled="withdrawLoading">Annuler</button>
          <button class="wlt__modal-btn confirm" @click="requestWithdraw" :disabled="withdrawLoading">
            {{ withdrawLoading ? 'Traitement...' : 'Confirmer le retrait' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wlt { max-width: 1000px; }
.wlt__title { font-size: 24px; font-weight: 700; color: #0F0F0F; margin-bottom: 24px; }
.wlt__loading { padding: 48px 0; text-align: center; color: #606060; }

/* KPI Row */
.wlt__kpi-row {
  display: grid;
  grid-template-columns: 1.4fr 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
.wlt__kpi {
  background: #fff;
  border: 1px solid #E0E0E0;
  border-radius: 14px;
  padding: 20px;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  position: relative;
}
.wlt__kpi--balance { border-left: 4px solid #1DA53F; }
.wlt__kpi--earned { border-left: 4px solid #0F0F0F; }
.wlt__kpi--withdrawn { border-left: 4px solid #d97706; }

.wlt__kpi-icon {
  width: 44px; height: 44px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.wlt__kpi--balance .wlt__kpi-icon { background: rgba(29,165,63,.1); color: #1DA53F; }
.wlt__kpi--earned .wlt__kpi-icon { background: #f3f4f6; color: #0F0F0F; }
.wlt__kpi--withdrawn .wlt__kpi-icon { background: #fef3c7; color: #d97706; }

.wlt__kpi-body { flex: 1; min-width: 0; }
.wlt__kpi-label { display: block; font-size: 12px; color: #606060; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
.wlt__kpi-value { display: block; font-size: 24px; font-weight: 700; line-height: 1.2; }
.wlt__kpi-value--balance { color: #1DA53F; }
.wlt__kpi-value--earned { color: #0F0F0F; }
.wlt__kpi-value--withdrawn { color: #d97706; }
.wlt__kpi-sub { display: block; font-size: 11px; color: #999; margin-top: 4px; }

.wlt__withdraw-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border: none;
  border-radius: 20px;
  background: #1DA53F;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background .15s;
  flex-shrink: 0;
  white-space: nowrap;
  position: absolute;
  top: 16px;
  right: 16px;
}
.wlt__withdraw-btn:hover:not(:disabled) { background: #178A33; }
.wlt__withdraw-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.wlt__pending-alert {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 10px;
  font-size: 14px;
  color: #92400e;
  margin-bottom: 24px;
}

.wlt__grid {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 24px;
  margin-top: 12px;
}

.wlt__section {
  background: #fff;
  border: 1px solid #E0E0E0;
  border-radius: 12px;
  padding: 20px;
}
.wlt__section-title { font-size: 16px; font-weight: 600; color: #0F0F0F; margin-bottom: 16px; }

.wlt__entries { display: flex; flex-direction: column; }
.wlt__entry {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f2f2f2;
}
.wlt__entry:last-child { border-bottom: none; }

.wlt__entry-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.wlt__entry-icon.credit { background: rgba(29,165,63,.1); color: #1DA53F; }
.wlt__entry-icon.debit { background: #fef2f2; color: #dc2626; }

.wlt__entry-info { flex: 1; min-width: 0; }
.wlt__entry-label {
  display: block;
  font-size: 14px;
  color: #0F0F0F;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.wlt__entry-date { font-size: 12px; color: #606060; }

.wlt__entry-amount { font-weight: 600; font-size: 14px; flex-shrink: 0; }
.wlt__entry-amount.credit { color: #1DA53F; }
.wlt__entry-amount.debit { color: #dc2626; }

.wlt__withdrawals { display: flex; flex-direction: column; gap: 0; }
.wlt__withdrawal {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f2f2f2;
}
.wlt__withdrawal:last-child { border-bottom: none; }
.wlt__withdrawal-amount { font-weight: 600; color: #0F0F0F; display: block; }
.wlt__withdrawal-method { font-size: 13px; color: #606060; display: block; }
.wlt__withdrawal-date { font-size: 12px; color: #606060; }

.wlt__withdrawal-badge {
  padding: 4px 12px;
  border-radius: 14px;
  font-size: 12px;
  font-weight: 500;
  flex-shrink: 0;
}
.wlt__withdrawal-badge.pending { background: #fef3c7; color: #d97706; }
.wlt__withdrawal-badge.completed { background: rgba(29,165,63,.1); color: #1DA53F; }
.wlt__withdrawal-badge.rejected { background: #fef2f2; color: #dc2626; }

.wlt__filters {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
  align-items: center;
}
.wlt__filter-select {
  padding: 6px 12px;
  border: 1px solid #E0E0E0;
  border-radius: 8px;
  font-size: 13px;
  color: #0F0F0F;
  background: #fff;
  cursor: pointer;
}
.wlt__filter-select:focus {
  outline: none;
  border-color: #1DA53F;
}
.wlt__filter-clear {
  background: none;
  border: none;
  color: #dc2626;
  font-size: 12px;
  cursor: pointer;
  font-weight: 500;
}

.wlt__empty { color: #606060; font-size: 14px; padding: 12px 0; }

/* Modal */
.wlt__modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.5);
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
}
.wlt__modal {
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  max-width: 460px;
  width: 90%;
}
.wlt__modal-title { font-size: 20px; font-weight: 700; color: #0F0F0F; margin-bottom: 4px; }
.wlt__modal-sub { font-size: 14px; color: #606060; margin-bottom: 24px; }

.wlt__modal-field { margin-bottom: 18px; }
.wlt__modal-field label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #272727;
  margin-bottom: 8px;
}
.wlt__modal-field input[type="number"],
.wlt__modal-field input[type="tel"],
.wlt__modal-field input[type="password"] {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #E0E0E0;
  border-radius: 8px;
  font-size: 16px;
  color: #0F0F0F;
  box-sizing: border-box;
}
.wlt__modal-field input:focus {
  outline: none;
  border-color: #1DA53F;
  box-shadow: 0 0 0 3px rgba(29,165,63,.12);
}

.wlt__modal-methods { display: flex; gap: 10px; flex-wrap: wrap; }
.wlt__method {
  flex: 1;
  min-width: 100px;
  padding: 10px 14px;
  border: 1px solid #E0E0E0;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  transition: border-color .15s;
}
.wlt__method.active { border-color: #1DA53F; background: rgba(29,165,63,.04); }
.wlt__method input { display: none; }

.wlt__modal-actions { display: flex; gap: 12px; justify-content: flex-end; margin-top: 8px; }
.wlt__modal-btn {
  padding: 10px 24px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
}
.wlt__modal-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.wlt__modal-btn.cancel { background: #f2f2f2; color: #272727; }
.wlt__modal-btn.cancel:hover:not(:disabled) { background: #e5e5e5; }
.wlt__modal-btn.confirm { background: #1DA53F; color: #fff; }
.wlt__modal-btn.confirm:hover:not(:disabled) { background: #178A33; }

@media (max-width: 768px) {
  .wlt__kpi-row { grid-template-columns: 1fr; }
  .wlt__kpi-value { font-size: 20px; }
  .wlt__withdraw-btn { position: static; margin-top: 12px; }
  .wlt__kpi--balance { flex-wrap: wrap; }
  .wlt__grid { grid-template-columns: 1fr; }
  .wlt__modal-methods { flex-direction: column; }
}
</style>
