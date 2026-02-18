<template>
  <div class="studio-panel">
    <el-tabs v-model="studioStore.activeTab" class="studio-tabs">
      <!-- Notes Tab -->
      <el-tab-pane label="Notes" name="notes">
        <div class="tab-toolbar">
          <el-button size="small" type="primary" @click="createNote">
            <el-icon class="el-icon--left">
              <Plus />
            </el-icon>
            New Note
          </el-button>
        </div>
        <div v-if="notes.length === 0" class="tab-empty">
          <p>No notes yet. Create one or save from chat.</p>
        </div>
        <div v-else class="notes-list">
          <div
            v-for="note of notes"
            :key="note.id"
            class="note-card"
            @click="editingNote = note"
          >
            <div class="note-header">
              <el-icon
                v-if="note.is_pinned"
                size="14"
                color="#f4b400"
                class="pin-icon"
              >
                <Star />
              </el-icon>
              <span class="note-title">{{ note.title }}</span>
            </div>
            <p class="note-preview">{{ note.content.substring(0, 100) }}</p>
            <div class="note-meta">
              {{ formatDate(note.updated_at) }}
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- Mind Map Tab -->
      <el-tab-pane label="Mind Map" name="mindmap">
        <div class="tab-toolbar">
          <el-button
            size="small"
            type="primary"
            :loading="studioStore.loading"
            :disabled="sourceStore.activeSourceIds.length === 0 || studioStore.loading"
            @click="handleGenerateMindMap"
          >
            Generate Mind Map
          </el-button>
          <span v-if="sourceStore.activeSourceIds.length === 0" class="toolbar-hint">
            Please check sources first
          </span>
          <span v-else class="toolbar-hint">
            {{ sourceStore.activeSourceIds.length }} source(s) selected
          </span>
        </div>
        <div v-if="studioStore.mindMaps.length === 0" class="tab-empty">
          <p>
            Generate a mind map from your sources to visualize key concepts and relationships.
          </p>
        </div>
        <div v-else class="mindmap-list">
          <div
            v-for="mm of studioStore.mindMaps"
            :key="mm.id"
            class="mindmap-card"
            @dblclick="openMindMapDialog(mm)"
          >
            <el-icon size="24" color="#4285f4">
              <Share />
            </el-icon>
            <div class="mindmap-card-info">
              <span class="mindmap-card-title">{{ mm.title }}</span>
              <span class="mindmap-card-meta">{{ formatDate(mm.created_at) }}</span>
            </div>
            <el-button
              text
              size="small"
              class="mindmap-delete"
              @click.stop="handleDeleteMindMap(mm.id)"
            >
              <el-icon size="14">
                <Delete />
              </el-icon>
            </el-button>
          </div>
        </div>
      </el-tab-pane>

      <!-- Slides Tab -->
      <el-tab-pane label="Slides" name="slides">
        <div class="tab-toolbar">
          <el-button
            size="small"
            type="primary"
            :loading="studioStore.loading"
            @click="generateSlides"
          >
            Generate Slides
          </el-button>
        </div>
        <div v-if="studioStore.slideDecks.length === 0" class="tab-empty">
          <p>Generate a slide deck from your sources. Choose a theme and let AI create presentation slides.</p>
        </div>
        <div v-else class="slides-list">
          <div
            v-for="deck of studioStore.slideDecks"
            :key="deck.id"
            class="slide-card"
            :title="deck.file_path ? 'Double-click to open PDF' : ''"
            @dblclick="openSlidePdf(deck)"
          >
            <el-icon size="24" color="#4285f4">
              <Monitor />
            </el-icon>
            <div class="slide-info">
              <span class="slide-title">{{ deck.title }}</span>
              <span class="slide-meta">Theme: {{ deck.theme }} | {{ deck.status }}</span>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- Infographic Tab -->
      <el-tab-pane label="Infographic" name="infographic">
        <div class="tab-toolbar">
          <el-select v-model="infographicTemplate" size="small" style="width: 140px; margin-right: 8px">
            <el-option label="Timeline" value="timeline" />
            <el-option label="Comparison" value="comparison" />
            <el-option label="Process" value="process" />
            <el-option label="Statistics" value="statistics" />
            <el-option label="Hierarchy" value="hierarchy" />
          </el-select>
          <el-button
            size="small"
            type="primary"
            :loading="studioStore.loading"
            @click="generateInfographic"
          >
            Generate
          </el-button>
        </div>
        <div v-if="studioStore.infographics.length === 0" class="tab-empty">
          <p>Generate infographics from your sources. Choose a template type to visualize key data.</p>
        </div>
        <div v-else class="infographic-list">
          <div
            v-for="info of studioStore.infographics"
            :key="info.id"
            class="infographic-card"
          >
            <el-icon size="24" color="#34a853">
              <PictureFilled />
            </el-icon>
            <div class="infographic-info">
              <span class="infographic-title">{{ info.title }}</span>
              <span class="infographic-meta">{{ info.template_type }} | {{ info.status }}</span>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- Reports Tab -->
      <el-tab-pane label="Reports" name="reports">
        <div class="tab-empty">
          <p>Reports generation (FAQ, Study Guide, Briefing) coming in a future update.</p>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- Mind Map Preview Dialog -->
    <el-dialog
      v-model="showMindMapDialog"
      :title="previewMindMap?.title || 'Mind Map'"
      width="90%"
      top="5vh"
      destroy-on-close
    >
      <MindMapViewer
        v-if="previewMindMap"
        :graph-data="previewMindMap.graph_data"
        :title="previewMindMap.title"
        fullscreen
      />
    </el-dialog>

    <!-- Note Edit Dialog -->
    <el-dialog
      v-model="showNoteDialog"
      :title="editingNote ? 'Edit Note' : 'New Note'"
      width="560px"
    >
      <el-form label-position="top">
        <el-form-item label="Title">
          <el-input v-model="noteForm.title" placeholder="Note title" />
        </el-form-item>
        <el-form-item label="Content">
          <el-input
            v-model="noteForm.content"
            type="textarea"
            :rows="8"
            placeholder="Write your note..."
          />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="noteForm.is_pinned">Pin this note</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button v-if="editingNote" type="danger" text @click="deleteNote">Delete</el-button>
        <el-button @click="showNoteDialog = false">Cancel</el-button>
        <el-button type="primary" @click="saveNote">Save</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Star, Share, Monitor, PictureFilled, Delete,
} from '@element-plus/icons-vue'
import { useStudioStore } from '@/stores/useStudioStore'
import { useSourceStore } from '@/stores/useSourceStore'
import { noteApi } from '@/api/note'
import type { Note } from '@/api/note'
import { studioApi } from '@/api/studio'
import type { MindMapData, SlideDeckData } from '@/api/studio'
import MindMapViewer from './MindMapViewer.vue'

