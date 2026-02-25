<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useAgentStore, type ListingCreatePayload } from '@/Stores/agent'
import http, { mediaUrl } from '@/services/http'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import InputNumber from 'primevue/inputnumber'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Message from 'primevue/message'
import Dialog from 'primevue/dialog'
import ProgressBar from 'primevue/progressbar'
import { useToast } from 'vue-toastification'

const props = defineProps<{
  visible: boolean
  listingId: number | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'update:listingId', val: number | null): void
  (e: 'saved'): void
}>()

const agent = useAgentStore()
const toast = useToast()

const isEdit = computed(() => props.listingId !== null)
const loading = ref(false)
const saving = ref(false)
const savingStep = ref('')
const serverError = ref('')

const form = reactive<ListingCreatePayload>({
  title: '',
  description: '',
  listing_type: 'LOCATION',
  status: agent.isVerified ? 'ACTIF' : 'INACTIF',
  city: '',
  neighborhood: '',
  address: '',
  latitude: null,
  longitude: null,
  price: 0,
  rooms: null,
  bedrooms: null,
  bathrooms: null,
  surface_m2: null,
  furnishing: '',
  amenities: [],
})

// Fichiers en attente (mode création)
const pendingImages = ref<File[]>([])
const pendingVideo = ref<File | null>(null)

const amenityInput = ref('')
const typeOptions = [
  { label: 'Location', value: 'LOCATION' },
  { label: 'Vente', value: 'VENTE' },
]
const statusOptions = computed(() => {
  if (agent.isVerified) {
    return [
      { label: 'Active (publiée)', value: 'ACTIF' },
      { label: 'Inactive (brouillon)', value: 'INACTIF' },
    ]
  }
  return [
    { label: 'Brouillon (KYC requis pour publier)', value: 'INACTIF' },
  ]
})
const furnishingOptions = [
  { label: 'Non précisé', value: '' },
  { label: 'Meublé', value: 'FURNISHED' },
  { label: 'Non meublé', value: 'UNFURNISHED' },
  { label: 'Semi-meublé', value: 'SEMI_FURNISHED' },
]

function resetForm() {
  form.title = ''
  form.description = ''
  form.listing_type = 'LOCATION'
  form.status = agent.isVerified ? 'ACTIF' : 'INACTIF'
  form.city = ''
  form.neighborhood = ''
  form.address = ''
  form.latitude = null
  form.longitude = null
  form.price = 0
  form.rooms = null
  form.bedrooms = null
  form.bathrooms = null
  form.surface_m2 = null
  form.furnishing = ''
  form.amenities = []
  amenityInput.value = ''
  serverError.value = ''
  savingStep.value = ''
  pendingImages.value = []
  pendingVideo.value = null
  agent.currentListing = null
}

watch(() => props.visible, async (open) => {
  if (!open) return
  if (isEdit.value && props.listingId) {
    loading.value = true
    try {
      const data = await agent.fetchListing(props.listingId)
      form.title = data.title
      form.description = data.description || ''
      form.listing_type = data.listing_type
      form.status = (data.status === 'EXPIRED' ? 'ACTIF' : data.status) as 'ACTIF' | 'INACTIF'
      form.city = data.city
      form.neighborhood = data.neighborhood || ''
      form.address = data.address || ''
      form.latitude = data.latitude ? Number(data.latitude) : null
      form.longitude = data.longitude ? Number(data.longitude) : null
      form.price = Number(data.price)
      form.rooms = data.rooms
      form.bedrooms = data.bedrooms
      form.bathrooms = data.bathrooms
      form.surface_m2 = data.surface_m2 ? Number(data.surface_m2) : null
      form.furnishing = data.furnishing || ''
      form.amenities = data.amenities || []
    } catch (_) {
      toast.error('Impossible de charger l\'annonce')
      close()
    }
    loading.value = false
  } else {
    resetForm()
  }
})

function close() {
  emit('update:visible', false)
}

function addAmenity() {
  const val = amenityInput.value.trim()
  if (val && !form.amenities!.includes(val)) {
    form.amenities!.push(val)
  }
  amenityInput.value = ''
}

function removeAmenity(idx: number) {
  form.amenities!.splice(idx, 1)
}

