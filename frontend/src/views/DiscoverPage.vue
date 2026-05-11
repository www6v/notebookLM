<template>

  <div class="discover-page">
    <header class="discover-header">
      <h1 class="discover-title">{{ t('discover.title') }}</h1>
      <div class="discover-header-actions">
        <v-text-field
          v-model="searchInput"
          density="compact"
          variant="outlined"
          hide-details
          clearable
          class="discover-search"
          :placeholder="t('discover.searchPlaceholder')"
          prepend-inner-icon="mdi-magnify"
          @keyup.enter="runSearch"
          @click:clear="runSearch"
        />
        <v-btn
          variant="text"
          icon
          :title="t('discover.refresh')"
          @click="shuffleFeatured"
        >
          <v-icon>mdi-refresh</v-icon>
        </v-btn>
      </div>
    </header>

    <v-progress-linear
      v-if="listLoading"
      indeterminate
      color="primary"
      class="discover-progress"
    />

    <main class="discover-main">
      <section class="discover-section">
        <div class="discover-section-head">
          <h2 class="discover-section-title">{{ t('discover.featured') }}</h2>
        </div>
        <div
          v-if="featuredLoading"
          class="discover-skeleton"
        >
          <v-skeleton-loader type="card" />
        </div>
        <div
          v-else
          class="discover-featured-grid"
        >
          <DiscoverNotebookCard
            v-for="item of featuredItems"
            :key="item.share_token"
            :title="item.title"
            :description="''"
            :subscriber-count="0"
            :source-count="item.source_count"
            :owner-label="t('discover.featuredCurated')"
            :cover-url="''"
            :show-subscribe="false"
            @open="() => onOpenFeatured(item)"
            @subscribe="onSubscribeFeaturedStub"
          />
        </div>
      </section>

      <section class="discover-section">
        <v-tabs
          v-model="categoryTab"
          class="discover-tabs"
          color="primary"
          @update:model-value="onCategoryChange"
        >
          <v-tab
            v-for="tab of categoryTabs"
            :key="tab.value"
            :value="tab.value"
          >
            {{ tab.label }}
          </v-tab>
        </v-tabs>

        <div
          v-if="listLoadFailed"
          class="discover-empty"
        >
          {{ t('discover.listFailed') }}
        </div>
        <div
          v-else-if="!listLoading && items.length === 0"
          class="discover-empty"
        >
          {{ t('discover.listEmpty') }}
        </div>
        <v-row
          v-else
          class="discover-grid"
        >
          <v-col
            v-for="item of items"
            :key="item.id"
            cols="12"
            md="6"
          >
            <DiscoverNotebookCard
              :title="item.title"
              :description="item.description"
              :subscriber-count="item.subscriber_count"
              :source-count="item.source_count"
              :owner-label="item.owner_display_name"
              :cover-url="item.cover_url"
              :show-subscribe="userStore.isLoggedIn"
              @open="onOpenDiscoverItem(item)"
              @subscribe="onSubscribeById(item.id)"
            />
          </v-col>
        </v-row>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import DiscoverNotebookCard from '@/components/discover/DiscoverNotebookCard.vue'
import {
  fetchDiscoverNotebooks,
  fetchDiscoverNotebookDetail,
  subscribeDiscoverNotebook,
  type DiscoverNotebookListItem,
} from '@/api/discover'
import {
  fetchPublicFeaturedNotebooks,
  type PublicFeaturedNotebookItem,
} from '@/api/publicClient'
import { useRouteLocale } from '@/i18n/useRouteLocale'
import { useUserStore } from '@/stores/useUserStore'
import { useSnackbarStore } from '@/stores/useSnackbarStore'

defineOptions({
  name: 'DiscoverPage',
})

const { t, locale } = useI18n()
const router = useRouter()
const routeLocale = useRouteLocale()
const userStore = useUserStore()
const snackbar = useSnackbarStore()

