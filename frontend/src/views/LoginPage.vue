<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-card-inner">
        <div class="login-branding">
          <AppLogo size="large" />
          <h2 class="login-title">{{ t('login.title') }}</h2>
          <p class="login-subtitle">
            {{ t('login.subtitle') }}
          </p>
          <router-link
            :to="toPricing"
            class="login-pricing-link"
          >
            {{ t('common.viewPricing') }}
          </router-link>
        </div>

        <div class="login-form-wrap">
          <template v-if="step === 1">
            <v-form
              ref="emailFormRef"
              class="login-form"
              @submit.prevent="goToPasswordStep"
            >
              <v-text-field
                v-model="emailForm.email"
                :placeholder="t('login.emailOrPhone')"
                :rules="emailRules"
                autocomplete="username"
                density="comfortable"
              />
              <div class="form-links">
                <a
                  href="#"
                  class="text-link"
                  @click.prevent="handleForgotEmail"
                >
                  {{ t('login.forgotEmail') }}
                </a>
              </div>
              <p class="guest-hint">
                {{ t('login.guestHint') }}
              </p>
              <div class="form-actions">
                <router-link
                  :to="toRegister"
                  class="text-link"
                >
                  {{ t('login.createAccount') }}
                </router-link>
                <v-btn
                  color="primary"
                  size="large"
                  class="login-btn"
                  type="submit"
                >
                  {{ t('login.next') }}
                </v-btn>
              </div>
            </v-form>
            <div class="oauth-social-block">
              <p class="oauth-other-title">
                {{ t('login.oauthOtherMethods') }}
              </p>
              <div class="oauth-social-row">
                <button
                  type="button"
                  class="oauth-social-item"
                  :aria-label="t('login.oauthWeibo')"
                  @click="startWeiboOAuth"
                >
                  <span class="oauth-social-icon oauth-social-icon--weibo">
                    <v-icon
                      color="white"
                      size="22"
                    >
                      mdi-sina-weibo
                    </v-icon>
                  </span>
                </button>
                <button
                  type="button"
                  class="oauth-social-item"
                  :aria-label="t('login.oauthAlipay')"
                  @click="startAlipayOAuth"
                >
                  <span class="oauth-social-icon oauth-social-icon--alipay">
                    <img
                      :src="oauthAlipayIconUrl"
                      alt=""
                      class="oauth-social-icon-img oauth-social-icon-img--alipay"
                    />
                  </span>
                </button>
                <button
                  type="button"
                  class="oauth-social-item oauth-social-item--disabled"
                  :aria-label="t('login.oauthGoogle')"
                  disabled
                >
                  <span class="oauth-social-icon oauth-social-icon--google">
                    <v-icon
                      color="white"
                      size="22"
                    >
                      mdi-google
                    </v-icon>
                  </span>
                </button>
                <button
                  type="button"
                  class="oauth-social-item oauth-social-item--disabled"
                  :aria-label="t('login.oauthQQ')"
                  disabled
                >
                  <span class="oauth-social-icon oauth-social-icon--qq">
                    <v-icon
                      color="white"
                      size="22"
                    >
                      mdi-qqchat
                    </v-icon>
                  </span>
                </button>
              </div>
            </div>
          </template>

          <template v-else-if="step === 2 && !showRegister">
            <v-form
              ref="loginFormRef"
              class="login-form"
              @submit.prevent="handleLogin"
            >
              <div class="account-display">
                <span class="account-email">{{ emailForm.email }}</span>
              </div>
              <v-text-field
                v-model="loginForm.password"
                :type="showPassword ? 'text' : 'password'"
                :placeholder="t('login.enterPassword')"
                :rules="loginRules"
                autocomplete="current-password"
                density="comfortable"
              />
              <div class="form-links">
                <v-checkbox
                  v-model="showPassword"
                  :label="t('login.showPassword')"
                  density="compact"
                  hide-details
                />
              </div>
              <div class="form-actions">
                <a
                  href="#"
                  class="text-link"
                  @click.prevent="step = 1"
                >
                  {{ t('login.tryAnotherWay') }}
                </a>
                <v-btn
                  color="primary"
                  size="large"
                  :loading="loading"
                  class="login-btn"
                  type="submit"
                >
                  {{ t('login.next') }}
                </v-btn>
              </div>
            </v-form>
          </template>

          <template v-else>
            <v-form
              ref="registerFormRef"
              class="login-form"
              @submit.prevent="handleRegister"
            >
              <v-text-field
                v-model="registerForm.email"
                :label="t('login.emailOrPhone')"
                type="email"
                placeholder="you@example.com"
                :rules="registerEmailRules"
                density="comfortable"
              />
              <v-text-field
                v-model="registerForm.username"
                :label="t('login.username')"
                :placeholder="t('login.username')"
                :rules="registerUsernameRules"
                density="comfortable"
                class="mt-2"
              />
              <v-text-field
                v-model="registerForm.password"
                :label="t('login.createPassword')"
                type="password"
                :placeholder="t('login.createPassword')"
                :rules="registerPasswordRules"
                density="comfortable"
                class="mt-2"
              />
              <div class="form-actions mt-4">
                <router-link
                  :to="toLogin"
                  class="text-link"
                >
                  {{ t('login.tryAnotherWay') }}
                </router-link>
                <v-btn
                  color="primary"
                  size="large"
                  :loading="loading"
                  class="login-btn"
                  type="submit"
                >
                  {{ t('login.createAccount') }}
                </v-btn>
              </div>
            </v-form>
          </template>
        </div>
      </div>

      <footer class="login-footer">
        <div class="footer-links">
          <a
            href="#"
            class="footer-link"
            @click.prevent
          >
            {{ t('common.help') }}
          </a>
          <a
            href="#"
            class="footer-link"
            @click.prevent
          >
            {{ t('common.privacy') }}
          </a>
          <a
            href="#"
            class="footer-link"
            @click.prevent
          >
            {{ t('common.terms') }}
          </a>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppLogo from '@/components/AppLogo.vue'
