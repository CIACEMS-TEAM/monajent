<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAgentStore, type ListingListItem } from '@/Stores/agent'
import ListingFormDialog from './ListingFormDialog.vue'
import ListingDetailDialog from './ListingDetailDialog.vue'
import ShareDialog from './ShareDialog.vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import TabMenu from 'primevue/tabmenu'
import InputText from 'primevue/inputtext'
import { useToast } from 'vue-toastification'

const agent = useAgentStore()
const toast = useToast()
const route = useRoute()

const filter = ref('ALL')
const search = ref((route.query.q as string) || '')
const deleteTarget = ref<ListingListItem | null>(null)
const deleting = ref(false)
const renewing = ref<number | null>(null)
const toggling = ref<number | null>(null)
const selectedIds = ref<number[]>([])
const bulkLoading = ref(false)

const formVisible = ref(false)
const formListingId = ref<number | null>(null)
const detailVisible = ref(false)
const detailListingId = ref<number | null>(null)
const shareVisible = ref(false)
const shareListingId = ref<number | null>(null)
const showKycModal = ref(false)

onMounted(async () => {
  try { await agent.fetchListings() } catch (_) {}
})

watch(() => route.query.q, (q) => {
  search.value = (q as string) || ''
})

watch(() => route.query.action, (action) => {
  if (action === 'new') openNew()
}, { immediate: true })

const filtered = computed(() => {
  let list = agent.listings
  if (filter.value !== 'ALL') {
    list = list.filter(l => l.status === filter.value)
  }
  if (search.value.trim()) {
    const q = search.value.toLowerCase().trim()
    list = list.filter(l =>
      l.title.toLowerCase().includes(q) ||
      l.city.toLowerCase().includes(q) ||
      (l.neighborhood || '').toLowerCase().includes(q),
    )
  }
  return list
})

const tabs = computed(() => [
  { label: `Toutes (${agent.listings.length})`, command: () => { filter.value = 'ALL' } },
  { label: `Actives (${agent.publishedCount})`, command: () => { filter.value = 'ACTIF' } },
  { label: `Inactives (${agent.inactifCount})`, command: () => { filter.value = 'INACTIF' } },
  { label: `Expirées (${agent.expiredCount})`, command: () => { filter.value = 'EXPIRED' } },
])

const activeTabIndex = computed(() => {
  const map: Record<string, number> = { ALL: 0, ACTIF: 1, INACTIF: 2, EXPIRED: 3 }
  return map[filter.value] ?? 0
})

function formatPrice(val: string | number): string {
  return Number(val).toLocaleString('fr-FR') + ' F CFA'
}

function statusSeverity(s: string): "success" | "info" | "warn" | "danger" | "secondary" | undefined {
  const map: Record<string, "success" | "warn" | "danger" | "secondary"> = {
    ACTIF: 'success', INACTIF: 'secondary', EXPIRED: 'danger', SUSPENDED: 'warn',
  }
  return map[s]
}

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    ACTIF: 'Active', INACTIF: 'Inactive', EXPIRED: 'Expirée', SUSPENDED: 'Suspendue',
  }
  return map[s] || s
}

function typeLabel(t: string): string {
  return t === 'LOCATION' ? 'Location' : 'Vente'
}

function coverUrl(item: ListingListItem): string | null {
  if (!item.cover_image) return null
  if (item.cover_image.startsWith('http')) return item.cover_image
  const base = (import.meta as any).env?.VITE_API_BASE_URL || window.location.origin
  return `${base}${item.cover_image}`
}

function expirySeverity(days: number): "success" | "warn" | "danger" {
  if (days <= 0) return 'danger'
  if (days <= 2) return 'warn'
  return 'success'
}

function expiryLabel(item: ListingListItem): string {
  if (!item.expires_at) return '—'
  if (item.days_remaining <= 0) return 'Expirée'
  if (item.days_remaining === 1) return '1 jour'
  return `${item.days_remaining} jours`
}

