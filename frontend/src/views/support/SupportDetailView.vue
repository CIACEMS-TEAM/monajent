<template>
  <div class="sd">
    <!-- Header -->
    <div class="sd-header">
      <router-link :to="backRoute" class="sd-header__back" title="Retour à la liste">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
      </router-link>
      <div class="sd-header__text">
        <div class="sd-header__crumb">
          <router-link :to="backRoute" class="sd-header__crumb-link">Support</router-link>
          <span class="sd-header__crumb-sep">/</span>
          <span class="sd-header__crumb-id">#{{ ticketId }}</span>
        </div>
        <h1 class="sd-header__title">{{ ticket?.subject || 'Chargement...' }}</h1>
      </div>
    </div>

    <!-- Info bar -->
    <div v-if="ticket" class="sd-info">
      <div class="sd-info__item">
        <span class="sd-info__label">Statut</span>
        <span class="sd-badge" :class="'sd-badge--' + (ticket.status || '').toLowerCase()">{{ ticket.status_label }}</span>
      </div>
      <div class="sd-info__divider"></div>
      <div class="sd-info__item">
        <span class="sd-info__label">Catégorie</span>
        <span class="sd-info__value">{{ ticket.category_label }}</span>
      </div>
      <div class="sd-info__divider"></div>
      <div class="sd-info__item">
        <span class="sd-info__label">Priorité</span>
        <span class="sd-info__value sd-info__priority" :class="'sd-info__priority--' + (ticket.priority || 'NORMAL').toLowerCase()">
          <span class="sd-info__dot"></span>
          {{ ticket.priority_label || 'Normal' }}
        </span>
      </div>
      <div class="sd-info__divider"></div>
      <div class="sd-info__item">
        <span class="sd-info__label">Créé le</span>
        <span class="sd-info__value">{{ formatDate(ticket.created_at) }}</span>
      </div>
      <div class="sd-info__spacer"></div>
      <button
        v-if="ticket.status !== 'CLOSED'"
        class="sd-info__close-btn"
        @click="handleClose"
        :disabled="closing"
      >
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
        Fermer le ticket
      </button>
    </div>

    <!-- Loading -->
    <div v-if="support.currentTicketLoading" class="sd-loading">
      <div class="sd-loading__spinner"></div>
      <span>Chargement de la conversation...</span>
    </div>

    <template v-else-if="ticket">
      <!-- Messages -->
      <div class="sd-messages" ref="messagesRef">
        <div class="sd-messages__date-sep" v-if="ticket.messages.length">
          <span>{{ formatDate(ticket.messages[0]?.created_at || ticket.created_at) }}</span>
        </div>

        <div
          v-for="(msg, i) in ticket.messages" :key="msg.id"
          class="sd-msg" :class="{ 'sd-msg--staff': msg.is_staff_reply }"
        >
          <div class="sd-msg__avatar" :class="msg.is_staff_reply ? 'sd-msg__avatar--staff' : 'sd-msg__avatar--user'">
            <svg v-if="msg.is_staff_reply" viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.94-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
            <svg v-else viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
          </div>
          <div class="sd-msg__bubble">
            <div class="sd-msg__header">
              <span class="sd-msg__author">{{ msg.is_staff_reply ? 'Équipe MonaJent' : (msg.author_name || 'Vous') }}</span>
              <span class="sd-msg__time">{{ formatTime(msg.created_at) }}</span>
            </div>
            <div class="sd-msg__text">{{ msg.content }}</div>
          </div>
        </div>

        <div v-if="ticket.messages.length === 0" class="sd-messages__hint">
          Démarrez la conversation en envoyant un message ci-dessous.
        </div>
      </div>

      <!-- Reply form -->
      <form v-if="ticket.status !== 'CLOSED'" class="sd-reply" @submit.prevent="sendMessage">
        <div class="sd-reply__input-wrap">
          <textarea
            ref="textareaRef"
            v-model="newMessage"
            placeholder="Écrivez votre message..."
            rows="1"
            @input="autoResize"
            @keydown.enter.ctrl.exact="sendMessage"
            required
          ></textarea>
          <span class="sd-reply__hint">Ctrl + Entrée pour envoyer</span>
        </div>
        <button type="submit" class="sd-reply__send" :disabled="sending || !newMessage.trim()" :title="sending ? 'Envoi...' : 'Envoyer'">
          <svg v-if="!sending" viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
          <div v-else class="sd-reply__spinner"></div>
        </button>
      </form>

      <!-- Closed banner -->
      <div v-else class="sd-closed">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        <div>
          <strong>Ticket fermé</strong>
          <p>Ce ticket a été résolu. Si vous avez besoin d'aide supplémentaire, créez un nouveau ticket.</p>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useSupportStore } from '@/Stores/support'

