<template>
  <div class="home-page">
    <header class="home-header">
      <div class="header-left">
        <h1 class="logo">NotebookLM</h1>
      </div>
      <div class="header-right">
        <el-button
          text
          @click="router.push('/pricing')"
        >
          <span class="header-btn-label">定价</span>
        </el-button>
        <el-button
          text
          @click="router.push('/settings')"
        >
          <el-icon size="20">
            <Setting />
          </el-icon>
          <span class="header-btn-label">设置</span>
        </el-button>
        <el-button text @click="handleLogout">
          <el-icon size="20">
            <SwitchButton />
          </el-icon>
        </el-button>
      </div>
    </header>

    <main class="home-main">
      <div class="home-title-row">
        <h2>我的笔记本</h2>
        <div class="home-actions">
          <div class="view-toggle">
            <button
              type="button"
              class="view-toggle-btn"
              :class="{ active: viewMode === 'grid' }"
              aria-label="网格视图"
              @click="viewMode = 'grid'"
            >
              <el-icon size="18">
                <Grid />
              </el-icon>
              <el-icon v-if="viewMode === 'grid'" class="view-check" size="14">
                <Check />
              </el-icon>
            </button>
            <button
              type="button"
              class="view-toggle-btn"
              :class="{ active: viewMode === 'list' }"
              aria-label="列表视图"
              @click="viewMode = 'list'"
            >
              <el-icon size="18">
                <List />
              </el-icon>
              <el-icon v-if="viewMode === 'list'" class="view-check" size="14">
                <Check />
              </el-icon>
            </button>
          </div>
          <el-select
            v-model="sortBy"
            class="sort-select"
            placeholder="排序"
            size="default"
          >
            <el-option label="最近" value="recent" />
            <el-option label="创建时间" value="created" />
            <el-option label="标题" value="title" />
          </el-select>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon class="el-icon--left">
              <Plus />
            </el-icon>
            新建
          </el-button>
        </div>
      </div>

      <div v-if="notebookStore.loading" class="loading-state">
        <el-skeleton :rows="3" animated />
      </div>

      <div v-else-if="notebookStore.notebooks.length === 0" class="empty-state">
        <el-empty description="还没有笔记本，点击「新建」开始创建" />
      </div>

      <template v-else>
        <!-- 网格视图 -->
        <div v-show="viewMode === 'grid'" class="notebook-grid">
          <div
            class="notebook-card notebook-card--new"
            @click="showCreateDialog = true"
          >
            <div class="card-new-icon">
              <el-icon size="32">
                <Plus />
              </el-icon>
            </div>
            <span class="card-new-label">新建笔记本</span>
          </div>
          <div
            v-for="nb of sortedNotebooks"
            :key="nb.id"
            class="notebook-card"
            @click="router.push(`/notebook/${nb.id}`)"
          >
            <div class="card-emoji">{{ getCardEmoji(nb) }}</div>
            <h3 class="card-title">{{ nb.title }}</h3>
            <div class="card-meta">
              <span>{{ formatDate(nb.updated_at) }}</span>
              <span>{{ nb.source_count }}个来源</span>
            </div>
            <div class="card-actions" @click.stop>
              <el-dropdown trigger="click">
                <el-button text size="small" class="card-more-btn">
                  <el-icon>
                    <MoreFilled />
                  </el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="openEditDialog(nb)">
                      重命名
                    </el-dropdown-item>
                    <el-dropdown-item @click="handleDelete(nb.id)">
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </div>

        <!-- 列表视图 -->
        <div v-show="viewMode === 'list'" class="notebook-list-wrap">
          <table class="notebook-table">
            <thead>
              <tr>
                <th>标题</th>
                <th>来源</th>
                <th>创建日期</th>
                <th>角色</th>
                <th class="th-actions" />
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="nb of sortedNotebooks"
                :key="nb.id"
                class="notebook-row"
                @click="router.push(`/notebook/${nb.id}`)"
              >
                <td class="col-title">
                  <span class="row-emoji">{{ getCardEmoji(nb) }}</span>
                  {{ nb.title }}
                </td>
                <td class="col-sources">{{ nb.source_count }}个来源</td>
                <td class="col-date">{{ formatDateCn(nb.created_at) }}</td>
                <td class="col-role">Owner</td>
                <td class="col-actions" @click.stop>
                  <el-dropdown trigger="click">
                    <el-button text size="small">
                      <el-icon>
                        <MoreFilled />
                      </el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="openEditDialog(nb)">
                          重命名
                        </el-dropdown-item>
                        <el-dropdown-item @click="handleDelete(nb.id)">
                          删除
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </main>

    <!-- Create Dialog -->
    <el-dialog
      v-model="showCreateDialog"
      title="新建笔记本"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form label-position="top">
        <el-form-item label="标题">
          <el-input
            v-model="newNotebook.title"
            placeholder="我的研究项目"
            autofocus
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="newNotebook.description"
            type="textarea"
            :rows="3"
            placeholder="这个笔记本是关于什么的？"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- Edit Dialog -->
    <el-dialog
      v-model="showEditDialog"
      title="重命名笔记本"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form label-position="top">
        <el-form-item label="标题">
          <el-input v-model="editNotebook.title" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="editNotebook.description"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Setting,
  SwitchButton,
  MoreFilled,
  Grid,
  List,
  Check,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/useUserStore'