async function doPublish(item: ListingListItem) {
  if (!agent.isVerified) {
    showKycModal.value = true
    return
  }
  toggling.value = item.id
  try {
    await agent.toggleListingStatus(item.id)
    toast.success('Annonce publiée')
  } catch (err: any) {
    if (err?.response?.status === 403) showKycModal.value = true
    else toast.error('Erreur lors de la publication')
  }
  toggling.value = null
}

async function doUnpublish(item: ListingListItem) {
  toggling.value = item.id
  try {
    await agent.toggleListingStatus(item.id)
    toast.success('Annonce retirée')
  } catch {
    toast.error('Erreur lors du retrait')
  }
  toggling.value = null
}

async function doDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await agent.deleteListing(deleteTarget.value.id)
    toast.success('Annonce supprimée')
  } catch (_) {
    toast.error('Erreur lors de la suppression')
  }
  deleting.value = false
  deleteTarget.value = null
}

async function doRenew(id: number) {
  renewing.value = id
  try {
    const res = await agent.renewListing(id)
    toast.success(res.detail || 'Annonce renouvelée')
  } catch (e: any) {
    toast.error(e?.response?.data?.detail || 'Erreur lors du renouvellement')
  }
  renewing.value = null
}

function openNew() {
  formListingId.value = null
  formVisible.value = true
}

function openEdit(id: number) {
  formListingId.value = id
  formVisible.value = true
}

function openDetail(id: number) {
  detailListingId.value = id
  detailVisible.value = true
}

function onDetailEdit(id: number) {
  openEdit(id)
}

function openShare(id: number) {
  shareListingId.value = id
  shareVisible.value = true
}

async function onFormSaved() {
  try { await agent.fetchListings() } catch (_) {}
}

function toggleSelect(id: number) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

function toggleSelectAll() {
  if (selectedIds.value.length === filtered.value.length) {
    selectedIds.value = []
  } else {
    selectedIds.value = filtered.value.map(l => l.id)
  }
}

async function doBulk(action: 'activate' | 'deactivate' | 'delete') {
  if (!selectedIds.value.length) return
  if (action === 'activate' && !agent.isVerified) {
    showKycModal.value = true
    return
  }
  bulkLoading.value = true
  try {
    const result = await agent.bulkAction(selectedIds.value, action)
    toast.success(result.detail)
    selectedIds.value = []
  } catch (e: any) {
    if (e?.response?.status === 403) showKycModal.value = true
    else toast.error(e?.response?.data?.detail || 'Erreur lors de l\'action en masse')
  } finally {
    bulkLoading.value = false
  }
}
</script>