// ─── Fichiers locaux (mode création) ────────────────────────

function onSelectImages(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files) return
  pendingImages.value.push(...Array.from(input.files))
  input.value = ''
}

function removePendingImage(idx: number) {
  pendingImages.value.splice(idx, 1)
}

function onSelectVideo(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  pendingVideo.value = input.files[0]
  input.value = ''
}

function removePendingVideo() {
  pendingVideo.value = null
}

function imagePreviews(files: File[]): string[] {
  return files.map(f => URL.createObjectURL(f))
}

// ─── Upload direct (mode édition) ───────────────────────────

async function onEditImageUpload(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files || !props.listingId) return
  for (const file of Array.from(input.files)) {
    try {
      await agent.uploadListingImage(props.listingId, file)
    } catch (_) {
      toast.error(`Erreur upload : ${file.name}`)
    }
  }
  input.value = ''
  toast.success('Image(s) ajoutée(s)')
}

const dragIdx = ref<number | null>(null)

async function removeImage(imageId: number) {
  if (!props.listingId) return
  try {
    await agent.deleteListingImage(props.listingId, imageId)
  } catch (_) {
    toast.error('Erreur suppression image')
  }
}

function onDragStart(idx: number) { dragIdx.value = idx }
function onDragOver(e: DragEvent) { e.preventDefault() }

async function onDropImage(targetIdx: number) {
  if (dragIdx.value === null || dragIdx.value === targetIdx || !agent.currentListing) return
  const images = [...agent.currentListing.images]
  const [moved] = images.splice(dragIdx.value, 1)
  images.splice(targetIdx, 0, moved)
  agent.currentListing.images = images
  dragIdx.value = null

  if (props.listingId) {
    try {
      await http.post(`/api/agent/listings/${props.listingId}/images/reorder/`, {
        order: images.map(img => img.id),
      })
    } catch (_) {
      toast.error('Erreur lors du réordonnancement')
    }
  }
}

async function onEditVideoUpload(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length || !props.listingId) return
  const file = input.files[0]
  try {
    await agent.uploadListingVideo(props.listingId, file)
    toast.success('Vidéo ajoutée')
  } catch (err: any) {
    const msg = err?.response?.data?.file
    toast.error(typeof msg === 'string' ? msg : Array.isArray(msg) ? msg.join(', ') : `Erreur upload vidéo`)
  }
  input.value = ''
}

async function removeVideo(videoId: number) {
  if (!props.listingId) return
  try {
    await agent.deleteListingVideo(props.listingId, videoId)
  } catch (_) {
    toast.error('Erreur suppression vidéo')
  }
}

// mediaUrl imported from @/services/http

const savingAs = ref<'draft' | 'publish' | ''>('')

function submitDraft() { doSubmit('INACTIF') }
function submitPublish() { doSubmit('ACTIF') }

async function doSubmit(targetStatus: string) {
  serverError.value = ''
  if (!form.title || !form.city || !form.price) {
    serverError.value = 'Veuillez remplir les champs obligatoires (titre, ville, prix)'
    return
  }

  savingAs.value = targetStatus === 'ACTIF' ? 'publish' : 'draft'
  saving.value = true

  const payload = { ...form, status: targetStatus }

  try {
    if (isEdit.value && props.listingId) {
      savingStep.value = 'Mise à jour...'
      await agent.updateListing(props.listingId, payload)
      toast.success(targetStatus === 'ACTIF' ? 'Annonce publiée' : 'Brouillon enregistré')
      await agent.fetchListings()
      emit('saved')
      close()
    } else {
      savingStep.value = 'Création de l\'annonce...'
      const created = await agent.createListing(payload)
      const newId = created.id

      if (pendingImages.value.length) {
        savingStep.value = `Upload photos (0/${pendingImages.value.length})...`
        for (let i = 0; i < pendingImages.value.length; i++) {
          savingStep.value = `Upload photos (${i + 1}/${pendingImages.value.length})...`
          try {
            await agent.uploadListingImage(newId, pendingImages.value[i])
          } catch (_) {
            toast.error(`Erreur photo : ${pendingImages.value[i].name}`)
          }
        }
      }

      if (pendingVideo.value) {
        savingStep.value = 'Upload vidéo...'
        try {
          await agent.uploadListingVideo(newId, pendingVideo.value)
        } catch (err: any) {
          const msg = err?.response?.data?.file
          toast.error(typeof msg === 'string' ? msg : 'Erreur upload vidéo')
        }
      }

      toast.success(targetStatus === 'ACTIF' ? 'Annonce publiée avec succès' : 'Brouillon créé avec succès')
      await agent.fetchListings()
      emit('saved')
      close()
    }
  } catch (e: any) {
    const d = e?.response?.data
    if (d?.detail && typeof d.detail === 'string') {
      serverError.value = d.detail
    } else if (typeof d === 'object' && d) {
      serverError.value = Object.entries(d)
        .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
        .join(' | ')
    } else {
      serverError.value = 'Erreur lors de la sauvegarde'
    }
  }

  saving.value = false
  savingAs.value = ''
  savingStep.value = ''
}
</script>

