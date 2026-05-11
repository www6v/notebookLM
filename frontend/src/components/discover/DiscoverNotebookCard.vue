<template>

  <v-card
    variant="outlined"
    class="discover-nb-card"
    role="button"
    tabindex="0"
    @click="onOpen"
    @keydown.enter="onOpen"
  >
    <div class="discover-nb-card-inner">
      <div
        class="discover-nb-thumb"
        :style="thumbStyle"
      />
      <div class="discover-nb-body">
        <h3 class="discover-nb-title">{{ title }}</h3>
        <p class="discover-nb-desc">{{ truncatedDescription }}</p>
        <div class="discover-nb-meta">
          <span>{{ t('discover.subscriberCountLabel', { count: subscriberCount }) }}</span>
          <span>|</span>
          <span>{{ t('chat.sourceCount', { count: sourceCount }) }}</span>
          <span>|</span>
          <span>{{ ownerLabel }}</span>
        </div>
        <div
          v-if="showSubscribe"
          class="discover-nb-actions"
          @click.stop
        >
          <v-btn
            size="small"
            variant="tonal"
            color="primary"
            @click="onSubscribe"
          >
            {{ t('discover.subscribe') }}
          </v-btn>
        </div>
      </div>
    </div>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

defineOptions({
  name: 'DiscoverNotebookCard',
})

const props = defineProps<{
  title: string
  description: string
  subscriberCount: number
  sourceCount: number
  ownerLabel: string
  coverUrl: string
  showSubscribe?: boolean
}>()

const emit = defineEmits<{
  'open': []
  'subscribe': []
}>()

const { t } = useI18n()

function onOpen() {
  emit('open')
}

function onSubscribe() {
  emit('subscribe')
}

const truncatedDescription = computed(() => {
  const s = props.description.trim()
  if (s.length <= 120) {
    return s || t('discover.noDescription')
  }
  return `${s.slice(0, 117)}…`
})

const thumbStyle = computed(() => {
  if (!props.coverUrl) {
    return { background: 'linear-gradient(135deg,#e2e8f0,#cbd5e1)' }
  }
  return {
    backgroundImage: `url(${props.coverUrl})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
  }
})
</script>

<style scoped>
.discover-nb-card {
  cursor: pointer;
  border-radius: 12px;
  transition: box-shadow 0.15s ease;
}

.discover-nb-card:hover {
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
}

.discover-nb-card-inner {
  display: flex;
  gap: 14px;
  padding: 14px 16px;
  align-items: stretch;
}

.discover-nb-thumb {
  width: 72px;
  min-height: 72px;
  flex-shrink: 0;
  border-radius: 8px;
  background: #e2e8f0;
}

.discover-nb-body {
  flex: 1;
  min-width: 0;
}

.discover-nb-title {
  margin: 0 0 6px;
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.35;
}

.discover-nb-desc {
  margin: 0 0 8px;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.65);
  line-height: 1.45;
}

.discover-nb-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.55);
}

.discover-nb-actions {
  margin-top: 10px;
}
</style>
