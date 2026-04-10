<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAgentStore, type Listing } from '@/Stores/agent'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { useToast } from 'vue-toastification'

const props = defineProps<{
  visible: boolean
  listingId: number | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
}>()

const agent = useAgentStore()
const toast = useToast()
const loading = ref(false)
const listing = ref<Listing | null>(null)
const selectedVideoKey = ref<string | null>(null)

const origin = typeof window !== 'undefined' ? window.location.origin : ''
const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || origin
const ogBase = `${origin}/share`

function mediaUrl(url: string | null): string | null {
  if (!url) return null
  if (url.startsWith('http')) return url
  return `${apiBase}${url}`
}

watch(() => props.visible, async (open) => {
  if (!open || !props.listingId) { listing.value = null; return }
  loading.value = true
  try {
    listing.value = await agent.fetchListing(props.listingId)
  } catch (_) {
    listing.value = null
  }
  loading.value = false
  selectedVideoKey.value = null
})

const listingUrl = computed(() => {
  if (!listing.value) return ''
  return `${origin}/home/annonce/${listing.value.slug || listing.value.id}`
})

const shareOgUrl = computed(() => {
  if (!listing.value) return ''
  return `${ogBase}/${listing.value.slug || listing.value.id}/`
})

const shareUrl = computed(() => {
  if (!listing.value) return ''
  if (selectedVideoKey.value) {
    return `${origin}/home/annonce/${listing.value.slug || listing.value.id}?video=${selectedVideoKey.value}`
  }
  return listingUrl.value
})

const shareText = computed(() => {
  if (!listing.value) return ''
  const price = Number(listing.value.price).toLocaleString('fr-FR') + ' F CFA'
  const type = listing.value.listing_type === 'LOCATION' ? 'Location' : 'Vente'
  let text = `${listing.value.title}\n${type} — ${price}\n${listing.value.city}`
  if (listing.value.neighborhood) text += `, ${listing.value.neighborhood}`
  text += `\n\n*VISITE GRATUITE!*\n\n${shareUrl.value}`
  return text
})

function close() { emit('update:visible', false) }

async function copyLink() {
  try {
    await navigator.clipboard.writeText(shareUrl.value)
    toast.success('Lien copié !')
  } catch (_) {
    toast.error('Impossible de copier')
  }
}

function shareWhatsApp() {
  const text = shareText.value.replace(shareUrl.value, shareOgUrl.value)
  window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank')
}

function shareFacebook() {
  window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareOgUrl.value)}`, '_blank')
}

function shareTelegram() {
  window.open(`https://t.me/share/url?url=${encodeURIComponent(shareOgUrl.value)}&text=${encodeURIComponent(shareText.value)}`, '_blank')
}

function selectVideo(key: string | null) {
  selectedVideoKey.value = selectedVideoKey.value === key ? null : key
}
</script>