<template>
  <Dialog
    :visible="props.visible"
    @update:visible="(v: boolean) => emit('update:visible', v)"
    :header="isEdit ? 'Modifier l\'annonce' : 'Nouvelle annonce'"
    :modal="true"
    :closable="!saving"
    :draggable="false"
    :maximizable="true"
    class="lf-dialog"
    :pt="{
      root: { class: 'lf-dialog-root' },
      content: { class: 'lf-dialog-content' },
    }"
  >
    <div v-if="loading" class="lf__loading">
      <i class="pi pi-spin pi-spinner" style="font-size: 1.5rem"></i>
      Chargement...
    </div>

    <form v-else class="lf__form" @submit.prevent="submit">
      <!-- Progress pendant la sauvegarde -->
      <div v-if="saving" class="lf__progress">
        <ProgressBar mode="indeterminate" style="height: 4px" />
        <span class="lf__progress-text">{{ savingStep }}</span>
      </div>

      <Message v-if="serverError" severity="error" :closable="true" @close="serverError = ''">
        {{ serverError }}
      </Message>

      <div class="lf__columns">
        <!-- Colonne gauche -->
        <div class="lf__col">
          <section class="lf__section">
            <h2 class="lf__section-title">Informations principales</h2>
            <div class="lf__grid">
              <div class="lf__field lf__field--full">
                <label>Titre <span class="req">*</span></label>
                <InputText v-model="form.title" placeholder="Ex: Appartement 3 pièces Cocody Riviera" fluid :disabled="saving" />
              </div>
              <div class="lf__field lf__field--full">
                <label>Description</label>
                <Textarea v-model="form.description" rows="3" placeholder="Description détaillée du bien..." fluid autoResize :disabled="saving" />
              </div>
              <div class="lf__field">
                <label>Type <span class="req">*</span></label>
                <Select v-model="form.listing_type" :options="typeOptions" optionLabel="label" optionValue="value" fluid :disabled="saving" />
              </div>
            </div>
          </section>

          <section class="lf__section">
            <h2 class="lf__section-title">Localisation</h2>
            <div class="lf__grid">
              <div class="lf__field">
                <label>Ville <span class="req">*</span></label>
                <InputText v-model="form.city" placeholder="Abidjan" fluid :disabled="saving" />
              </div>
              <div class="lf__field">
                <label>Quartier</label>
                <InputText v-model="form.neighborhood" placeholder="Cocody, Plateau..." fluid :disabled="saving" />
              </div>
              <div class="lf__field lf__field--full">
                <label>Adresse</label>
                <InputText v-model="form.address" placeholder="Adresse complète" fluid :disabled="saving" />
              </div>
            </div>
          </section>

          <section class="lf__section">
            <h2 class="lf__section-title">Commodités</h2>
            <div class="lf__amenities-input">
              <InputText v-model="amenityInput" placeholder="Ex: Parking, Gardien, Eau courante..." @keydown.enter.prevent="addAmenity" fluid :disabled="saving" />
              <Button type="button" icon="pi pi-plus" severity="secondary" @click="addAmenity" :disabled="saving" />
            </div>
            <div class="lf__amenities-list" v-if="form.amenities?.length">
              <Tag v-for="(a, i) in form.amenities" :key="i" :value="a" severity="info" rounded>
                {{ a }}
                <button type="button" class="lf__amenity-remove" @click="removeAmenity(i)" :disabled="saving">
                  <i class="pi pi-times" style="font-size: 10px"></i>
                </button>
              </Tag>
            </div>
          </section>
        </div>

        <!-- Colonne droite -->
        <div class="lf__col">
          <section class="lf__section">
            <h2 class="lf__section-title">Caractéristiques</h2>
            <div class="lf__grid">
              <div class="lf__field">
                <label>Prix (F CFA) <span class="req">*</span></label>
                <InputNumber v-model="form.price" :min="0" locale="fr-FR" fluid :disabled="saving" />
              </div>
              <div class="lf__field">
                <label>Surface (m²)</label>
                <InputNumber v-model="form.surface_m2" :min="0" :maxFractionDigits="2" suffix=" m²" fluid :disabled="saving" />
              </div>
              <div class="lf__field">
                <label>Pièces</label>
                <InputNumber v-model="form.rooms" :min="0" :max="50" fluid :disabled="saving" />
              </div>
              <div class="lf__field">
                <label>Chambres</label>
                <InputNumber v-model="form.bedrooms" :min="0" :max="30" fluid :disabled="saving" />
              </div>
              <div class="lf__field">
                <label>Salles de bain</label>
                <InputNumber v-model="form.bathrooms" :min="0" :max="20" fluid :disabled="saving" />
              </div>
              <div class="lf__field">
                <label>Ameublement</label>
                <Select v-model="form.furnishing" :options="furnishingOptions" optionLabel="label" optionValue="value" fluid :disabled="saving" />
              </div>
            </div>
          </section>

          <!-- ═══ MÉDIAS : MODE CRÉATION ═══ -->
          <section v-if="!isEdit" class="lf__section">
            <h2 class="lf__section-title">Photos</h2>
            <div class="lf__media-grid" v-if="pendingImages.length">
              <div v-for="(file, i) in pendingImages" :key="i" class="lf__media-item">
                <img :src="imagePreviews(pendingImages)[i]" alt="" />
                <button type="button" class="lf__media-delete" @click="removePendingImage(i)" :disabled="saving">
                  <i class="pi pi-times"></i>
                </button>
                <span class="lf__media-name">{{ file.name }}</span>
              </div>
            </div>
            <label class="lf__file-btn" :class="{ disabled: saving }">
              <i class="pi pi-plus"></i> Ajouter des photos
              <input type="file" accept="image/*" multiple hidden @change="onSelectImages" :disabled="saving" />
            </label>

            <h2 class="lf__section-title" style="margin-top: 24px">Vidéo</h2>
            <div v-if="pendingVideo" class="lf__pending-video">
              <div class="lf__pending-video-icon">
                <i class="pi pi-video" style="font-size: 20px; color: #1DA53F"></i>
              </div>
              <div class="lf__pending-video-info">
                <span class="lf__pending-video-name">{{ pendingVideo.name }}</span>
                <span class="lf__pending-video-size">{{ (pendingVideo.size / 1024 / 1024).toFixed(1) }} Mo</span>
              </div>
              <button type="button" class="lf__pending-video-remove" @click="removePendingVideo" :disabled="saving">
                <i class="pi pi-times"></i>
              </button>
            </div>
            <label v-else class="lf__file-btn" :class="{ disabled: saving }">
              <i class="pi pi-video"></i> Ajouter une vidéo
              <input type="file" accept="video/*" hidden @change="onSelectVideo" :disabled="saving" />
            </label>
            <p class="lf__media-hint">
              <i class="pi pi-info-circle"></i>
              La vidéo est la pièce maîtresse de votre annonce MonaJent. Les clients paient pour la visionner.
            </p>
          </section>

          <!-- ═══ MÉDIAS : MODE ÉDITION ═══ -->
          <section v-if="isEdit && agent.currentListing" class="lf__section">
            <h2 class="lf__section-title">Photos</h2>
            <p class="lf__drag-hint">Glissez-déposez pour réorganiser l'ordre des photos</p>
            <div class="lf__media-grid" v-if="agent.currentListing.images.length">
              <div
                v-for="(img, idx) in agent.currentListing.images"
                :key="img.id"
                class="lf__media-item"
                :class="{ 'lf__media-item--dragging': dragIdx === idx }"
                draggable="true"
                @dragstart="onDragStart(idx)"
                @dragover="onDragOver"
                @drop="onDropImage(idx)"
              >
                <img :src="mediaUrl(img.image)!" alt="" />
                <span v-if="idx === 0" class="lf__media-cover-badge">Couverture</span>
                <button type="button" class="lf__media-delete" @click="removeImage(img.id)">
                  <i class="pi pi-times"></i>
                </button>
              </div>
            </div>
            <label class="lf__file-btn">
              <i class="pi pi-plus"></i> Ajouter des photos
              <input type="file" accept="image/*" multiple hidden @change="onEditImageUpload" />
            </label>

            <h2 class="lf__section-title" style="margin-top: 24px">Vidéos</h2>
            <div class="lf__media-grid" v-if="agent.currentListing.videos.length">
              <div v-for="vid in agent.currentListing.videos" :key="vid.id" class="lf__media-item lf__media-item--video">
                <div class="lf__video-thumb">
                  <img v-if="vid.thumbnail" :src="mediaUrl(vid.thumbnail)!" alt="" />
                  <div v-else class="lf__video-placeholder">
                    <i class="pi pi-video" style="font-size: 24px; color: #aaa"></i>
                  </div>
                  <span v-if="vid.duration_sec" class="lf__video-dur">{{ Math.floor(vid.duration_sec / 60) }}:{{ String(vid.duration_sec % 60).padStart(2, '0') }}</span>
                </div>
                <div class="lf__video-info">
                  <span>{{ vid.views_count }} vues</span>
                  <span>{{ new Date(vid.created_at).toLocaleDateString('fr-FR') }}</span>
                </div>
                <button type="button" class="lf__media-delete" @click="removeVideo(vid.id)">
                  <i class="pi pi-times"></i>
                </button>
              </div>
            </div>
            <label class="lf__file-btn">
              <i class="pi pi-video"></i> Ajouter une vidéo
              <input type="file" accept="video/*" hidden @change="onEditVideoUpload" />
            </label>
            <p class="lf__media-hint">
              <i class="pi pi-info-circle"></i>
              La vidéo est la pièce maîtresse de votre annonce MonaJent.
            </p>
          </section>
        </div>
      </div>
    </form>

    <template #footer>
      <div class="lf__footer">
        <Button label="Annuler" severity="secondary" text @click="close" :disabled="saving" />
        <div class="lf__footer-right">
          <Button
            label="Enregistrer en brouillon"
            icon="pi pi-save"
            severity="secondary"
            outlined
            :loading="saving && savingAs === 'draft'"
            :disabled="saving"
            @click="submitDraft"
          />
          <span v-if="!agent.isVerified" class="lf__publish-wrap" title="Veuillez vérifier votre identité pour publier">
            <Button
              label="Publier l'annonce"
              icon="pi pi-send"
              severity="success"
              disabled
              class="lf__publish-btn--disabled"
            />
            <span class="lf__publish-badge">KYC requis</span>
          </span>
          <Button
            v-else
            label="Publier l'annonce"
            icon="pi pi-send"
            severity="success"
            :loading="saving && savingAs === 'publish'"
            :disabled="saving"
            @click="submitPublish"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<style>