<template>
  <div class="lstg">
    <!-- KYC Banner -->
    <div v-if="!agent.isVerified" class="lstg__kyc-banner">
      <div class="lstg__kyc-icon">
        <svg viewBox="0 0 24 24" width="24" height="24"><path fill="#d97706" d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>
      </div>
      <div class="lstg__kyc-text">
        <strong>Vérification KYC requise pour publier</strong>
        <p>Vous pouvez créer vos annonces, mais elles resteront en brouillon tant que votre identité n'est pas vérifiée.</p>
      </div>
      <router-link to="/agent/settings" class="lstg__kyc-btn">
        Vérifier mon identité
      </router-link>
    </div>

    <div class="lstg__header">
      <h1 class="lstg__title">Gestion des Annonces</h1>
      <div class="lstg__header-right">
        <span class="lstg__search p-input-icon-left">
          <i class="pi pi-search" />
          <InputText v-model="search" placeholder="Rechercher une annonce..." class="lstg__search-input" />
        </span>
        <Button
          label="Nouvelle annonce"
          icon="pi pi-plus"
          @click="openNew"
          class="lstg__new-btn"
        />
      </div>
    </div>

    <TabMenu :model="tabs" :activeIndex="activeTabIndex" class="lstg__tabs" />

    <!-- Bulk actions bar -->
    <div v-if="selectedIds.length > 0" class="lstg__bulk-bar">
      <span class="lstg__bulk-count">{{ selectedIds.length }} sélectionnée(s)</span>
      <button class="lstg__bulk-btn lstg__bulk-btn--activate" @click="doBulk('activate')" :disabled="bulkLoading">Activer</button>
      <button class="lstg__bulk-btn lstg__bulk-btn--deactivate" @click="doBulk('deactivate')" :disabled="bulkLoading">Désactiver</button>
      <button class="lstg__bulk-btn lstg__bulk-btn--delete" @click="doBulk('delete')" :disabled="bulkLoading">Supprimer</button>
      <button class="lstg__bulk-btn lstg__bulk-btn--cancel" @click="selectedIds = []">Annuler</button>
    </div>

    <div v-if="agent.listingsLoading" class="lstg__loading">
      <i class="pi pi-spin pi-spinner" style="font-size: 1.5rem"></i>
      <span>Chargement des annonces...</span>
    </div>

    <DataTable
      v-else
      :value="filtered"
      :paginator="filtered.length > 10"
      :rows="10"
      :rowsPerPageOptions="[10, 25, 50]"
      stripedRows
      removableSort
      dataKey="id"
      emptyMessage="Aucune annonce dans cette catégorie"
      class="lstg__datatable"
      :pt="{ root: { style: 'border: none' } }"
    >
      <Column header="" style="width: 50px">
        <template #header>
          <input type="checkbox" :checked="selectedIds.length === filtered.length && filtered.length > 0" @change="toggleSelectAll" class="lstg__checkbox" />
        </template>
        <template #body="{ data }">
          <input type="checkbox" :checked="selectedIds.includes(data.id)" @change="toggleSelect(data.id)" class="lstg__checkbox" />
        </template>
      </Column>
      <Column header="Annonce" :sortable="false" style="min-width: 260px">
        <template #body="{ data }">
          <div class="lstg__cell-title" @click="openDetail(data.id)" style="cursor: pointer">
            <div class="lstg__thumb">
              <img v-if="coverUrl(data)" :src="coverUrl(data)!" alt="" />
              <svg v-else viewBox="0 0 24 24" width="20" height="20"><path fill="#aaa" d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8 12.5v-9l6 4.5-6 4.5z"/></svg>
            </div>
            <div class="lstg__cell-text">
              <span class="lstg__cell-name lstg__cell-name--link">{{ data.title }}</span>
              <span class="lstg__cell-sub">{{ data.city }}<template v-if="data.neighborhood"> — {{ data.neighborhood }}</template></span>
            </div>
          </div>
        </template>
      </Column>

      <Column header="Type" field="listing_type" :sortable="true" style="width: 100px">
        <template #body="{ data }">
          <Tag :value="typeLabel(data.listing_type)" :severity="data.listing_type === 'LOCATION' ? 'info' : 'warn'" />
        </template>
      </Column>

      <Column header="Statut" field="status" :sortable="true" style="width: 100px">
        <template #body="{ data }">
          <Tag :value="statusLabel(data.status)" :severity="statusSeverity(data.status)" />
        </template>
      </Column>

      <Column header="Prix" field="price" :sortable="true" style="width: 150px">
        <template #body="{ data }">
          {{ formatPrice(data.price) }}
        </template>
      </Column>

      <Column header="Expire" field="days_remaining" :sortable="true" style="width: 110px">
        <template #body="{ data }">
          <Tag
            v-if="data.expires_at"
            :value="expiryLabel(data)"
            :severity="expirySeverity(data.days_remaining)"
            :icon="data.days_remaining <= 2 ? 'pi pi-clock' : ''"
          />
          <span v-else class="lstg__no-expiry">—</span>
        </template>
      </Column>

      <Column header="Vidéos" field="videos_count" :sortable="true" style="width: 70px; text-align: center">
        <template #body="{ data }">
          <span class="lstg__video-count">
            <i class="pi pi-video"></i> {{ data.videos_count }}
          </span>
        </template>
      </Column>

      <Column header="Vues" field="views_count" :sortable="true" style="width: 70px; text-align: center">
        <template #body="{ data }">
          {{ data.views_count }}
        </template>
      </Column>

      <Column header="Date" field="created_at" :sortable="true" style="width: 100px">
        <template #body="{ data }">
          {{ new Date(data.created_at).toLocaleDateString('fr-FR') }}
        </template>
      </Column>

      <Column header="Actions" style="width: 240px">
        <template #body="{ data }">
          <div class="lstg__actions">
            <Button v-if="data.status === 'INACTIF'" label="Publier" icon="pi pi-send" severity="success" size="small" :loading="toggling === data.id" @click="doPublish(data)" class="lstg__publish-btn" />
            <Button v-if="data.status === 'ACTIF'" label="Retirer" icon="pi pi-eye-slash" severity="secondary" size="small" outlined :loading="toggling === data.id" @click="doUnpublish(data)" class="lstg__unpublish-btn" />
            <Button icon="pi pi-eye" severity="info" text rounded size="small" title="Voir" @click="openDetail(data.id)" />
            <Button icon="pi pi-share-alt" severity="success" text rounded size="small" title="Partager" @click="openShare(data.id)" />
            <Button icon="pi pi-pencil" severity="secondary" text rounded size="small" title="Modifier" @click="openEdit(data.id)" />
            <Button icon="pi pi-trash" severity="danger" text rounded size="small" title="Supprimer" @click="deleteTarget = data" />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Delete Dialog -->
    <Dialog
      :visible="!!deleteTarget"
      @update:visible="(v: boolean) => { if (!v) deleteTarget = null }"
      header="Supprimer cette annonce ?"
      :modal="true"
      :closable="true"
      :style="{ width: '420px' }"
    >
      <p style="margin: 0; color: #606060">
        L'annonce <strong>{{ deleteTarget?.title }}</strong> sera définitivement supprimée. Cette action est irréversible.
      </p>
      <template #footer>
        <Button label="Annuler" severity="secondary" text @click="deleteTarget = null" />
        <Button label="Supprimer" severity="danger" :loading="deleting" @click="doDelete" />
      </template>
    </Dialog>

    <!-- Create / Edit Dialog -->
    <ListingFormDialog
      v-model:visible="formVisible"
      v-model:listingId="formListingId"
      @saved="onFormSaved"
    />

    <ListingDetailDialog
      v-model:visible="detailVisible"
      :listingId="detailListingId"
      @edit="onDetailEdit"
    />

    <ShareDialog
      v-model:visible="shareVisible"
      :listingId="shareListingId"
    />

    <!-- KYC Required Modal -->
    <Dialog
      v-model:visible="showKycModal"
      header="Vérification d'identité requise"
      :modal="true"
      :closable="true"
      :style="{ width: '440px' }"
    >
      <div class="lstg__kyc-modal">
        <svg viewBox="0 0 24 24" width="48" height="48"><path fill="#d97706" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
        <p class="lstg__kyc-modal-text">
          Vous devez vérifier votre identité avant de pouvoir publier ou activer une annonce.
          Rendez-vous dans vos paramètres pour soumettre vos documents KYC.
        </p>
        <div class="lstg__kyc-modal-actions">
          <button class="lstg__kyc-modal-cancel" @click="showKycModal = false">Plus tard</button>
          <router-link to="/agent/settings" class="lstg__kyc-modal-go" @click="showKycModal = false">
            Vérifier mon identité
          </router-link>
        </div>
      </div>
    </Dialog>
  </div>