import { useNotebookStore } from '@/stores/useNotebookStore'
import type { Notebook as NotebookType } from '@/api/notebook'

const VIEW_MODE_KEY = 'notebook-list-view'

const router = useRouter()
const userStore = useUserStore()
const notebookStore = useNotebookStore()

const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const creating = ref(false)
const newNotebook = reactive({ title: '', description: '' })
const editNotebook = reactive({ id: '', title: '', description: '' })

const viewMode = ref<'grid' | 'list'>('grid')
const sortBy = ref<'recent' | 'created' | 'title'>('recent')

function loadViewMode() {
  const saved = localStorage.getItem(VIEW_MODE_KEY) as 'grid' | 'list' | null
  if (saved === 'grid' || saved === 'list') {
    viewMode.value = saved
  }
}

watch(
  viewMode,
  (val) => {
    localStorage.setItem(VIEW_MODE_KEY, val)
  },
  { immediate: false },
)

onMounted(() => {
  loadViewMode()
  notebookStore.fetchNotebooks()
})

const sortedNotebooks = computed(() => {
  const list = [...notebookStore.notebooks]
  if (sortBy.value === 'recent') {
    list.sort(
      (a, b) =>
        new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
    )
  } else if (sortBy.value === 'created') {
    list.sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    )
  } else {
    list.sort((a, b) => a.title.localeCompare(b.title, 'zh-CN'))
  }
  return list
})

const EMOJI_LIST = ['🧠', '😊', '💡', '🦩', '🧬', '💨', '🥮', '📁', '🔧', '🔍', '🤖', '😴']

function getCardEmoji(nb: NotebookType) {
  const idx = Math.abs(hashCode(nb.id)) % EMOJI_LIST.length
  return EMOJI_LIST[idx]
}

function hashCode(str: string) {
  let h = 0
  for (let i = 0; i < str.length; i++) {
    h = (h << 5) - h + str.charCodeAt(i)
    h |= 0
  }
  return h
}

const handleCreate = async () => {
  if (!newNotebook.title.trim()) {
    ElMessage.warning('Title is required')
    return
  }
  creating.value = true
  try {
    const nb = await notebookStore.createNotebook(newNotebook.title, newNotebook.description)
    showCreateDialog.value = false
    newNotebook.title = ''
    newNotebook.description = ''
    router.push(`/notebook/${nb.id}`)
  } catch {
    ElMessage.error('Failed to create notebook')
  } finally {
    creating.value = false
  }
}

const openEditDialog = (nb: NotebookType) => {
  editNotebook.id = nb.id
  editNotebook.title = nb.title
  editNotebook.description = nb.description
  showEditDialog.value = true
}

const handleEdit = async () => {
  try {
    await notebookStore.updateNotebook(editNotebook.id, {
      title: editNotebook.title,
      description: editNotebook.description,
    })
    showEditDialog.value = false
    ElMessage.success('Notebook updated')
  } catch {
    ElMessage.error('Failed to update')
  }
}

