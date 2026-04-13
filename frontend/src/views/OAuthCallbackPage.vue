
<template>
  <div class="oauth-callback-page">
    <p class="oauth-callback-text">
      {{ t('login.oauthProcessing') }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/useUserStore'
import { useSnackbarStore } from '@/stores/useSnackbarStore'
import { getCurrentLocaleForNavigation } from '@/i18n/locale-resolver'

defineOptions({
  name: 'OAuthCallbackPage',
})

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const snackbar = useSnackbarStore()

onMounted(async () => {
  const err = typeof route.query.error === 'string' ? route.query.error : ''
  const token = typeof route.query.token === 'string' ? route.query.token : ''
  const oauthErrSuffix: Record<string, string> = {
    invalid_state: 'invalidState',
    email_conflict: 'emailConflict',
    oauth_failed: 'oauthFailed',
    invalid_request: 'invalidRequest',
    oauth_denied: 'oauthDenied',
  }
  if (err) {
    const sub = oauthErrSuffix[err]
    const msg = sub
      ? t(`login.oauthErrors.${sub}`)
      : t('login.oauthErrors.generic')
    snackbar.error(msg)
    await router.replace({
      name: 'Login',
      params: { locale: getCurrentLocaleForNavigation() },
    })
    return
  }
  if (token) {
    userStore.setToken(token)
    await userStore.fetchUser()
    snackbar.success(t('login.welcomeBack'))
    await router.replace({
      name: 'Home',
      params: { locale: getCurrentLocaleForNavigation() },
    })
    return
  }
  await router.replace({
    name: 'Login',
    params: { locale: getCurrentLocaleForNavigation() },
  })
})
</script>

<style scoped>
.oauth-callback-page {
  align-items: center;
  display: flex;
  justify-content: center;
  min-height: 40vh;
  padding: 2rem;
}

.oauth-callback-text {
  color: rgb(var(--v-theme-on-surface));
  font-size: 1rem;
}
</style>
