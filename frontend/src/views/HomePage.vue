<template>
  <div class="home-page">
    <header class="home-header">
      <div class="header-left">
        <AppLogo />
      </div>
      <div class="header-right">
        <v-btn
          variant="text"
          @click="goDiscover"
        >
          <v-icon size="20">mdi-compass-outline</v-icon>
          <span class="header-btn-label">{{ t('home.discoverNav') }}</span>
        </v-btn>
        <v-btn
          variant="text"
          @click="goPricing"
        >
          <span class="header-btn-label">{{ t('home.pricing') }}</span>
        </v-btn>
        <v-btn
          variant="text"
          @click="goSettings"
        >
          <v-icon size="20">mdi-cog</v-icon>
          <span class="header-btn-label">{{ t('home.settings') }}</span>
        </v-btn>
        <v-btn
          variant="text"
          icon
          @click="handleLogout"
        >
          <v-icon size="20">mdi-logout</v-icon>
        </v-btn>
      </div>
    </header>

    <main class="home-main">
      <div class="home-content-card">
        <div class="home-title-row">
          <div class="home-tabs-cluster">
            <div
              class="home-tabs"
              role="tablist"
            >
              <button
                v-for="scopeOpt of notebookScopeOptions"
                :key="scopeOpt.value"
                type="button"
                class="home-tab-btn"
                :class="{ active: notebookScopeTab === scopeOpt.value }"
                role="tab"
                :aria-selected="notebookScopeTab === scopeOpt.value"
                @click="setNotebookScopeTab(scopeOpt.value)"
              >
                {{ scopeOpt.label }}
              </button>
            </div>
          </div>
          <div class="home-actions">
            <div class="view-toggle">
              <button
                type="button"
                class="view-toggle-btn"
                :class="{ active: viewMode === 'grid' }"
                :aria-label="t('home.gridView')"
                @click="viewMode = 'grid'"
              >
                <v-icon size="18">mdi-view-grid</v-icon>
                <v-icon
                  v-if="viewMode === 'grid'"
                  class="view-check"
                  size="14"
                >
                  mdi-check
                </v-icon>
              </button>
              <button
                type="button"
                class="view-toggle-btn"
                :class="{ active: viewMode === 'list' }"
                :aria-label="t('home.listView')"
                @click="viewMode = 'list'"
              >
                <v-icon size="18">mdi-format-list-bulleted</v-icon>
                <v-icon
                  v-if="viewMode === 'list'"
                  class="view-check"
                  size="14"
                >
                  mdi-check
                </v-icon>
              </button>
            </div>
            <v-select
              v-model="sortBy"
              class="sort-select action-bar-select"
              :placeholder="t('home.sortPlaceholder')"
              density="compact"
              hide-details
              :items="sortSelectItems"
              item-title="title"
              item-value="value"
            />
            <v-btn
              class="action-bar-primary-btn"
              :loading="creating"
              @click="handleQuickCreate"
            >
              <v-icon class="mr-1">mdi-plus</v-icon>
              {{ t('home.new') }}
            </v-btn>
          </div>
        </div>

        <div class="home-tab-panel">
          <div v-if="scopeLoading" class="loading-state">
            <v-skeleton-loader
              type="list-item-three-line"
              class="mb-2"
            />
            <v-skeleton-loader
              type="list-item-three-line"
              class="mb-2"
            />
            <v-skeleton-loader type="list-item-three-line" />
          </div>

          <template v-else-if="notebookScopeTab === 'subscribed'">
            <div
              v-if="subscribedRows.length === 0"
              class="empty-state"
            >
              <v-alert
                type="info"
                variant="tonal"
                class="text-center"
              >
                {{ t('home.subscribedEmpty') }}
              </v-alert>
            </div>
            <template v-else>
              <div
                v-show="viewMode === 'grid'"
                class="notebook-grid"
              >
                <div
                  v-for="row of subscribedRows"
                  :key="row.notebook.id"
                  class="notebook-card"
                  :class="{ 'is-disabled': !row.read_available }"
                  @click="onSubscribedCardClick(row)"
                >
                  <div class="card-emoji">{{ getCardEmoji(row.notebook) }}</div>
                  <h3 class="card-title">{{ row.notebook.title }}</h3>
                  <div class="card-meta">
                    <span>{{ formatNotebookDate(row.notebook.updated_at) }}</span>
                    <span>{{ t('chat.sourceCount', { count: row.notebook.source_count }) }}</span>
                  </div>
                  <div
                    v-if="!row.read_available"
                    class="card-unavailable"
                  >
                    {{ t('home.subscribedUnavailable') }}
                  </div>
                </div>
              </div>
              <div
                v-show="viewMode === 'list'"
                class="notebook-list-wrap"
              >
                <div class="notebook-list-header">
                  <div class="col-title">{{ t('home.colTitle') }}</div>
                  <div class="col-sources">{{ t('home.colSources') }}</div>
                  <div class="col-date">{{ t('home.colDate') }}</div>
                  <div class="col-role">{{ t('home.subscribedReader') }}</div>
                  <div class="col-actions" />
                </div>
                <div
                  v-for="row of subscribedRows"
                  :key="row.notebook.id"
                  class="notebook-list-row"
                  :class="{ 'is-disabled': !row.read_available }"
                  @click="onSubscribedCardClick(row)"
                >
                  <div class="col-title">
                    <span class="row-emoji">{{ getCardEmoji(row.notebook) }}</span>
                    <span class="row-title-text">{{ row.notebook.title }}</span>
                  </div>
                  <div class="col-sources">{{ t('chat.sourceCount', { count: row.notebook.source_count }) }}</div>
                  <div class="col-date">{{ formatNotebookDate(row.notebook.created_at) }}</div>
                  <div class="col-role">
                    {{ row.read_available ? t('home.subscribedReader') : t('home.subscribedUnavailable') }}
                  </div>
                  <div class="col-actions" />
                </div>
              </div>
            </template>
          </template>

          <div
            v-else-if="displayedNotebookList.length === 0"
            class="empty-state"
          >
            <v-alert
              type="info"
              variant="tonal"
              class="text-center"
            >
              {{ t('home.emptyHint') }}
            </v-alert>
          </div>

          <template v-else>
            <div v-show="viewMode === 'grid'" class="notebook-grid">
              <div
                class="notebook-card notebook-card--new"
                @click="handleQuickCreate"
              >
                <div class="card-new-icon">
                  <v-icon size="32">mdi-plus</v-icon>
                </div>
                <span class="card-new-label">{{ t('home.newNotebookCard') }}</span>
              </div>
              <div
                v-for="nb of displayedNotebookList"
                :key="nb.id"
                class="notebook-card"
                @click="goNotebook(nb.id)"
              >
                <div class="card-emoji">{{ getCardEmoji(nb) }}</div>
                <h3 class="card-title">
                  {{ nb.title }}
                  <v-chip
                    v-if="notebookScopeTab === 'mine' && publishedIdSet.has(nb.id)"
                    size="x-small"
                    class="ml-2"
                    color="primary"
                    variant="tonal"
                  >
                    {{ t('home.discoverPublishedBadge') }}
                  </v-chip>
                </h3>
                <div class="card-meta">
                  <span>{{ formatNotebookDate(nb.updated_at) }}</span>
                  <span>{{ t('chat.sourceCount', { count: nb.source_count }) }}</span>
                </div>
                <div
                  class="card-actions"
                  @click.stop
                >
                  <v-menu location="bottom">
                    <template #activator="{ props: menuProps }">
                      <v-btn
                        v-bind="menuProps"
                        icon
                        variant="text"
                        size="small"
                        class="card-more-btn"
                      >
                        <v-icon>mdi-dots-vertical</v-icon>
                      </v-btn>
                    </template>
                    <v-list>
                      <v-list-item
                        @click="openEditDialog(nb)"
                      >
                        {{ t('home.rename') }}
                      </v-list-item>
                      <v-list-item
                        @click="handleDelete(nb.id)"
                      >
                        {{ t('home.delete') }}
                      </v-list-item>
                    </v-list>
                  </v-menu>
                </div>
              </div>
            </div>

            <div v-show="viewMode === 'list'" class="notebook-list-wrap">
              <div class="notebook-list-header">
                <div class="col-title">{{ t('home.colTitle') }}</div>
                <div class="col-sources">{{ t('home.colSources') }}</div>
                <div class="col-date">{{ t('home.colDate') }}</div>
                <div class="col-role">{{ t('home.colRole') }}</div>
                <div class="col-actions" />
              </div>
              <div
                v-for="nb of displayedNotebookList"
                :key="nb.id"
                class="notebook-list-row"
                @click="goNotebook(nb.id)"
              >
                <div class="col-title">
                  <span class="row-emoji">{{ getCardEmoji(nb) }}</span>
                  <span class="row-title-text">{{ nb.title }}</span>
                  <v-chip
                    v-if="notebookScopeTab === 'mine' && publishedIdSet.has(nb.id)"
                    size="x-small"
                    class="ml-2"
                    color="primary"
                    variant="tonal"
                  >
                    {{ t('home.discoverPublishedBadge') }}
                  </v-chip>
                </div>
                <div class="col-sources">{{ t('chat.sourceCount', { count: nb.source_count }) }}</div>
                <div class="col-date">{{ formatNotebookDate(nb.created_at) }}</div>
                <div class="col-role">{{ t('home.owner') }}</div>
                <div
                  class="col-actions"
                  @click.stop
                >
                  <v-menu location="bottom">
                    <template #activator="{ props: menuProps }">
                      <v-btn
                        v-bind="menuProps"
                        icon
                        variant="text"
                        size="small"
                        class="row-action-btn"
                      >
                        <v-icon>mdi-dots-vertical</v-icon>
                      </v-btn>
                    </template>
                    <v-list>
                      <v-list-item @click="openEditDialog(nb)">
                        {{ t('home.rename') }}
                      </v-list-item>
                      <v-list-item @click="handleDelete(nb.id)">
                        {{ t('home.delete') }}
                      </v-list-item>
                    </v-list>
                  </v-menu>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </main>

    <v-dialog
      v-model="showEditDialog"
      max-width="480"
      persistent
    >
      <v-card>
        <v-card-title>{{ t('home.renameDialogTitle') }}</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="editNotebook.title"
            :label="t('home.fieldTitle')"
          />
          <v-textarea
            v-model="editNotebook.description"
            :label="t('home.fieldDescription')"
            rows="3"
            class="mt-2"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            variant="text"
            @click="showEditDialog = false"
          >
            {{ t('common.cancel') }}
          </v-btn>
          <v-btn
            color="primary"
            @click="handleEdit"
          >
            {{ t('common.save') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useRouteLocale } from '@/i18n/useRouteLocale'
import AppLogo from '@/components/AppLogo.vue'
import { useNotebookStore } from '@/stores/useNotebookStore'
import { useUserStore } from '@/stores/useUserStore'
import { useSnackbarStore } from '@/stores/useSnackbarStore'
import { useConfirmStore } from '@/stores/useConfirmStore'
import {
  notebookApi,
  type Notebook as NotebookType,
  type SubscribedNotebookItem,
} from '@/api/notebook'
const VIEW_MODE_KEY = 'notebook-list-view'

type NotebookScopeTab = 'mine' | 'published' | 'subscribed'

const { t, locale: i18nLocale } = useI18n()
const router = useRouter()
const routeLocale = useRouteLocale()
const userStore = useUserStore()
const notebookStore = useNotebookStore()
const snackbar = useSnackbarStore()
const confirmStore = useConfirmStore()

const showEditDialog = ref(false)
const creating = ref(false)
const editNotebook = reactive({ id: '', title: '', description: '' })

const viewMode = ref<'grid' | 'list'>('grid')
const notebookScopeTab = ref<NotebookScopeTab>('mine')
const sortBy = ref<'recent' | 'created' | 'title'>('recent')
const scopeLoading = ref(false)
const publishedList = ref<NotebookType[]>([])
const subscribedRows = ref<SubscribedNotebookItem[]>([])
const publishedIdSet = ref<Set<string>>(new Set())

const sortSelectItems = computed(() => [
  { title: t('home.sortRecent'), value: 'recent' as const },
  { title: t('home.sortCreated'), value: 'created' as const },
  { title: t('home.sortTitle'), value: 'title' as const },
])

const notebookScopeOptions = computed(() => [
  { value: 'mine' as const, label: t('home.notebookTabMine') },
  { value: 'published' as const, label: t('home.notebookTabPublished') },
  { value: 'subscribed' as const, label: t('home.notebookTabSubscribed') },
])

function loadViewMode() {
  const saved = localStorage.getItem(VIEW_MODE_KEY) as 'grid' | 'list' | null
  if (saved === 'grid' || saved === 'list') {
    viewMode.value = saved
  }
}

function setNotebookScopeTab(tab: NotebookScopeTab) {
  notebookScopeTab.value = tab
  void loadNotebookScope()
}

async function loadNotebookScope() {
  scopeLoading.value = true
  try {
    if (notebookScopeTab.value === 'mine') {
      await notebookStore.fetchNotebooks()
      try {
        const r = await notebookApi.listPublished()
        publishedIdSet.value = new Set(r.notebooks.map((n) => n.id))
      } catch {
        publishedIdSet.value = new Set()
      }
    } else if (notebookScopeTab.value === 'published') {
      const r = await notebookApi.listPublished()
      publishedList.value = r.notebooks
    } else {
      const r = await notebookApi.listSubscriptions()
      subscribedRows.value = r.items
    }
  } catch {
    if (notebookScopeTab.value === 'published') {
      publishedList.value = []
    }
    if (notebookScopeTab.value === 'subscribed') {
      subscribedRows.value = []
    }
  } finally {
    scopeLoading.value = false
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
  void loadNotebookScope()
})

function applyNotebookSort(list: NotebookType[]): NotebookType[] {
  const arr = [...list]
  if (sortBy.value === 'recent') {
    arr.sort(
      (a, b) =>
        new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
    )
  } else if (sortBy.value === 'created') {
    arr.sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    )
  } else {
    arr.sort((a, b) =>
      a.title.localeCompare(
        b.title,
        i18nLocale.value === 'zh-CN' ? 'zh-CN' : 'en',
      ),
    )
  }
  return arr
}

