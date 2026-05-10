<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-card-body">
        <div class="login-card-inner">
          <div class="login-branding">
            <h1 class="login-title">后台管理系统</h1>
            <p class="login-subtitle">仅限管理员登录</p>
          </div>

          <div class="login-form-wrap">
            <v-form
              ref="loginFormRef"
              class="login-form"
              @submit.prevent="handleLogin"
            >
              <v-text-field
                v-model="email"
                label="邮箱"
                placeholder="admin@example.com"
                :rules="[(v: string) => !!v?.trim() || '请输入邮箱']"
                autocomplete="username"
                density="comfortable"
              />
              <v-text-field
                v-model="password"
                label="密码"
                :type="showPassword ? 'text' : 'password'"
                :rules="[(v: string) => !!v?.trim() || '请输入密码']"
                autocomplete="current-password"
                density="comfortable"
                class="mt-2"
              />
              <div class="form-links">
                <v-checkbox
                  v-model="showPassword"
                  label="显示密码"
                  density="compact"
                  hide-details
                />
              </div>
              <div class="form-actions">
                <v-btn
                  color="primary"
                  size="large"
                  :loading="loading"
                  class="login-btn"
                  type="submit"
                  block
                >
                  登录
                </v-btn>
              </div>
            </v-form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import type { VForm } from 'vuetify/components'
import { useUserStore } from '@/stores/useUserStore'
import { useSnackbarStore } from '@/stores/useSnackbarStore'

defineOptions({ name: 'LoginPage' })

const router = useRouter()
const userStore = useUserStore()
const snackbar = useSnackbarStore()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const loginFormRef = ref<VForm | null>(null)

async function handleLogin() {
  const { valid } = await loginFormRef.value?.validate() ?? { valid: false }
  if (!valid) return
  loading.value = true
  try {
    await userStore.login(email.value, password.value)
    if (!userStore.isAdmin) {
      userStore.logout()
      snackbar.error('无管理员权限')
      return
    }
    router.push('/admin')
  } catch {
    snackbar.error('邮箱或密码错误')
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
  max-width: 480px;
  background: #fff;
  border-radius: 12px;
  padding: 48px 40px 40px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
}

.login-card-body {
  display: flex;
  flex-direction: column;
}

.login-card-inner {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.login-branding {
  text-align: center;
}

.login-title {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 8px;
}

.login-subtitle {
  font-size: 14px;
  color: #666;
}

.login-form-wrap {
  display: flex;
  flex-direction: column;
}

.login-form {
  display: flex;
  flex-direction: column;
}

.form-links {
  margin-bottom: 4px;
}

.form-actions {
  margin-top: 16px;
}

.login-btn {
  width: 100%;
}
</style>