const props = defineProps<{ notebookId: string }>()

const studioStore = useStudioStore()
const sourceStore = useSourceStore()
const notes = ref<Note[]>([])
const editingNote = ref<Note | null>(null)
const showNoteDialog = ref(false)
const showMindMapDialog = ref(false)
const previewMindMap = ref<MindMapData | null>(null)
const infographicTemplate = ref('timeline')
const noteForm = reactive({ title: '', content: '', is_pinned: false })

onMounted(async () => {
  await fetchNotes()
  await studioStore.fetchMindMaps(props.notebookId)
  await studioStore.fetchSlideDecks(props.notebookId)
  await studioStore.fetchInfographics(props.notebookId)
})

watch(editingNote, (note) => {
  if (note) {
    noteForm.title = note.title
    noteForm.content = note.content
    noteForm.is_pinned = note.is_pinned
    showNoteDialog.value = true
  }
})

const fetchNotes = async () => {
  notes.value = await noteApi.list(props.notebookId)
}

const createNote = () => {
  editingNote.value = null
  noteForm.title = ''
  noteForm.content = ''
  noteForm.is_pinned = false
  showNoteDialog.value = true
}

const saveNote = async () => {
  try {
    if (editingNote.value) {
      await noteApi.update(editingNote.value.id, noteForm)
    } else {
      await noteApi.create(props.notebookId, noteForm)
    }
    showNoteDialog.value = false
    editingNote.value = null
    await fetchNotes()
    ElMessage.success('Note saved')
  } catch {
    ElMessage.error('Failed to save note')
  }
}

