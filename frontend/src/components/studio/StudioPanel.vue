<template>
  <div class="studio-panel">
    <!-- Upper: 功能模块 -->
    <section class="studio-modules">
      <h4 class="section-title">功能模块</h4>
      <div class="modules-grid">
        <div
          v-for="mod in moduleList"
          :key="mod.id"
          class="module-card"
          :class="{ 'module-card--disabled': mod.disabled }"
          @click="mod.disabled ? undefined : onModuleClick(mod)"
        >
          <el-icon class="module-icon" :size="20">
            <component :is="mod.icon" />
          </el-icon>
          <span class="module-label">{{ mod.label }}</span>
          <span v-if="mod.beta" class="module-beta">Beta</span>
        </div>
      </div>
    </section>

    <!-- Lower: 输出的内容 -->
    <section class="studio-output">
      <h4 class="section-title">输出的内容</h4>
      <div v-if="studioStore.loading" class="output-loading">
        <el-icon class="is-loading" :size="16">
          <Loading />
        </el-icon>
        <span>正在生成笔记...</span>
      </div>
      <div v-if="outputList.length === 0 && !studioStore.loading" class="output-empty">
        <p>暂无内容。使用上方功能模块生成笔记、思维导图或演示文稿。</p>
      </div>
      <div v-else class="output-list">
        <div
          v-for="item in outputList"
          :key="item.id"
          class="output-item"
          @click="onOutputItemClick(item)"
          @dblclick="onOutputItemDblClick(item)"
        >
          <el-icon class="output-item-icon" :size="20">
            <component :is="item.icon" />
          </el-icon>
          <div class="output-item-body">
            <span class="output-item-title">{{ item.title }}</span>
            <span class="output-item-meta">{{ item.meta }}</span>
          </div>
          <el-dropdown trigger="click" @command="(cmd) => handleOutputCommand(cmd, item)">
            <el-button text size="small" class="output-item-more">
              <el-icon :size="14">
                <MoreFilled />
              </el-icon>
            </el-button>
            <template #dropdown>
                <el-dropdown-menu>
                <el-dropdown-item
                  v-if="item.type === 'note'"
                  command="edit"
                >
                  编辑
                </el-dropdown-item>
                <el-dropdown-item
                  v-if="item.type === 'mindmap' && !isOutputItemPending(item)"
                  command="open"
                >
                  打开
                </el-dropdown-item>
                <el-dropdown-item
                  v-if="item.type === 'slide' && !isOutputItemPending(item)"
                  command="open"
                >
                  打开 PDF
                </el-dropdown-item>
                <el-dropdown-item command="delete">
                  删除
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
      <div class="output-add">
        <el-button size="small" type="primary" class="add-note-btn" @click="createNote">
          <el-icon class="el-icon--left">
            <Plus />
          </el-icon>
          添加笔记
        </el-button>
      </div>
    </section>

    <!-- Infographic template dialog (when clicking Infographic card) -->
    <el-dialog
      v-model="showInfographicDialog"
      title="生成信息图"
      width="360px"
      @close="showInfographicDialog = false"
    >
      <el-form label-position="top">
        <el-form-item label="模板类型">
          <el-select v-model="infographicTemplate" size="default" style="width: 100%">
            <el-option label="Timeline" value="timeline" />
            <el-option label="Comparison" value="comparison" />
            <el-option label="Process" value="process" />
            <el-option label="Statistics" value="statistics" />
            <el-option label="Hierarchy" value="hierarchy" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showInfographicDialog = false">取消</el-button>
        <el-button type="primary" :loading="studioStore.loading" @click="confirmGenerateInfographic">
          生成
        </el-button>
      </template>
    </el-dialog>

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
      :title="editingNote ? '编辑笔记' : '新建笔记'"
      width="560px"
    >
      <el-form label-position="top">
        <el-form-item label="标题">
          <el-input v-model="noteForm.title" placeholder="Note title" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="noteForm.content"
            type="textarea"
            :rows="8"
            placeholder="Write your note..."
          />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="noteForm.is_pinned">置顶</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button v-if="editingNote" type="danger" text @click="deleteNote">删除</el-button>
        <el-button @click="showNoteDialog = false">取消</el-button>
        <el-button type="primary" @click="saveNote">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Share,
  Monitor,
  PictureFilled,
  Loading,
  MoreFilled,
  Headset,
  VideoCamera,
  Document,
  List,
  Grid,
} from '@element-plus/icons-vue'
import { useStudioStore } from '@/stores/useStudioStore'
import { useSourceStore } from '@/stores/useSourceStore'
import { noteApi } from '@/api/note'
import type { Note } from '@/api/note'
import { studioApi } from '@/api/studio'
import type { MindMapData, SlideDeckData, InfographicData } from '@/api/studio'
import MindMapViewer from './MindMapViewer.vue'

defineOptions({
  name: 'StudioPanel',
})

