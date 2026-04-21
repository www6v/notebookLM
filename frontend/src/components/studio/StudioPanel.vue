<template>
  <div
    ref="panelRef"
    :class="[
      'studio-panel',
      { 'studio-panel--compact': isCompactPanel },
    ]"
  >
    <section class="studio-modules">
      <div class="modules-grid">
        <template
          v-for="mod in visibleModuleList"
          :key="mod.id"
        >
          <div
            v-if="mod.id === 'audio'"
            class="module-card module-card--audio module-card--audio-split"
            :class="{ 'module-card--disabled': mod.disabled }"
          >
            <button
              type="button"
              class="module-card-audio-main"
              :disabled="mod.disabled"
              :aria-label="t('studio.ariaAudioDefault')"
              @click="onAudioOverviewOuterClick"
            >
              <div class="module-card-audio-icon-wrap">
                <v-icon
                  class="module-card-audio-wave"
                  :size="18"
                >
                  mdi-waveform
                </v-icon>
                <v-icon
                  class="module-card-audio-sparkle"
                  :size="10"
                >
                  mdi-sparkles
                </v-icon>
              </div>
              <span class="module-label module-card-audio-label">{{ mod.label }}</span>
              <span
                v-if="mod.beta"
                class="module-beta"
              >
                {{ t('studio.beta') }}
              </span>
            </button>
            <v-icon
              v-if="!readOnly"
              class="module-edit-btn module-card-audio-options"
              :size="18"
              :aria-label="t('studio.ariaAudioOptions')"
              @click.stop="openPodcastCustomizeDialog"
            >
              mdi-chevron-right
            </v-icon>
          </div>
          <div
            v-else
            class="module-card"
            :class="[
              `module-card--${mod.id}`,
              { 'module-card--disabled': mod.disabled },
            ]"
            @click="mod.disabled ? undefined : onModuleClick(mod)"
          >
            <v-icon
              class="module-icon"
              :size="18"
            >
              {{ mod.icon }}
            </v-icon>
            <span class="module-label">{{ mod.label }}</span>
            <span
              v-if="mod.beta"
              class="module-beta"
            >
              {{ t('studio.beta') }}
            </span>
            <v-icon
              v-if="!readOnly && mod.action === 'slides' && !mod.disabled"
              class="module-edit-btn module-card-audio-options"
              :size="18"
              :aria-label="t('studio.ariaSlideOptions')"
              @click.stop="openSlideCustomizeDialog()"
            >
              mdi-chevron-right
            </v-icon>
            <v-icon
              v-if="!readOnly && mod.action === 'infographic' && !mod.disabled"
              class="module-edit-btn module-card-audio-options"
              :size="18"
              :aria-label="t('studio.ariaInfographicOptions')"
              @click.stop="openInfographicCustomizeDialog()"
            >
              mdi-chevron-right
            </v-icon>
          </div>
        </template>
      </div>
    </section>

    <section class="studio-output">
      <div class="output-header">
        <div
          class="output-export-btn-wrap"
          :title="t('studio.exportZipTitle')"
        >
          <v-btn
            variant="text"
            size="small"
            icon
            class="output-export-btn"
            :disabled="!canExportZip"
            :loading="exportZipBusy"
            :aria-label="t('studio.exportZipAria')"
            @click="exportCompletedOutputsZip"
          >
            <v-icon :size="18">
              mdi-folder-zip-outline
            </v-icon>
          </v-btn>
        </div>
      </div>
      <div v-if="generatingList.length > 0" class="output-generating">
        <div
          v-for="item in generatingList"
          :key="item.id"
          class="output-item output-item--generating"
        >
          <v-icon
            class="output-item-icon rotating"
            :size="20"
          >
            mdi-cached
          </v-icon>
          <div class="output-item-body">
            <span class="output-item-status">{{ t('studio.generatingLine', { type: item.typeLabel }) }}</span>
            <span class="output-item-meta">
              {{
                item.sourceCount != null && item.sourceCount > 0
                  ? t('studio.basedOnSources', { count: item.sourceCount })
                  : t('studio.basedOnManySources')
              }}
            </span>
          </div>
        </div>
      </div>
      <div v-if="outputList.length === 0 && !studioStore.loading" class="output-empty">
        <v-icon
          class="output-empty-icon"
          :size="48"
          color="primary"
        >
          mdi-auto-fix
        </v-icon>
        <p class="output-empty-title">{{ t('studio.outputEmptyTitle') }}</p>
        <p class="output-empty-desc">{{ t('studio.outputEmptyDesc') }}</p>
      </div>
      <div v-else-if="completedList.length > 0" class="output-list">
        <div
          v-for="item in completedList"
          :key="item.id"
          :class="[
            'output-item',
            {
              'output-item--error':
                isOutputItemError(item) && !isOutputItemRateLimited(item),
            },
            { 'output-item--rate-limited': isOutputItemRateLimited(item) },
          ]"
          @click="onOutputItemClick(item)"
          @dblclick="onOutputItemDblClick(item)"
        >
          <v-icon
            :class="[
              'output-item-icon',
              {
                'output-item-icon--error':
                  isOutputItemError(item) && !isOutputItemRateLimited(item),
              },
              {
                'output-item-icon--rate-limited':
                  isOutputItemRateLimited(item),
              },
            ]"
            :size="20"
          >
            {{ item.icon }}
          </v-icon>
          <div class="output-item-body">
            <span class="output-item-title">{{ item.title }}</span>
            <span class="output-item-meta">{{ item.meta }}</span>
          </div>
          <v-menu
            v-if="!(readOnly && item.type === 'note')"
            location="bottom"
          >
            <template #activator="{ props: menuProps }">
              <v-btn
                v-bind="menuProps"
                variant="text"
                size="small"
                icon
                class="output-item-more"
              >
                <v-icon :size="14">mdi-dots-vertical</v-icon>
              </v-btn>
            </template>
            <v-list>
              <v-list-item
                v-if="!readOnly && item.type === 'note'"
                @click="handleOutputCommand('edit', item)"
              >
                {{ t('studio.menuEdit') }}
              </v-list-item>
              <v-list-item
                v-if="item.type === 'mindmap' && !isOutputItemPending(item) && !isOutputItemError(item)"
                @click="handleOutputCommand('open', item)"
              >
                {{ t('studio.menuOpen') }}
              </v-list-item>
              <v-list-item
                v-if="!readOnly && item.type === 'slide' && !isOutputItemPending(item)"
                @click="handleOutputCommand('editSlide', item)"
              >
                {{ t('studio.menuEdit') }}
              </v-list-item>
              <v-list-item
                v-if="item.type === 'slide' && !isOutputItemPending(item) && !isOutputItemError(item)"
                @click="handleOutputCommand('open', item)"
              >
                {{ t('studio.menuOpenPdf') }}
              </v-list-item>
              <v-list-item
                v-if="!readOnly && item.type === 'infographic' && !isOutputItemPending(item)"
                @click="handleOutputCommand('editInfographic', item)"
              >
                {{ t('studio.menuEdit') }}
              </v-list-item>
              <v-list-item
                v-if="item.type === 'infographic' && !isOutputItemPending(item) && !isOutputItemError(item)"
                @click="handleOutputCommand('openInfographic', item)"
              >
                {{ t('studio.menuOpenImage') }}
              </v-list-item>
              <v-list-item
                v-if="item.type === 'report' && !isOutputItemPending(item) && !isOutputItemError(item)"
                @click="handleOutputCommand('openReport', item)"
              >
                {{ t('studio.menuOpen') }}
              </v-list-item>
              <v-list-item
                v-if="!readOnly && item.type === 'report' && !isOutputItemPending(item)"
                @click="handleOutputCommand('editReport', item)"
              >
                {{ t('studio.menuEdit') }}
              </v-list-item>
              <v-list-item
                v-if="item.type === 'podcast' && !isOutputItemPending(item) && !isOutputItemError(item)"
                @click="handleOutputCommand('openPodcast', item)"
              >
                {{ t('studio.menuPlayAudio') }}
              </v-list-item>
              <v-list-item
                v-if="!readOnly"
                @click="handleOutputCommand('delete', item)"
              >
                {{ t('studio.menuDelete') }}
              </v-list-item>
            </v-list>
          </v-menu>
        </div>
      </div>
      <div
        v-if="!readOnly"
        class="output-add"
      >
        <v-btn
          color="black"
          rounded="pill"
          class="add-note-btn"
          @click="createNote"
        >
          <v-icon class="mr-1">mdi-note-plus-outline</v-icon>
          {{ t('studio.addNote') }}
        </v-btn>
      </div>
    </section>

    <v-dialog
      v-model="showInfographicDialog"
      max-width="560"
      persistent
      class="infographic-customize-dialog"
      @after-leave="closeInfographicCustomizeDialog"
    >
      <v-card class="infographic-customize-card">
        <v-card-title class="infographic-customize-header">
          <div class="infographic-customize-header-left">
            <v-icon :size="20">mdi-chart-box-outline</v-icon>
            <span>{{ t('studio.infographicCustomize.title') }}</span>
          </div>
          <v-btn
            icon
            variant="text"
            size="small"
            class="infographic-customize-close"
            @click="showInfographicDialog = false"
          >
            <v-icon :size="18">mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="infographic-customize-body">
          <div class="infographic-section infographic-section-row">
            <div class="infographic-section-half">
              <div class="infographic-section-label">
                {{ t('studio.infographicCustomize.selectLanguage') }}
              </div>
              <v-select
                v-model="infographicForm.infographic_language"
                hide-details
                density="compact"
                class="infographic-select"
                :items="infographicLanguageOptions"
                item-title="label"
                item-value="value"
                :placeholder="t('studio.infographicCustomize.selectLanguage')"
              />
            </div>
            <div class="infographic-section-half">
              <div class="infographic-section-label">
                {{ t('studio.infographicCustomize.selectOrientation') }}
              </div>
              <div class="infographic-toggle-group">
                <div
                  v-for="dir in infographicDirectionOptions"
                  :key="dir.value"
                  class="infographic-toggle-btn"
                  :class="{ 'is-active': infographicForm.infographic_direction === dir.value }"
                  @click="infographicForm.infographic_direction = dir.value"
                >
                  <v-icon
                    v-if="infographicForm.infographic_direction === dir.value"
                    :size="12"
                    class="infographic-toggle-check"
                  >
                    mdi-check
                  </v-icon>
                  {{ dir.label }}
                </div>
              </div>
            </div>
          </div>
          <div class="infographic-section">
            <div class="infographic-section-label">
              {{ t('studio.infographicCustomize.selectVisualStyle') }}
            </div>
            <div class="infographic-style-scroll">
              <div
                v-for="vis in infographicVisualStyleOptions"
                :key="vis.value"
                class="infographic-style-card"
                :class="{ 'is-selected': infographicForm.infographic_visual_style === vis.value }"
                @click="infographicForm.infographic_visual_style = vis.value"
              >
                <v-icon
                  v-if="infographicForm.infographic_visual_style === vis.value"
                  class="infographic-style-check"
                >
                  mdi-check
                </v-icon>
                <v-icon
                  class="infographic-style-icon"
                  :icon="vis.icon"
                  :size="28"
                />
                <span class="infographic-style-label">{{ vis.label }}</span>
              </div>
            </div>
          </div>
          <div class="infographic-section">
            <div class="infographic-section-label">
              {{ t('studio.infographicCustomize.detailLevel') }}
            </div>
            <div class="infographic-toggle-group">
              <div
                v-for="opt in infographicStyleOptions"
                :key="opt.value"
                class="infographic-toggle-btn"
                :class="{ 'is-active': infographicForm.infographic_style === opt.value }"
                @click="infographicForm.infographic_style = opt.value"
              >
                <v-icon
                  v-if="infographicForm.infographic_style === opt.value"
                  :size="12"
                  class="infographic-toggle-check"
                >
                  mdi-check
                </v-icon>
                {{ opt.label }}
                <span
                  v-if="opt.beta"
                  class="infographic-toggle-beta"
                >
                  {{ t('studio.beta') }}
                </span>
              </div>
            </div>
          </div>
          <div class="infographic-section">
            <div class="infographic-section-label">
              {{ t('studio.infographicCustomize.describeLabel') }}
            </div>
            <v-textarea
              v-model="infographicForm.infographic_custom_prompt"
              hide-details
              class="infographic-textarea"
              rows="4"
              :placeholder="t('studio.infographicCustomize.describePlaceholder')"
            />
          </div>
        </v-card-text>
        <v-card-actions class="infographic-customize-actions">
          <v-btn
            variant="text"
            @click="showInfographicDialog = false"
          >
            {{ t('common.cancel') }}
          </v-btn>
          <v-btn
            color="primary"
            :loading="studioStore.loading"
            @click="submitInfographicCustomize"
          >
            {{ t('studio.infographicCustomize.generate') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog
      v-model="showMindMapDialog"
      max-width="90%"
    >
      <v-card>
        <v-card-title class="d-flex align-center justify-space-between">
          <span>{{ previewMindMap?.title || 'Mind Map' }}</span>
          <v-btn
            icon
            variant="text"
            size="small"
            aria-label="关闭"
            @click="showMindMapDialog = false"
          >
            <v-icon :size="18">mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text>
          <MindMapViewer
            v-if="previewMindMap"
            :graph-data="previewMindMap.graph_data as GraphData"
            :title="previewMindMap.title"
            fullscreen
          />
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog
      v-model="showSlideCustomizeDialog"
      max-width="600"
      persistent
      class="slide-customize-dialog"
      @after-leave="closeSlideCustomizeDialog"
    >
      <v-card class="slide-customize-card">
        <v-card-title class="slide-customize-header">
          <div class="slide-customize-header-left">
            <v-icon :size="20">mdi-presentation</v-icon>
            <span>{{ t('studio.slide.customize.title') }}</span>
          </div>
          <v-btn
            icon
            variant="text"
            size="small"
            class="slide-customize-close"
            :aria-label="t('studio.slide.customize.ariaClose')"
            @click="showSlideCustomizeDialog = false"
          >
            <v-icon :size="18">mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text>
          <div class="slide-customize-section">
            <div class="slide-customize-section-label">
              {{ t('studio.slide.customize.styleSection') }}
            </div>
            <div class="slide-style-scroll">
              <div
                v-for="opt in slideStyleOptions"
                :key="opt.value"
                class="slide-style-card"
                :class="{ 'is-selected': slideForm.slide_style === opt.value }"
                @click="slideForm.slide_style = opt.value"
              >
                <v-icon
                  v-if="slideForm.slide_style === opt.value"
                  class="slide-style-check"
                >
                  mdi-check
                </v-icon>
                <v-icon
                  class="slide-style-icon"
                  :icon="opt.icon"
                  :size="28"
                />
                <span class="slide-style-label">{{ opt.label }}</span>
              </div>
            </div>
          </div>
          <div class="slide-customize-row">
            <div class="slide-customize-row-item">
              <div class="slide-customize-section-label">
                {{ t('studio.slide.customize.audienceSection') }}
              </div>
              <v-select
                v-model="slideForm.slide_audience"
                hide-details
                density="compact"
                class="slide-customize-select mt-1"
                :items="slideAudienceOptions"
                item-title="label"
                item-value="value"
                :placeholder="t('studio.slide.customize.audiencePlaceholder')"
              />
            </div>
          </div>
          <div class="slide-customize-row mt-3">
            <div class="slide-customize-row-item">
              <div class="slide-customize-section-label">
                {{ t('studio.slide.customize.selectLanguage') }}
              </div>
              <v-select
                v-model="slideForm.slide_language"
                hide-details
                density="compact"
                class="slide-customize-select mt-1"
                :items="slideLanguageOptions"
                item-title="label"
                item-value="value"
                :placeholder="t('studio.slide.customize.languagePlaceholder')"
              />
            </div>
            <div class="slide-customize-row-item">
              <div class="slide-customize-section-label">
                {{ t('studio.slide.customize.durationSection') }}
              </div>
              <div class="slide-duration-toggle mt-1">
                <button
                  type="button"
                  class="slide-duration-option"
                  :class="{ 'is-active': slideForm.slide_duration === 'shortest' }"
                  @click="slideForm.slide_duration = 'shortest'"
                >
                  <v-icon
                    v-if="slideForm.slide_duration === 'shortest'"
                    class="slide-duration-check"
                    size="14"
                  >
                    mdi-check
                  </v-icon>
                  <span>{{ t('studio.slide.customize.durationShortest') }}</span>
                </button>
                <button
                  type="button"
                  class="slide-duration-option"
                  :class="{ 'is-active': slideForm.slide_duration === 'short' }"
                  @click="slideForm.slide_duration = 'short'"
                >
                  <v-icon
                    v-if="slideForm.slide_duration === 'short'"
                    class="slide-duration-check"
                    size="14"
                  >
                    mdi-check
                  </v-icon>
                  <span>{{ t('studio.slide.customize.durationShort') }}</span>
                </button>
                <button
                  type="button"
                  class="slide-duration-option"
                  :class="{ 'is-active': slideForm.slide_duration === 'default' }"
                  @click="slideForm.slide_duration = 'default'"
                >
                  <v-icon
                    v-if="slideForm.slide_duration === 'default'"
                    class="slide-duration-check"
                    size="14"
                  >
                    mdi-check
                  </v-icon>
                  <span>{{ t('studio.slide.customize.durationDefault') }}</span>
                </button>
              </div>
            </div>
          </div>
          <div class="slide-customize-section-label mt-3">
            {{ t('studio.slide.customize.describeLabel') }}
          </div>
          <v-textarea
            v-model="slideForm.slide_custom_prompt"
            hide-details
            rows="4"
            :placeholder="t('studio.slide.customize.describePlaceholder')"
            class="slide-customize-textarea mt-1"
          />
        </v-card-text>
        <v-card-actions class="slide-customize-actions">
          <v-btn
            variant="text"
            @click="showSlideCustomizeDialog = false"
          >
            {{ t('common.cancel') }}
          </v-btn>
          <v-btn
            color="primary"
            :loading="studioStore.loading"
            @click="submitSlideCustomize"
          >
            {{ t('studio.slide.customize.generate') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog
      v-model="showNoteDialog"
      max-width="560"
      persistent
    >
      <v-card>
        <v-card-title>
          {{
            noteDialogViewOnly
              ? t('studio.noteViewTitle')
              : (editingNote ? '编辑笔记' : '新建笔记')
          }}
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="noteForm.title"
            label="标题"
            placeholder="Note title"
            :readonly="noteDialogViewOnly"
          />
          <v-textarea
            v-model="noteForm.content"
            label="内容"
            rows="8"
            placeholder="Write your note..."
            class="mt-2"
            :readonly="noteDialogViewOnly"
          />
          <v-checkbox
            v-model="noteForm.is_pinned"
            label="置顶"
            hide-details
            class="mt-2"
            :disabled="noteDialogViewOnly"
          />
        </v-card-text>
        <v-card-actions>
          <v-btn
            v-if="editingNote && !noteDialogViewOnly"
            color="error"
            variant="text"
            @click="deleteNote"
          >
            删除
          </v-btn>
          <v-spacer />
          <v-btn
            variant="text"
            @click="showNoteDialog = false"
          >
            {{ noteDialogViewOnly ? t('common.close') : t('common.cancel') }}
          </v-btn>
          <v-btn
            v-if="!noteDialogViewOnly"
            color="primary"
            @click="saveNote"
          >
            保存
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog
      v-model="showReportConfigDialog"
      max-width="560"
      persistent
      class="report-config-dialog"
    >
      <v-card>
        <v-card-title class="report-dialog-header d-flex align-center justify-space-between">
          <div class="report-dialog-header-left d-flex align-center gap-2">
            <v-icon :size="20">mdi-file-document</v-icon>
            <span>创建报告</span>
          </div>
          <v-btn
            icon
            variant="text"
            size="small"
            @click="showReportConfigDialog = false"
          >
            <v-icon :size="18">mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text>
          <div class="report-format-section">
            <div class="report-format-label">格式</div>
            <div class="report-format-grid">
              <div
                v-for="mod of reportFormatModules"
                :key="mod.id"
                class="report-format-card"
                @click="onReportFormatClick(mod)"
              >
                <div class="report-format-card-header">
                  <span class="report-format-card-title">{{ mod.label }}</span>
                  <v-icon
                    v-if="mod.hasEdit"
                    class="report-format-card-edit"
                    :size="14"
                    @click.stop="onReportFormatEdit(mod)"
                  >
                    mdi-pencil
                  </v-icon>
                </div>
                <div class="report-format-card-desc">{{ mod.desc }}</div>
              </div>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog
      v-model="showReportEditDialog"
      max-width="560"
      persistent
      class="report-edit-dialog"
      @after-leave="closeReportEditDialog"
    >
      <v-card>
        <v-card-title class="report-dialog-header d-flex align-center justify-space-between">
          <div class="report-dialog-header-left d-flex align-center gap-2">
            <v-btn
              icon
              variant="text"
              size="small"
              class="report-back-btn"
              @click="showReportEditDialog = false"
            >
              <v-icon :size="18">mdi-arrow-left</v-icon>
            </v-btn>
            <v-icon :size="20">mdi-file-document</v-icon>
            <span>创建报告</span>
          </div>
          <v-btn
            icon
            variant="text"
            size="small"
            @click="showReportEditDialog = false; showReportConfigDialog = false"
          >
            <v-icon :size="18">mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text>
          <div class="report-edit-body">
            <div
              v-if="editingReportFormat"
              class="report-edit-format-info"
            >
              <div class="report-edit-format-title">{{ editingReportFormat.label }}</div>
              <div class="report-edit-format-desc">Key insights and important quotes</div>
            </div>
            <v-select
              v-model="reportForm.report_language"
              label="选择语言"
              :items="reportLanguageOptions"
              item-title="label"
              item-value="value"
              placeholder="选择语言"
            />
            <v-textarea
              v-model="reportForm.report_custom_prompt"
              label="请描述您要创建什么样的报告"
              rows="5"
              placeholder="指定报告的结构、风格、语气等方面的要求。"
              class="mt-2"
            />
          </div>
        </v-card-text>
        <v-card-actions>
          <v-btn
            variant="text"
            @click="showReportEditDialog = false"
          >
            取消
          </v-btn>
          <template v-if="editingReportData">
            <v-btn @click="saveReportOptions">保存</v-btn>
            <v-btn
              color="primary"
              :loading="studioStore.loading"
              @click="handleRegenerateReport"
            >
              重新生成
            </v-btn>
          </template>
          <template v-else>
            <v-btn
              color="primary"
              :loading="studioStore.loading"
              @click="confirmGenerateReport"
            >
              生成
            </v-btn>
          </template>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog
      v-model="showReportContentDialog"
      max-width="70%"
      class="report-content-dialog"
      @after-leave="onReportContentDialogAfterLeave"
    >
      <v-card>
        <v-card-title>{{ previewReport?.title || t('studio.reportFallbackTitle') }}</v-card-title>
        <v-card-text>
            <MarkdownRenderer
              v-if="previewReport"
              class="report-content-body"
              :content="previewReport.content || ''"
            />
        </v-card-text>
      </v-card>
    </v-dialog>

    <SlideDeckPreviewDialog
      v-model="showSlideDeckPreviewDialog"
      :deck="slideDeckPreview"
      :share-token="shareToken"
      @after-leave="onSlideDeckPreviewAfterLeave"
    />

    <InfographicPreviewDialog
      v-model="showInfographicPreviewDialog"
      :infographic="previewInfographic"
      :share-token="shareToken"
      @after-leave="onInfographicPreviewAfterLeave"
    />

    <v-dialog
      v-model="showPodcastCustomizeDialog"
      max-width="520"
      persistent
      class="podcast-customize-dialog"
    >
      <v-card class="podcast-customize-card">
        <v-card-title class="podcast-customize-header">
          <div class="podcast-customize-header-left">
            <v-icon :size="20">
              mdi-waveform
            </v-icon>
            <span>音频概览</span>
          </div>
          <v-btn
            icon
            variant="text"
            size="small"
            class="podcast-customize-close"
            @click="showPodcastCustomizeDialog = false"
          >
            <v-icon :size="18">
              mdi-close
            </v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text>
          <div class="podcast-customize-section-label">
            形式
          </div>
          <v-select
            v-model="podcastForm.audio_format"
            hide-details
            density="compact"
            class="podcast-customize-select mt-1"
            :items="podcastFormatOptions"
            item-title="label"
            item-value="value"
          />
          <div class="podcast-customize-section-label mt-3">
            语言
          </div>
          <v-select
            v-model="podcastForm.audio_language"
            hide-details
            density="compact"
            class="podcast-customize-select mt-1"
            :items="podcastLanguageOptions"
            item-title="label"
            item-value="value"
          />
          <div class="podcast-customize-section-label mt-3">
            时长
          </div>
          <div class="podcast-length-toggle mt-1">
            <button
              type="button"
              class="podcast-length-option"
              :class="{ 'is-active': podcastForm.audio_length === 'default' }"
              @click="podcastForm.audio_length = 'default'"
            >
              <v-icon
                v-if="podcastForm.audio_length === 'default'"
                class="podcast-length-check"
                size="14"
              >
                mdi-check
              </v-icon>
              <span>默认</span>
            </button>
            <button
              type="button"
              class="podcast-length-option"
              :class="{ 'is-active': podcastForm.audio_length === 'short' }"
              @click="podcastForm.audio_length = 'short'"
            >
              <v-icon
                v-if="podcastForm.audio_length === 'short'"
                class="podcast-length-check"
                size="14"
              >
                mdi-check
              </v-icon>
              <span>短</span>
            </button>
          </div>
          <div class="podcast-customize-section-label mt-3">
            重点与风格说明（可选）
          </div>
          <v-textarea
            v-model="podcastForm.audio_focus_prompt"
            hide-details
            rows="4"
            placeholder="例如：多举例、侧重某章节、语气更轻松等"
            class="podcast-customize-textarea mt-1"
          />
        </v-card-text>
        <v-card-actions class="podcast-customize-actions">
          <v-btn
            variant="text"
            @click="showPodcastCustomizeDialog = false"
          >
            取消
          </v-btn>
          <v-btn
            color="primary"
            :loading="studioStore.loading"
            @click="confirmGeneratePodcast"
          >
            生成
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog
      v-model="showPodcastPlayerDialog"
      max-width="480"
      @after-leave="onPodcastPlayerDialogAfterLeave"
    >
      <v-card class="podcast-player-card">
        <v-card-title class="podcast-player-header">
          <v-icon
            class="mr-2"
            :size="20"
          >
            mdi-waveform
          </v-icon>
          <span class="text-truncate">{{ podcastPlayerTitle }}</span>
          <v-spacer />
          <v-btn
            icon
            variant="text"
            size="small"
            aria-label="关闭"
            @click="showPodcastPlayerDialog = false"
          >
            <v-icon :size="18">mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="podcast-player-body">
          <audio
            v-if="podcastPlayerUrl"
            class="podcast-player-audio"
            controls
            :src="podcastPlayerUrl"
          />
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, withDefaults } from 'vue'
import { useI18n } from 'vue-i18n'
import JSZip from 'jszip'
import { useSnackbarStore } from '@/stores/useSnackbarStore'
import { useConfirmStore } from '@/stores/useConfirmStore'
import { useStudioStore } from '@/stores/useStudioStore'
import { useSourceStore } from '@/stores/useSourceStore'
import { useSettingsStore, OUTPUT_LANGUAGE_OPTIONS } from '@/stores/useSettingsStore'
import { useResizeObserver } from '@/composables/useResizeObserver'
import { noteApi } from '@/api/note'
import type { Note } from '@/api/note'
import { shareReadApi } from '@/api/shareRead'
import { studioApi } from '@/api/studio'
import type {
  MindMapData,
  SlideDeckData,
  InfographicData,
  ReportData,
  PodcastData,
} from '@/api/studio'
import {
  buildStudioExportFilename,
  sanitizeFileName,
  triggerBlobDownload,
} from '@/utils/exportZip'
import {
  GENERATION_RATE_LIMIT_SNACKBAR_MESSAGE,
  isAxiosGenerationRateLimited,
  isStudioErrorMessageRateLimited,
} from '@/utils/generationErrors'
import { openSlidePdfWithFallback } from '@/utils/slidePdf'
import MindMapViewer from './MindMapViewer.vue'
import type { GraphData } from './MindMapViewer.vue'
import SlideDeckPreviewDialog from './SlideDeckPreviewDialog.vue'
import InfographicPreviewDialog from './InfographicPreviewDialog.vue'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'

defineOptions({
  name: 'StudioPanel',
})

const props = withDefaults(
  defineProps<{
    notebookId: string
    readOnly?: boolean
    shareToken?: string | null
  }>(),
  { readOnly: false, shareToken: null },
)

const slidePdfMode = computed(() =>
  props.shareToken ? { shareToken: props.shareToken } : undefined,
)

const { t, locale, tm } = useI18n()
const studioStore = useStudioStore()
const sourceStore = useSourceStore()
const settingsStore = useSettingsStore()
const snackbar = useSnackbarStore()
const confirmStore = useConfirmStore()
const { elementRef: panelRef, width: panelWidth } = useResizeObserver<HTMLDivElement>()
const isCompactPanel = computed(() => panelWidth.value > 0 && panelWidth.value < 360)
const notes = ref<Note[]>([])
const editingNote = ref<Note | null>(null)
const noteDialogViewOnly = ref(false)
const showNoteDialog = ref(false)
const showMindMapDialog = ref(false)
const previewMindMap = ref<MindMapData | null>(null)
const showInfographicDialog = ref(false)
const editingInfographic = ref<InfographicData | null>(null)
const showSlideCustomizeDialog = ref(false)
const showSlideDeckPreviewDialog = ref(false)
const slideDeckPreview = ref<SlideDeckData | null>(null)
const showInfographicPreviewDialog = ref(false)
const previewInfographic = ref<InfographicData | null>(null)
const editingSlideDeck = ref<SlideDeckData | null>(null)
const exportZipBusy = ref(false)
const slideForm = reactive({
  slide_style: 'blueprint',
  slide_audience: 'general',
  slide_language: settingsStore.settings.outputLanguage,
  slide_duration: 'default',
  slide_custom_prompt: '',
})
const noteForm = reactive({ title: '', content: '', is_pinned: false })
const infographicForm = reactive({
  infographic_style: '标准',
  infographic_language: settingsStore.settings.outputLanguage,
  infographic_direction: '横向',
  infographic_visual_style: 'craft-handmade',
  infographic_custom_prompt: '',
})

const showReportConfigDialog = ref(false)
const showReportEditDialog = ref(false)
const showReportContentDialog = ref(false)
const previewReport = ref<ReportData | null>(null)
type ReportFormatModule = {
  id: string
  value: string
  label: string
  desc: string
  hasEdit: boolean
}

const editingReportFormat = ref<ReportFormatModule | null>(null)
const editingReportData = ref<ReportData | null>(null)
const reportForm = reactive({
  report_format: 'briefing_doc',
  report_language: settingsStore.settings.outputLanguage,
  report_custom_prompt: '',
})

const showPodcastCustomizeDialog = ref(false)
const showPodcastPlayerDialog = ref(false)
const podcastPlayerUrl = ref('')
const podcastPlayerTitle = ref('')
const podcastForm = reactive({
  audio_format: 'deep_dive',
  audio_language: '简体中文',
  audio_length: 'default' as 'default' | 'short',
  audio_focus_prompt: '',
})

const podcastFormatOptions = [
  { value: 'deep_dive', label: '深入探究' },
  { value: 'summary', label: '摘要' },
  { value: 'commentary', label: '评论' },
  { value: 'debate', label: '辩论' },
]

const podcastLanguageOptions = OUTPUT_LANGUAGE_OPTIONS

const reportFormatModules = computed<ReportFormatModule[]>(() => [
  {
    id: 'custom',
    value: 'custom',
    label: t('studio.reportFormats.custom.label'),
    desc: t('studio.reportFormats.custom.desc'),
    hasEdit: false,
  },
  {
    id: 'briefing_doc',
    value: 'briefing_doc',
    label: t('studio.reportFormats.briefing_doc.label'),
    desc: t('studio.reportFormats.briefing_doc.desc'),
    hasEdit: true,
  },
  {
    id: 'study_guide',
    value: 'study_guide',
    label: t('studio.reportFormats.study_guide.label'),
    desc: t('studio.reportFormats.study_guide.desc'),
    hasEdit: true,
  },
  {
    id: 'blog_post',
    value: 'blog_post',
    label: t('studio.reportFormats.blog_post.label'),
    desc: t('studio.reportFormats.blog_post.desc'),
    hasEdit: true,
  },
])

const reportLanguageOptions = OUTPUT_LANGUAGE_OPTIONS

const reportDefaultPrompts: Record<string, string> = {
  custom: '',
  briefing_doc: 'Create a comprehensive briefing document that synthesizes the main themes and ideas from the sources. Start with a concise Executive Summary that presents the most critical takeaways upfront. The body of the document must provide a detailed and thorough examination of the main themes, evidence, and conclusions found in the sources. This analysis should be structured logically with headings and bullet points to ensure clarity. The tone must be objective and incisive.',
  study_guide: 'Create a comprehensive study guide based on the sources. Include short answer quiz questions, recommended essay topics and discussion questions, and a glossary of key terms with definitions. Structure the content logically by topic area.',
  blog_post: 'Transform the key insights from the sources into an engaging, accessible blog post. Use a conversational yet informative tone. Include relevant examples and make complex ideas easy to understand for a general audience.',
}

const infographicStyleOptions = computed(() => [
  {
    value: '简短',
    label: t('studio.infographicCustomize.detailBrief'),
    beta: false,
  },
  {
    value: '标准',
    label: t('studio.infographicCustomize.detailStandard'),
    beta: false,
  },
  {
    value: '详细',
    label: t('studio.infographicCustomize.detailDetailed'),
    beta: true,
  },
])

const infographicDirectionOptions = computed(() => [
  {
    value: '横向',
    label: t('studio.infographicCustomize.orientationLandscape'),
  },
  {
    value: '纵向',
    label: t('studio.infographicCustomize.orientationPortrait'),
  },
  {
    value: '方形',
    label: t('studio.infographicCustomize.orientationSquare'),
  },
])

type InfographicVisualStyleOption = {
  value: string
  icon: string
}

type SlideStyleOption = {
  value: string
  label: string
  icon: string
}

const infographicVisualStyleBaseOptions: InfographicVisualStyleOption[] = [
  { value: 'craft-handmade', icon: 'mdi-draw' },
  { value: 'claymation', icon: 'mdi-toy-brick-outline' },
  { value: 'kawaii', icon: 'mdi-heart-outline' },
  { value: 'storybook-watercolor', icon: 'mdi-palette-outline' },
  { value: 'chalkboard', icon: 'mdi-pencil' },
  { value: 'cyberpunk-neon', icon: 'mdi-lightning-bolt-outline' },
  { value: 'bold-graphic', icon: 'mdi-alpha-b-box-outline' },
  { value: 'aged-academia', icon: 'mdi-book-open-variant' },
  { value: 'corporate-memphis', icon: 'mdi-shape-outline' },
  { value: 'technical-schematic', icon: 'mdi-cog-outline' },
  { value: 'origami', icon: 'mdi-send-outline' },
  { value: 'pixel-art', icon: 'mdi-grid' },
  { value: 'ui-wireframe', icon: 'mdi-application-outline' },
  { value: 'subway-map', icon: 'mdi-train' },
  { value: 'ikea-manual', icon: 'mdi-hammer-wrench' },
  { value: 'knolling', icon: 'mdi-view-grid-outline' },
  { value: 'lego-brick', icon: 'mdi-toy-brick' },
  { value: 'pop-laboratory', icon: 'mdi-flask-outline' },
  { value: 'morandi-journal', icon: 'mdi-notebook-outline' },
  { value: 'retro-pop-grid', icon: 'mdi-view-dashboard-outline' },
]

const infographicVisualStyleOptions = computed(() => {
  void locale.value
  const labels = tm('studio.infographic.visualStyles') as Record<string, string>
  return infographicVisualStyleBaseOptions.map((option) => ({
    ...option,
    label: labels[option.value] ?? option.value,
  }))
})

const infographicLanguageOptions = OUTPUT_LANGUAGE_OPTIONS

const slideStyleBaseOptions = [
  { value: 'blueprint', label: 'Blueprint', icon: 'mdi-ruler-square-compass' },
  { value: 'chalkboard', label: 'Chalkboard', icon: 'mdi-pencil' },
  { value: 'corporate', label: 'Corporate', icon: 'mdi-briefcase-outline' },
  { value: 'minimal', label: 'Minimal', icon: 'mdi-minus-box-outline' },
  { value: 'sketch-notes', label: 'Sketch Notes', icon: 'mdi-notebook-edit-outline' },
  { value: 'watercolor', label: 'Watercolor', icon: 'mdi-palette-outline' },
  { value: 'dark-atmospheric', label: 'Dark Atmospheric', icon: 'mdi-weather-night' },
  { value: 'notion', label: 'Notion', icon: 'mdi-view-dashboard-outline' },
  { value: 'bold-editorial', label: 'Bold Editorial', icon: 'mdi-alpha-b-box-outline' },
  { value: 'editorial-infographic', label: 'Editorial Infographic', icon: 'mdi-newspaper-variant-outline' },
  { value: 'fantasy-animation', label: 'Fantasy Animation', icon: 'mdi-auto-fix' },
  { value: 'intuition-machine', label: 'Intuition Machine', icon: 'mdi-brain' },
  { value: 'pixel-art', label: 'Pixel Art', icon: 'mdi-grid' },
  { value: 'scientific', label: 'Scientific', icon: 'mdi-flask-outline' },
  { value: 'vector-illustration', label: 'Vector Illustration', icon: 'mdi-draw-pen' },
  { value: 'vintage', label: 'Vintage', icon: 'mdi-book-open-page-variant-outline' },
] satisfies SlideStyleOption[]

const slideStyleOptions = computed(() => {
  void locale.value
  const labels = tm('studio.slide.styles') as Record<string, string>
  return slideStyleBaseOptions.map((option) => ({
    ...option,
    label: labels[option.value] ?? option.label,
  }))
})

const slideAudienceBaseOptions = [
  { value: 'general' },
  { value: 'beginners' },
  { value: 'intermediate' },
  { value: 'experts' },
  { value: 'executives' },
] as const

const slideAudienceOptions = computed(() => {
  void locale.value
  return slideAudienceBaseOptions.map((option) => ({
    value: option.value,
    label: t(`studio.slide.audiences.${option.value}`),
  }))
})

const slideLanguageOptions = OUTPUT_LANGUAGE_OPTIONS

function outputTypeLabel(type: string): string {
  return t(`studio.outputTypes.${type}`)
}

type OutputItem = {
  id: string
  type: 'note' | 'mindmap' | 'slide' | 'infographic' | 'report' | 'podcast'
  title: string
  meta: string
  date: string
  icon: string
  typeLabel: string
  sourceCount: number | null
  raw: Note | MindMapData | SlideDeckData | InfographicData | ReportData | PodcastData
}

type StudioOutputRaw =
  | MindMapData
  | SlideDeckData
  | InfographicData
  | ReportData
  | PodcastData

type ModuleListItem = {
  id: string
  label: string
  icon: string
  beta: boolean
  action:
    | 'mindmap'
    | 'report'
    | 'infographic'
    | 'slides'
    | 'audio'
    | 'placeholder'
  disabled: boolean
  hidden?: boolean
}

const moduleListBase: Omit<ModuleListItem, 'label'>[] = [
  { id: 'mindmap', icon: 'mdi-sitemap', beta: false, action: 'mindmap', disabled: false },
  { id: 'report', icon: 'mdi-file-document', beta: false, action: 'report', disabled: false },
  { id: 'infographic', icon: 'mdi-chart-box', beta: false, action: 'infographic', disabled: false },
  { id: 'slides', icon: 'mdi-presentation', beta: false, action: 'slides', disabled: false },
  { id: 'audio', icon: 'mdi-waveform', beta: false, action: 'audio', disabled: false },
  { id: 'video', icon: 'mdi-video', beta: false, action: 'placeholder', disabled: true },
  { id: 'table', icon: 'mdi-grid', beta: false, action: 'placeholder', disabled: true },
  {
    id: 'flashcard',
    icon: 'mdi-format-list-bulleted',
    beta: false,
    action: 'placeholder',
    disabled: true,
    hidden: true,
  },
  {
    id: 'quiz',
    icon: 'mdi-format-list-bulleted',
    beta: false,
    action: 'placeholder',
    disabled: true,
    hidden: true,
  },
]
const hasActiveSources = computed(() => sourceStore.activeSourceIds.length > 0)
const moduleList = computed<ModuleListItem[]>(() =>
  moduleListBase.map((m) => ({
    ...m,
    label: t(`studio.tools.${m.id}`),
  })),
)
const visibleModuleList = computed(() =>
  moduleList.value
    .filter((m) => !('hidden' in m && m.hidden))
    .map((m) => ({
      ...m,
      disabled:
        props.readOnly
        || !hasActiveSources.value
        || m.disabled,
    })),
)

function getSourceCount(
  raw: MindMapData | SlideDeckData | InfographicData | ReportData | PodcastData,
): number | null {
  const r = raw as { source_count?: number | null }
  return r.source_count != null && r.source_count > 0 ? r.source_count : null
}

function isStudioOutputPending(raw: StudioOutputRaw): boolean {
  return raw.status === 'pending' || raw.status === 'processing'
}

function isStudioOutputError(raw: StudioOutputRaw): boolean {
  return raw.status === 'error'
}

function isStudioOutputRateLimited(raw: StudioOutputRaw): boolean {
  if (!isStudioOutputError(raw)) {
    return false
  }
  return isStudioErrorMessageRateLimited(raw.error_message)
}

function getStudioOutputMeta(raw: StudioOutputRaw): string {
  if (isStudioOutputPending(raw)) {
    return t('studio.metaGenerating')
  }
  if (isStudioOutputError(raw)) {
    if (isStudioOutputRateLimited(raw)) {
      return GENERATION_RATE_LIMIT_SNACKBAR_MESSAGE
    }
    return t('studio.outputFailedUnified')
  }
  const sourceCount = getSourceCount(raw)
  const srcPart =
    sourceCount != null ? t('chat.sourceCount', { count: sourceCount }) : null
  return [srcPart, formatDate(raw.created_at)].filter(Boolean).join(' · ')
}

const outputList = computed<OutputItem[]>(() => {
  const items: OutputItem[] = []
  notes.value.forEach((n) => {
    items.push({
      id: `note-${n.id}`,
      type: 'note',
      title: n.title,
      meta: formatDate(n.updated_at),
      date: n.updated_at,
      icon: 'mdi-file-document',
      typeLabel: outputTypeLabel('note'),
      sourceCount: null,
      raw: n,
    })
  })
  studioStore.mindMaps.forEach((m) => {
    const typeLabel = outputTypeLabel('mindmap')
    const sourceCount = getSourceCount(m)
    items.push({
      id: `mindmap-${m.id}`,
      type: 'mindmap',
      title: m.suggested_filename || m.title,
      meta: getStudioOutputMeta(m),
      date: m.created_at,
      icon: 'mdi-sitemap',
      typeLabel,
      sourceCount,
      raw: m,
    })
  })
  studioStore.slideDecks.forEach((d) => {
    const typeLabel = outputTypeLabel('slide')
    const sourceCount = getSourceCount(d)
    items.push({
      id: `slide-${d.id}`,
      type: 'slide',
      title: d.suggested_filename || d.title,
      meta: getStudioOutputMeta(d),
      date: d.created_at,
      icon: 'mdi-presentation',
      typeLabel,
      sourceCount,
      raw: d,
    })
  })
  studioStore.infographics.forEach((i) => {
    const typeLabel = outputTypeLabel('infographic')
    const sourceCount = getSourceCount(i)
    items.push({
      id: `infographic-${i.id}`,
      type: 'infographic',
      title: i.suggested_filename || i.title,
      meta: getStudioOutputMeta(i),
      date: i.created_at,
      icon: 'mdi-chart-box',
      typeLabel,
      sourceCount,
      raw: i,
    })
  })
  studioStore.reports.forEach((r) => {
    const formatMod = reportFormatModules.value.find((m) => m.value === r.report_format)
    const typeLabel = formatMod?.label ?? outputTypeLabel('report')
    const sourceCount = getSourceCount(r)
    items.push({
      id: `report-${r.id}`,
      type: 'report',
      title: formatMod?.label || r.title,
      meta: getStudioOutputMeta(r),
      date: r.created_at,
      icon: 'mdi-file-document',
      typeLabel,
      sourceCount,
      raw: r,
    })
  })
  studioStore.podcasts.forEach((p) => {
    const typeLabel = outputTypeLabel('podcast')
    const sourceCount = getSourceCount(p)
    items.push({
      id: `podcast-${p.id}`,
      type: 'podcast',
      title: p.suggested_filename || p.title,
      meta: getStudioOutputMeta(p),
      date: p.created_at,
      icon: 'mdi-waveform',
      typeLabel,
      sourceCount,
      raw: p,
    })
  })
  items.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
  return items
})

const generatingList = computed<OutputItem[]>(() =>
  outputList.value.filter((item) => isOutputItemPending(item))
)
const completedList = computed<OutputItem[]>(() =>
  outputList.value.filter((item) => !isOutputItemPending(item))
)
const exportableCompletedList = computed<OutputItem[]>(() =>
  completedList.value.filter((item) => !isOutputItemError(item))
)
const canExportZip = computed(
  () => !props.readOnly && exportableCompletedList.value.length > 0,
)

onMounted(async () => {
  await fetchNotes()
  await studioStore.fetchMindMaps(props.notebookId)
  await studioStore.fetchSlideDecks(props.notebookId)
  await studioStore.fetchInfographics(props.notebookId)
  await studioStore.fetchReports(props.notebookId)
  await studioStore.fetchPodcasts(props.notebookId)
})

watch(editingNote, (note) => {
  if (note) {
    noteForm.title = note.title
    noteForm.content = note.content
    noteForm.is_pinned = note.is_pinned
    noteDialogViewOnly.value = false
    showNoteDialog.value = true
  }
})

function onModuleClick(mod: ModuleListItem) {
  if (props.readOnly) {
    return
  }
  if (mod.action === 'placeholder') {
    snackbar.info('敬请期待')
    return
  }
  if (mod.action === 'audio') {
    void quickGeneratePodcast()
    return
  }
  if (mod.action === 'mindmap') {
    handleGenerateMindMap()
    return
  }
  if (mod.action === 'infographic') {
    openInfographicCustomizeDialog()
    return
  }
  if (mod.action === 'slides') {
    quickGenerateSlides()
    return
  }
  if (mod.action === 'report') {
    openReportConfigDialog()
    return
  }
}

function onOutputItemClick(item: OutputItem) {
  if (item.type === 'note') {
    const n = item.raw as Note
    noteForm.title = n.title
    noteForm.content = n.content
    noteForm.is_pinned = n.is_pinned
    if (props.readOnly) {
      editingNote.value = null
      noteDialogViewOnly.value = true
    } else {
      editingNote.value = n
      noteDialogViewOnly.value = false
    }
    showNoteDialog.value = true
    return
  }
  if (isOutputItemError(item)) {
    notifyOutputItemFailure(item)
    return
  }
  if (item.type === 'mindmap' && !isOutputItemPending(item)) {
    void openMindMapDialog(item.raw as MindMapData)
  }
  if (item.type === 'report' && !isOutputItemPending(item)) {
    openReportContentDialog(item.raw as ReportData)
  }
  if (item.type === 'podcast' && !isOutputItemPending(item)) {
    void openPodcastPlayer(item.raw as PodcastData)
  }
}

function isOutputItemPending(item: OutputItem): boolean {
  if (item.type === 'mindmap') {
    return isStudioOutputPending(item.raw as MindMapData)
  }
  if (item.type === 'slide') {
    return isStudioOutputPending(item.raw as SlideDeckData)
  }
  if (item.type === 'infographic') {
    return isStudioOutputPending(item.raw as InfographicData)
  }
  if (item.type === 'report') {
    return isStudioOutputPending(item.raw as ReportData)
  }
  if (item.type === 'podcast') {
    return isStudioOutputPending(item.raw as PodcastData)
  }
  return false
}

function isOutputItemError(item: OutputItem): boolean {
  if (item.type === 'note') {
    return false
  }
  return isStudioOutputError(item.raw as StudioOutputRaw)
}

function isOutputItemRateLimited(item: OutputItem): boolean {
  if (item.type === 'note') {
    return false
  }
  return isStudioOutputRateLimited(item.raw as StudioOutputRaw)
}

function notifyStudioGenerationFailure(err: unknown, defaultErrorLabel: string) {
  if (isAxiosGenerationRateLimited(err)) {
    snackbar.warning(GENERATION_RATE_LIMIT_SNACKBAR_MESSAGE, 5000)
    return
  }
  snackbar.error(defaultErrorLabel)
}

function notifyOutputItemFailure(item: OutputItem) {
  if (isOutputItemRateLimited(item)) {
    snackbar.warning(GENERATION_RATE_LIMIT_SNACKBAR_MESSAGE, 5000)
    return
  }
  snackbar.error(t('studio.outputFailedUnified'), 5000)
}

function onOutputItemDblClick(item: OutputItem) {
  if (isOutputItemPending(item)) return
  if (isOutputItemError(item)) {
    notifyOutputItemFailure(item)
    return
  }
  if (item.type === 'mindmap') {
    void openMindMapDialog(item.raw as MindMapData)
  }
  if (item.type === 'slide') {
    openSlideDeckPreviewDialog(item.raw as SlideDeckData)
  }
  if (item.type === 'infographic') {
    openInfographicImage(item.raw as InfographicData)
  }
  if (item.type === 'report' && !isOutputItemPending(item)) {
    openReportContentDialog(item.raw as ReportData)
  }
  if (item.type === 'podcast') {
    void openPodcastPlayer(item.raw as PodcastData)
  }
}

function handleOutputCommand(command: string, item: OutputItem) {
  if (command === 'edit' && item.type === 'note') {
    editingNote.value = item.raw as Note
  }
  if (command === 'editSlide' && item.type === 'slide' && !isOutputItemPending(item)) {
    openSlideCustomizeDialog(item.raw as SlideDeckData)
  }
  if (command === 'open' && item.type === 'mindmap' && !isOutputItemPending(item) && !isOutputItemError(item)) {
    void openMindMapDialog(item.raw as MindMapData)
  }
  if (command === 'open' && item.type === 'slide' && !isOutputItemPending(item) && !isOutputItemError(item)) {
    openSlidePdf(item.raw as SlideDeckData)
  }
  if (command === 'editInfographic' && item.type === 'infographic' && !isOutputItemPending(item)) {
    openInfographicCustomizeDialog(item.raw as InfographicData)
  }
  if (command === 'openInfographic' && item.type === 'infographic' && !isOutputItemPending(item) && !isOutputItemError(item)) {
    openInfographicImage(item.raw as InfographicData)
  }
  if (command === 'openReport' && item.type === 'report' && !isOutputItemPending(item) && !isOutputItemError(item)) {
    openReportContentDialog(item.raw as ReportData)
  }
  if (command === 'editReport' && item.type === 'report') {
    openReportEditFromData(item.raw as ReportData)
  }
  if (
    command === 'openPodcast'
    && item.type === 'podcast'
    && !isOutputItemPending(item)
    && !isOutputItemError(item)
  ) {
    void openPodcastPlayer(item.raw as PodcastData)
  }
  if (command === 'delete') {
    handleDeleteOutputItem(item)
  }
}

async function handleDeleteOutputItem(item: OutputItem) {
  if (props.readOnly) {
    return
  }
  if (item.type === 'note') {
    try {
      const ok = await confirmStore.confirm({
        title: '删除笔记',
        text: '删除这条笔记？',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
      })
      if (!ok) return
      await noteApi.remove((item.raw as Note).id)
      await fetchNotes()
      snackbar.success('已删除')
    } catch {
      // cancelled
    }
    return
  }
  if (item.type === 'mindmap') {
    await handleDeleteMindMap(item.raw.id)
    return
  }
  if (item.type === 'slide') {
    await handleDeleteSlide(item.raw.id)
    return
  }
  if (item.type === 'infographic') {
    await handleDeleteInfographic(item.raw.id)
    return
  }
  if (item.type === 'report') {
    await handleDeleteReport(item.raw.id)
    return
  }
  if (item.type === 'podcast') {
    await handleDeletePodcast(item.raw.id)
    return
  }
  snackbar.info('该类型暂不支持在此删除')
}

const fetchNotes = async () => {
  const tok = props.shareToken
  notes.value = tok
    ? await shareReadApi.listNotes(tok)
    : await noteApi.list(props.notebookId)
}

const createNote = () => {
  editingNote.value = null
  noteDialogViewOnly.value = false
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
    snackbar.success('已保存')
  } catch {
    snackbar.error('保存失败')
  }
}

const deleteNote = async () => {
  if (!editingNote.value) return
  try {
    await noteApi.remove(editingNote.value.id)
    showNoteDialog.value = false
    editingNote.value = null
    await fetchNotes()
    snackbar.success('已删除')
  } catch {
    snackbar.error('删除失败')
  }
}

const handleGenerateMindMap = async () => {
  const ids = sourceStore.activeSourceIds
  if (ids.length === 0) {
    snackbar.warning('请先勾选至少一个来源')
    return
  }
  try {
    await studioStore.generateMindMap(
      props.notebookId,
      ids,
      'Mind Map',
      settingsStore.settings.outputLanguage,
    )
    snackbar.success('思维导图已生成')
  } catch (err) {
    notifyStudioGenerationFailure(err, '生成失败')
  }
}

const openMindMapDialog = async (mm: MindMapData) => {
  try {
    const shouldFetchDetail = !mm.graph_data
    const tok = props.shareToken
    const resolvedMindMap = shouldFetchDetail
      ? (
          tok
            ? await shareReadApi.getMindMap(tok, mm.id)
            : await studioApi.getMindMap(mm.id)
        )
      : mm
    if (!resolvedMindMap.graph_data) {
      snackbar.warning('该思维导图内容尚未就绪')
      return
    }
    previewMindMap.value = resolvedMindMap
    showMindMapDialog.value = true
  } catch {
    snackbar.error('打开思维导图失败')
  }
}

const handleDeleteMindMap = async (mindmapId: string) => {
  try {
    const ok = await confirmStore.confirm({
      title: '删除思维导图',
      text: '删除此思维导图？',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    if (!ok) return
    await studioStore.removeMindMap(mindmapId)
    snackbar.success('已删除')
  } catch {
    // cancelled
  }
}

function onAudioOverviewOuterClick() {
  if (!hasActiveSources.value) return
  void quickGeneratePodcast()
}

const quickGeneratePodcast = async () => {
  const ids = sourceStore.activeSourceIds
  if (ids.length === 0) {
    snackbar.warning('请先勾选至少一个来源')
    return
  }
  try {
    await studioStore.generatePodcast(props.notebookId, {
      title: '音频概览',
      source_ids: ids.length > 0 ? ids : undefined,
      audio_format: 'deep_dive',
      audio_language: '简体中文',
      audio_length: 'default',
      audio_focus_prompt: undefined,
    })
    snackbar.success('音频概览已开始生成')
  } catch (err) {
    notifyStudioGenerationFailure(err, '生成失败')
  }
}

function openPodcastCustomizeDialog() {
  if (!hasActiveSources.value) {
    snackbar.warning('请先勾选至少一个来源')
    return
  }
  podcastForm.audio_format = 'deep_dive'
  podcastForm.audio_language = settingsStore.settings.outputLanguage
  podcastForm.audio_length = 'default'
  podcastForm.audio_focus_prompt = ''
  showPodcastCustomizeDialog.value = true
}

const confirmGeneratePodcast = async () => {
  const ids = sourceStore.activeSourceIds
  if (ids.length === 0) {
    snackbar.warning('请先勾选至少一个来源')
    return
  }
  const focus = (podcastForm.audio_focus_prompt || '').trim()
  showPodcastCustomizeDialog.value = false
  try {
    await studioStore.generatePodcast(props.notebookId, {
      title: '音频概览',
      source_ids: ids.length > 0 ? ids : undefined,
      audio_format: podcastForm.audio_format,
      audio_language: podcastForm.audio_language,
      audio_length: podcastForm.audio_length,
      audio_focus_prompt: focus || undefined,
    })
    snackbar.success('音频概览已开始生成')
  } catch (err) {
    notifyStudioGenerationFailure(err, '生成失败')
  }
}

function onPodcastPlayerDialogAfterLeave() {
  podcastPlayerUrl.value = ''
  podcastPlayerTitle.value = ''
}

async function openPodcastPlayer(podcast: PodcastData) {
  if (podcast.status !== 'ready' || !podcast.file_path) {
    snackbar.warning('音频尚未就绪')
    return
  }
  try {
    const tok = props.shareToken
    const { url } = tok
      ? await shareReadApi.getPodcastAudioUrl(tok, podcast.id)
      : await studioApi.getPodcastAudioUrl(podcast.id)
    podcastPlayerTitle.value =
      podcast.suggested_filename?.trim()
      || podcast.title?.trim()
      || outputTypeLabel('podcast')
    podcastPlayerUrl.value = url
    showPodcastPlayerDialog.value = true
  } catch {
    snackbar.error('无法加载音频')
  }
}

const handleDeletePodcast = async (podcastId: string) => {
  try {
    const ok = await confirmStore.confirm({
      title: '删除音频概览',
      text: '删除此音频概览？',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    if (!ok) return
    await studioStore.removePodcast(podcastId)
    snackbar.success('已删除')
  } catch {
    // cancelled
  }
}

const quickGenerateSlides = async () => {
  const ids = sourceStore.activeSourceIds
  if (ids.length === 0) {
    snackbar.warning('请先勾选至少一个来源')
    return
  }
  try {
    await studioStore.generateSlides(props.notebookId, {
      title: 'Generated Slides',
      theme: 'light',
      source_ids: ids.length > 0 ? ids : undefined,
      slide_style: 'blueprint',
      slide_audience: 'general',
      slide_language: settingsStore.settings.outputLanguage,
      slide_duration: 'default',
      slide_custom_prompt: undefined,
    })
    snackbar.success('演示文稿已生成')
  } catch (err) {
    notifyStudioGenerationFailure(err, '生成失败')
  }
}

function openSlideCustomizeDialog(deck?: SlideDeckData | null) {
  editingSlideDeck.value = deck ?? null
  if (deck) {
    slideForm.slide_style = deck.slide_style ?? 'blueprint'
    slideForm.slide_audience = deck.slide_audience ?? 'general'
    slideForm.slide_language = deck.slide_language ?? settingsStore.settings.outputLanguage
    slideForm.slide_duration = deck.slide_duration ?? 'default'
    slideForm.slide_custom_prompt = deck.slide_custom_prompt ?? ''
  } else {
    slideForm.slide_style = 'blueprint'
    slideForm.slide_audience = 'general'
    slideForm.slide_language = settingsStore.settings.outputLanguage
    slideForm.slide_duration = 'default'
    slideForm.slide_custom_prompt = ''
  }
  showSlideCustomizeDialog.value = true
}

function closeSlideCustomizeDialog() {
  editingSlideDeck.value = null
}

const confirmGenerateSlide = async () => {
  const ids = sourceStore.activeSourceIds
  if (ids.length === 0) {
    snackbar.warning('请先勾选至少一个来源')
    return
  }
  showSlideCustomizeDialog.value = false
  try {
    await studioStore.generateSlides(props.notebookId, {
      title: 'Generated Slides',
      theme: 'light',
      source_ids: ids.length > 0 ? ids : undefined,
      slide_style: slideForm.slide_style,
      slide_audience: slideForm.slide_audience,
      slide_language: slideForm.slide_language,
      slide_duration: slideForm.slide_duration,
      slide_custom_prompt: slideForm.slide_custom_prompt || undefined,
    })
    snackbar.success('演示文稿已生成')
  } catch (err) {
    notifyStudioGenerationFailure(err, '生成失败')
  }
}

const submitSlideCustomize = () => {
  const existingId = editingSlideDeck.value?.id
  if (existingId) {
    void regenerateSlideDeck()
  } else {
    void confirmGenerateSlide()
  }
}

const regenerateSlideDeck = async () => {
  if (!editingSlideDeck.value) return
  try {
    await studioStore.regenerateSlideDeck(editingSlideDeck.value.id, {
      slide_style: slideForm.slide_style,
      slide_audience: slideForm.slide_audience,
      slide_language: slideForm.slide_language,
      slide_duration: slideForm.slide_duration,
      slide_custom_prompt: slideForm.slide_custom_prompt || undefined,
    })
    showSlideCustomizeDialog.value = false
    snackbar.success('正在重新生成演示文稿')
  } catch (err) {
    notifyStudioGenerationFailure(err, '重新生成失败')
  }
}

const openSlidePdf = async (deck: SlideDeckData) => {
  if (!deck.file_path) {
    snackbar.warning('该演示文稿的 PDF 尚未就绪')
    return
  }
  try {
    await openSlidePdfWithFallback(
      deck.id,
      deck.suggested_filename || deck.title || 'slides',
      slidePdfMode.value,
    )
  } catch {
    snackbar.error('打开 PDF 失败')
  }
}

function openSlideDeckPreviewDialog(deck: SlideDeckData) {
  if (!deck.file_path) {
    snackbar.warning('该演示文稿的 PDF 尚未就绪')
    return
  }
  slideDeckPreview.value = deck
  showSlideDeckPreviewDialog.value = true
}

function onSlideDeckPreviewAfterLeave() {
  slideDeckPreview.value = null
}

function onInfographicPreviewAfterLeave() {
  previewInfographic.value = null
}

const quickGenerateInfographic = async () => {
  const ids = sourceStore.activeSourceIds
  if (ids.length === 0) {
    snackbar.warning('请先勾选至少一个来源')
    return
  }
  try {
    await studioStore.generateInfographic(props.notebookId, {
      title: 'Generated Infographic',
      source_ids: ids.length > 0 ? ids : undefined,
      infographic_style: '标准',
      infographic_language: settingsStore.settings.outputLanguage,
      infographic_direction: '横向',
      infographic_visual_style: 'craft-handmade',
      infographic_custom_prompt: undefined,
    })
    snackbar.success('信息图已生成')
  } catch (err) {
    notifyStudioGenerationFailure(err, '生成失败')
  }
}

function getEffectiveInfographicCustomPrompt(): string | undefined {
  const userPrompt = (infographicForm.infographic_custom_prompt || '').trim()
  return userPrompt || undefined
}

function normalizeInfographicVisualStyle(style?: string | null): string {
  const fallback = 'craft-handmade'
  if (!style) return fallback

  const legacyStyleMap: Record<string, string> = {
    auto: 'craft-handmade',
    hand_drawn: 'craft-handmade',
    cute: 'kawaii',
    professional: 'corporate-memphis',
    science: 'technical-schematic',
    anime: 'bold-graphic',
  }
  const normalized = legacyStyleMap[style] ?? style
  return infographicVisualStyleOptions.value.some(
    (option) => option.value === normalized
  )
    ? normalized
    : fallback
}

function openInfographicCustomizeDialog(info?: InfographicData | null) {
  editingInfographic.value = info ?? null
  if (info) {
    infographicForm.infographic_style = info.infographic_style ?? '标准'
    infographicForm.infographic_language = info.infographic_language ?? settingsStore.settings.outputLanguage
    infographicForm.infographic_direction = info.infographic_direction ?? '横向'
    infographicForm.infographic_visual_style = normalizeInfographicVisualStyle(
      info.infographic_visual_style
    )
    infographicForm.infographic_custom_prompt = info.infographic_custom_prompt ?? ''
  } else {
    infographicForm.infographic_style = '标准'
    infographicForm.infographic_language = settingsStore.settings.outputLanguage
    infographicForm.infographic_direction = '横向'
    infographicForm.infographic_visual_style = 'craft-handmade'
    infographicForm.infographic_custom_prompt = ''
  }
  showInfographicDialog.value = true
}

function closeInfographicCustomizeDialog() {
  editingInfographic.value = null
}

const confirmGenerateInfographic = async () => {
  const ids = sourceStore.activeSourceIds
  if (ids.length === 0) {
    snackbar.warning('请先勾选至少一个来源')
    return
  }
  showInfographicDialog.value = false
  try {
    await studioStore.generateInfographic(props.notebookId, {
      title: 'Generated Infographic',
      source_ids: ids.length > 0 ? ids : undefined,
      infographic_style: infographicForm.infographic_style,
      infographic_language: infographicForm.infographic_language,
      infographic_direction: infographicForm.infographic_direction,
      infographic_visual_style: infographicForm.infographic_visual_style,
      infographic_custom_prompt: getEffectiveInfographicCustomPrompt(),
    })
    snackbar.success('信息图已生成')
  } catch (err) {
    notifyStudioGenerationFailure(err, '生成失败')
  }
}

const submitInfographicCustomize = () => {
  const existingId = editingInfographic.value?.id
  if (existingId) {
    void handleRegenerateInfographic()
    return
  }
  void confirmGenerateInfographic()
}

const handleRegenerateInfographic = async () => {
  const id = editingInfographic.value?.id
  if (!id) {
    return
  }
  try {
    await studioStore.regenerateInfographic(id, {
      infographic_style: infographicForm.infographic_style,
      infographic_language: infographicForm.infographic_language,
      infographic_direction: infographicForm.infographic_direction,
      infographic_visual_style: infographicForm.infographic_visual_style,
      infographic_custom_prompt: getEffectiveInfographicCustomPrompt(),
    })
    showInfographicDialog.value = false
    snackbar.success('正在重新生成信息图')
  } catch (err) {
    notifyStudioGenerationFailure(err, '重新生成失败')
  }
}

function openInfographicImage(info: InfographicData) {
  if (!info.file_path) {
    snackbar.warning('该信息图的图片尚未就绪')
    return
  }
  previewInfographic.value = info
  showInfographicPreviewDialog.value = true
}

const handleDeleteInfographic = async (infographicId: string) => {
  try {
    const okInfo = await confirmStore.confirm({
      title: '删除信息图',
      text: '删除此信息图？',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    if (!okInfo) return
    await studioStore.removeInfographic(infographicId)
    snackbar.success('已删除')
  } catch {
    // cancelled
  }
}

const handleDeleteSlide = async (slideId: string) => {
  try {
    const okSlide = await confirmStore.confirm({
      title: '删除演示文稿',
      text: '删除此演示文稿？',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    if (!okSlide) return
    await studioApi.deleteSlide(slideId)
    await studioStore.fetchSlideDecks(props.notebookId)
    snackbar.success('已删除')
  } catch {
    // cancelled
  }
}

function openReportConfigDialog() {
  showReportConfigDialog.value = true
}

function openReportContentDialog(report: ReportData) {
  previewReport.value = report
  showReportContentDialog.value = true
}

function onReportContentDialogAfterLeave() {
  previewReport.value = null
}

function stripKnownExtension(name: string): string {
  const lower = name.toLowerCase()
  if (lower.endsWith('.pdf')) {
    return name.slice(0, -4)
  }
  if (lower.endsWith('.pptx')) {
    return name.slice(0, -5)
  }
  if (lower.endsWith('.png')) {
    return name.slice(0, -4)
  }
  if (lower.endsWith('.json')) {
    return name.slice(0, -5)
  }
  if (lower.endsWith('.md')) {
    return name.slice(0, -3)
  }
  return name
}

function buildExportBaseName(item: OutputItem): string {
  const raw = item.raw as
    | Note
    | MindMapData
    | SlideDeckData
    | InfographicData
    | ReportData
    | PodcastData
  const preferredName =
    'suggested_filename' in raw && raw.suggested_filename
      ? raw.suggested_filename
      : item.title
  const normalizedName = stripKnownExtension(preferredName || item.typeLabel)
  return `${sanitizeFileName(normalizedName, item.type)}-${raw.id.slice(0, 8)}`
}

function formatNoteExport(note: Note): string {
  const lines = [`# ${note.title || '未命名笔记'}`, '']
  if (note.content?.trim()) {
    lines.push(note.content.trim(), '')
  }
  return lines.join('\n')
}

async function resolveMindMapExportData(mindMap: MindMapData): Promise<MindMapData> {
  if (mindMap.graph_data) {
    return mindMap
  }
  const tok = props.shareToken
  return tok
    ? shareReadApi.getMindMap(tok, mindMap.id)
    : studioApi.getMindMap(mindMap.id)
}

async function resolveReportExportData(report: ReportData): Promise<ReportData> {
  if (report.content?.trim()) {
    return report
  }
  const tok = props.shareToken
  return tok
    ? shareReadApi.getReport(tok, report.id)
    : studioApi.getReport(report.id)
}

async function exportCompletedOutputsZip() {
  if (exportZipBusy.value) {
    return
  }

  const items = exportableCompletedList.value
  if (items.length === 0) {
    snackbar.info('暂无可导出的内容')
    return
  }

  exportZipBusy.value = true
  const zip = new JSZip()
  let exportedCount = 0
  let skippedCount = 0

  try {
    for (const item of items) {
      try {
        const baseName = buildExportBaseName(item)

        if (item.type === 'note') {
          zip.file(`notes/${baseName}.md`, formatNoteExport(item.raw as Note))
          exportedCount += 1
          continue
        }

        if (item.type === 'mindmap') {
          const mindMap = await resolveMindMapExportData(item.raw as MindMapData)
          if (!mindMap.graph_data) {
            skippedCount += 1
            continue
          }
          zip.file(
            `mindmaps/${baseName}.json`,
            JSON.stringify(mindMap.graph_data, null, 2)
          )
          exportedCount += 1
          continue
        }

        if (item.type === 'slide') {
          const deck = item.raw as SlideDeckData
          if (!deck.file_path) {
            skippedCount += 1
            continue
          }
          const tok = props.shareToken
          const pdfBuffer = tok
            ? await shareReadApi.getSlidePdfArrayBuffer(tok, deck.id)
            : await studioApi.getSlidePdfArrayBuffer(deck.id)
          zip.file(`slides/${baseName}.pdf`, pdfBuffer)
          exportedCount += 1
          continue
        }

        if (item.type === 'infographic') {
          const infographic = item.raw as InfographicData
          if (!infographic.file_path) {
            skippedCount += 1
            continue
          }
          const tokZip = props.shareToken
          const imageBuffer = tokZip
            ? await shareReadApi.getInfographicImageArrayBuffer(
              tokZip,
              infographic.id,
            )
            : await studioApi.getInfographicImageArrayBuffer(
              infographic.id,
            )
          zip.file(`infographics/${baseName}.png`, imageBuffer)
          exportedCount += 1
          continue
        }

        if (item.type === 'report') {
          const report = await resolveReportExportData(item.raw as ReportData)
          if (!report.content?.trim()) {
            skippedCount += 1
            continue
          }
          zip.file(`reports/${baseName}.md`, `${report.content.trim()}\n`)
          exportedCount += 1
          continue
        }

        if (item.type === 'podcast') {
          const podcast = item.raw as PodcastData
          if (!podcast.file_path) {
            skippedCount += 1
            continue
          }
          const tokWav = props.shareToken
          const wavBuffer = tokWav
            ? await shareReadApi.getPodcastAudioArrayBuffer(tokWav, podcast.id)
            : await studioApi.getPodcastAudioArrayBuffer(podcast.id)
          zip.file(`podcasts/${baseName}.wav`, wavBuffer)
          exportedCount += 1
        }
      } catch {
        skippedCount += 1
      }
    }

    if (exportedCount === 0) {
      snackbar.warning('没有可加入 ZIP 的已完成内容')
      return
    }

    const zipBlob = await zip.generateAsync({ type: 'blob' })
    triggerBlobDownload(zipBlob, buildStudioExportFilename())

    if (skippedCount > 0) {
      snackbar.warning(`已导出 ${exportedCount} 项，另有 ${skippedCount} 项未能加入`)
      return
    }

    snackbar.success(`已导出 ${exportedCount} 项`)
  } catch {
    snackbar.error('导出 ZIP 失败')
  } finally {
    exportZipBusy.value = false
  }
}

function onReportFormatClick(mod: ReportFormatModule) {
  editingReportFormat.value = mod
  editingReportData.value = null
  reportForm.report_format = mod.value
  reportForm.report_language = settingsStore.settings.outputLanguage
  reportForm.report_custom_prompt = reportDefaultPrompts[mod.value] || ''
  showReportEditDialog.value = true
}

function onReportFormatEdit(mod: ReportFormatModule) {
  editingReportFormat.value = mod
  editingReportData.value = null
  reportForm.report_format = mod.value
  reportForm.report_language = settingsStore.settings.outputLanguage
  reportForm.report_custom_prompt = reportDefaultPrompts[mod.value] || ''
  showReportEditDialog.value = true
}

function openReportEditFromData(report: ReportData) {
  const mod =
    reportFormatModules.value.find((m) => m.value === report.report_format)
    || reportFormatModules.value[0]
  editingReportFormat.value = mod
  editingReportData.value = report
  reportForm.report_format = report.report_format
  reportForm.report_language = report.report_language
  reportForm.report_custom_prompt = report.report_custom_prompt || ''
  showReportEditDialog.value = true
}

function closeReportEditDialog() {
  showReportEditDialog.value = false
  editingReportFormat.value = null
  editingReportData.value = null
}

const confirmGenerateReport = async () => {
  const ids = sourceStore.activeSourceIds
  if (ids.length === 0) {
    snackbar.warning('请先勾选至少一个来源')
    return
  }
  showReportEditDialog.value = false
  showReportConfigDialog.value = false
  try {
    const formatMod = editingReportFormat.value
    await studioStore.generateReport(props.notebookId, {
      title: formatMod?.label || t('studio.reportFallbackTitle'),
      source_ids: ids.length > 0 ? ids : undefined,
      report_format: reportForm.report_format,
      report_language: reportForm.report_language,
      report_custom_prompt: reportForm.report_custom_prompt || undefined,
    })
    snackbar.success('报告已生成')
  } catch (err) {
    notifyStudioGenerationFailure(err, '生成失败')
  }
}

const saveReportOptions = async () => {
  if (!editingReportData.value) return
  try {
    await studioStore.updateReport(editingReportData.value.id, {
      report_format: reportForm.report_format,
      report_language: reportForm.report_language,
      report_custom_prompt: reportForm.report_custom_prompt || undefined,
    })
    showReportEditDialog.value = false
    snackbar.success('已保存')
  } catch {
    snackbar.error('保存失败')
  }
}

const handleRegenerateReport = async () => {
  if (!editingReportData.value) return
  try {
    await studioStore.regenerateReport(editingReportData.value.id, {
      report_format: reportForm.report_format,
      report_language: reportForm.report_language,
      report_custom_prompt: reportForm.report_custom_prompt || undefined,
    })
    showReportEditDialog.value = false
    snackbar.success('正在重新生成报告')
  } catch (err) {
    notifyStudioGenerationFailure(err, '重新生成失败')
  }
}

const handleDeleteReport = async (reportId: string) => {
  try {
    const okReport = await confirmStore.confirm({
      title: '删除报告',
      text: '删除此报告？',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    if (!okReport) return
    await studioStore.removeReport(reportId)
    snackbar.success('已删除')
  } catch {
    // cancelled
  }
}

const formatDate = (dateStr: string) => {
  const tag = locale.value === 'zh-CN' ? 'zh-CN' : 'en-US'
  return new Date(dateStr).toLocaleDateString(tag, {
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

.studio-panel--compact .modules-grid {
  grid-template-columns: 1fr;
}

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
  flex-direction: row;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.15s;
  position: relative;
}

/* 思维导图：淡紫，图标与文字为同色系深紫 */
.module-card--mindmap {
  background: #e8dff8;
}

.module-card--mindmap .module-icon,
.module-card--mindmap .module-label {
  color: #5c4d7a;
}

/* 报告：淡米白/橄榄绿，图标与文字为同色系深绿 */
.module-card--report {
  background: #f0f0e8;
}

.module-card--report .module-icon,
.module-card--report .module-label {
  color: #5c6047;
}

/* 信息图：淡紫粉，图标与文字为同色系深粉紫 */
.module-card--infographic {
  background: #f2e8f8;
}

.module-card--infographic .module-icon,
.module-card--infographic .module-label {
  color: #8b5b7a;
}

/* 演示文稿：淡米白，图标与文字为同色系深棕黄 */
.module-card--slides {
  background: #f7f7f0;
}

.module-card--slides .module-icon,
.module-card--slides .module-label {
  color: #7a6b55;
}

/* 音频概览：与其它模块同宽同高，浅蓝底 + 右侧选项图标 */
.module-card--audio-split {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.module-card--audio-split:not(.module-card--disabled) {
  background: #e8eaf6;
  border-color: #d5dae8;
}

.module-card--audio-split:not(.module-card--disabled):hover {
  border-color: var(--primary-color);
}

.module-card-audio-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  margin: 0;
  padding: 0;
  border: none;
  background: transparent;
  font: inherit;
  text-align: left;
  cursor: pointer;
  color: inherit;
}

.module-card-audio-main:disabled {
  cursor: not-allowed;
}

.module-card-audio-main:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
  border-radius: 8px;
}

.module-card-audio-icon-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.module-card-audio-wave {
  color: #3d5a80;
}

.module-card-audio-sparkle {
  position: absolute;
  top: -4px;
  right: -5px;
  color: #3d5a80;
  opacity: 0.9;
}

.module-card-audio-label {
  color: #3d5a80;
  font-weight: 500;
}

.module-card--audio-split .module-card-audio-options.module-edit-btn,
.module-card--infographic .module-card-audio-options.module-edit-btn,
.module-card--slides .module-card-audio-options.module-edit-btn {
  flex-shrink: 0;
  color: #5a6578;
  opacity: 0.65;
}

.module-card--audio-split:hover:not(.module-card--disabled) .module-card-audio-options.module-edit-btn,
.module-card--infographic:hover:not(.module-card--disabled) .module-card-audio-options.module-edit-btn,
.module-card--slides:hover:not(.module-card--disabled) .module-card-audio-options.module-edit-btn {
  opacity: 1;
  color: #3d5a80;
}

.module-card:hover {
  border-color: var(--primary-color);
}

.module-card--disabled {
  position: relative;
  cursor: not-allowed;
  background: var(--surface-variant, #f1f3f4);
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
  color: var(--text-secondary);
}

.module-card--disabled .module-label {
  position: relative;
  z-index: 1;
  color: var(--text-secondary);
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
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.module-beta {
  font-size: 10px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.module-edit-btn {
  flex-shrink: 0;
  color: var(--text-secondary);
  opacity: 0.6;
  transition: opacity 0.15s, color 0.15s;
  cursor: pointer;
}

.module-card:hover .module-edit-btn {
  opacity: 1;
  color: var(--primary-color);
}

.studio-output {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 12px;
}

.output-header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  margin-bottom: 8px;
}

.output-export-btn-wrap {
  display: inline-flex;
  flex-shrink: 0;
}

.output-export-btn {
  flex-shrink: 0;
  min-width: 32px;
}

.output-generating .rotating {
  animation: studio-spin 1s linear infinite;
}

@keyframes studio-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.output-generating {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.output-item--generating {
  cursor: default;
}

.output-item--generating .output-item-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.output-item-status {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
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
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 32px 16px;
  color: var(--text-secondary);
  font-size: 13px;
}

.output-empty-icon {
  color: var(--text-tertiary, #999);
  margin-bottom: 16px;
}

.output-empty-title {
  margin: 0 0 8px;
  font-size: 14px;
  color: var(--text-primary, #333);
}

.output-empty-desc {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
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

.output-item--error {
  border-color: rgba(var(--v-theme-error), 0.35);
  background: rgba(var(--v-theme-error), 0.04);
}

.output-item--error:hover {
  border-color: rgb(var(--v-theme-error));
}

.output-item-icon {
  color: var(--primary-color);
  flex-shrink: 0;
}

.output-item-icon--error {
  color: rgb(var(--v-theme-error));
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

.output-item--error .output-item-meta {
  color: rgb(var(--v-theme-error));
}

.output-item--rate-limited {
  border-color: rgba(var(--v-theme-warning), 0.4);
  background: rgba(var(--v-theme-warning), 0.08);
}

.output-item--rate-limited:hover {
  border-color: rgb(var(--v-theme-warning));
}

.output-item-icon--rate-limited {
  color: rgb(var(--v-theme-warning));
}

.output-item--rate-limited .output-item-meta {
  color: rgb(var(--v-theme-warning));
}

.output-item-more {
  flex-shrink: 0;
  opacity: 0.7;
}

.output-add {
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
  margin-top: 8px;
}

.add-note-btn {
  padding-left: 24px;
  padding-right: 24px;
}

/* 自定义演示文稿 */
.slide-customize-card .v-card-title {
  padding: 16px 20px;
}

.slide-customize-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.slide-customize-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
}

.slide-customize-close {
  color: var(--text-secondary);
}

.slide-customize-close:hover {
  color: var(--text-primary);
}

.slide-customize-section-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.slide-customize-section {
  margin-bottom: 20px;
}

.slide-customize-section:last-of-type {
  margin-bottom: 0;
}

.slide-customize-row {
  display: flex;
  gap: 16px;
}

.slide-customize-row-item {
  flex: 1;
  min-width: 0;
}

.slide-customize-actions {
  padding: 12px 20px 16px;
  justify-content: flex-end;
}

.slide-style-scroll {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding: 4px 0 8px;
  margin-top: 6px;
  scrollbar-width: thin;
}

.slide-style-scroll::-webkit-scrollbar {
  height: 6px;
}

.slide-style-card {
  flex-shrink: 0;
  position: relative;
  width: 88px;
  padding: 12px 8px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.15s, background-color 0.15s, box-shadow 0.15s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.slide-style-card:hover {
  border-color: var(--border-color);
  background: var(--surface-variant, #f8f9fa);
}

.slide-style-card.is-selected {
  border-color: transparent;
  background: color-mix(in srgb, var(--primary-color) 14%, transparent);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.slide-style-check {
  position: absolute;
  top: 8px;
  right: 8px;
  color: var(--primary-color);
  font-size: 14px;
}

.slide-style-icon {
  color: var(--text-secondary);
}

.slide-style-card.is-selected .slide-style-icon {
  color: var(--primary-color);
}

.slide-style-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
  text-align: center;
}

.slide-customize-select :deep(.v-field) {
  border-radius: 8px;
}

.slide-duration-toggle {
  display: inline-flex;
  gap: 0;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  background: var(--surface-variant, #f1f3f4);
}

.slide-duration-option {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 16px;
  font-size: 13px;
  cursor: pointer;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  transition: background 0.15s, color 0.15s;
  min-width: 72px;
}

.slide-duration-option:hover {
  background: rgba(0, 0, 0, 0.04);
}

.slide-duration-option.is-active {
  background: #fff;
  color: var(--text-primary);
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.slide-duration-check {
  flex-shrink: 0;
}

.slide-customize-textarea :deep(.v-field) {
  border-radius: 8px;
}

/* 音频概览编辑 */
.podcast-customize-card .v-card-title {
  padding: 16px 20px;
}

.podcast-customize-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.podcast-customize-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
}

.podcast-customize-close {
  color: var(--text-secondary);
}

.podcast-customize-close:hover {
  color: var(--text-primary);
}

.podcast-customize-section-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.podcast-customize-actions {
  padding: 12px 20px 16px;
  justify-content: flex-end;
}

.podcast-customize-select :deep(.v-field) {
  border-radius: 8px;
}

.podcast-length-toggle {
  display: inline-flex;
  gap: 0;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  background: var(--surface-variant, #f1f3f4);
}

.podcast-length-option {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 16px;
  font-size: 13px;
  cursor: pointer;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  transition: background 0.15s, color 0.15s;
  min-width: 72px;
}

.podcast-length-option:hover {
  background: rgba(0, 0, 0, 0.04);
}

.podcast-length-option.is-active {
  background: #fff;
  color: var(--text-primary);
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.podcast-length-check {
  flex-shrink: 0;
}

.podcast-customize-textarea :deep(.v-field) {
  border-radius: 8px;
}

.podcast-player-card .v-card-title {
  padding: 12px 16px;
  font-size: 15px;
  font-weight: 600;
}

.podcast-player-header {
  display: flex;
  align-items: center;
  width: 100%;
}

.podcast-player-body {
  padding-top: 0;
}

.podcast-player-audio {
  width: 100%;
}

/* 自定义信息图 */
.infographic-customize-card .v-card-title {
  padding: 16px 20px;
}

.infographic-customize-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.infographic-customize-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
}

.infographic-customize-close {
  color: var(--text-secondary);
}

.infographic-customize-close:hover {
  color: var(--text-primary);
}

.infographic-customize-body {
  padding: 0 20px 8px;
}

.infographic-section {
  margin-bottom: 20px;
}

.infographic-section:last-of-type {
  margin-bottom: 0;
}

.infographic-section-row {
  display: flex;
  gap: 16px;
}

.infographic-section-half {
  flex: 1;
  min-width: 0;
}

.infographic-section-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.infographic-select :deep(.v-field) {
  border-radius: 8px;
}

.infographic-toggle-group {
  display: flex;
  gap: 0;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.infographic-toggle-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 12px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  border-right: 1px solid var(--border-color);
  white-space: nowrap;
  background: #fff;
}

.infographic-toggle-btn:last-child {
  border-right: none;
}

.infographic-toggle-btn:hover {
  background: var(--surface-variant, #f1f3f4);
}

.infographic-toggle-btn.is-active {
  background: color-mix(in srgb, var(--primary-color) 14%, transparent);
  color: var(--primary-color);
  font-weight: 600;
}

.infographic-toggle-check {
  flex-shrink: 0;
}

.infographic-toggle-beta {
  font-size: 10px;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 1px 4px;
  margin-left: 2px;
}

.infographic-style-scroll {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding: 4px 0 8px;
  margin-top: 6px;
  scrollbar-width: thin;
}

.infographic-style-scroll::-webkit-scrollbar {
  height: 6px;
}

.infographic-style-card {
  flex-shrink: 0;
  position: relative;
  width: 88px;
  padding: 12px 8px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.15s, background-color 0.15s, box-shadow 0.15s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.infographic-style-card:hover {
  border-color: var(--border-color);
  background: var(--surface-variant, #f8f9fa);
}

.infographic-style-card.is-selected {
  border-color: transparent;
  background: color-mix(in srgb, var(--primary-color) 14%, transparent);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.infographic-style-check {
  position: absolute;
  top: 8px;
  right: 8px;
  color: var(--primary-color);
  font-size: 14px;
}

.infographic-style-icon {
  color: var(--text-secondary);
}

.infographic-style-card.is-selected .infographic-style-icon {
  color: var(--primary-color);
}

.infographic-style-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
  text-align: center;
}

.infographic-textarea :deep(.v-field) {
  border-radius: 8px;
}

.infographic-customize-actions {
  padding: 12px 20px 16px;
  justify-content: flex-end;
}

/* 报告配置 Dialog */
.report-dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.report-dialog-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
}

.report-dialog-close {
  cursor: pointer;
  color: var(--text-secondary);
  transition: color 0.15s;
}

.report-dialog-close:hover {
  color: var(--text-primary);
}

.report-back-btn {
  cursor: pointer;
  color: var(--text-secondary);
  transition: color 0.15s;
}

.report-back-btn:hover {
  color: var(--text-primary);
}

.report-format-section {
  padding: 0;
}

.report-format-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.report-format-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.report-format-card {
  padding: 14px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  min-height: 90px;
  display: flex;
  flex-direction: column;
}

.report-format-card:hover {
  border-color: var(--primary-color);
  background: var(--surface-variant, #f1f3f4);
}

.report-format-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.report-format-card-title {
  font-size: 14px;
  font-weight: 600;
}

.report-format-card-edit {
  color: var(--text-secondary);
  opacity: 0.6;
  transition: opacity 0.15s, color 0.15s;
  cursor: pointer;
}

.report-format-card:hover .report-format-card-edit {
  opacity: 1;
  color: var(--primary-color);
}

.report-format-card-desc {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
  flex: 1;
}

/* 报告编辑 Dialog */
.report-edit-body {
  padding: 0;
}

.report-edit-format-info {
  background: var(--surface-variant, #f1f3f4);
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 20px;
}

.report-edit-format-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
}

.report-edit-format-desc {
  font-size: 12px;
  color: var(--text-secondary);
}

/* 报告内容预览 */
.report-content-body {
  max-height: 70vh;
  overflow-y: auto;
  padding: 0 8px;
  font-size: 14px;
  line-height: 1.7;
}

.report-content-body :deep(h1) {
  font-size: 22px;
  font-weight: 700;
  margin: 20px 0 12px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border-color);
}

.report-content-body :deep(h2) {
  font-size: 18px;
  font-weight: 600;
  margin: 18px 0 10px;
}

.report-content-body :deep(h3) {
  font-size: 15px;
  font-weight: 600;
  margin: 14px 0 8px;
}

.report-content-body :deep(p) {
  margin: 8px 0;
}

.report-content-body :deep(ul),
.report-content-body :deep(ol) {
  padding-left: 24px;
  margin: 8px 0;
}

.report-content-body :deep(li) {
  margin: 4px 0;
}

.report-content-body :deep(blockquote) {
  border-left: 3px solid var(--primary-color);
  padding: 8px 16px;
  margin: 12px 0;
  background: var(--surface-variant, #f1f3f4);
  border-radius: 0 6px 6px 0;
  color: var(--text-secondary);
}

.report-content-body :deep(code) {
  background: var(--surface-variant, #f1f3f4);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.report-content-body :deep(pre) {
  background: var(--surface-variant, #f1f3f4);
  padding: 12px 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}

.report-content-body :deep(strong) {
  font-weight: 600;
}
</style>