.lf-dialog-root {
  width: 90vw !important;
  max-width: 1100px !important;
  max-height: 92vh;
}
.lf-dialog-content {
  overflow-y: auto;
  padding: 0 24px 24px !important;
}
@media (max-width: 768px) {
  .lf-dialog-root {
    width: 98vw !important;
    max-height: 96vh;
  }
}
</style>

<style scoped>
.lf__loading {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 60px 20px;
  color: #606060;
  justify-content: center;
}

.lf__progress {
  margin-bottom: 12px;
}
.lf__progress-text {
  display: block;
  text-align: center;
  font-size: 13px;
  color: #1DA53F;
  margin-top: 8px;
  font-weight: 500;
}

.lf__form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.lf__columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: start;
}
.lf__col {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.lf__section {
  background: #fafafa;
  border: 1px solid #eee;
  border-radius: 10px;
  padding: 20px;
}
.lf__section-title {
  font-size: 15px;
  font-weight: 600;
  color: #0F0F0F;
  margin-bottom: 14px;
}

.lf__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.lf__field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.lf__field--full { grid-column: 1 / -1; }
.lf__field label {
  font-size: 13px;
  font-weight: 500;
  color: #272727;
}
.req { color: #dc2626; }

.lf__amenities-input {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}
.lf__amenities-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.lf__amenity-remove {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  margin-left: 6px;
  display: inline-flex;
  align-items: center;
  opacity: 0.6;
}
.lf__amenity-remove:hover { opacity: 1; }

/* File pick button */
.lf__file-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: 1px dashed #ccc;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #555;
  background: #fff;
  transition: border-color .15s, background .15s;
}
.lf__file-btn:hover {
  border-color: #1DA53F;
  background: rgba(29,165,63,.04);
  color: #1DA53F;
}
.lf__file-btn.disabled {
  opacity: 0.5;
  pointer-events: none;
}

/* Media grid */
.lf__media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}
.lf__drag-hint {
  font-size: 12px;
  color: #888;
  margin-bottom: 8px;
}
.lf__media-item {
  position: relative;
  border-radius: 6px;
  overflow: hidden;
  aspect-ratio: 16/10;
  background: #e8e8e8;
  cursor: grab;
  transition: opacity .15s, transform .15s;
}
.lf__media-item--dragging {
  opacity: 0.4;
  transform: scale(0.95);
}
.lf__media-cover-badge {
  position: absolute;
  top: 6px;
  left: 6px;
  background: #1DA53F;
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}
.lf__media-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.lf__media-name {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0,0,0,.55);
  color: #fff;
  font-size: 10px;
  padding: 2px 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.lf__media-delete {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(0,0,0,.6);
  color: #fff;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
}
.lf__media-delete:hover { background: rgba(220,38,38,.9); }

