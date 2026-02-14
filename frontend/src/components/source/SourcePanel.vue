<template>
  <div class="source-panel">
    <div v-if="sourceStore.loading" class="panel-loading">
      <el-skeleton :rows="4" animated />
    </div>

    <div v-else-if="sourceStore.sources.length === 0" class="panel-empty">
      <p>No sources yet</p>
      <el-button size="small" type="primary" @click="$emit('addSource')">
        Add your first source
      </el-button>
    </div>

    <div v-else class="source-list">
      <div
        v-for="source of sourceStore.sources"
        :key="source.id"
        class="source-item"
      >
        <el-checkbox
          :model-value="source.is_active"
          @change="(val: boolean) => sourceStore.toggleSource(source.id, val)"
        />
        <div
          class="source-info"
          :class="{ inactive: !source.is_active }"
          @dblclick="handleViewContent(source.id)"
        >
          <el-icon size="16" class="source-type-icon">
            <Document v-if="source.type === 'pdf'" />
            <Link v-else-if="source.type === 'web'" />
            <VideoPlay v-else-if="source.type === 'youtube'" />
            <Document v-else />
          </el-icon>
          <span class="source-title" :title="source.title">
            {{ source.title }}
          </span>
        </div>
        <el-tag
          v-if="source.status === 'pending'"
          size="small"
          type="warning"
        >
          pending
        </el-tag>
        <el-tag
          v-else-if="source.status === 'processing'"
          size="small"
          type="info"
        >
          processing
        </el-tag>
        <el-button
          text
          size="small"
          class="source-delete"
          @click="handleDelete(source.id)"
        >
          <el-icon size="14">
            <Delete />
          </el-icon>
        </el-button>
      </div>
    </div>

    <!-- Source Content Viewer Dialog -->
    <el-dialog
      v-model="showContentDialog"
      :title="sourceStore.currentContent?.title || 'Source Content'"
      width="700px"
      top="5vh"
      :close-on-click-modal="true"
      @closed="sourceStore.clearContent()"
    >
      <div v-if="sourceStore.contentLoading" class="content-loading">
        <el-skeleton :rows="8" animated />
      </div>
      <div v-else-if="sourceStore.currentContent" class="content-viewer">
        <div
          v-if="sourceStore.currentContent.raw_content"
          class="content-text"
        >
          <pre>{{ sourceStore.currentContent.raw_content }}</pre>
        </div>
        <el-empty v-else description="No content available for this source" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Link, VideoPlay, Delete } from '@element-plus/icons-vue'
import { useSourceStore } from '@/stores/useSourceStore'

defineProps<{ notebookId: string }>()
defineEmits<{ addSource: [] }>()

const sourceStore = useSourceStore()
const showContentDialog = ref(false)

const handleDelete = async (sourceId: string) => {
  try {
    await ElMessageBox.confirm('Remove this source?', 'Remove Source', {
      confirmButtonText: 'Remove',
      type: 'warning',
    })
    await sourceStore.removeSource(sourceId)
    ElMessage.success('Source removed')
  } catch {
    // cancelled
  }
}

const handleViewContent = async (sourceId: string) => {
  showContentDialog.value = true
  try {
    await sourceStore.getContent(sourceId)
  } catch {
    ElMessage.error('Failed to load source content')
  }
}
</script>

<style scoped>
.source-panel {
  padding: 8px;
}

.panel-loading,
.panel-empty {
  padding: 20px 12px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 13px;
}

.panel-empty p {
  margin-bottom: 12px;
}

.source-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.source-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 6px;
  transition: background 0.15s;
}

.source-item:hover {
  background: #f1f3f4;
}

.source-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  cursor: pointer;
}

.source-info.inactive {
  opacity: 0.5;
}

.source-type-icon {
  color: var(--text-secondary);
  flex-shrink: 0;
}

.source-title {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-delete {
  opacity: 0;
  transition: opacity 0.15s;
}

.source-item:hover .source-delete {
  opacity: 1;
}

.content-loading {
  padding: 16px 0;
}

.content-viewer {
  max-height: 70vh;
  overflow-y: auto;
}

.content-text {
  background: #f8f9fa;
  border: 1px solid #e8eaed;
  border-radius: 8px;
  padding: 16px;
}

.content-text pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'SF Mono', 'Menlo', 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #333;
}
</style>
