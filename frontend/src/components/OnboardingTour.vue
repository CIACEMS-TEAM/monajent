<script setup lang="ts">
import { ref, reactive, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'

const emit = defineEmits<{ (e: 'done'): void }>()

const STORAGE_KEY = 'monajent_onboarding_done'

interface Step {
  selectors: string[]
  title: string
  desc: string
}

const steps: Step[] = [
  {
    selectors: [],
    title: 'Les annonces en vidéo',
    desc: 'Parcourez les biens immobiliers en vidéo. Cliquez sur une annonce pour voir les détails, les photos, la vidéo et contacter l\'agent.',
  },
  {
    selectors: ['[data-tour="sidebar"]', '[data-tour="nav"]'],
    title: 'Votre navigation',
    desc: 'Accédez à l\'accueil, vos packs de clés, vos favoris et votre espace personnel.',
  },
  {
    selectors: ['[data-tour="sidebar-packs"]', '[data-tour="packs"]'],
    title: 'Les Packs de clés',
    desc: 'Achetez des clés virtuelles ou physiques pour débloquer des visites physiques gratuites, sans frais d\'agence.',
  },
  {
    selectors: ['[data-tour="mona"]'],
    title: 'Mona — Assistante IA',
    desc: 'Cliquez ici et décrivez ce que vous cherchez par la voix. Mona trouve le bien idéal pour vous en quelques secondes !',
  },
]

const active = ref(false)
const idx = ref(0)
const stepping = ref(false)
const hasTarget = ref(false)
const spot = reactive({ top: 0, left: 0, width: 0, height: 0 })
const tipStyle = reactive<Record<string, string>>({})
const tipPlacement = ref<'center' | 'above' | 'right'>('center')

const step = computed(() => steps[idx.value])
const isLast = computed(() => idx.value === steps.length - 1)
const progressPct = computed(() => ((idx.value + 1) / steps.length) * 100)

function findVisibleEl(selectors: string[]): HTMLElement | null {
  for (const sel of selectors) {
    const el = document.querySelector(sel) as HTMLElement | null
    if (!el) continue
    const r = el.getBoundingClientRect()
    if (r.width > 0 && r.height > 0) return el
  }
  return null
}

function measure() {
  const el = findVisibleEl(step.value.selectors)
  if (!el) {
    hasTarget.value = false
    tipPlacement.value = 'center'
    Object.assign(tipStyle, { top: '50%', bottom: 'auto', left: '50%', right: 'auto', transform: 'translate(-50%, -50%)' })
    return
  }

  const r = el.getBoundingClientRect()
  const pad = 8
  spot.top = r.top - pad
  spot.left = r.left - pad
  spot.width = r.width + pad * 2
  spot.height = r.height + pad * 2
  hasTarget.value = true

  const vw = window.innerWidth
  const vh = window.innerHeight
  const cardW = Math.min(360, vw - 32)

  if (r.left < vw / 3 && r.height > vh * 0.4) {
    tipPlacement.value = 'right'
    const tipTop = Math.max(80, r.top + r.height / 2 - 120)
    Object.assign(tipStyle, {
      top: `${tipTop}px`,
      bottom: 'auto',
      left: `${r.right + 24}px`,
      right: 'auto',
      transform: 'none',
    })
  } else {
    tipPlacement.value = 'above'
    let tipLeft = Math.max(16, (vw - cardW) / 2)
    Object.assign(tipStyle, {
      bottom: `${vh - r.top + 20}px`,
      top: 'auto',
      left: `${tipLeft}px`,
      right: 'auto',
      transform: 'none',
    })
  }
}

async function goNext() {
  if (isLast.value) return finish()
  stepping.value = true
  await new Promise(r => setTimeout(r, 150))
  idx.value++
  await nextTick()
  measure()
  stepping.value = false
}

function finish() {
  active.value = false
  localStorage.setItem(STORAGE_KEY, '1')
  emit('done')
}

onMounted(() => {
  active.value = true
  nextTick(measure)
  window.addEventListener('resize', measure)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', measure)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="ot-fade">
      <div v-if="active" class="ot">

        <!-- Spotlight (targets a specific visible element) -->
        <div
          v-if="hasTarget"
          class="ot__spot"
          :style="{
            top: spot.top + 'px',
            left: spot.left + 'px',
            width: spot.width + 'px',
            height: spot.height + 'px',
          }"
        />
        <!-- Full dark backdrop (no specific target) -->
        <div v-else class="ot__dim" @click.stop />

        <!-- Block all clicks outside the card -->
        <div class="ot__tap" />

        <!-- Tooltip card -->
        <div
          class="ot__card"
          :class="{ 'ot__card--stepping': stepping }"
          :style="tipStyle"
        >
          <!-- Progress bar -->
          <div class="ot__bar-track">
            <div class="ot__bar-fill" :style="{ width: progressPct + '%' }" />
          </div>

          <span class="ot__count">{{ idx + 1 }} / {{ steps.length }}</span>

          <!-- Step icon -->
          <div class="ot__icon">
            <svg v-if="idx === 0" viewBox="0 0 24 24" width="32" height="32">
              <rect x="2" y="4" width="20" height="16" rx="3" fill="none" stroke="#1DA53F" stroke-width="1.8"/>
              <polygon points="10,8 10,16 16,12" fill="#1DA53F"/>
            </svg>
            <svg v-else-if="idx === 1" viewBox="0 0 24 24" width="32" height="32">
              <path fill="#1DA53F" d="M4 21V10.08l8-6.96 8 6.96V21h-6v-6h-4v6H4z"/>
            </svg>
            <svg v-else-if="idx === 2" viewBox="0 0 24 24" width="32" height="32">
              <path fill="#1DA53F" d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zM12 17c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zM9 8V6c0-1.66 1.34-3 3-3s3 1.34 3 3v2H9z"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" width="32" height="32">
              <path fill="#1DA53F" d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
              <path fill="#fff" d="M13.5 7.5l.9-1.9 1.9-.9-1.9-.9-.9-1.9-.9 1.9-1.9.9 1.9.9z"/>
            </svg>
          </div>

          <h3 class="ot__title">{{ step.title }}</h3>
          <p class="ot__desc">{{ step.desc }}</p>

          <div class="ot__actions">
            <button class="ot__skip" @click.stop="finish">Passer</button>
            <button class="ot__next" @click.stop="goNext">
              {{ isLast ? "C'est parti !" : 'Suivant →' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* ─── Spotlight ───────────────────────────────────────── */
.ot__spot {
  position: fixed;
  z-index: 10000;
  border-radius: 14px;
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.65);
  pointer-events: none;
  transition: top 0.4s cubic-bezier(.4,0,.2,1),
              left 0.4s cubic-bezier(.4,0,.2,1),
              width 0.4s cubic-bezier(.4,0,.2,1),
              height 0.4s cubic-bezier(.4,0,.2,1);
}

.ot__dim {
  position: fixed;
  inset: 0;
  z-index: 10000;
  background: rgba(0, 0, 0, 0.65);
}

.ot__tap {
  position: fixed;
  inset: 0;
  z-index: 10001;
  cursor: pointer;
}

/* ─── Tooltip card ────────────────────────────────────── */
.ot__card {
  position: fixed;
  z-index: 10002;
  width: 360px;
  max-width: calc(100vw - 32px);
  background: #fff;
  border-radius: 18px;
  padding: 20px 22px 18px;
  box-shadow: 0 12px 40px rgba(0,0,0,.22);
  transition: opacity 0.15s ease;
}

.ot__card--stepping {
  opacity: 0;
}

/* ─── Progress bar ────────────────────────────────────── */
.ot__bar-track {
  height: 3px;
  background: #e5e7eb;
  border-radius: 2px;
  margin-bottom: 14px;
  overflow: hidden;
}
.ot__bar-fill {
  height: 100%;
  background: #1DA53F;
  border-radius: 2px;
  transition: width 0.4s ease;
}

.ot__count {
  display: block;
  font-size: 11px;
  color: #aaa;
  font-weight: 600;
  margin-bottom: 10px;
  letter-spacing: 0.5px;
}

/* ─── Icon ────────────────────────────────────────────── */
.ot__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: rgba(29, 165, 63, 0.08);
  margin: 0 auto 14px;
}

/* ─── Text ────────────────────────────────────────────── */
.ot__title {
  font-size: 18px;
  font-weight: 700;
  color: #111;
  margin: 0 0 6px;
  text-align: center;
}
.ot__desc {
  font-size: 14px;
  line-height: 1.55;
  color: #555;
  margin: 0 0 18px;
  text-align: center;
}

/* ─── Actions ─────────────────────────────────────────── */
.ot__actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ot__skip {
  background: none;
  border: none;
  font-size: 14px;
  font-weight: 500;
  color: #999;
  cursor: pointer;
  padding: 10px 16px;
  border-radius: 10px;
  transition: color 0.15s, background 0.15s;
}
.ot__skip:hover { color: #555; background: #f5f5f5; }

.ot__next {
  flex: 1;
  background: #1DA53F;
  color: #fff;
  border: none;
  border-radius: 12px;
  padding: 12px 20px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, box-shadow 0.15s;
}
.ot__next:hover {
  background: #178A33;
  box-shadow: 0 4px 14px rgba(29,165,63,.3);
}

/* ─── Transition ──────────────────────────────────────── */
.ot-fade-enter-active { transition: opacity 0.3s ease; }
.ot-fade-leave-active { transition: opacity 0.25s ease; }
.ot-fade-enter-from,
.ot-fade-leave-to { opacity: 0; }

/* ─── Mobile ──────────────────────────────────────────── */
@media (max-width: 480px) {
  .ot__card { padding: 16px 18px 14px; }
  .ot__title { font-size: 16px; }
  .ot__desc { font-size: 13px; }
}
</style>
