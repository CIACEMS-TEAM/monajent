<template>
  <div class="support-detail">
    <div class="support-detail__header">
      <router-link :to="backRoute" class="support-detail__back">
        <svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
      </router-link>
      <div class="support-detail__header-info">
        <h1 class="support-detail__title">{{ ticket?.subject || 'Chargement...' }}</h1>
        <div v-if="ticket" class="support-detail__meta">
          <span class="support-detail__badge" :class="'badge--' + ticket.status.toLowerCase()">
            {{ ticket.status_label }}
          </span>
          <span class="support-detail__cat">{{ ticket.category_label }}</span>
          <span class="support-detail__date">Créé le {{ formatDate(ticket.created_at) }}</span>
        </div>
      </div>
      <button
        v-if="ticket && ticket.status !== 'CLOSED'"
        class="support-detail__close-btn"
        @click="handleClose"
        :disabled="closing"
      >Fermer le ticket</button>
    </div>

    <div v-if="support.currentTicketLoading" class="support-detail__loading">Chargement...</div>

    <template v-else-if="ticket">
      <div class="support-detail__messages" ref="messagesRef">
        <div
          v-for="msg in ticket.messages"
          :key="msg.id"
          class="support-detail__msg"
          :class="{ 'msg--staff': msg.is_staff_reply, 'msg--user': !msg.is_staff_reply }"
        >
          <div class="support-detail__msg-header">
            <span class="support-detail__msg-author">
              {{ msg.is_staff_reply ? 'Équipe MonaJent' : (msg.author_name || msg.author_phone || 'Vous') }}
            </span>
            <span class="support-detail__msg-time">{{ formatTime(msg.created_at) }}</span>
          </div>
          <div class="support-detail__msg-content">{{ msg.content }}</div>
        </div>
      </div>

      <form
        v-if="ticket.status !== 'CLOSED'"
        class="support-detail__reply"
        @submit.prevent="sendMessage"
      >
        <textarea
          v-model="newMessage"
          placeholder="Écrivez votre message..."
          rows="3"
          required
        ></textarea>
        <button type="submit" :disabled="sending || !newMessage.trim()">
          <svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
          {{ sending ? 'Envoi...' : 'Envoyer' }}
        </button>
      </form>

      <div v-else class="support-detail__closed-banner">
        Ce ticket est fermé. Vous ne pouvez plus y répondre.
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

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('fr-FR', {
    day: 'numeric', month: 'long', year: 'numeric',
  })
}

function formatTime(iso: string) {
  const d = new Date(iso)
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })
    + ' à ' + d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

async function sendMessage() {
  if (!newMessage.value.trim() || sending.value) return
  sending.value = true
  try {
    await support.addMessage(ticketId.value, newMessage.value.trim())
    newMessage.value = ''
    scrollToBottom()
  } finally {
    sending.value = false
  }
}

async function handleClose() {
  if (!confirm('Voulez-vous vraiment fermer ce ticket ?')) return
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
.support-detail {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px 0;
}

.support-detail__header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 24px;
}

.support-detail__back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  color: #272727;
  text-decoration: none;
  transition: background 0.15s;
  flex-shrink: 0;
  margin-top: 2px;
}
.support-detail__back:hover { background: #f2f2f2; }

.support-detail__header-info { flex: 1; min-width: 0; }

.support-detail__title {
  font-size: 20px;
  font-weight: 700;
  color: #0f0f0f;
  margin-bottom: 8px;
  line-height: 1.3;
}

.support-detail__meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.support-detail__badge {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 10px;
  border-radius: 4px;
  letter-spacing: 0.3px;
}
.badge--open { background: #dcfce7; color: #16a34a; }
.badge--in_progress { background: #dbeafe; color: #2563eb; }
.badge--resolved { background: #fef3c7; color: #d97706; }
.badge--closed { background: #f3f4f6; color: #6b7280; }

.support-detail__cat { font-size: 12px; color: #888; }
.support-detail__date { font-size: 12px; color: #888; }

.support-detail__close-btn {
  padding: 6px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  background: #fff;
  font-size: 13px;
  color: #606060;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: all 0.15s;
}
.support-detail__close-btn:hover { border-color: #dc2626; color: #dc2626; }
.support-detail__close-btn:disabled { opacity: 0.5; }

.support-detail__loading {
  text-align: center;
  padding: 40px;
  color: #888;
}

.support-detail__messages {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 500px;
  overflow-y: auto;
  padding: 16px;
  background: #fafafa;
  border-radius: 12px;
  margin-bottom: 20px;
}

.support-detail__msg {
  padding: 14px 16px;
  border-radius: 12px;
  max-width: 85%;
}

.msg--user {
  background: #fff;
  border: 1px solid #e0e0e0;
  align-self: flex-end;
}

.msg--staff {
  background: rgba(29,165,63,.06);
  border: 1px solid rgba(29,165,63,.15);
  align-self: flex-start;
}

.support-detail__msg-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
}

.support-detail__msg-author {
  font-size: 12px;
  font-weight: 700;
  color: #272727;
}

.msg--staff .support-detail__msg-author { color: #1DA53F; }

.support-detail__msg-time {
  font-size: 11px;
  color: #999;
}

.support-detail__msg-content {
  font-size: 14px;
  line-height: 1.5;
  color: #272727;
  white-space: pre-wrap;
}

.support-detail__reply {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.support-detail__reply textarea {
  flex: 1;
  padding: 12px 14px;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  font-size: 14px;
  font-family: inherit;
  color: #0f0f0f;
  resize: vertical;
  min-height: 56px;
  transition: border-color 0.15s;
}
.support-detail__reply textarea:focus {
  outline: none;
  border-color: #1DA53F;
  box-shadow: 0 0 0 3px rgba(29,165,63,.1);
}

.support-detail__reply button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  background: #1DA53F;
  color: #fff;
  border: none;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s;
}
.support-detail__reply button:hover:not(:disabled) { background: #178A33; }
.support-detail__reply button:disabled { opacity: 0.5; cursor: not-allowed; }

.support-detail__closed-banner {
  text-align: center;
  padding: 16px;
  background: #f3f4f6;
  border-radius: 12px;
  color: #6b7280;
  font-size: 14px;
}

@media (max-width: 600px) {
  .support-detail__msg { max-width: 95%; }
  .support-detail__reply { flex-direction: column; }
  .support-detail__reply button { align-self: flex-end; }
  .support-detail__close-btn { display: none; }
}
</style>