const route = useRoute()
const support = useSupportStore()

const ticketId = computed(() => Number(route.params.id))
const ticket = computed(() => support.currentTicket)
const isAgent = computed(() => route.path.startsWith('/agent'))
const backRoute = computed(() => isAgent.value ? '/agent/support' : '/home/support')

const newMessage = ref('')
const sending = ref(false)
const closing = ref(false)
const messagesRef = ref<HTMLElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
}

function formatTime(iso: string) {
  const d = new Date(iso)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  const time = d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
  if (isToday) return `Aujourd'hui à ${time}`
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (d.toDateString() === yesterday.toDateString()) return `Hier à ${time}`
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }) + ` à ${time}`
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

function autoResize() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 160) + 'px'
}

async function sendMessage() {
  if (!newMessage.value.trim() || sending.value) return
  sending.value = true
  try {
    await support.addMessage(ticketId.value, newMessage.value.trim())
    newMessage.value = ''
    if (textareaRef.value) textareaRef.value.style.height = 'auto'
    scrollToBottom()
  } finally {
    sending.value = false
  }
}

async function handleClose() {
  if (!confirm('Voulez-vous vraiment fermer ce ticket ? Vous ne pourrez plus y répondre.')) return
  closing.value = true
  try {
    await support.closeTicket(ticketId.value)
  } finally {
    closing.value = false
  }
}

onMounted(async () => {
  await support.fetchTicket(ticketId.value)
  scrollToBottom()
})
</script>

<style scoped>
.sd {
  max-width: 860px;
  margin: 0 auto;
  padding: 24px 16px 16px;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 80px);
}

