<template>
  <div class="admin-detail-page">
    <header class="admin-header">
      <v-btn
        icon
        variant="text"
        @click="goAdminList"
      >
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <h1>用户详情</h1>
    </header>

    <main class="admin-detail-main">
      <v-card
        v-if="userDetail"
        class="user-info-card"
      >
        <v-card-title class="text-subtitle-1 font-weight-medium">
          基本信息
        </v-card-title>
        <v-card-text>
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">用户名</span>
              <span class="info-value">{{ userDetail.username }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">邮箱</span>
              <span class="info-value">{{ userDetail.email }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">角色</span>
              <v-chip
                :color="roleColor(userDetail.role)"
                size="small"
              >
                {{ roleLabel(userDetail.role) }}
              </v-chip>
            </div>
            <div class="info-item">
              <span class="info-label">状态</span>
              <v-chip
                :color="userDetail.is_active ? 'success' : 'error'"
                size="small"
              >
                {{ userDetail.is_active ? '正常' : '已禁用' }}
              </v-chip>
            </div>
            <div class="info-item">
              <span class="info-label">注册时间</span>
              <span class="info-value">{{ formatDate(userDetail.created_at) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">笔记本数量</span>
              <span class="info-value">{{ userDetail.notebook_count }}</span>
            </div>
          </div>
        </v-card-text>
      </v-card>

      <v-card
        v-if="userDetail && userDetail.notebooks.length > 0"
        class="notebooks-card"
      >
        <v-card-title class="text-subtitle-1 font-weight-medium">
          笔记本列表
        </v-card-title>
        <v-card-text>
          <v-table>
            <thead>
              <tr>
                <th>标题</th>
                <th class="text-center">资源数</th>
                <th>用户上传（按类型）</th>
                <th class="text-center studio-type-col">
                  <div>思维导图</div>
                  <div class="col-sub">成功 · 失败</div>
                </th>
                <th class="text-center studio-type-col">
                  <div>演示文稿</div>
                  <div class="col-sub">成功 · 失败</div>
                </th>
                <th class="text-center studio-type-col">
                  <div>信息图</div>
                  <div class="col-sub">成功 · 失败</div>
                </th>
                <th class="text-center studio-type-col">
                  <div>报告</div>
                  <div class="col-sub">成功 · 失败</div>
                </th>
                <th class="text-center studio-type-col">
                  <div>音频概览</div>
                  <div class="col-sub">成功 · 失败</div>
                </th>
                <th>创建时间</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="nb of userDetail.notebooks"
                :key="nb.id"
              >
                <td>{{ nb.title }}</td>
                <td class="text-center">{{ nb.source_count }}</td>
                <td class="upload-by-type-cell">
                  <template v-if="nb.uploaded_file_total_count > 0">
                    <div class="upload-total text-caption text-medium-emphasis">
                      合计 {{ nb.uploaded_file_total_count }} 个 ·
                      {{ formatBytes(nb.uploaded_file_total_bytes) }}
                    </div>
                    <ul class="upload-type-list">
                      <li
                        v-for="u of nb.uploaded_file_stats"
                        :key="u.source_type"
                      >
                        {{ uploadedTypeLabel(u.source_type) }}
                        {{ u.count }} 个 · {{ formatBytes(u.size_bytes) }}
                      </li>
                    </ul>
                  </template>
                  <span
                    v-else
                    class="text-medium-emphasis"
                  >—</span>
                </td>
                <td class="text-center studio-stat-cell">
                  {{ nb.mind_map_success_count }} · {{ nb.mind_map_failed_count }}
                </td>
                <td class="text-center studio-stat-cell">
                  {{ nb.slide_deck_success_count }} · {{ nb.slide_deck_failed_count }}
                </td>
                <td class="text-center studio-stat-cell">
                  {{ nb.infographic_success_count }} · {{ nb.infographic_failed_count }}
                </td>
                <td class="text-center studio-stat-cell">
                  {{ nb.report_success_count }} · {{ nb.report_failed_count }}
                </td>
                <td class="text-center studio-stat-cell">
                  {{ nb.podcast_overview_success_count }} · {{ nb.podcast_overview_failed_count }}
                </td>
                <td>{{ formatDate(nb.created_at) }}</td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
      </v-card>

      <v-card
        v-if="userDetail && userDetail.notebooks.length === 0"
        class="notebooks-card"
      >
        <v-card-text class="text-center pa-8">
          该用户暂无笔记本
        </v-card-text>
      </v-card>

      <div
        v-if="!userDetail && !loading"
        class="not-found"
      >
        <v-alert type="error">
          用户不存在
        </v-alert>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { adminApi } from '@/api/admin'
import { useSnackbarStore } from '@/stores/useSnackbarStore'
import type { AdminUserDetailResponse } from '@/api/admin'

const router = useRouter()
const route = useRoute()
const snackbar = useSnackbarStore()

function goAdminList() {
  router.push({ name: 'AdminUserList' })
}

const userDetail = ref<AdminUserDetailResponse | null>(null)
const loading = ref(true)

const fetchDetail = async () => {
  loading.value = true
  try {
    userDetail.value = await adminApi.getUserDetail(route.params.id as string)
  } catch {
    snackbar.error('获取用户详情失败')
  } finally {
    loading.value = false
  }
}

const roleColor = (role: string) => {
  const map: Record<string, string> = {
    free: 'grey',
    paid: 'primary',
    admin: 'warning',
  }
  return map[role] || 'grey'
}

const roleLabel = (role: string) => {
  const map: Record<string, string> = {
    free: '免费用户',
    paid: '付费用户',
    admin: '管理员',
  }
  return map[role] || role
}

const formatDate = (dateStr: string) => {
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

const formatBytes = (n: number) => {
  if (n <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let v = n
  let i = 0
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024
    i += 1
  }
  const digits = i === 0 ? 0 : v < 10 ? 1 : v < 100 ? 1 : 0
  return `${v.toFixed(digits)} ${units[i]}`
}

const uploadedTypeLabel = (t: string) => {
  const map: Record<string, string> = {
    pdf: 'PDF',
    docx: 'Word',
    txt: '文本',
    markdown: 'Markdown',
    csv: 'CSV',
    pptx: 'PPT',
    image: '图片',
    audio: '音频',
    video: '视频',
    web: '网页',
    youtube: 'YouTube',
    bilibili: 'B站',
  }
  return map[t] || t
}

onMounted(() => {
  fetchDetail()
})
</script>

<style scoped>
.admin-detail-page {
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

.upload-by-type-cell {
  min-width: 200px;
  max-width: 320px;
  vertical-align: top;
  font-size: 13px;
}

.upload-total {
  margin-bottom: 6px;
  font-weight: 500;
}

.upload-type-list {
  margin: 0;
  padding-left: 18px;
}

.upload-type-list li {
  margin: 2px 0;
}

.admin-detail-main {
  max-width: 1100px;
  margin: 32px auto;
  padding: 0 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.user-info-card,
.notebooks-card {
  border-radius: 12px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  font-weight: 500;
  opacity: 0.6;
  text-transform: uppercase;
}

.info-value {
  font-size: 15px;
  font-weight: 500;
}

.not-found {
  margin-top: 48px;
}

.studio-type-col .col-sub {
  margin-top: 2px;
  font-size: 11px;
  font-weight: 400;
  opacity: 0.65;
}

.studio-stat-cell {
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}
</style>