const props = defineProps<{ notebookId: string }>()

const studioStore = useStudioStore()
const sourceStore = useSourceStore()
const notes = ref<Note[]>([])
const editingNote = ref<Note | null>(null)
const showNoteDialog = ref(false)
const showMindMapDialog = ref(false)
const previewMindMap = ref<MindMapData | null>(null)
const showInfographicDialog = ref(false)
const infographicTemplate = ref('timeline')
const noteForm = reactive({ title: '', content: '', is_pinned: false })

type OutputItem = {
  id: string
  type: 'note' | 'mindmap' | 'slide' | 'infographic'
  title: string
  meta: string
  date: string
  icon: unknown
  raw: Note | MindMapData | SlideDeckData | InfographicData
}

const moduleList = [
  { id: 'audio', label: '音频概览', icon: Headset, beta: false, action: 'placeholder' as const, disabled: true },
  { id: 'video', label: '视频概览', icon: VideoCamera, beta: false, action: 'placeholder' as const, disabled: true },
  { id: 'mindmap', label: '思维导图', icon: Share, beta: false, action: 'mindmap' as const, disabled: false },
  { id: 'report', label: '报告', icon: Document, beta: false, action: 'placeholder' as const, disabled: false },
  { id: 'flashcard', label: '闪卡', icon: List, beta: false, action: 'placeholder' as const, disabled: true },
  { id: 'quiz', label: '测验', icon: List, beta: false, action: 'placeholder' as const, disabled: true },
  { id: 'infographic', label: '信息图', icon: PictureFilled, beta: false, action: 'infographic' as const, disabled: false },
  { id: 'slides', label: '演示文稿', icon: Monitor, beta: false, action: 'slides' as const, disabled: false },
  { id: 'table', label: '数据表格', icon: Grid, beta: false, action: 'placeholder' as const, disabled: true },
]

const outputList = computed<OutputItem[]>(() => {
  const items: OutputItem[] = []
  notes.value.forEach((n) => {
    items.push({
      id: `note-${n.id}`,
      type: 'note',
      title: n.title,
      meta: formatDate(n.updated_at),
      date: n.updated_at,
      icon: Document,
      raw: n,
    })
  })
  studioStore.mindMaps.forEach((m) => {
    const isPending = m.status === 'pending' || m.status === 'processing'
    items.push({
      id: `mindmap-${m.id}`,
      type: 'mindmap',
      title: m.title,
      meta: isPending ? '生成中…' : formatDate(m.created_at),
      date: m.created_at,
      icon: Share,
      raw: m,
    })
  })
  studioStore.slideDecks.forEach((d) => {
    const isPending = d.status === 'pending' || d.status === 'processing'
    items.push({
      id: `slide-${d.id}`,
      type: 'slide',
      title: d.title,
      meta: isPending ? '生成中…' : `${d.theme} · ${d.status}`,
      date: d.created_at,
      icon: Monitor,
      raw: d,
    })
  })
  studioStore.infographics.forEach((i) => {
    items.push({
      id: `infographic-${i.id}`,
      type: 'infographic',
      title: i.title,
      meta: `${i.template_type} · ${i.status}`,
      date: i.created_at,
      icon: PictureFilled,
      raw: i,
    })
  })
  items.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
  return items
})

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

function onModuleClick(mod: (typeof moduleList)[0]) {
  if (mod.action === 'placeholder') {
    ElMessage.info('敬请期待')
    return
  }
  if (mod.action === 'note') {
    createNote()
    return
  }
  if (mod.action === 'mindmap') {
    handleGenerateMindMap()
    return
  }
  if (mod.action === 'slides') {
    generateSlides()
    return
  }
  if (mod.action === 'infographic') {
    showInfographicDialog.value = true
    return
  }
}

function onOutputItemClick(item: OutputItem) {
  if (item.type === 'note') {
    editingNote.value = item.raw as Note
  }
}

function isOutputItemPending(item: OutputItem): boolean {
  if (item.type === 'mindmap') {
    const s = (item.raw as MindMapData).status
    return s === 'pending' || s === 'processing'
  }
  if (item.type === 'slide') {
    const s = (item.raw as SlideDeckData).status
    return s === 'pending' || s === 'processing'
  }
  return false
}

function onOutputItemDblClick(item: OutputItem) {
  if (isOutputItemPending(item)) return
  if (item.type === 'mindmap') {
    openMindMapDialog(item.raw as MindMapData)
  }
  if (item.type === 'slide') {
    openSlidePdf(item.raw as SlideDeckData)
  }
}

function handleOutputCommand(command: string, item: OutputItem) {
  if (command === 'edit' && item.type === 'note') {
    editingNote.value = item.raw as Note
  }
  if (command === 'open' && item.type === 'mindmap' && !isOutputItemPending(item)) {
    openMindMapDialog(item.raw as MindMapData)
  }
  if (command === 'open' && item.type === 'slide' && !isOutputItemPending(item)) {
    openSlidePdf(item.raw as SlideDeckData)
  }
  if (command === 'delete') {
    handleDeleteOutputItem(item)
  }
}