const handleDelete = async (id: string) => {
  try {
    await ElMessageBox.confirm('Delete this notebook and all its contents?', 'Delete Notebook', {
      confirmButtonText: 'Delete',
      cancelButtonText: 'Cancel',
      type: 'warning',
    })
    await notebookStore.deleteNotebook(id)
    ElMessage.success('Notebook deleted')
  } catch {
    // cancelled
  }
}

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}

const formatDate = (dateStr: string) => {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

const formatDateCn = (dateStr: string) => {
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: var(--home-bg);
  color: var(--home-text);
}

.home-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: var(--home-surface);
  border-bottom: 1px solid var(--home-border);
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-left .logo {
  font-size: 22px;
  font-weight: 700;
  color: var(--home-primary);
}

.header-right {
  display: flex;
  gap: 4px;
  align-items: center;
}

.header-btn-label {
  margin-left: 4px;
}

.home-main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 24px;
}

.home-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.home-title-row h2 {
  font-size: 24px;
  font-weight: 600;
  color: var(--home-text);
}

.home-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.view-toggle {
  display: inline-flex;
  background: var(--home-surface);
  border: 1px solid var(--home-border);
  border-radius: var(--radius);
  overflow: hidden;
}

.view-toggle-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 12px;
  background: transparent;
  border: none;
  color: var(--home-text-secondary);
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.view-toggle-btn:hover {
  color: var(--home-text);
  background: rgba(255, 255, 255, 0.06);
}

.view-toggle-btn.active {
  background: rgba(255, 255, 255, 0.1);
  color: var(--home-text);
}

.view-check {
  margin-left: 2px;
  color: var(--home-primary);
}

.sort-select {
  width: 100px;
}

.sort-select :deep(.el-input__wrapper) {
  background: var(--home-surface);
  border-color: var(--home-border);
  color: var(--home-text);
}

.notebook-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.notebook-card {
  position: relative;
  padding: 20px;
  background: var(--home-surface);
  border: 1px solid var(--home-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}

.notebook-card:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: var(--home-text-secondary);
}

.card-emoji {
  font-size: 32px;
  line-height: 1;
  margin-bottom: 12px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--home-text);
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--home-text-secondary);
}

.card-actions {
  position: absolute;
  top: 12px;
  right: 8px;
}

.card-more-btn {
  color: var(--home-text-secondary);
}

.card-more-btn:hover {
  color: var(--home-text);
}

.notebook-card--new {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 160px;
}

.card-new-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--home-text-secondary);
  margin-bottom: 12px;
}

.notebook-card--new:hover .card-new-icon {
  background: rgba(255, 255, 255, 0.12);
  color: var(--home-text);
}

.card-new-label {
  font-size: 14px;
  color: var(--home-text-secondary);
}

.notebook-list-wrap {
  background: var(--home-surface);
  border: 1px solid var(--home-border);
  border-radius: var(--radius);
  overflow: hidden;
}

.notebook-table {
  width: 100%;
  border-collapse: collapse;
}

.notebook-table th,
.notebook-table td {
  padding: 14px 16px;
  text-align: left;
  border-bottom: 1px solid var(--home-border);
}

.notebook-table th {
  font-size: 13px;
  font-weight: 500;
  color: var(--home-text-secondary);
}

.notebook-table tbody tr:last-child td {
  border-bottom: none;
}

.notebook-row {
  cursor: pointer;
  transition: background 0.2s;
}

.notebook-row:hover {
  background: rgba(255, 255, 255, 0.04);
}

.col-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--home-text);
  font-weight: 500;
}

.row-emoji {
  font-size: 18px;
  flex-shrink: 0;
}

.col-sources,
.col-date,
.col-role {
  color: var(--home-text-secondary);
  font-size: 13px;
}

.col-role {
  font-size: 13px;
}

.th-actions,
.col-actions {
  width: 48px;
  text-align: right;
}

.col-actions .el-button {
  color: var(--home-text-secondary);
}

.col-actions .el-button:hover {
  color: var(--home-text);
}

.loading-state,
.empty-state {
  margin-top: 60px;
}
</style>