</template>

<style scoped>
.lstg__kyc-banner {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border: 1px solid #fbbf24;
  border-radius: 12px;
  margin-bottom: 1.5rem;
}
.lstg__kyc-icon { flex-shrink: 0; }
.lstg__kyc-text { flex: 1; }
.lstg__kyc-text strong { color: #92400e; font-size: 0.95rem; }
.lstg__kyc-text p { margin: 0.25rem 0 0; color: #a16207; font-size: 0.85rem; }
.lstg__kyc-btn {
  flex-shrink: 0;
  padding: 0.5rem 1.25rem;
  background: #d97706;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.85rem;
  text-decoration: none;
  cursor: pointer;
  transition: background 0.2s;
}
.lstg__kyc-btn:hover { background: #b45309; }

@media (max-width: 640px) {
  .lstg__kyc-banner { flex-direction: column; text-align: center; }
}

.lstg__bulk-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 10px;
  margin-bottom: 12px;
}
.lstg__bulk-count { font-size: 13px; font-weight: 600; color: #166534; margin-right: 8px; }
.lstg__bulk-btn {
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background .12s;
}
.lstg__bulk-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.lstg__bulk-btn--activate { background: #dcfce7; color: #166534; border-color: #bbf7d0; }
.lstg__bulk-btn--activate:hover:not(:disabled) { background: #bbf7d0; }
.lstg__bulk-btn--deactivate { background: #f3f4f6; color: #374151; border-color: #d1d5db; }
.lstg__bulk-btn--deactivate:hover:not(:disabled) { background: #e5e7eb; }
.lstg__bulk-btn--delete { background: #fef2f2; color: #dc2626; border-color: #fecaca; }
.lstg__bulk-btn--delete:hover:not(:disabled) { background: #fee2e2; }
.lstg__bulk-btn--cancel { background: none; color: #606060; }
.lstg__checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #1DA53F;
}

.lstg {
  width: 100%;
}

.lstg__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}
.lstg__title {
  font-size: 24px;
  font-weight: 700;
  color: #0F0F0F;
}
.lstg__header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.lstg__search {
  position: relative;
}
.lstg__search > i {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #aaa;
  font-size: 14px;
  z-index: 1;
  pointer-events: none;
}
.lstg__search-input {
  padding-left: 36px;
  width: 260px;
  height: 38px;
  border-radius: 20px;
  font-size: 14px;
}
.lstg__new-btn {
  background: #1DA53F !important;
  border-color: #1DA53F !important;
}
.lstg__new-btn:hover {
  background: #178A33 !important;
  border-color: #178A33 !important;
}

.lstg__tabs { margin-bottom: 0; }

.lstg__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 20px;
  color: #606060;
  font-size: 15px;
}

.lstg__datatable { font-size: 14px; }

.lstg__cell-title {
  display: flex;
  align-items: center;
  gap: 12px;
}
.lstg__thumb {
  width: 120px;
  height: 68px;
  background: #f2f2f2;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}
.lstg__thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.lstg__cell-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.lstg__cell-name {
  font-weight: 500;
  color: #0F0F0F;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.lstg__cell-name--link:hover {
  color: #1DA53F;
  text-decoration: underline;
}
.lstg__cell-sub {
  font-size: 12px;
  color: #606060;
}


.lstg__no-expiry {
  color: #aaa;
}

.lstg__video-count {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: #606060;
}

.lstg__actions {
  display: flex;
  align-items: center;
  gap: 4px;
}
.lstg__publish-btn { font-size: 12px !important; padding: 4px 10px !important; }
.lstg__unpublish-btn { font-size: 12px !important; padding: 4px 10px !important; }

.lstg__kyc-modal {
  display: flex; flex-direction: column; align-items: center; text-align: center; gap: 16px; padding: 8px 0;
}
.lstg__kyc-modal-text { font-size: 15px; color: #272727; line-height: 1.6; margin: 0; }
.lstg__kyc-modal-actions { display: flex; gap: 12px; margin-top: 8px; }
.lstg__kyc-modal-cancel {
  padding: 10px 20px; border: 1px solid #E0E0E0; border-radius: 20px; background: #fff;
  font-size: 14px; color: #606060; cursor: pointer; transition: background .15s;
}
.lstg__kyc-modal-cancel:hover { background: #f2f2f2; }
.lstg__kyc-modal-go {
  padding: 10px 24px; border: none; border-radius: 20px; background: #1DA53F;
  color: #fff; font-size: 14px; font-weight: 600; text-decoration: none; transition: background .15s;
}
.lstg__kyc-modal-go:hover { background: #178A33; }

@media (max-width: 768px) {
  .lstg__thumb { width: 80px; height: 48px; }
  .lstg__header { flex-direction: column; align-items: flex-start; }
  .lstg__header-right { flex-direction: column; width: 100%; }
  .lstg__search-input { width: 100%; }
}
</style>