import oauthAlipayIconUrl from '@/assets/oauth-alipay-icon.png'
import { useI18n } from 'vue-i18n'
import type { VForm } from 'vuetify/components'
import { useUserStore, LAST_LOGIN_ACCOUNT_KEY } from '@/stores/useUserStore'
import { useThemeStore } from '@/stores/useThemeStore'
import { useSnackbarStore } from '@/stores/useSnackbarStore'
import { useRouteLocale } from '@/i18n/useRouteLocale'

defineOptions({
  name: 'LoginPage',
})

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const themeStore = useThemeStore()
const snackbar = useSnackbarStore()

const step = ref(1)
const showRegister = ref(false)
const showPassword = ref(false)
const loading = ref(false)

const emailFormRef = ref<VForm | null>(null)
const loginFormRef = ref<VForm | null>(null)
const registerFormRef = ref<VForm | null>(null)

const emailForm = reactive({ email: '' })
const loginForm = reactive({ email: '', password: '' })
const registerForm = reactive({ username: '', email: '', password: '' })

const routeLocale = useRouteLocale()
const toPricing = computed(() => ({
  name: 'Pricing' as const,
  params: { locale: routeLocale.value },
}))
const toLogin = computed(() => ({
  name: 'Login' as const,
  params: { locale: routeLocale.value },
}))
const toRegister = computed(() => ({
  name: 'Register' as const,
  params: { locale: routeLocale.value },
}))

const emailRules = computed(() => [
  (v: string) => !!v?.trim() || t('login.emailRequired'),
])

const loginRules = computed(() => [
  (v: string) => !!v?.trim() || t('login.passwordRequired'),
])

const registerUsernameRules = computed(() => [
  (v: string) => !!v?.trim() || t('login.usernameRequired'),
])

const registerEmailRules = computed(() => [
  (v: string) => !!v?.trim() || t('login.emailRequired'),
])

const registerPasswordRules = computed(() => [
  (v: string) => !!v?.trim() || t('login.passwordRequired'),
  (v: string) => (v?.length >= 6) || t('login.passwordMinLength'),
])

function applyRouteMode() {
  if (route.name === 'Register') {
    showRegister.value = true
    step.value = 2
    registerForm.email = emailForm.email
  }
}

onMounted(() => {
  document.documentElement.classList.add('theme-light')
  document.documentElement.classList.remove('theme-dark')
  const lastAccount = localStorage.getItem(LAST_LOGIN_ACCOUNT_KEY)
  if (lastAccount) {
    emailForm.email = lastAccount
  }
  applyRouteMode()
})

watch(() => route.name, () => {
  applyRouteMode()
})

onUnmounted(() => {
  themeStore.setTheme(themeStore.theme)
})

async function goToPasswordStep() {
  const { valid } = await emailFormRef.value?.validate() ?? { valid: false }
  if (valid) {
    loginForm.email = emailForm.email
    step.value = 2
  }
}

function handleForgotEmail() {
  snackbar.info(t('login.forgotEmail'))
}

function startGoogleOAuth() {
  window.location.href = '/api/auth/oauth/google/start'
}