const sortedNotebooks = computed(() => applyNotebookSort(notebookStore.notebooks))

const displayedNotebookList = computed(() => {
  if (notebookScopeTab.value === 'mine') {
    return sortedNotebooks.value
  }
  if (notebookScopeTab.value === 'published') {
    return applyNotebookSort(publishedList.value)
  }
  return []
})

function goDiscover() {
  router.push({ name: 'Discover', params: { locale: routeLocale.value } })
}

function goPricing() {
  router.push({ name: 'Pricing', params: { locale: routeLocale.value } })
}

function goSettings() {
  router.push({ name: 'Settings', params: { locale: routeLocale.value } })
}

function goNotebook(id: string) {
  router.push({
    name: 'NotebookDetail',
    params: { locale: routeLocale.value, id },
  })
}

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

const handleQuickCreate = async () => {
  if (creating.value) return
  creating.value = true
  try {
    const nb = await notebookStore.createNotebook('Untitled notebook')
    goNotebook(nb.id)
  } catch (err: unknown) {
    const detail = extractErrorDetail(err)
    snackbar.error(detail || t('home.createFailed'))
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
    snackbar.success(t('home.updateSuccess'))
  } catch {
    snackbar.error(t('home.updateFailed'))
  }
}

const handleDelete = async (id: string) => {
  try {
    const ok = await confirmStore.confirm({
      title: 'Delete Notebook',
      text: 'Delete this notebook and all its contents?',
      confirmButtonText: 'Delete',
      cancelButtonText: 'Cancel',
    })
    if (!ok) return
    await notebookStore.deleteNotebook(id)
    snackbar.success(t('home.deleteSuccess'))
    void loadNotebookScope()
  } catch {
    // cancelled
  }
}

