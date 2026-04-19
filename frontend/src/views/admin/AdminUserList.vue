<template>
  <div class="admin-page">
    <header class="admin-header">
      <v-btn
        icon
        variant="text"
        @click="goHome"
      >
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <h1>用户管理</h1>
    </header>

    <main class="admin-main">
      <div class="admin-toolbar">
        <v-btn
          v-if="isTauriDesktop"
          class="desktop-api-entry"
          color="primary"
          variant="outlined"
          @click="goDesktopApi"
        >
          {{ t('admin.navDesktopApi') }}
        </v-btn>
        <v-text-field
          v-model="search"
          placeholder="搜索邮箱或用户名"
          prepend-inner-icon="mdi-magnify"
          density="compact"
          hide-details
          clearable
          class="search-field"
          @update:model-value="debouncedFetch"
        />
        <v-select
          v-model="roleFilter"
          label="角色筛选"
          :items="roleOptions"
          item-title="title"
          item-value="value"
          density="compact"
          hide-details
          clearable
          class="role-select"
          @update:model-value="fetchUsers"
        />
      </div>

      <v-card class="user-table-card">
        <v-table>
          <thead>
            <tr>
              <th>用户名</th>
              <th>邮箱</th>
              <th>角色</th>
              <th>状态</th>
              <th>注册时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="u of users"
              :key="u.id"
            >
              <td>
                <a
                  class="user-link"
                  @click="goUserDetail(u.id)"
                >
                  {{ u.username }}
                </a>
              </td>
              <td>{{ u.email }}</td>
              <td>
                <v-select
                  :model-value="u.role"
                  :items="editableRoles"
                  item-title="title"
                  item-value="value"
                  density="compact"
                  hide-details
                  variant="plain"
                  class="role-inline-select"
                  @update:model-value="(val: string) => handleRoleChange(u.id, val)"
                />
              </td>
              <td>
                <v-switch
                  :model-value="u.is_active"
                  color="success"
                  hide-details
                  density="compact"
                  @update:model-value="(val: boolean | null) => handleToggleActive(u.id, val ?? false)"
                />
              </td>
              <td>{{ formatDate(u.created_at) }}</td>
              <td>
                <v-btn
                  size="small"
                  variant="text"
                  @click="goUserDetail(u.id)"
                >
                  详情
                </v-btn>
              </td>
            </tr>
          </tbody>
        </v-table>

        <div
          v-if="!loading && users.length === 0"
          class="empty-hint"
        >
          暂无匹配用户
        </div>

        <div
          v-if="totalPages > 1"
          class="pagination-row"
        >
          <v-pagination
            v-model="page"
            :length="totalPages"
            :total-visible="7"
            density="compact"
            @update:model-value="fetchUsers"
          />
        </div>
      </v-card>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useRouteLocale } from '@/i18n/useRouteLocale'
import { adminApi } from '@/api/admin'
import { useSnackbarStore } from '@/stores/useSnackbarStore'
import type { UserResponse } from '@/api/auth'
import { isTauriApp } from '@/utils/isTauriApp'

const { t } = useI18n()
const router = useRouter()
const locale = useRouteLocale()
const snackbar = useSnackbarStore()
const isTauriDesktop = isTauriApp()

function goHome() {
  router.push({ name: 'Home', params: { locale: locale.value } })
}

function goUserDetail(id: string) {
  router.push({
    name: 'AdminUserDetail',
    params: { locale: locale.value, id },
  })
}

function goDesktopApi() {
  router.push({
    name: 'AdminDesktop',
    params: { locale: locale.value },
  })
}

const users = ref<UserResponse[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const search = ref('')
const roleFilter = ref('')
const loading = ref(false)

const totalPages = computed(() => Math.ceil(total.value / pageSize))

const roleOptions = [
  { title: '全部', value: '' },
  { title: '免费用户', value: 'free' },
  { title: '付费用户', value: 'paid' },
  { title: '管理员', value: 'admin' },
]

const editableRoles = [
  { title: '免费用户', value: 'free' },
  { title: '付费用户', value: 'paid' },
  { title: '管理员', value: 'admin' },
]

let debounceTimer: ReturnType<typeof setTimeout> | null = null

const debouncedFetch = () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    page.value = 1
    fetchUsers()
  }, 300)
}

const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await adminApi.listUsers({
      page: page.value,
      page_size: pageSize,
      search: search.value,
      role: roleFilter.value,
    })
    users.value = res.users
    total.value = res.total
  } catch {
    snackbar.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const handleRoleChange = async (userId: string, newRole: string) => {
  try {
    await adminApi.updateUser(userId, { role: newRole })
    snackbar.success('角色已更新')
    await fetchUsers()
  } catch {
    snackbar.error('更新角色失败')
  }
}

const handleToggleActive = async (userId: string, active: boolean) => {
  try {
    await adminApi.updateUser(userId, { is_active: active })
    snackbar.success(active ? '账户已启用' : '账户已禁用')
    await fetchUsers()
  } catch {
    snackbar.error('更新状态失败')
  }
}

const formatDate = (dateStr: string) => {
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
}

.admin-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  background: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.admin-header h1 {
  font-size: 20px;
  font-weight: 600;
}

.admin-main {
  max-width: 1100px;
  margin: 32px auto;
  padding: 0 24px;
}

.admin-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.search-field {
  max-width: 320px;
}

.role-select {
  max-width: 160px;
}

.user-table-card {
  border-radius: 12px;
}

.user-link {
  color: rgb(var(--v-theme-primary));
  cursor: pointer;
  font-weight: 500;
}

.user-link:hover {
  text-decoration: underline;
}

.role-inline-select {
  max-width: 120px;
}

.empty-hint {
  text-align: center;
  padding: 32px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.pagination-row {
  display: flex;
  justify-content: center;
  padding: 16px;
}
</style>
