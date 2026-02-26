<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-card-inner">
        <div class="login-branding">
          <h1 class="logo-text">NotebookLM</h1>
          <h2 class="login-title">{{ t('login.title') }}</h2>
          <p class="login-subtitle">
            {{ t('login.subtitle') }}
          </p>
          <router-link
            to="/pricing"
            class="login-pricing-link"
          >
            {{ t('common.viewPricing') }}
          </router-link>
        </div>

        <div class="login-form-wrap">
          <!-- Step 1: Email or phone -->
          <template v-if="step === 1">
            <el-form
              ref="emailFormRef"
              :model="emailForm"
              :rules="emailRules"
              label-position="top"
              class="login-form"
              @submit.prevent="goToPasswordStep"
            >
              <el-form-item prop="email">
                <el-input
                  v-model="emailForm.email"
                  type="text"
                  :placeholder="t('login.emailOrPhone')"
                  size="large"
                  autocomplete="username"
                />
              </el-form-item>
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
                <a
                  href="#"
                  class="text-link"
                  @click.prevent="showRegisterForm"
                >
                  {{ t('login.createAccount') }}
                </a>
                <el-button
                  type="primary"
                  size="large"
                  class="login-btn"
                  native-type="submit"
                >
                  {{ t('login.next') }}
                </el-button>
              </div>
            </el-form>
          </template>

          <!-- Step 2: Password -->
          <template v-else-if="step === 2 && !showRegister">
            <el-form
              ref="loginFormRef"
              :model="loginForm"
              :rules="loginRules"
              label-position="top"
              class="login-form"
              @submit.prevent="handleLogin"
            >
              <div class="account-display">
                <span class="account-email">{{ emailForm.email }}</span>
              </div>
              <el-form-item prop="password">
                <el-input
                  v-model="loginForm.password"
                  :type="showPassword ? 'text' : 'password'"
                  :placeholder="t('login.enterPassword')"
                  size="large"
                  autocomplete="current-password"
                />
              </el-form-item>
              <div class="form-links">
                <el-checkbox v-model="showPassword">
                  {{ t('login.showPassword') }}
                </el-checkbox>
              </div>
              <div class="form-actions">
                <a
                  href="#"
                  class="text-link"
                  @click.prevent="step = 1"
                >
                  {{ t('login.tryAnotherWay') }}
                </a>
                <el-button
                  type="primary"
                  size="large"
                  :loading="loading"
                  class="login-btn"
                  native-type="submit"
                >
                  {{ t('login.next') }}
                </el-button>
              </div>
            </el-form>
          </template>

          <!-- Register -->
          <template v-else>
            <el-form
              ref="registerFormRef"
              :model="registerForm"
              :rules="registerRules"
              label-position="top"
              class="login-form"
              @submit.prevent="handleRegister"
            >
              <el-form-item
                :label="t('login.emailOrPhone')"
                prop="email"
              >
                <el-input
                  v-model="registerForm.email"
                  type="email"
                  placeholder="you@example.com"
                  size="large"
                />
              </el-form-item>
              <el-form-item
                :label="t('login.username')"
                prop="username"
              >
                <el-input
                  v-model="registerForm.username"
                  :placeholder="t('login.username')"
                  size="large"
                />
              </el-form-item>
              <el-form-item
                :label="t('login.createPassword')"
                prop="password"
              >
                <el-input
                  v-model="registerForm.password"
                  type="password"
                  :placeholder="t('login.createPassword')"
                  size="large"
                  show-password
                />
              </el-form-item>
              <div class="form-actions">
                <a
                  href="#"
                  class="text-link"
                  @click.prevent="showRegister = false; step = 1"
                >
                  {{ t('login.tryAnotherWay') }}
                </a>
                <el-button
                  type="primary"
                  size="large"
                  :loading="loading"
                  class="login-btn"
                  native-type="submit"
                >
                  {{ t('login.createAccount') }}
                </el-button>
              </div>
            </el-form>
          </template>
        </div>
      </div>

      <footer class="login-footer">
        <div class="footer-lang">
          <el-select
            :model-value="currentLocale"
            class="lang-select"
            popper-class="lang-select-popper"
            @change="onLocaleChange"
          >
            <el-option
              value="en"
              :label="t('language.en')"
            />
            <el-option
              value="zh-CN"
              :label="t('language.zh')"
            />
          </el-select>
        </div>
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { useUserStore, LAST_LOGIN_ACCOUNT_KEY } from '@/stores/useUserStore'
import { getLocale, setLocale } from '@/plugins/i18n'
import type { FormInstance, FormRules } from 'element-plus'

defineOptions({
  name: 'LoginPage',
})

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()

const step = ref(1)
const showRegister = ref(false)
const showPassword = ref(false)
const loading = ref(false)

const emailFormRef = ref<FormInstance>()
const loginFormRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()

const emailForm = reactive({ email: '' })
const loginForm = reactive({ email: '', password: '' })
const registerForm = reactive({ username: '', email: '', password: '' })

const currentLocale = computed(() => getLocale())

const emailRules: FormRules = {
  email: [{ required: true, message: () => t('login.emailRequired'), trigger: 'blur' }],
}

const loginRules: FormRules = {
  password: [{ required: true, message: () => t('login.passwordRequired'), trigger: 'blur' }],
}

const registerRules: FormRules = {
  username: [{ required: true, message: () => t('login.usernameRequired'), trigger: 'blur' }],
  email: [{ required: true, message: () => t('login.emailRequired'), trigger: 'blur' }],
  password: [
    { required: true, min: 6, message: () => t('login.passwordMinLength'), trigger: 'blur' },
  ],
}

onMounted(() => {
  const lastAccount = localStorage.getItem(LAST_LOGIN_ACCOUNT_KEY)
  if (lastAccount) {
    emailForm.email = lastAccount
  }
})

function onLocaleChange(locale: string) {
  setLocale(locale === 'zh-CN' ? 'zh-CN' : 'en')
}

function goToPasswordStep() {
  emailFormRef.value?.validate((valid) => {
    if (valid) {
      loginForm.email = emailForm.email
      step.value = 2
    }
  })
}

function showRegisterForm() {
  showRegister.value = true
  registerForm.email = emailForm.email
}

function handleForgotEmail() {
  ElMessage.info(t('login.forgotEmail'))
}

async function handleLogin() {
  loginFormRef.value?.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await userStore.login(loginForm.email, loginForm.password)
      localStorage.setItem(LAST_LOGIN_ACCOUNT_KEY, loginForm.email)
      ElMessage.success(t('login.welcomeBack'))
      router.push('/')
    } catch {
      ElMessage.error(t('login.invalidCredentials'))
    } finally {
      loading.value = false
    }
  })
}

async function handleRegister() {
  registerFormRef.value?.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await userStore.register(
        registerForm.email,
        registerForm.username,
        registerForm.password,
      )
      ElMessage.success(t('login.accountCreated'))
      showRegister.value = false
      step.value = 1
      emailForm.email = registerForm.email
    } catch (error: unknown) {
      const axiosError = error as { response?: { data?: { detail?: string } } }
      const detail =
        axiosError.response?.data?.detail || t('login.registerFailed')
      ElMessage.error(detail)
    } finally {
      loading.value = false
    }
  })
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

.logo-text {
  font-size: 28px;
  font-weight: 700;
  color: var(--primary-color);
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
  justify-content: space-between;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.footer-lang :deep(.el-select .el-input__wrapper) {
  box-shadow: none;
  padding-left: 0;
  min-height: 32px;
}

.lang-select {
  width: 140px;
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
