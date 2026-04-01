<template>
  <div class="support-create">
    <div class="support-create__header">
      <router-link :to="backRoute" class="support-create__back">
        <svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
      </router-link>
      <h1 class="support-create__title">Nouveau ticket</h1>
    </div>

    <form class="support-create__form" @submit.prevent="submit">
      <div class="support-create__field">
        <label>Catégorie</label>
        <div class="support-create__categories">
          <button
            v-for="cat in categories"
            :key="cat.value"
            type="button"
            class="support-create__cat"
            :class="{ active: form.category === cat.value }"
            @click="form.category = cat.value"
          >
            <svg v-if="cat.icon === 'bug'" viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M20 8h-2.81a5.985 5.985 0 00-1.82-1.96L17 4.41 15.59 3l-2.17 2.17C12.96 5.06 12.49 5 12 5c-.49 0-.96.06-1.41.17L8.41 3 7 4.41l1.62 1.63C7.88 6.55 7.26 7.22 6.81 8H4v2h2.09c-.05.33-.09.66-.09 1v1H4v2h2v1c0 .34.04.67.09 1H4v2h2.81c1.04 1.79 2.97 3 5.19 3s4.15-1.21 5.19-3H20v-2h-2.09c.05-.33.09-.66.09-1v-1h2v-2h-2v-1c0-.34-.04-.67-.09-1H20V8zm-6 8h-4v-2h4v2zm0-4h-4v-2h4v2z"/></svg>
            <svg v-else-if="cat.icon === 'bulb'" viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1zm3-19C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7z"/></svg>
            <svg v-else-if="cat.icon === 'warning'" viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>
            <svg v-else-if="cat.icon === 'help'" viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/></svg>
            <svg v-else viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/></svg>
            <span>{{ cat.label }}</span>
          </button>
        </div>
      </div>

      <div class="support-create__field">
        <label for="subject">Sujet</label>
        <input
          id="subject"
          v-model="form.subject"
          type="text"
          placeholder="Résumez votre demande en quelques mots"
          maxlength="255"
          required
        />
      </div>

      <div class="support-create__field">
        <label for="content">Description</label>
        <textarea
          id="content"
          v-model="form.content"
          placeholder="Décrivez votre problème ou demande en détail..."
          rows="6"
          required
        ></textarea>
      </div>

      <div v-if="error" class="support-create__error">{{ error }}</div>

      <button type="submit" class="support-create__submit" :disabled="submitting || !isValid">
        {{ submitting ? 'Envoi en cours...' : 'Envoyer le ticket' }}
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useSupportStore } from '@/Stores/support'

const router = useRouter()
const route = useRoute()
const support = useSupportStore()

const isAgent = computed(() => route.path.startsWith('/agent'))
const backRoute = computed(() => isAgent.value ? '/agent/support' : '/home/support')

const categories = [
  { value: 'BUG', label: 'Bug', icon: 'bug' },
  { value: 'SUGGESTION', label: 'Suggestion', icon: 'bulb' },
  { value: 'COMPLAINT', label: 'Plainte', icon: 'warning' },
  { value: 'HELP', label: 'Aide', icon: 'help' },
  { value: 'OTHER', label: 'Autre', icon: 'other' },
]

const form = reactive({
  category: 'HELP',
  subject: '',
  content: '',
})

const submitting = ref(false)
const error = ref('')

const isValid = computed(() =>
  form.category && form.subject.trim().length >= 3 && form.content.trim().length >= 10
)

async function submit() {
  if (!isValid.value || submitting.value) return
  submitting.value = true
  error.value = ''
  try {
    const ticket = await support.createTicket({
      category: form.category,
      subject: form.subject.trim(),
      content: form.content.trim(),
    })
    const detailPath = isAgent.value
      ? `/agent/support/${ticket.id}`
      : `/home/support/${ticket.id}`
    router.push(detailPath)
  } catch (e: any) {
    error.value = e?.response?.data?.detail || 'Erreur lors de la création du ticket.'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.support-create {
  max-width: 640px;
  margin: 0 auto;
  padding: 24px 0;
}

.support-create__header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 28px;
}

.support-create__back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  color: #272727;
  text-decoration: none;
  transition: background 0.15s;
}
.support-create__back:hover { background: #f2f2f2; }

.support-create__title {
  font-size: 20px;
  font-weight: 700;
  color: #0f0f0f;
}

.support-create__form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.support-create__field label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #272727;
  margin-bottom: 8px;
}

.support-create__field input,
.support-create__field textarea {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  color: #0f0f0f;
  background: #fff;
  transition: border-color 0.15s;
  font-family: inherit;
}
.support-create__field input:focus,
.support-create__field textarea:focus {
  outline: none;
  border-color: #1DA53F;
  box-shadow: 0 0 0 3px rgba(29,165,63,.1);
}
.support-create__field textarea { resize: vertical; min-height: 120px; }

.support-create__categories {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.support-create__cat {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  background: #fff;
  font-size: 13px;
  color: #606060;
  cursor: pointer;
  transition: all 0.15s;
}
.support-create__cat:hover { border-color: #1DA53F; color: #1DA53F; }
.support-create__cat.active {
  background: rgba(29,165,63,.08);
  border-color: #1DA53F;
  color: #1DA53F;
  font-weight: 600;
}

.support-create__error {
  padding: 10px 14px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 13px;
}

.support-create__submit {
  padding: 12px 28px;
  background: #1DA53F;
  color: #fff;
  border: none;
  border-radius: 24px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
  align-self: flex-start;
}
.support-create__submit:hover:not(:disabled) { background: #178A33; }
.support-create__submit:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