async function handleDeleteOutputItem(item: OutputItem) {
  if (item.type === 'note') {
    try {
      await ElMessageBox.confirm('删除这条笔记？', '删除笔记', {
        confirmButtonText: '删除',
        type: 'warning',
      })
      await noteApi.remove((item.raw as Note).id)
      await fetchNotes()
      ElMessage.success('已删除')
    } catch {
      // cancelled
    }
    return
  }
  if (item.type === 'mindmap') {
    await handleDeleteMindMap(item.raw.id)
    return
  }
  ElMessage.info('该类型暂不支持在此删除')
}

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
    ElMessage.success('已保存')
  } catch {
    ElMessage.error('保存失败')
  }
}

const deleteNote = async () => {
  if (!editingNote.value) return
  try {
    await noteApi.remove(editingNote.value.id)
    showNoteDialog.value = false
    editingNote.value = null
    await fetchNotes()
    ElMessage.success('已删除')
  } catch {
    ElMessage.error('删除失败')
  }
}

const handleGenerateMindMap = async () => {
  if (studioStore.loading) return
  const ids = sourceStore.activeSourceIds
  if (ids.length === 0) {
    ElMessage.warning('请先勾选至少一个来源')
    return
  }
  try {
    await studioStore.generateMindMap(props.notebookId, ids)
    ElMessage.success('思维导图已生成')
  } catch {
    ElMessage.error('生成失败')
  }
}

const openMindMapDialog = (mm: MindMapData) => {
  previewMindMap.value = mm
  showMindMapDialog.value = true
}

const handleDeleteMindMap = async (mindmapId: string) => {
  try {
    await ElMessageBox.confirm('删除此思维导图？', '删除思维导图', {
      confirmButtonText: '删除',
      type: 'warning',
    })
    await studioStore.removeMindMap(mindmapId)
    ElMessage.success('已删除')
  } catch {
    // cancelled
  }
}

const generateSlides = async () => {
  if (studioStore.loading) return
  try {
    await studioStore.generateSlides(props.notebookId, {
      title: 'Generated Slides',
      theme: 'light',
    })
    ElMessage.success('演示文稿已生成')
  } catch {
    ElMessage.error('生成失败')
  }
}

const openSlidePdf = async (deck: SlideDeckData) => {
  if (!deck.file_path) {
    ElMessage.warning('该演示文稿的 PDF 尚未就绪')
    return
  }
  try {
    const { url } = await studioApi.getSlidePdfUrl(deck.id)
    window.open(url, '_blank', 'noopener,noreferrer')
  } catch {
    ElMessage.error('打开 PDF 失败')
  }
}

const confirmGenerateInfographic = async () => {
  try {
    await studioStore.generateInfographic(props.notebookId, {
      title: 'Generated Infographic',
      template_type: infographicTemplate.value,
    })
    showInfographicDialog.value = false
    ElMessage.success('信息图已生成')
  } catch {
    ElMessage.error('生成失败')
  }
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('zh-CN', {
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
  min-height: 0;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0 0 8px 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Upper: 功能模块 */
.studio-modules {
  flex-shrink: 0;
  padding: 12px 12px 8px;
  border-bottom: 1px solid var(--border-color);
}

.modules-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.module-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.15s;
  position: relative;
}

.module-card:hover {
  border-color: var(--primary-color);
}

.module-card--disabled {
  position: relative;
  cursor: not-allowed;
  background: var(--el-fill-color-light);
  pointer-events: none;
}

.module-card--disabled::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.12);
  pointer-events: none;
}

.module-card--disabled .module-icon {
  position: relative;
  z-index: 1;
  color: var(--el-text-color-secondary);
}

.module-card--disabled .module-label {
  position: relative;
  z-index: 1;
  color: var(--el-text-color-regular);
}

.module-icon {
  color: var(--primary-color);
  flex-shrink: 0;
}

.module-label {
  font-size: 13px;
  font-weight: 500;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.module-beta {
  font-size: 10px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

/* Lower: 输出的内容 */
.studio-output {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 12px;
}

.output-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.output-empty {
  flex: 1;
  text-align: center;
  padding: 24px 12px;
  color: var(--text-secondary);
  font-size: 13px;
}

.output-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.output-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.15s;
}

.output-item:hover {
  border-color: var(--primary-color);
}

.output-item-icon {
  color: var(--primary-color);
  flex-shrink: 0;
}

.output-item-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.output-item-title {
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.output-item-meta {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.output-item-more {
  flex-shrink: 0;
  opacity: 0.7;
}

.output-add {
  flex-shrink: 0;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
  margin-top: 8px;
}

.add-note-btn {
  width: 100%;
}
</style>