function startWeiboOAuth() {
  window.location.href = '/api/auth/oauth/weibo/start'
}

function startQqOAuth() {
  window.location.href = '/api/auth/oauth/qq/start'
}

function startAlipayOAuth() {
  window.location.href = '/api/auth/oauth/alipay/start'
}

async function handleLogin() {
  const { valid } = await loginFormRef.value?.validate() ?? { valid: false }
  if (!valid) return
  loading.value = true
  try {
    await userStore.login(loginForm.email, loginForm.password)
    localStorage.setItem(LAST_LOGIN_ACCOUNT_KEY, loginForm.email)
    snackbar.success(t('login.welcomeBack'))
    router.push({
      name: 'Home',
      params: { locale: routeLocale.value },
    })
  } catch {
    snackbar.error(t('login.invalidCredentials'))
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  const { valid } = await registerFormRef.value?.validate() ?? { valid: false }
  if (!valid) return
  loading.value = true
  try {
    await userStore.register(
      registerForm.email,
      registerForm.username,
      registerForm.password,
    )
    snackbar.success(t('login.accountCreated'))
    showRegister.value = false
    step.value = 1
    emailForm.email = registerForm.email
    if (route.name === 'Register') {
      router.push({
        name: 'Login',
        params: { locale: routeLocale.value },
      })
    }
  } catch (error: unknown) {
    const axiosError = error as { response?: { data?: { detail?: string } } }
    const detail =
      axiosError.response?.data?.detail || t('login.registerFailed')
    snackbar.error(detail)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f4f8;
}

.login-card {
  width: 100%;
  max-width: 900px;
  background: var(--surface-color);
  border-radius: var(--radius-lg);
  padding: 48px 40px 24px;
  box-shadow: var(--shadow-md);
  display: flex;
  flex-direction: column;
  min-height: 560px;
}

.login-card-inner {
  display: flex;
  gap: 48px;
  flex: 1;
}

.login-branding {
  flex: 0 0 320px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.login-branding .app-logo {
  margin-bottom: 24px;
}

.login-title {
  font-size: 24px;
  font-weight: 400;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.login-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 16px;
}

.login-pricing-link {
  font-size: 14px;
  color: var(--primary-color);
}

.login-pricing-link:hover {
  text-decoration: underline;
}

.login-form-wrap {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.oauth-social-block {
  margin-top: 24px;
  margin-bottom: 8px;
  max-width: 360px;
}

.oauth-other-title {
  color: var(--text-secondary);
  font-size: 12px;
  text-align: center;
  margin-bottom: 14px;
}

.oauth-social-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 20px 24px;
}

.oauth-social-item {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  font: inherit;
  color: var(--text-secondary);
}

.oauth-social-item:hover .oauth-social-icon {
  filter: brightness(1.06);
}

.oauth-social-item--disabled {
  cursor: not-allowed;
  opacity: 0.6;
  pointer-events: none;
}

.oauth-social-item--disabled .oauth-social-icon {
  background: #ccc !important;
}

.oauth-social-item--disabled:hover .oauth-social-icon {
  filter: none;
}

.oauth-social-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.oauth-social-icon--google {
  background: #4285f4;
}

.oauth-social-icon--weibo {
  background: #e6162d;
  color: #fff;
}

.oauth-social-icon--qq {
  background: #12b7f5;
  color: #fff;
}

.oauth-social-icon--alipay {
  padding: 0;
  overflow: hidden;
  background: transparent;
}

.oauth-social-icon-img--alipay {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.login-form {
  max-width: 360px;
}

.account-display {
  margin-bottom: 16px;
  font-size: 14px;
  color: var(--text-primary);
}

.account-email {
  font-weight: 500;
}

.form-links {
  margin-bottom: 12px;
}

.text-link {
  font-size: 14px;
  color: var(--primary-color);
}

.text-link:hover {
  text-decoration: underline;
}

.guest-hint {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
  margin-bottom: 24px;
}

.form-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 24px;
}

.form-actions .login-btn {
  flex-shrink: 0;
}

.login-btn {
  min-width: 100px;
}

.login-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.footer-links {
  display: flex;
  gap: 24px;
}

.footer-link {
  font-size: 12px;
  color: var(--text-secondary);
}

.footer-link:hover {
  color: var(--primary-color);
  text-decoration: underline;
}

@media (max-width: 768px) {
  .login-card-inner {
    flex-direction: column;
    gap: 24px;
  }

  .login-branding {
    flex: none;
    text-align: center;
  }

  .login-form {
    max-width: none;
  }

  .login-footer {
    flex-wrap: wrap;
    gap: 16px;
  }
}
</style>
