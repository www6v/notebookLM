<template>
  <div class="notebook-detail">
    <!-- Header -->
    <header class="nb-header">
      <div class="header-left">
        <el-button text @click="router.push('/')">
          <el-icon size="18">
            <ArrowLeft />
          </el-icon>
        </el-button>
        <h1 class="nb-title">{{ notebookStore.currentNotebook?.title || 'Loading...' }}</h1>
      </div>
      <div class="header-right">
        <el-button text @click="router.push('/settings')">
          <el-icon size="18">
            <Setting />
          </el-icon>
        </el-button>
      </div>
    </header>

    <!-- Three-panel layout -->
    <div class="nb-panels">
      <!-- Left: Sources Panel -->
      <aside class="panel panel-sources" :class="{ collapsed: sourcesCollapsed }">
        <div class="panel-header">
          <h3>Sources</h3>
          <div class="panel-header-actions">
            <el-button size="small" type="primary" @click="showAddSource = true">
              <el-icon class="el-icon--left">
                <Plus />
              </el-icon>
              Add
            </el-button>
            <el-button text size="small" @click="sourcesCollapsed = !sourcesCollapsed">
              <el-icon>
                <Fold v-if="!sourcesCollapsed" />
                <Expand v-else />
              </el-icon>
            </el-button>
          </div>
        </div>
        <div v-if="!sourcesCollapsed" class="panel-body">
          <SourcePanel
            :notebook-id="notebookId"
            @add-source="showAddSource = true"
          />
        </div>
      </aside>

      <!-- Center: Chat Panel -->
      <main class="panel panel-chat">
        <ChatPanel :notebook-id="notebookId" />
      </main>

      <!-- Right: Studio Panel -->
      <aside class="panel panel-studio" :class="{ collapsed: studioCollapsed }">
        <div class="panel-header">
          <h3>Studio</h3>
          <el-button text size="small" @click="studioCollapsed = !studioCollapsed">
            <el-icon>
              <Fold v-if="!studioCollapsed" />
              <Expand v-else />
            </el-icon>
          </el-button>
        </div>
        <div v-if="!studioCollapsed" class="panel-body">
          <StudioPanel :notebook-id="notebookId" />
        </div>
      </aside>
    </div>

    <!-- Add Source Dialog -->
    <el-dialog
      v-model="showAddSource"
      title="Add Source"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-tabs v-model="addSourceTab">
        <el-tab-pane label="Upload File" name="upload">
          <el-upload
            ref="uploadRef"
            drag
            :auto-upload="false"
            :limit="1"
            accept=".pdf,.docx,.doc,.txt,.md"
            :on-change="handleFileChange"
          >
            <el-icon class="el-icon--upload" size="40">
              <UploadFilled />
            </el-icon>
            <div class="el-upload__text">
              Drop file here or <em>click to upload</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                PDF, DOCX, TXT, Markdown files (max 50MB)
              </div>
            </template>
          </el-upload>
        </el-tab-pane>
        <el-tab-pane label="URL" name="url">
          <el-form label-position="top">
            <el-form-item label="URL">
              <el-input
                v-model="sourceUrl"
                placeholder="https://example.com or YouTube URL"
              />
            </el-form-item>
            <el-form-item label="Type">
              <el-select v-model="sourceType" style="width: 100%">
                <el-option label="Web Page" value="web" />
                <el-option label="YouTube Video" value="youtube" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="showAddSource = false">Cancel</el-button>
        <el-button type="primary" :loading="addingSource" @click="handleAddSource">
          Add Source
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, Setting, Plus, Fold, Expand, UploadFilled,
} from '@element-plus/icons-vue'
import { useNotebookStore } from '@/stores/useNotebookStore'
import { useSourceStore } from '@/stores/useSourceStore'
import SourcePanel from '@/components/source/SourcePanel.vue'
import ChatPanel from '@/components/chat/ChatPanel.vue'
import StudioPanel from '@/components/studio/StudioPanel.vue'

const route = useRoute()
const router = useRouter()
const notebookStore = useNotebookStore()
const sourceStore = useSourceStore()

const notebookId = computed(() => route.params.id as string)
const sourcesCollapsed = ref(false)
const studioCollapsed = ref(false)
const showAddSource = ref(false)
const addSourceTab = ref('upload')
const addingSource = ref(false)
const sourceUrl = ref('')
const sourceType = ref('web')
const selectedFile = ref<File | null>(null)

onMounted(async () => {
  await notebookStore.fetchNotebook(notebookId.value)
  await sourceStore.fetchSources(notebookId.value)
})

const handleFileChange = (uploadFile: { raw: File }) => {
  selectedFile.value = uploadFile.raw
}

const handleAddSource = async () => {
  addingSource.value = true
  try {
    if (addSourceTab.value === 'upload' && selectedFile.value) {
      await sourceStore.uploadSource(notebookId.value, selectedFile.value)
      ElMessage.success('File uploaded successfully')
    } else if (addSourceTab.value === 'url' && sourceUrl.value) {
      await sourceStore.addSource(notebookId.value, {
        type: sourceType.value,
        url: sourceUrl.value,
      })
      ElMessage.success('Source added successfully')
    } else {
      ElMessage.warning('Please select a file or enter a URL')
      addingSource.value = false
      return
    }
    showAddSource.value = false
    sourceUrl.value = ''
    selectedFile.value = null
  } catch {
    ElMessage.error('Failed to add source')
  } finally {
    addingSource.value = false
  }
}
</script>

<style scoped>
.notebook-detail {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.nb-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: var(--surface-color);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nb-title {
  font-size: 18px;
  font-weight: 600;
}

.nb-panels {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.panel {
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-color);
  background: var(--surface-color);
  overflow: hidden;
}

.panel:last-child {
  border-right: none;
}

.panel-sources {
  width: 280px;
  flex-shrink: 0;
  transition: width 0.2s;
}

.panel-sources.collapsed {
  width: 48px;
}

.panel-chat {
  flex: 1;
  min-width: 0;
}

.panel-studio {
  width: 320px;
  flex-shrink: 0;
  transition: width 0.2s;
  border-left: 1px solid var(--border-color);
  border-right: none;
}

.panel-studio.collapsed {
  width: 48px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 12px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.panel-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.panel-header-actions {
  display: flex;
  gap: 4px;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
}
</style>