<template>
  <Dialog
    :visible="props.visible"
    @update:visible="(v: boolean) => emit('update:visible', v)"
    header="Partager l'annonce"
    :modal="true"
    :closable="true"
    :draggable="false"
    :style="{ width: '520px' }"
  >
    <div v-if="loading" class="sd__loading">
      <i class="pi pi-spin pi-spinner" style="font-size: 1.5rem"></i>
    </div>

    <div v-else-if="listing" class="sd">
      <!-- Listing preview -->
      <div class="sd__preview">
        <div class="sd__preview-thumb" v-if="listing.images.length">
          <img :src="mediaUrl(listing.images[0].image)!" alt="" />
        </div>
        <div class="sd__preview-info">
          <span class="sd__preview-title">{{ listing.title }}</span>
          <span class="sd__preview-sub">{{ listing.city }} — {{ Number(listing.price).toLocaleString('fr-FR') }} F CFA</span>
        </div>
      </div>

      <!-- Video selector -->
      <div v-if="listing.videos.length" class="sd__video-select">
        <p class="sd__label">Partager une vidéo spécifique (optionnel) :</p>
        <div class="sd__video-chips">
          <button
            v-for="vid in listing.videos"
            :key="vid.id"
            class="sd__chip"
            :class="{ 'sd__chip--active': selectedVideoKey === vid.access_key }"
            @click="selectVideo(vid.access_key)"
          >
            <i class="pi pi-video"></i>
            Vidéo {{ listing.videos.indexOf(vid) + 1 }}
          </button>
        </div>
      </div>

      <!-- Link -->
      <div class="sd__link-box">
        <p class="sd__label">Lien à partager :</p>
        <div class="sd__link-row">
          <InputText :modelValue="shareUrl" readonly class="sd__link-input" />
          <Button icon="pi pi-copy" severity="secondary" @click="copyLink" title="Copier" />
        </div>
      </div>

      <!-- Share buttons -->
      <div class="sd__actions">
        <Button
          icon="pi pi-whatsapp"
          label="WhatsApp"
          severity="success"
          class="sd__btn sd__btn--wa"
          @click="shareWhatsApp"
        />
        <Button
          icon="pi pi-facebook"
          label="Facebook"
          severity="info"
          class="sd__btn"
          @click="shareFacebook"
        />
        <Button
          icon="pi pi-send"
          label="Telegram"
          severity="secondary"
          class="sd__btn"
          @click="shareTelegram"
        />
      </div>

      <p class="sd__hint">
        <i class="pi pi-info-circle"></i>
        Plus vous partagez, plus vos vidéos sont visionnées et plus vous gagnez de revenus !
      </p>
      <p class="sd__hint sd__hint--wa">
        <i class="pi pi-whatsapp"></i>
        Pour que l'aperçu avec image s'affiche sur WhatsApp, envoyez à <strong>un seul contact à la fois</strong>.
      </p>
    </div>

    <template #footer>
      <Button label="Fermer" severity="secondary" text @click="close" />
    </template>
  </Dialog>
</template>

<style scoped>
.sd__loading {
  display: flex;
  justify-content: center;
  padding: 40px;
  color: #606060;
}

.sd__preview {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px;
  background: #fafafa;
  border-radius: 10px;
  margin-bottom: 16px;
}
.sd__preview-thumb {
  width: 80px;
  height: 50px;
  border-radius: 6px;
  overflow: hidden;
  background: #eee;
  flex-shrink: 0;
}
.sd__preview-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.sd__preview-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.sd__preview-title {
  font-weight: 600;
  font-size: 14px;
  color: #0F0F0F;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sd__preview-sub {
  font-size: 12px;
  color: #606060;
}

.sd__label {
  font-size: 13px;
  font-weight: 500;
  color: #272727;
  margin: 0 0 8px;
}

.sd__video-select {
  margin-bottom: 16px;
}
.sd__video-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.sd__chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid #ddd;
  background: #fff;
  font-size: 13px;
  color: #606060;
  cursor: pointer;
  transition: all 0.15s;
}
.sd__chip:hover {
  border-color: #1DA53F;
  color: #1DA53F;
}
.sd__chip--active {
  border-color: #1DA53F;
  background: #e8f5e9;
  color: #1DA53F;
  font-weight: 600;
}

.sd__link-box {
  margin-bottom: 16px;
}
.sd__link-row {
  display: flex;
  gap: 8px;
}
.sd__link-input {
  flex: 1;
  font-size: 13px;
}

.sd__actions {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.sd__btn {
  flex: 1;
}
.sd__btn--wa {
  background: #25D366 !important;
  border-color: #25D366 !important;
}
.sd__btn--wa:hover {
  background: #1ebe57 !important;
  border-color: #1ebe57 !important;
}

.sd__hint {
  font-size: 12px;
  color: #999;
  margin: 0;
  padding: 10px 12px;
  background: #f8f9fa;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.sd__hint + .sd__hint { margin-top: 6px; }
.sd__hint--wa {
  background: #f0fdf4;
  color: #15803d;
}
.sd__hint--wa strong { font-weight: 600; }
</style>
