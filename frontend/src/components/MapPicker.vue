<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = withDefaults(defineProps<{
  latitude?: number | null
  longitude?: number | null
  readonly?: boolean
}>(), {
  latitude: null,
  longitude: null,
  readonly: false,
})

const emit = defineEmits<{
  (e: 'update', coords: { latitude: number; longitude: number }): void
}>()

const mapContainer = ref<HTMLDivElement | null>(null)
const searchQuery = ref('')
const searching = ref(false)
const searchError = ref('')

let map: L.Map | null = null
let marker: L.Marker | null = null

const DEFAULT_CENTER: [number, number] = [5.345, -4.025] // Abidjan
const DEFAULT_ZOOM = 13
const MARKER_ZOOM = 16

const markerIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

function initMap() {
  if (!mapContainer.value || map) return

  const center: [number, number] = (props.latitude && props.longitude)
    ? [props.latitude, props.longitude]
    : DEFAULT_CENTER
  const zoom = (props.latitude && props.longitude) ? MARKER_ZOOM : DEFAULT_ZOOM

  map = L.map(mapContainer.value, {
    center,
    zoom,
    zoomControl: true,
  })

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>',
    maxZoom: 19,
  }).addTo(map)

  if (props.latitude && props.longitude) {
    placeMarker(props.latitude, props.longitude, false)
  }

  if (!props.readonly) {
    map.on('click', (e: L.LeafletMouseEvent) => {
      placeMarker(e.latlng.lat, e.latlng.lng, true)
    })
  }
}

function placeMarker(lat: number, lng: number, emitEvent: boolean) {
  if (!map) return
  if (marker) {
    marker.setLatLng([lat, lng])
  } else {
    marker = L.marker([lat, lng], { icon: markerIcon, draggable: !props.readonly }).addTo(map)
    if (!props.readonly) {
      marker.on('dragend', () => {
        const pos = marker!.getLatLng()
        emit('update', { latitude: round6(pos.lat), longitude: round6(pos.lng) })
      })
    }
  }
  if (emitEvent) {
    emit('update', { latitude: round6(lat), longitude: round6(lng) })
  }
}

function round6(n: number): number {
  return Math.round(n * 1e6) / 1e6
}

async function handleSearch() {
  if (!searchQuery.value.trim() || !map) return
  searching.value = true
  searchError.value = ''
  try {
    const q = encodeURIComponent(searchQuery.value.trim())
    const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${q}&limit=1`, {
      headers: { 'Accept-Language': 'fr' },
    })
    const data = await res.json()
    if (data.length > 0) {
      const { lat, lon } = data[0]
      const latN = parseFloat(lat)
      const lngN = parseFloat(lon)
      map.setView([latN, lngN], MARKER_ZOOM)
      placeMarker(latN, lngN, true)
    } else {
      searchError.value = 'Aucun résultat trouvé'
    }
  } catch {
    searchError.value = 'Erreur de recherche'
  } finally {
    searching.value = false
  }
}

watch(() => [props.latitude, props.longitude], ([lat, lng]) => {
  if (lat && lng && map) {
    map.setView([lat as number, lng as number], MARKER_ZOOM)
    placeMarker(lat as number, lng as number, false)
  }
})

onMounted(() => {
  nextTick(() => initMap())
})

onBeforeUnmount(() => {
  if (map) {
    map.remove()
    map = null
    marker = null
  }
})
</script>

<template>
  <div class="mp">
    <div v-if="!readonly" class="mp__search">
      <input
        v-model="searchQuery"
        type="text"
        class="mp__search-input"
        placeholder="Rechercher un lieu : Cocody, Plateau, Marcory..."
        @keydown.enter.prevent="handleSearch"
      />
      <button class="mp__search-btn" @click="handleSearch" :disabled="searching">
        <svg v-if="!searching" viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
        <span v-else class="mp__spinner"></span>
      </button>
    </div>
    <p v-if="searchError" class="mp__error">{{ searchError }}</p>
    <div ref="mapContainer" class="mp__map"></div>
    <p v-if="!readonly" class="mp__hint">Cliquez sur la carte pour placer le marqueur, ou recherchez un lieu.</p>
  </div>
</template>

<style scoped>
.mp { width: 100%; }
.mp__search {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
}
.mp__search-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #E0E0E0;
  border-radius: 8px;
  font-size: 14px;
  color: #0F0F0F;
  box-sizing: border-box;
}
.mp__search-input:focus { outline: none; border-color: #1DA53F; }
.mp__search-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border: none;
  background: #1DA53F;
  color: #fff;
  border-radius: 8px;
  cursor: pointer;
  flex-shrink: 0;
}
.mp__search-btn:hover { background: #178A33; }
.mp__search-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.mp__spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.mp__error {
  font-size: 12px;
  color: #dc2626;
  margin-bottom: 6px;
}
.mp__map {
  width: 100%;
  height: 300px;
  border-radius: 10px;
  border: 1px solid #E0E0E0;
  z-index: 0;
}
.mp__hint {
  font-size: 12px;
  color: #888;
  margin-top: 6px;
}
</style>
