<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

const props = defineProps<{
  url: string
  height?: number
}>()

const canvas = ref<HTMLCanvasElement | null>(null)
const loading = ref(true)
const failed = ref(false)

const PDFJS_CDN = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js'
const WORKER_CDN = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js'

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) {
      resolve()
      return
    }
    const s = document.createElement('script')
    s.src = src
    s.onload = () => resolve()
    s.onerror = () => reject(new Error(`Failed to load ${src}`))
    document.head.appendChild(s)
  })
}

async function getPdfJs(): Promise<any> {
  const w = window as any
  if (w.pdfjsLib) return w.pdfjsLib
  await loadScript(PDFJS_CDN)
  if (!w.pdfjsLib) throw new Error('pdfjsLib not found')
  w.pdfjsLib.GlobalWorkerOptions.workerSrc = WORKER_CDN
  return w.pdfjsLib
}

async function renderPage() {
  if (!props.url || !canvas.value) return
  loading.value = true
  failed.value = false
  try {
    const lib = await getPdfJs()
    const pdf = await lib.getDocument(props.url).promise
    const page = await pdf.getPage(1)
    const targetH = props.height || 160
    const vp = page.getViewport({ scale: 1 })
    const scale = targetH / vp.height
    const scaled = page.getViewport({ scale })

    canvas.value.width = scaled.width
    canvas.value.height = scaled.height
    const ctx = canvas.value.getContext('2d')!
    await page.render({ canvasContext: ctx, viewport: scaled }).promise
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
}

onMounted(renderPage)
watch(() => props.url, renderPage)
</script>

<template>
  <div class="pdf-thumb" :style="{ height: (height || 160) + 'px' }">
    <canvas v-show="!loading && !failed" ref="canvas" class="pdf-thumb__canvas" />
    <div v-if="loading && !failed" class="pdf-thumb__loading">
      <svg class="pdf-thumb__spinner" viewBox="0 0 24 24" width="24" height="24">
        <circle cx="12" cy="12" r="10" fill="none" stroke="#e0e0e0" stroke-width="2.5" />
        <path fill="none" stroke="#1DA53F" stroke-width="2.5" stroke-linecap="round" d="M12 2a10 10 0 0 1 10 10">
          <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
        </path>
      </svg>
    </div>
    <div v-if="failed" class="pdf-thumb__fallback">
      <svg viewBox="0 0 24 24" width="36" height="36"><path fill="#dc2626" d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm0 18H6V4h7v5h5v11z"/></svg>
      <span class="pdf-thumb__badge">PDF</span>
      <span class="pdf-thumb__hint">Cliquer pour ouvrir</span>
    </div>
  </div>
</template>

<style scoped>
.pdf-thumb {
  width: 100%; border-radius: 10px; overflow: hidden;
  background: #f5f5f5; display: flex; align-items: center; justify-content: center;
  position: relative;
}
.pdf-thumb__canvas {
  max-width: 100%; max-height: 100%; display: block;
  object-fit: contain;
}
.pdf-thumb__loading { display: flex; align-items: center; justify-content: center; }
.pdf-thumb__fallback {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
}
.pdf-thumb__badge {
  font-size: 13px; font-weight: 700; color: #fff; background: #dc2626;
  padding: 3px 12px; border-radius: 6px;
}
.pdf-thumb__hint { font-size: 11px; color: #909090; }
</style>
