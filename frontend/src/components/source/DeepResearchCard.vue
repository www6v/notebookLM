<template>
  <div class="deep-research-card">
    <!-- 输入区：两行布局，第一行问题，第二行操作 -->
    <div
      v-if="!readOnly"
      class="deep-research-input-wrap"
      :class="{ disabled: isInputDisabled }"
    >
      <!-- 第一行：用户输入的问题 -->
      <div class="input-row">
        <v-icon
          class="input-icon"
          size="18"
        >
          mdi-magnify
        </v-icon>
        <input
          v-model="queryText"
          type="text"
          class="deep-research-input"
          :placeholder="inputPlaceholder"
          :readonly="isInputDisabled"
          :disabled="isInputDisabled"
          @keydown.enter="handleSubmit"
        >
      </div>
      <!-- 第二行：Web / Deep Research 下拉与提交按钮 -->
      <div class="input-actions">
        <v-menu
          v-if="!isInputDisabled"
          location="bottom"
          :close-on-content-click="true"
        >
          <template #activator="{ props: menuProps }">
            <button
              v-bind="menuProps"
              type="button"
              class="pill-btn web-pill"
            >
              <v-icon size="14">mdi-web</v-icon>
              <span>Web</span>
              <v-icon size="14">mdi-chevron-down</v-icon>
            </button>
          </template>
          <v-list density="compact">
            <v-list-item
              title="Web"
              @click="searchMode = 'web'"
            />
            <v-list-item
              title="Deep Research"
              @click="searchMode = 'deep'"
            />
          </v-list>
        </v-menu>
        <span
          v-if="!isInputDisabled"
          class="pill-separator"
        />
        <v-menu
          v-if="!isInputDisabled"
          location="bottom"
          :close-on-content-click="true"
        >
          <template #activator="{ props: menuProps }">
            <button
              v-bind="menuProps"
              type="button"
              class="pill-btn deep-pill"
            >
              <v-icon size="14">mdi-magnify</v-icon>
              <span>Deep Research</span>
              <v-icon size="14">mdi-chevron-down</v-icon>
            </button>
          </template>
          <v-list density="compact">
            <v-list-item
              title="Deep Research"
              @click="researchType = 'deep'"
            />
          </v-list>
        </v-menu>
        <v-btn
          icon
          class="submit-btn"
          :disabled="isInputDisabled || !queryText.trim()"
          @click="handleSubmit"
        >
          <v-icon>mdi-arrow-right</v-icon>
        </v-btn>
      </div>
    </div>

    <!-- 进行中：规划提示 -->
    <div
      v-if="!readOnly && status === 'planning'"
      class="deep-research-status planning"
    >
      <v-progress-circular
        indeterminate
        :size="20"
        :width="2"
        color="grey"
        class="status-spinner"
      />
      <span class="status-text">
        {{ t('deepResearch.planningHint') }}
      </span>
      <button
        type="button"
        class="text-btn cancel-planning-btn"
        @click="handleCancelPlanning"
      >
        {{ t('common.cancel') }}
      </button>
    </div>

    <!-- 已完成：结果卡片 -->
    <div
      v-if="status === 'completed' && report"
      class="deep-research-result-card"
    >
      <div class="result-header">
        <v-icon
          size="20"
          class="result-title-icon"
        >
          mdi-magnify
        </v-icon>
        <div class="result-title-block">
          <span class="result-title">{{ resultHeaderTitle }}</span>
          <span
            v-if="report.query"
            class="result-query"
          >{{ report.query }}</span>
        </div>
        <button
          type="button"
          class="view-link"
          @click="handleViewReport"
        >
          {{ t('deepResearch.view') }}
        </button>
      </div>
      <p
        v-if="report.apiStatus === 'error'"
        :class="[
          'result-error-text',
          { 'result-rate-limited-text': isReportRateLimited },
        ]"
      >
        {{
          isReportRateLimited
            ? GENERATION_RATE_LIMIT_SNACKBAR_MESSAGE
            : (report.errorMessage || t('deepResearch.errorRetry'))
        }}
      </p>
      <div
        v-else
        class="result-summary"
      >
        <div class="summary-row">
          <v-icon
            size="16"
            class="summary-icon pdf"
          >
            mdi-file-document
          </v-icon>
          <span>{{ t('deepResearch.sourcesTotal', { count: report.sourceCount }) }}</span>
        </div>
        <div class="summary-row">
          <v-icon
            size="16"
            class="summary-icon folder"
          >
            mdi-folder-multiple
          </v-icon>
          <span>{{ t('deepResearch.popularSources', { count: report.popularCount }) }}</span>
        </div>
      </div>
      <div
        v-if="!readOnly"
        class="result-footer"
      >
        <div class="feedback-icons">
          <v-btn
            icon
            variant="text"
            size="x-small"
            @click="handleFeedback('up')"
          >
            <v-icon size="18">mdi-thumb-up-outline</v-icon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="x-small"
            @click="handleFeedback('down')"
          >
            <v-icon size="18">mdi-thumb-down-outline</v-icon>
          </v-btn>
        </div>
        <div class="footer-actions">
          <button
            type="button"
            class="text-btn delete-btn"
            @click="handleDeleteReport"
          >
            {{ t('deepResearch.delete') }}
          </button>
          <v-btn
            color="primary"
            variant="flat"
            size="small"
            class="import-btn"
            @click="handleImport"
          >
            <v-icon size="16">mdi-plus</v-icon>
            {{ t('deepResearch.import') }}
          </v-btn>
        </div>
      </div>
    </div>

    <!-- 报告内容弹窗 -->
    <v-dialog
      v-model="showReportDialog"
      max-width="700"
      persistent
      @after-leave="reportDialogClosed"
    >
      <v-card>
        <v-card-title class="report-dialog-title">
          {{ t('deepResearch.dialogTitle') }}
        </v-card-title>
        <v-card-text class="report-dialog-content">
          <MarkdownRenderer
            v-if="reportDialogContent"
            class="report-body"
            :content="reportDialogContent"
          />
          <p
            v-else
            class="report-placeholder"
          >
            {{ t('deepResearch.loadingContent') }}
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            variant="text"
            @click="showReportDialog = false"
          >
            {{ t('deepResearch.close') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { shareReadApi } from '@/api/shareRead'
import {
  cancelDeepResearch,
  createDeepResearch,
  deleteDeepResearch,
  listDeepResearch,
  pollDeepResearchUntilDone,
  streamDeepResearchUntilDone,
  type DeepResearchReportDto,
} from '@/api/deepResearch'
import type { DeepResearchReport } from './deepResearchTypes'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'
import { useSnackbarStore } from '@/stores/useSnackbarStore'
import {
  GENERATION_RATE_LIMIT_SNACKBAR_MESSAGE,
  isAxiosGenerationRateLimited,
  isStudioErrorMessageRateLimited,
} from '@/utils/generationErrors'

defineOptions({
  name: 'DeepResearchCard',
})

const props = withDefaults(
  defineProps<{
    notebookId: string
    readOnly?: boolean
    shareToken?: string | null
  }>(),
  { readOnly: false, shareToken: null },
)

const emit = defineEmits<{
  viewReport: [report: DeepResearchReport]
  deleteReport: [report: DeepResearchReport]
  importReport: [report: DeepResearchReport]
}>()

const queryText = ref('')
const searchMode = ref<'web' | 'deep'>('web')
const researchType = ref<'deep'>('deep')
const status = ref<'idle' | 'planning' | 'completed'>('idle')
const report = ref<DeepResearchReport | null>(null)
const showReportDialog = ref(false)
/** Bumps when notebook changes or user starts/cancels; stale follow handlers exit. */
const sessionGen = ref(0)
const activeReportId = ref<string | null>(null)

const snackbar = useSnackbarStore()
const { t } = useI18n()

const inputPlaceholder = computed(() => t('deepResearch.inputPlaceholder'))
const isInputDisabled = computed(
  () =>
    props.readOnly
    || status.value === 'planning'
    || status.value === 'completed',
)

watch(
  () => [props.notebookId, props.shareToken, props.readOnly] as const,
  () => {
    sessionGen.value += 1
    const gen = sessionGen.value
    void bootstrapNotebook(gen)
  },
  { immediate: true },
)

async function bootstrapNotebook(expectedGen: number) {
  status.value = 'idle'
  report.value = null
  queryText.value = ''
  activeReportId.value = null
  if (props.readOnly && props.shareToken) {
    try {
      const sharedList = await shareReadApi.listDeepResearch(props.shareToken)
      if (expectedGen !== sessionGen.value) {
        return
      }
      const ready = sharedList.find((r) => r.status === 'ready')
      if (ready) {
        applyTerminalDto(ready)
      }
    } catch (err) {
      if (expectedGen !== sessionGen.value) {
        return
      }
      console.error('Deep Research share hydrate failed:', err)
    }
    return
  }
  try {
    const list = await listDeepResearch(props.notebookId)
    if (expectedGen !== sessionGen.value) return
    const inflight = list.find(
      (r) =>
        r.status === 'pending' || r.status === 'processing'
    )
    if (!inflight) return
    queryText.value = inflight.query
    activeReportId.value = inflight.id
    status.value = 'planning'
    await followUntilDone(inflight.id, expectedGen)
  } catch (err) {
    if (expectedGen !== sessionGen.value) return
    console.error('Deep Research hydrate failed:', err)
  }
}

function applyTerminalDto(final: DeepResearchReportDto) {
  report.value = dtoToReport(final)
  status.value = 'completed'
  activeReportId.value = null
  if (final.status === 'error') {
    const rateLimited = isStudioErrorMessageRateLimited(final.error_message)
    report.value = {
      ...dtoToReport(final),
      content: rateLimited
        ? GENERATION_RATE_LIMIT_SNACKBAR_MESSAGE
        : (final.error_message
          ? t('deepResearch.errorWithMsg', { msg: final.error_message })
          : t('deepResearch.errorRetry')),
    }
  }
}

async function followUntilDone(reportId: string, gen: number) {
  try {
    let final: DeepResearchReportDto
    try {
      final = await streamDeepResearchUntilDone(reportId)
    } catch {
      final = await pollDeepResearchUntilDone(reportId)
    }
    if (gen !== sessionGen.value) return
    applyTerminalDto(final)
  } catch (err) {
    if (gen !== sessionGen.value) return
    report.value = null
    status.value = 'idle'
    activeReportId.value = null
    if (isAxiosGenerationRateLimited(err)) {
      snackbar.warning(GENERATION_RATE_LIMIT_SNACKBAR_MESSAGE, 5000)
      return
    }
    console.error('Deep Research follow failed:', err)
  }
}

async function handleSubmit() {
  const q = queryText.value?.trim()
  if (!q || status.value !== 'idle') return
  sessionGen.value += 1
  const gen = sessionGen.value
  status.value = 'planning'
  try {
    const initial = await createDeepResearch(props.notebookId, { query: q })
    if (gen !== sessionGen.value) return
    activeReportId.value = initial.id
    await followUntilDone(initial.id, gen)
  } catch (err) {
    if (gen !== sessionGen.value) return
    report.value = null
    status.value = 'idle'
    activeReportId.value = null
    if (isAxiosGenerationRateLimited(err)) {
      snackbar.warning(GENERATION_RATE_LIMIT_SNACKBAR_MESSAGE, 5000)
      return
    }
    console.error('Deep Research failed:', err)
  }
}

async function handleCancelPlanning() {
  const id = activeReportId.value
  if (!id || status.value !== 'planning') return
  sessionGen.value += 1
  const gen = sessionGen.value
  try {
    const dto = await cancelDeepResearch(id)
    if (gen !== sessionGen.value) return
    applyTerminalDto(dto)
  } catch (err) {
    if (gen !== sessionGen.value) return
    if (isAxiosGenerationRateLimited(err)) {
      snackbar.warning(GENERATION_RATE_LIMIT_SNACKBAR_MESSAGE, 5000)
      return
    }
    snackbar.error(t('deepResearch.cancelFailed'))
    console.error('Deep Research cancel failed:', err)
  }
}

function dtoToReport(d: {
  id: string
  query: string
  sourceCount: number
  popularCount: number
  content: string | null
  status: string
  error_message: string | null
}): DeepResearchReport {
  const apiStatus: 'ready' | 'error' =
    d.status === 'error' ? 'error' : 'ready'
  return {
    id: d.id,
    query: d.query,
    sourceCount: d.sourceCount,
    popularCount: d.popularCount,
    content: d.content ?? undefined,
    apiStatus,
    errorMessage: d.error_message ?? undefined,
  }
}

const resultHeaderTitle = computed(() => {
  const r = report.value
  if (!r) return ''
  if (r.apiStatus === 'error') {
    return t('deepResearch.incomplete')
  }
  return t('deepResearch.complete')
})

const isReportRateLimited = computed(() =>
  isStudioErrorMessageRateLimited(report.value?.errorMessage),
)

const reportDialogContent = computed(() => {
  const r = report.value
  if (!r?.content?.trim()) {
    return ''
  }
  return r.content
})

function handleViewReport() {
  if (!report.value) return
  showReportDialog.value = true
  emit('viewReport', report.value)
}

function reportDialogClosed() {
  // 可在此清理或加载完整报告内容
}

function handleFeedback(direction: 'up' | 'down') {
  // 可调用反馈 API
}

async function handleDeleteReport() {
  if (!report.value) return
  sessionGen.value += 1
  try {
    await deleteDeepResearch(report.value.id)
    emit('deleteReport', report.value)
    report.value = null
    status.value = 'idle'
    queryText.value = ''
    activeReportId.value = null
  } catch (err) {
    console.error('Delete deep research failed:', err)
  }
}

function handleImport() {
  if (!report.value) return
  emit('importReport', report.value)
}
</script>

<style scoped>
.deep-research-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 12px;
}

.deep-research-input-wrap {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px 12px;
  background: #f1f3f4;
  border: 1px solid #dadce0;
  border-radius: 12px;
  transition: background 0.2s, opacity 0.2s;
}

.deep-research-input-wrap.disabled {
  opacity: 0.85;
  background: #e8eaed;
  pointer-events: none;
}

.input-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.input-icon {
  color: #5f6368;
  flex-shrink: 0;
}

.deep-research-input {
  flex: 1;
  min-width: 0;
  border: none;
  background: transparent;
  font-size: 14px;
  outline: none;
  color: #202124;
}

.deep-research-input::placeholder {
  color: #5f6368;
}

.deep-research-input:disabled,
.deep-research-input[readonly] {
  color: #5f6368;
  cursor: default;
}

.input-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.pill-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: none;
  border-radius: 16px;
  background: #fff;
  color: #5f6368;
  font-size: 12px;
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.pill-separator {
  width: 1px;
  height: 16px;
  background: #dadce0;
}

.submit-btn {
  background: #000000 !important;
  color: #fff !important;
}

.submit-btn:not(:disabled):hover {
  background: #333333 !important;
}

.submit-btn:disabled {
  background: #dadce0 !important;
  color: #9aa0a6 !important;
}

/* 进行中状态 */
.deep-research-status.planning {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding: 12px 14px;
  background: #e8f0fe;
  border-radius: 12px;
  border: 1px solid #d2e3fc;
}

.cancel-planning-btn {
  margin-left: auto;
  flex-shrink: 0;
}

.status-spinner {
  flex-shrink: 0;
}

.status-text {
  font-size: 13px;
  color: #3c4043;
}

/* 已完成结果卡片 */
.deep-research-result-card {
  padding: 14px;
  background: #e8f0fe;
  border: 1px solid #d2e3fc;
  border-radius: 12px;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.result-title-icon {
  color: #1a73e8;
  flex-shrink: 0;
}

.result-title-block {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-title {
  font-size: 14px;
  font-weight: 500;
  color: #202124;
}

.result-query {
  font-size: 12px;
  color: #5f6368;
  line-height: 1.4;
  word-break: break-word;
}

.view-link {
  border: none;
  background: none;
  font-size: 13px;
  color: #1a73e8;
  text-decoration: underline;
  cursor: pointer;
  padding: 0 4px;
}

.view-link:hover {
  color: #1557b0;
}

.result-summary {
  padding: 12px;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 12px;
}

.summary-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #3c4043;
}

.summary-row + .summary-row {
  margin-top: 6px;
}

.result-error-text {
  margin: 0 0 12px;
  padding: 12px;
  background: #fff;
  border-radius: 8px;
  font-size: 13px;
  color: #c5221f;
  line-height: 1.5;
}

.result-rate-limited-text {
  color: #b06000;
  background: #fff8e1;
}

.summary-icon.pdf {
  color: #d93025;
  flex-shrink: 0;
}

.summary-icon.folder {
  color: #1a73e8;
  flex-shrink: 0;
}

.result-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.feedback-icons {
  display: flex;
  gap: 0;
}

.footer-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.text-btn {
  border: none;
  background: none;
  font-size: 13px;
  color: #1a73e8;
  cursor: pointer;
  padding: 4px 0;
}

.text-btn.delete-btn:hover {
  text-decoration: underline;
}

.import-btn {
  text-transform: none;
}

.report-dialog-title {
  font-size: 16px;
}

.report-dialog-content {
  max-height: 60vh;
  overflow-y: auto;
}

.report-body {
  font-size: 14px;
  line-height: 1.7;
  color: #202124;
}

.report-body :deep(h1) {
  font-size: 22px;
  font-weight: 700;
  margin: 20px 0 12px;
  padding-bottom: 6px;
  border-bottom: 1px solid #dadce0;
}

.report-body :deep(h2) {
  font-size: 18px;
  font-weight: 600;
  margin: 18px 0 10px;
}

.report-body :deep(h3) {
  font-size: 15px;
  font-weight: 600;
  margin: 14px 0 8px;
}

.report-body :deep(p) {
  margin: 8px 0;
}

.report-body :deep(ul),
.report-body :deep(ol) {
  padding-left: 24px;
  margin: 8px 0;
}

.report-body :deep(li) {
  margin: 4px 0;
}

.report-body :deep(blockquote) {
  border-left: 3px solid #1a73e8;
  padding: 8px 16px;
  margin: 12px 0;
  background: #f1f3f4;
  border-radius: 0 6px 6px 0;
  color: #5f6368;
}

.report-body :deep(code) {
  background: #f1f3f4;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.report-body :deep(pre) {
  background: #f1f3f4;
  padding: 12px 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}

.report-body :deep(strong) {
  font-weight: 600;
}

.report-body :deep(a) {
  color: #1a73e8;
  text-decoration: underline;
  word-break: break-word;
}

.report-placeholder {
  color: #5f6368;
  font-size: 14px;
}
</style>