/* ── Header ──────────────────────────────── */
.sd-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 16px;
}
.sd-header__back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  color: #374151;
  text-decoration: none;
  transition: background 0.15s;
  flex-shrink: 0;
  margin-top: 2px;
}
.sd-header__back:hover { background: #F3F4F6; }
.sd-header__text { flex: 1; min-width: 0; }
.sd-header__crumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  margin-bottom: 2px;
}
.sd-header__crumb-link {
  color: #6B7280;
  text-decoration: none;
  transition: color 0.15s;
}
.sd-header__crumb-link:hover { color: #1DA53F; }
.sd-header__crumb-sep { color: #D1D5DB; }
.sd-header__crumb-id { color: #374151; font-weight: 600; }
.sd-header__title {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Info bar ────────────────────────────── */
.sd-info {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.sd-info__item { display: flex; flex-direction: column; gap: 2px; }
.sd-info__label { font-size: 11px; color: #9CA3AF; font-weight: 500; text-transform: uppercase; letter-spacing: 0.3px; }
.sd-info__value { font-size: 13px; color: #374151; font-weight: 500; }
.sd-info__divider { width: 1px; height: 28px; background: #E5E7EB; }
.sd-info__spacer { flex: 1; }

.sd-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 6px;
  letter-spacing: 0.3px;
}
.sd-badge--open { background: #DCFCE7; color: #15803D; }
.sd-badge--in_progress { background: #DBEAFE; color: #1D4ED8; }
.sd-badge--resolved { background: #FEF3C7; color: #B45309; }
.sd-badge--closed { background: #F3F4F6; color: #6B7280; }

.sd-info__priority {
  display: flex;
  align-items: center;
  gap: 6px;
}
.sd-info__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.sd-info__priority--low .sd-info__dot { background: #9CA3AF; }
.sd-info__priority--normal .sd-info__dot { background: #3B82F6; }
.sd-info__priority--high .sd-info__dot { background: #EF4444; }

.sd-info__close-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  background: #fff;
  font-size: 12px;
  font-weight: 500;
  color: #6B7280;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.sd-info__close-btn:hover { border-color: #EF4444; color: #EF4444; }
.sd-info__close-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── Loading ─────────────────────────────── */
.sd-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 20px;
  color: #9CA3AF;
  font-size: 14px;
}
.sd-loading__spinner {
  width: 28px;
  height: 28px;
  border: 3px solid #E5E7EB;
  border-top-color: #1DA53F;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Messages ────────────────────────────── */
.sd-messages {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  padding: 20px 4px;
  scroll-behavior: smooth;
}
.sd-messages__date-sep {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 4px 0 8px;
}
.sd-messages__date-sep::before,
.sd-messages__date-sep::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #E5E7EB;
}
.sd-messages__date-sep span {
  font-size: 11px;
  color: #9CA3AF;
  font-weight: 500;
  white-space: nowrap;
}
.sd-messages__hint {
  text-align: center;
  padding: 32px 20px;
  font-size: 14px;
  color: #9CA3AF;
}

.sd-msg {
  display: flex;
  gap: 10px;
  max-width: 80%;
  align-self: flex-start;
}
.sd-msg--staff { align-self: flex-start; }
.sd-msg:not(.sd-msg--staff) {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.sd-msg__avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}
.sd-msg__avatar--staff { background: #DCFCE7; color: #16A34A; }
.sd-msg__avatar--user { background: #F3F4F6; color: #6B7280; }

.sd-msg__bubble {
  padding: 10px 14px;
  border-radius: 14px;
  min-width: 0;
}
.sd-msg--staff .sd-msg__bubble {
  background: #F0FDF4;
  border: 1px solid #BBF7D0;
  border-top-left-radius: 4px;
}
.sd-msg:not(.sd-msg--staff) .sd-msg__bubble {
  background: #fff;
  border: 1px solid #E5E7EB;
  border-top-right-radius: 4px;
}

.sd-msg__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 4px;
}
.sd-msg__author {
  font-size: 12px;
  font-weight: 700;
  color: #374151;
}
.sd-msg--staff .sd-msg__author { color: #16A34A; }
.sd-msg__time {
  font-size: 11px;
  color: #9CA3AF;
  white-space: nowrap;
}
.sd-msg__text {
  font-size: 14px;
  line-height: 1.55;
  color: #374151;
  white-space: pre-wrap;
  word-break: break-word;
}

/* ── Reply form ──────────────────────────── */
.sd-reply {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 16px 0 4px;
  border-top: 1px solid #E5E7EB;
  background: #fff;
  position: sticky;
  bottom: 0;
}
.sd-reply__input-wrap {
  flex: 1;
  position: relative;
}
.sd-reply__input-wrap textarea {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  font-size: 14px;
  font-family: inherit;
  color: #111827;
  resize: none;
  min-height: 44px;
  max-height: 160px;
  line-height: 1.5;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.sd-reply__input-wrap textarea:focus {
  outline: none;
  border-color: #1DA53F;
  box-shadow: 0 0 0 3px rgba(29,165,63,.1);
}
.sd-reply__input-wrap textarea::placeholder { color: #9CA3AF; }
.sd-reply__hint {
  display: block;
  font-size: 11px;
  color: #D1D5DB;
  margin-top: 4px;
  padding-left: 2px;
}
.sd-reply__send {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background: #1DA53F;
  color: #fff;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.2s, transform 0.1s;
  box-shadow: 0 1px 3px rgba(29,165,63,.25);
}
.sd-reply__send:hover:not(:disabled) { background: #178A33; }
.sd-reply__send:active:not(:disabled) { transform: scale(0.95); }
.sd-reply__send:disabled { opacity: 0.4; cursor: not-allowed; }
.sd-reply__spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

/* ── Closed banner ───────────────────────── */
.sd-closed {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 20px;
  background: #F0FDF4;
  border: 1px solid #BBF7D0;
  border-radius: 12px;
  margin-top: 16px;
  color: #15803D;
}
.sd-closed strong { display: block; font-size: 14px; margin-bottom: 2px; }
.sd-closed p { font-size: 13px; color: #4B5563; margin: 0; line-height: 1.5; }
.sd-closed svg { flex-shrink: 0; margin-top: 2px; }

/* ── Responsive ──────────────────────────── */
@media (max-width: 640px) {
  .sd { padding: 16px 12px 8px; height: calc(100vh - 64px); }
  .sd-msg { max-width: 92%; }
  .sd-info { gap: 10px; }
  .sd-info__divider { display: none; }
  .sd-info__close-btn { width: 100%; justify-content: center; margin-top: 4px; }
  .sd-reply__hint { display: none; }
}
</style>