const deleteNote = async () => {
  if (!editingNote.value) return
  try {
    await noteApi.remove(editingNote.value.id)
    showNoteDialog.value = false
    editingNote.value = null
    await fetchNotes()
    ElMessage.success('Note deleted')
  } catch {
    ElMessage.error('Failed to delete note')
  }
}

const handleGenerateMindMap = async () => {
  if (studioStore.loading) return
  const ids = sourceStore.activeSourceIds
  if (ids.length === 0) {
    ElMessage.warning('Please check at least one source')
    return
  }
  try {
    await studioStore.generateMindMap(props.notebookId, ids)
    ElMessage.success('Mind map generated')
  } catch {
    ElMessage.error('Failed to generate mind map')
  }
}

const openMindMapDialog = (mm: MindMapData) => {
  previewMindMap.value = mm
  showMindMapDialog.value = true
}

const handleDeleteMindMap = async (mindmapId: string) => {
  try {
    await ElMessageBox.confirm('Delete this mind map?', 'Delete Mind Map', {
      confirmButtonText: 'Delete',
      type: 'warning',
    })
    await studioStore.removeMindMap(mindmapId)
    ElMessage.success('Mind map deleted')
  } catch {
    // cancelled
  }
}

const generateSlides = () => {
  studioStore.generateSlides(props.notebookId, {
    title: 'Generated Slides',
    theme: 'light',
  })
}

const openSlidePdf = async (deck: SlideDeckData) => {
  if (!deck.file_path) {
    ElMessage.warning('PDF is not ready yet for this slide deck')
    return
  }
  try {
    const { url } = await studioApi.getSlidePdfUrl(deck.id)
    window.open(url, '_blank', 'noopener,noreferrer')
  } catch {
    ElMessage.error('Failed to open PDF')
  }
}

const generateInfographic = () => {
  studioStore.generateInfographic(props.notebookId, {
    title: 'Generated Infographic',
    template_type: infographicTemplate.value,
  })
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  })
}
</script>

<style scoped>
.studio-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.studio-tabs {
  height: 100%;
}

.studio-tabs :deep(.el-tabs__header) {
  margin: 0;
  padding: 0 8px;
}

.studio-tabs :deep(.el-tabs__content) {
  padding: 0;
  flex: 1;
  overflow-y: auto;
}

.studio-tabs :deep(.el-tab-pane) {
  padding: 8px 12px;
}

.tab-toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  gap: 8px;
}

.toolbar-hint {
  font-size: 12px;
  color: var(--text-secondary);
}

.tab-empty {
  text-align: center;
  padding: 32px 16px;
  color: var(--text-secondary);
  font-size: 13px;
}

.notes-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.note-card {
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.15s;
}

.note-card:hover {
  border-color: var(--primary-color);
}

.note-header {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 4px;
}

.note-title {
  font-size: 14px;
  font-weight: 600;
}

.note-preview {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
  margin-bottom: 6px;
}

.note-meta {
  font-size: 11px;
  color: var(--text-secondary);
}

.mindmap-list,
.slides-list,
.infographic-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mindmap-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.15s;
}

.mindmap-card:hover {
  border-color: var(--primary-color);
}

.mindmap-card-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.mindmap-card-title {
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mindmap-card-meta {
  font-size: 12px;
  color: var(--text-secondary);
}

.mindmap-delete {
  opacity: 0;
  transition: opacity 0.15s;
}

.mindmap-card:hover .mindmap-delete {
  opacity: 1;
}

.slide-card,
.infographic-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
}

.slide-card:hover,
.infographic-card:hover {
  border-color: var(--primary-color);
}

.slide-info,
.infographic-info {
  display: flex;
  flex-direction: column;
}

.slide-title,
.infographic-title {
  font-size: 14px;
  font-weight: 500;
}

.slide-meta,
.infographic-meta {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