/* Pending video */
.lf__pending-video {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f0faf3;
  border: 1px solid #d0ecd8;
  border-radius: 8px;
  margin-bottom: 12px;
}
.lf__pending-video-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.lf__pending-video-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.lf__pending-video-name {
  font-size: 13px;
  font-weight: 500;
  color: #0F0F0F;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.lf__pending-video-size {
  font-size: 12px;
  color: #606060;
}
.lf__pending-video-remove {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
}
.lf__pending-video-remove:hover { color: #dc2626; }

/* Video thumb (edit mode) */
.lf__media-item--video {
  aspect-ratio: auto;
  display: flex;
  flex-direction: column;
}
.lf__video-thumb {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  background: #0F0F0F;
  display: flex;
  align-items: center;
  justify-content: center;
}
.lf__video-thumb img { width: 100%; height: 100%; object-fit: cover; }
.lf__video-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}
.lf__video-dur {
  position: absolute;
  bottom: 4px;
  right: 4px;
  background: rgba(0,0,0,.8);
  color: #fff;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 3px;
}
.lf__video-info {
  display: flex;
  justify-content: space-between;
  padding: 4px 6px;
  font-size: 11px;
  color: #606060;
}

.lf__media-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  font-size: 12px;
  color: #1DA53F;
  background: rgba(29,165,63,.06);
  padding: 8px 12px;
  border-radius: 6px;
}

.lf__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  width: 100%;
}
.lf__footer-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.lf__publish-wrap { cursor: not-allowed; display: inline-flex; position: relative; }
.lf__publish-btn--disabled { opacity: 0.55 !important; pointer-events: none; }
.lf__publish-badge {
  position: absolute; top: -7px; right: -8px;
  background: #d97706; color: #fff; font-size: 10px; font-weight: 700;
  padding: 2px 8px; border-radius: 10px; line-height: 1.3;
  white-space: nowrap; box-shadow: 0 1px 4px rgba(0,0,0,.18);
  pointer-events: none;
}
.lf__submit-btn {
  background: #1DA53F !important;
  border-color: #1DA53F !important;
}
.lf__submit-btn:hover {
  background: #178A33 !important;
  border-color: #178A33 !important;
}

@media (max-width: 768px) {
  .lf__columns { grid-template-columns: 1fr; }
  .lf__grid { grid-template-columns: 1fr; }
}
</style>