const handleLogout = () => {
  userStore.logout()
  router.push({ name: 'Login', params: { locale: routeLocale.value } })
}

const formatNotebookDate = (dateStr: string) => {
  const d = new Date(dateStr)
  const tag = i18nLocale.value === 'zh-CN' ? 'zh-CN' : 'en-US'
  return d.toLocaleDateString(tag, {
    year: 'numeric',
    month: i18nLocale.value === 'zh-CN' ? 'long' : 'short',
    day: 'numeric',
  })
}

function goSharedNotebook(shareToken: string) {
  router.push({
    name: 'SharedNotebook',
    params: { locale: routeLocale.value, shareToken },
  })
}

function onSubscribedCardClick(row: SubscribedNotebookItem) {
  if (!row.read_available || !row.share_token) {
    snackbar.error(t('home.subscribedUnavailable'))
    return
  }
  goSharedNotebook(row.share_token)
}

const extractErrorDetail = (err: unknown): string | null => {
  if (
    err &&
    typeof err === 'object' &&
    'response' in err
  ) {
    const axiosErr = err as { response?: { data?: { detail?: string } } }
    return axiosErr.response?.data?.detail || null
  }
  return null
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

.header-left .app-logo {
  cursor: default;
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
  margin: 0 auto;
  padding: 32px 24px;
}

/* 红框风格：主内容区 - 宽度占版式 90%、白底、轻微阴影、圆角 */
.home-content-card {
  width: 90%;
  margin: 0 auto;
  padding: 24px 28px 32px;
  background: var(--home-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.home-title-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 24px;
}

.home-tabs-cluster {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 12px 20px;
  flex: 1 1 auto;
  min-width: 0;
  border-bottom: 1px solid var(--home-border);
  padding-bottom: 0;
}

.home-tabs {
  display: inline-flex;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 4px 16px;
  min-width: 0;
  padding-bottom: 0;
}

.home-tab-btn {
  padding: 8px 14px 10px;
  margin-bottom: -1px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-size: 18px;
  font-weight: 600;
  color: var(--home-text-secondary);
  transition: color 0.2s, border-color 0.2s;
}

.home-tab-btn:hover {
  color: var(--home-text);
}

.home-tab-btn.active {
  color: var(--home-text);
  border-bottom-color: var(--home-text);
}

.home-tab-panel {
  min-height: 0;
}

.home-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 红框风格：分段视图切换 - 浅灰/深灰、无间隙、圆角 */
.view-toggle {
  display: inline-flex;
  background: var(--action-bar-inactive-bg);
  border: 1px solid var(--action-bar-border);
  border-radius: 8px;
  overflow: hidden;
  gap: 0;
}

.view-toggle-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 12px;
  background: var(--action-bar-inactive-bg);
  border: none;
  color: var(--home-text);
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.view-toggle-btn:hover {
  background: var(--action-bar-hover-bg);
  color: var(--home-text);
}

.view-toggle-btn.active {
  background: var(--action-bar-active-bg);
  color: var(--home-text);
}

.view-check {
  margin-left: 2px;
  color: var(--home-text);
}

/* 红框风格：下拉「最近」- 浅灰背景、圆角 */
.action-bar-select {
  max-width: 120px;
}

.action-bar-select :deep(.v-field) {
  background: var(--action-bar-inactive-bg) !important;
  border: 1px solid var(--action-bar-border);
  border-radius: 8px;
  box-shadow: none;
}

.action-bar-select :deep(.v-field__input) {
  color: var(--home-text);
}

.action-bar-select :deep(.v-field__outline) {
  --v-field-border-opacity: 0;
}

/* 红框风格：主按钮「+ 新建」- 黑色背景、白色文字、圆角 */
.action-bar-primary-btn {
  background: var(--action-bar-primary-bg) !important;
  color: var(--action-bar-primary-text) !important;
  border-radius: 8px;
  text-transform: none;
}

.action-bar-primary-btn:hover {
  opacity: 0.9;
}

.notebook-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
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
  border-radius: var(--radius);
  overflow: hidden;
  border: none;
}

/* 列表表头：浅灰背景、细分割线，与参考红框一致 */
.notebook-list-header {
  display: flex;
  align-items: center;
  height: 48px;
  padding: 0 16px;
  background: var(--list-header-bg);
  border-bottom: 1px solid var(--home-border);
  font-size: 13px;
  font-weight: 500;
  color: var(--home-text-secondary);
  flex-shrink: 0;
}

/* 每一行：固定高度 + flex 水平排列 + 垂直居中，保证同一行内所有内容一条线 */
.notebook-list-row {
  display: flex;
  align-items: center;
  height: 52px;
  padding: 0 16px;
  border-bottom: 1px solid var(--home-border);
  cursor: pointer;
  transition: background 0.2s;
  flex-shrink: 0;
}

.notebook-list-row:last-child {
  border-bottom: none;
}

.notebook-list-row:hover {
  background: var(--list-row-hover-bg);
}

/* 列宽比例：标题 2/5，来源 / 创建日期 / 角色 各 1/5 */
.notebook-list-header .col-title,
.notebook-list-row .col-title {
  flex: 2 1 0;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.notebook-list-row .col-title {
  color: var(--home-text);
  font-weight: 500;
  font-size: 14px;
}

.row-emoji {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  line-height: 1;
}

.row-title-text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notebook-list-header .col-sources,
.notebook-list-header .col-date,
.notebook-list-header .col-role,
.notebook-list-row .col-sources,
.notebook-list-row .col-date,
.notebook-list-row .col-role {
  flex: 1 1 0;
  font-size: 13px;
  color: var(--home-text-secondary);
  white-space: nowrap;
}

.notebook-list-header .col-actions,
.notebook-list-row .col-actions {
  width: 32px;
  flex: 0 0 32px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.row-action-btn {
  color: var(--home-text-secondary);
}

.row-action-btn:hover {
  color: var(--home-text);
}

.notebook-list-row .col-actions :deep(.v-btn) {
  min-height: 32px;
  height: 32px;
  width: 32px;
}

.notebook-card.is-disabled,
.notebook-list-row.is-disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.card-unavailable {
  margin-top: 6px;
  font-size: 12px;
  color: var(--home-text-secondary);
}

.loading-state,
.empty-state {
  margin-top: 60px;
}
</style>
