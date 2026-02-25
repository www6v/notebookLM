<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <h1 class="logo-text">NotebookLM</h1>
        <p class="login-subtitle">AI-powered research assistant</p>
        <router-link
          to="/pricing"
          class="login-pricing-link"
        >
          查看定价
        </router-link>
      </div>

      <el-tabs v-model="activeTab" class="login-tabs">
        <el-tab-pane label="Sign In" name="login">
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            label-position="top"
            @submit.prevent="handleLogin"
          >
            <el-form-item label="Email" prop="email">
              <el-input
                v-model="loginForm.email"
                type="email"
                placeholder="you@example.com"
                size="large"
              />
            </el-form-item>
            <el-form-item label="Password" prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="Enter password"
                size="large"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="loading"
                class="login-btn"
                native-type="submit"
              >
                Sign In
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="Sign Up" name="register">
          <el-form
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            label-position="top"
            @submit.prevent="handleRegister"
          >
            <el-form-item label="Username" prop="username">
              <el-input
                v-model="registerForm.username"
                placeholder="Choose a username"
                size="large"
              />
            </el-form-item>
            <el-form-item label="Email" prop="email">
              <el-input
                v-model="registerForm.email"
                type="email"
                placeholder="you@example.com"
                size="large"
              />
            </el-form-item>
            <el-form-item label="Password" prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="Create a password"
                size="large"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="loading"
                class="login-btn"
                native-type="submit"
              >
                Create Account
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/useUserStore'

const router = useRouter()
const userStore = useUserStore()
const activeTab = ref('login')
const loading = ref(false)

const loginForm = reactive({ email: '', password: '' })
const registerForm = reactive({ username: '', email: '', password: '' })

const loginRules = {
  email: [{ required: true, message: 'Email is required', trigger: 'blur' }],
  password: [{ required: true, message: 'Password is required', trigger: 'blur' }],
}

const registerRules = {
  username: [{ required: true, message: 'Username is required', trigger: 'blur' }],
  email: [{ required: true, message: 'Email is required', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' }],
}

const handleLogin = async () => {
  loading.value = true
  try {
    await userStore.login(loginForm.email, loginForm.password)
    ElMessage.success('Welcome back!')
    router.push('/')
  } catch {
    ElMessage.error('Invalid email or password')
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  loading.value = true
  try {
    await userStore.register(registerForm.email, registerForm.username, registerForm.password)
    ElMessage.success('Account created! Please sign in.')
    activeTab.value = 'login'
    loginForm.email = registerForm.email
  } catch (error: unknown) {
    const axiosError = error as { response?: { data?: { detail?: string } } }
    const detail = axiosError.response?.data?.detail || 'Registration failed. Please try again.'
    ElMessage.error(detail)
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 420px;
  background: var(--surface-color);
  border-radius: var(--radius-lg);
  padding: 40px;
  box-shadow: var(--shadow-md);
}

.login-header {
  text-align: center;
  margin-bottom: 24px;
}

.logo-text {
  font-size: 28px;
  font-weight: 700;
  color: var(--primary-color);
}

.login-subtitle {
  color: var(--text-secondary);
  margin-top: 4px;
  font-size: 14px;
}

.login-pricing-link {
  display: inline-block;
  margin-top: 8px;
  font-size: 14px;
  color: var(--primary-color);
}

.login-pricing-link:hover {
  text-decoration: underline;
}

.login-btn {
  width: 100%;
}

.login-tabs :deep(.el-tabs__nav-wrap) {
  justify-content: center;
}
</style>
