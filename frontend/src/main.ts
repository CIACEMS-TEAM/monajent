import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'
import Toast from 'vue-toastification'
import type { PluginOptions } from 'vue-toastification'
import 'vue-toastification/dist/index.css'
import posthog from 'posthog-js'

import App from './App.vue'
import router from './router'

const posthogToken = import.meta.env.VITE_POSTHOG_PROJECT_TOKEN
if (posthogToken) {
  posthog.init(posthogToken, {
    api_host: import.meta.env.VITE_POSTHOG_HOST || 'https://us.i.posthog.com',
    person_profiles: 'identified_only',
    capture_pageview: false,
  })

  router.afterEach((to) => {
    posthog.capture('$pageview', { $current_url: to.fullPath })
  })
}

const app = createApp(App)

app.use(createPinia())
app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
      darkModeSelector: false,
      cssLayer: false,
    },
  },
})
app.use(Toast, { position: 'top-right', timeout: 3000 } as PluginOptions)
app.use(router)

app.config.errorHandler = (err) => {
  if (posthogToken) posthog.captureException(err)
}

app.mount('#app')