const searchInput = ref('')
const listLoading = ref(false)
const listLoadFailed = ref(false)
const items = ref<DiscoverNotebookListItem[]>([])
const categoryTab = ref('all')

const featuredLoading = ref(false)
const featuredItems = ref<PublicFeaturedNotebookItem[]>([])

const categoryTabs = computed(() => {
  const isZh = locale.value === 'zh-CN'
  const labels = isZh
    ? ['推荐', '科技', '教育', '职场', '财经', '产业', '健康', '法律', '人文', '生活']
    : ['For you', 'Tech', 'Education', 'Work', 'Finance', 'Industry', 'Health', 'Law', 'Culture', 'Life']
  const values = [
    'all',
    'tech',
    'education',
    'workplace',
    'finance',
    'industry',
    'health',
    'law',
    'humanities',
    'life',
  ]
  return labels.map((label, i) => ({ label, value: values[i] }))
})

async function loadList() {
  listLoading.value = true
  listLoadFailed.value = false
  try {
    const cat =
      categoryTab.value === 'all' ? undefined : categoryTab.value
    const res = await fetchDiscoverNotebooks({
      q: searchInput.value.trim() || undefined,
      category: cat,
      offset: 0,
      limit: 24,
    })
    items.value = res.items
  } catch {
    items.value = []
    listLoadFailed.value = true
  } finally {
    listLoading.value = false
  }
}

async function loadFeatured() {
  featuredLoading.value = true
  try {
    featuredItems.value = await fetchPublicFeaturedNotebooks()
  } catch {
    featuredItems.value = []
  } finally {
    featuredLoading.value = false
  }
}

function shuffleFeatured() {
  void loadFeatured()
  void loadList()
}

function runSearch() {
  void loadList()
}

function onCategoryChange() {
  void loadList()
}

function goShared(shareToken: string) {
  router.push({
    name: 'SharedNotebook',
    params: { locale: routeLocale.value, shareToken },
  })
}

function onOpenFeatured(item: PublicFeaturedNotebookItem) {
  goShared(item.share_token)
}

function onSubscribeFeaturedStub() {
  /* Featured rows have no notebook id for the subscribe API. */
}

async function onOpenDiscoverItem(item: DiscoverNotebookListItem) {
  try {
    const detail = await fetchDiscoverNotebookDetail(item.id)
    if (detail.share_token) {
      goShared(detail.share_token)
    } else {
      snackbar.error(t('discover.readUnavailable'))
    }
  } catch {
    snackbar.error(t('discover.readUnavailable'))
  }
}

async function onSubscribeById(notebookId: string) {
  if (!userStore.isLoggedIn) {
    router.push({ name: 'Login', params: { locale: routeLocale.value } })
    return
  }
  try {
    await subscribeDiscoverNotebook(notebookId)
    snackbar.success(t('discover.subscribeOk'))
    void loadList()
  } catch {
    snackbar.error(t('discover.subscribeFailed'))
  }
}

onMounted(() => {
  void loadFeatured()
  void loadList()
})

watch(
  () => userStore.isLoggedIn,
  () => {
    void loadList()
  },
)
</script>

<style scoped>
.discover-page {
  min-height: 100vh;
  padding: 24px 20px 48px;
  max-width: 1100px;
  margin: 0 auto;
}

.discover-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 8px;
}

.discover-title {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
}

.discover-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 260px;
  flex: 1;
  justify-content: flex-end;
}

.discover-search {
  max-width: 360px;
  flex: 1;
}

.discover-progress {
  margin-bottom: 8px;
}

.discover-main {
  margin-top: 16px;
}

.discover-section {
  margin-bottom: 32px;
}

.discover-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.discover-section-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.discover-featured-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.discover-tabs {
  margin-bottom: 16px;
}

.discover-grid {
  margin-top: 8px;
}

.discover-empty {
  padding: 24px;
  text-align: center;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.discover-skeleton {
  max-width: 400px;
}
</style>
