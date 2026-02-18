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
          @dblclick="handleViewContent(source)"
        >
          <el-icon size="16" class="source-type-icon">
            <Document v-if="source.type === 'pdf'" />
            <Link v-else-if="source.type === 'web'" />
            <VideoPlay v-else-if="source.type === 'youtube'" />
            <Picture v-else-if="source.type === 'image'" />
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
      @closed="onContentDialogClosed()"
    >
      <div v-if="sourceStore.contentLoading" class="content-loading">
        <el-skeleton :rows="8" animated />
      </div>
      <div v-else-if="sourceStore.currentContent" class="content-viewer">
        <!-- 图片类 source：请求 /api/sources/:id/file 获取 OBS 链接并直接展示 -->
        <div
          v-if="sourceStore.currentContent.file_url"
          class="content-image"
        >
          <div v-if="imageLoading" class="image-loading">
            <el-icon class="is-loading" :size="32">
              <Loading />
            </el-icon>
          </div>
          <img
            v-else-if="imageUrl"
            :src="imageUrl"
            :alt="sourceStore.currentContent.title"
            decoding="async"
            @error="onImageError"
          />
          <el-empty
            v-else-if="imageError"
            description="Failed to load image"
          />
        </div>
        <div
          v-else-if="sourceStore.currentContent.raw_content"
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
import { Document, Link, VideoPlay, Picture, Delete, Loading } from '@element-plus/icons-vue'
import { useSourceStore } from '@/stores/useSourceStore'
import { sourceApi, type Source } from '@/api/source'

defineProps<{ notebookId: string }>()
defineEmits<{ addSource: [] }>()

const sourceStore = useSourceStore()
const showContentDialog = ref(false)
const imageUrl = ref<string | null>(null)
const imageLoading = ref(false)
const imageError = ref(false)
const currentContentId = ref<string | null>(null)

function clearImageUrl() {
  if (imageUrl.value?.startsWith('blob:')) {
    URL.revokeObjectURL(imageUrl.value)
  }
  imageUrl.value = null
  imageError.value = false
}

function onContentDialogClosed() {
  clearImageUrl()
  currentContentId.value = null
  sourceStore.clearContent()
}

/** OBS 链接加载失败时，改用后端流式接口拉取并展示 */
async function onImageError() {
  if (!currentContentId.value) return
  if (imageUrl.value?.startsWith('blob:')) return
  imageLoading.value = true
  try {
    const blob = await sourceApi.getFileStream(currentContentId.value)
    if (imageUrl.value?.startsWith('blob:')) return
    imageUrl.value = URL.createObjectURL(blob)
    imageError.value = false
  } catch {
    imageError.value = true
  } finally {
    imageLoading.value = false
  }
}

/** 请求接口获取 OBS 图片链接并供 img 直接展示；失败时可触发 onImageError 回退到流式接口 */
async function loadImageIfNeeded(content: { id: string; file_url: string | null } | null) {
  clearImageUrl()
  if (!content?.file_url) {
    currentContentId.value = null
    return
  }
  currentContentId.value = content.id
  imageLoading.value = true
  imageError.value = false
  try {
    const { url } = await sourceApi.getFileUrl(content.id)
    imageUrl.value = url
  } catch {
    imageError.value = true
  } finally {
    imageLoading.value = false
  }
}

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

const handleViewContent = async (source: Source) => {
  showContentDialog.value = true
  try {
    if (source.type === 'image') {
      sourceStore.setContentForImage(source)
      await loadImageIfNeeded(sourceStore.currentContent)
    } else {
      const content = await sourceStore.getContent(source.id)
      await loadImageIfNeeded(content ?? null)
    }
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

.content-image {
  display: flex;
  justify-content: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e8eaed;
}

.content-image .image-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 120px;
  color: var(--el-color-primary);
}

.content-image img {
  max-width: 100%;
  height: auto;
  object-fit: contain;
  border-radius: 4px;
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
