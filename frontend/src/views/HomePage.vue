<template>
  <div class="home-page">
    <header class="home-header">
      <div class="header-left">
        <h1 class="logo">NotebookLM</h1>
      </div>
      <div class="header-right">
        <el-button text @click="router.push('/settings')">
          <el-icon size="20">
            <Setting />
          </el-icon>
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
        <h2>My Notebooks</h2>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon class="el-icon--left">
            <Plus />
          </el-icon>
          Create Notebook
        </el-button>
      </div>

      <div v-if="notebookStore.loading" class="loading-state">
        <el-skeleton :rows="3" animated />
      </div>

      <div v-else-if="notebookStore.notebooks.length === 0" class="empty-state">
        <el-empty description="No notebooks yet. Create one to get started!" />
      </div>

      <div v-else class="notebook-grid">
        <div
          v-for="nb of notebookStore.notebooks"
          :key="nb.id"
          class="notebook-card"
          @click="router.push(`/notebook/${nb.id}`)"
        >
          <div class="card-icon">
            <el-icon size="32" color="#4285f4">
              <Notebook />
            </el-icon>
          </div>
          <div class="card-body">
            <h3 class="card-title">{{ nb.title }}</h3>
            <p class="card-desc">{{ nb.description || 'No description' }}</p>
            <div class="card-meta">
              <span>{{ nb.source_count }} sources</span>
              <span>{{ formatDate(nb.updated_at) }}</span>
            </div>
          </div>
          <div class="card-actions" @click.stop>
            <el-dropdown trigger="click">
              <el-button text size="small">
                <el-icon>
                  <MoreFilled />
                </el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="openEditDialog(nb)">
                    Rename
                  </el-dropdown-item>
                  <el-dropdown-item @click="handleDelete(nb.id)">
                    Delete
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </main>

    <!-- Create Dialog -->
    <el-dialog
      v-model="showCreateDialog"
      title="Create New Notebook"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form label-position="top">
        <el-form-item label="Title">
          <el-input
            v-model="newNotebook.title"
            placeholder="My Research Project"
            autofocus
          />
        </el-form-item>
        <el-form-item label="Description">
          <el-input
            v-model="newNotebook.description"
            type="textarea"
            :rows="3"
            placeholder="What is this notebook about?"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">Cancel</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">
          Create
        </el-button>
      </template>
    </el-dialog>

    <!-- Edit Dialog -->
    <el-dialog
      v-model="showEditDialog"
      title="Rename Notebook"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form label-position="top">
        <el-form-item label="Title">
          <el-input v-model="editNotebook.title" />
        </el-form-item>
        <el-form-item label="Description">
          <el-input
            v-model="editNotebook.description"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">Cancel</el-button>
        <el-button type="primary" @click="handleEdit">Save</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Setting, SwitchButton, MoreFilled, Notebook } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/useUserStore'
import { useNotebookStore } from '@/stores/useNotebookStore'
import type { Notebook as NotebookType } from '@/api/notebook'

const router = useRouter()
const userStore = useUserStore()
const notebookStore = useNotebookStore()

const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const creating = ref(false)
const newNotebook = reactive({ title: '', description: '' })
const editNotebook = reactive({ id: '', title: '', description: '' })

onMounted(() => {
  notebookStore.fetchNotebooks()
})

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
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
}

.home-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: var(--surface-color);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-left .logo {
  font-size: 22px;
  font-weight: 700;
  color: var(--primary-color);
}

.header-right {
  display: flex;
  gap: 4px;
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
}

.notebook-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.notebook-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 20px;
  cursor: pointer;
  transition: box-shadow 0.2s, border-color 0.2s;
}

.notebook-card:hover {
  box-shadow: var(--shadow-sm);
  border-color: var(--primary-color);
}

.card-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e8f0fe;
  border-radius: var(--radius);
}

.card-body {
  flex: 1;
  min-width: 0;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-secondary);
}

.card-actions {
  flex-shrink: 0;
}

.loading-state,
.empty-state {
  margin-top: 60px;
}
</style>
