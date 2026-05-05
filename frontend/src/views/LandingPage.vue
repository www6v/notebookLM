<template>
  <div class="landing-page">

    <a
      class="skip-link"
      href="#landing-main"
    >
      {{ t('common.skipToContent') }}
    </a>
    <div
      class="landing-stars"
      aria-hidden="true"
    />
    <div
      class="landing-atmosphere"
      aria-hidden="true"
    />
    <div
      class="landing-grain"
      aria-hidden="true"
    />

    <header class="landing-header">
      <AppLogo />
      <div class="landing-header-actions">
        <label class="header-lang-wrap">
          <span class="sr-only">{{ t('common.downloadMenuLabel') }}</span>
          <select
            class="header-lang-select"
            @change="handleDownloadPlatformChange"
          >
            <option value="">
              {{ t('common.download') }}
            </option>
            <option value="mac">
              Mac
            </option>
            <option value="windows">
              Windows
            </option>
            <option value="linux">
              Linux
            </option>
          </select>
        </label>
        <a
          class="header-github-link"
          href="https://github.com/www6v/notebookLM"
          target="_blank"
          rel="noopener noreferrer"
          :aria-label="t('common.githubRepository')"
        >
          <svg
            class="header-github-icon"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 98 96"
            width="22"
            height="22"
            aria-hidden="true"
          >
            <path
              fill-rule="evenodd"
              clip-rule="evenodd"
              d="M48.854 0C21.839 0 0 22 0 49.217c0 21.756 13.993 40.172 33.405 46.69 2.427.49 3.316-1.059 3.316-2.362 0-1.141-.08-5.052-.08-9.127-13.59 2.934-16.42-5.867-16.42-5.867-2.184-5.704-5.42-7.17-5.42-7.17-4.448-3.015.324-3.015.324-3.015 4.934.326 7.523 5.052 7.523 5.052 4.367 7.496 11.404 5.378 14.235 4.074.404-3.178 1.699-5.378 3.074-6.6-10.839-1.141-22.23-5.378-22.23-24.283 0-5.378 1.94-9.778 5.014-13.2-.485-1.222-2.184-6.275.486-13.038 0 0 4.125-1.304 13.426 5.052a46.97 46.97 0 0 1 12.214-1.63c4.125 0 8.33.571 12.213 1.63 9.302-6.356 13.427-5.052 13.427-5.052 2.67 6.763.97 11.816.485 13.038 3.155 3.422 5.014 7.822 5.014 13.2 0 18.905-11.404 23.06-22.324 24.283 1.78 1.548 3.316 4.481 3.316 9.126 0 6.6-.08 11.897-.08 13.526 0 1.304.89 2.853 3.316 2.364 19.412-6.52 33.405-24.935 33.405-46.691C97.707 22 75.788 0 48.854 0z"
              fill="currentColor"
            />
          </svg>
        </a>
        <label class="header-lang-wrap">
          <span class="sr-only">{{ t('common.localeSelector') }}</span>
          <select
            class="header-lang-select"
            :value="locale"
            @change="handleLocaleChange"
          >
            <option value="en">
              English
            </option>
            <option value="zh-CN">
              中文
            </option>
          </select>
        </label>
        <router-link
          :to="toLogin"
          class="header-cta"
        >
          {{ t('common.login') }}
        </router-link>
      </div>
    </header>

    <main
      id="landing-main"
      class="landing-main"
    >
      <section
        class="hero"
        aria-labelledby="hero-title"
      >
        <div class="hero-layout">
          <div class="hero-copy">
            <p class="hero-kicker">
              {{ t('landing.heroKicker') }}
            </p>
            <h1
              id="hero-title"
              class="hero-title"
            >
              <span class="hero-title-accent">{{ t('landing.heroTitleAccent') }}</span><span class="hero-title-plain">{{ t('landing.heroTitlePlain') }}</span>
            </h1>
            <p class="hero-subtitle">
              {{ t('landing.heroSubtitle') }}
            </p>
            <div class="hero-actions">
              <router-link
                :to="toLogin"
                class="btn-hero-primary"
              >
                {{ t('landing.getStarted') }}
              </router-link>
              <router-link
                :to="toPricing"
                class="btn-hero-ghost"
              >
                {{ t('landing.getStartedSecondary') }}
              </router-link>
            </div>
          </div>
          <div
            class="hero-visual"
            aria-hidden="true"
          >
            <div class="hero-showcase">
              <div class="hero-showcase__ambient" />
              <div class="hero-showcase__stack">
                <div class="hero-deck-card hero-deck-card--rear" />
                <div class="hero-deck-card hero-deck-card--mid" />
                <article class="hero-panel">
                  <div class="hero-panel__chrome">
                    <span class="hero-panel__chrome-dot" />
                    <span class="hero-panel__chrome-dot" />
                    <span class="hero-panel__chrome-dot" />
                  </div>
                  <div class="hero-panel__toolbar">
                    <span class="hero-panel__toolbar-pill" />
                    <span class="hero-panel__toolbar-pill hero-panel__toolbar-pill--short" />
                  </div>
                  <div class="hero-panel__body">
                    <span class="hero-panel__line hero-panel__line--title" />
                    <span class="hero-panel__line" />
                    <span class="hero-panel__line hero-panel__line--dim" />
                    <span class="hero-panel__cite">
                      <span class="hero-panel__cite-mark" />
                      <span class="hero-panel__cite-text" />
                    </span>
                    <span class="hero-panel__line hero-panel__line--medium" />
                    <span class="hero-panel__line hero-panel__line--short" />
                  </div>
                  <div class="hero-panel__foot">
                    <span class="hero-panel__status">
                      <span class="hero-panel__status-dot" />
                    </span>
                    <span class="hero-panel__meta" />
                  </div>
                </article>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section
        class="section section-features"
        aria-labelledby="features-heading"
      >
        <header class="section-intro">
          <p class="section-eyebrow">
            {{ t('landing.featuresEyebrow') }}
          </p>
          <h2
            id="features-heading"
            class="section-heading"
          >
            {{ t('landing.featuresTitle') }}
          </h2>
        </header>
        <ul class="feature-list">
          <li
            v-for="item of featureItems"
            :key="item.index"
            class="feature-row"
          >
            <span class="feature-row__index">{{ item.index }}</span>
            <div class="feature-row__body">
              <h3 class="feature-row__title">
                {{ item.title }}
              </h3>
              <p class="feature-row__desc">
                {{ item.body }}
              </p>
            </div>
          </li>
        </ul>
      </section>

      <section
        class="section section-use-cases"
        aria-labelledby="use-cases-heading"
      >
        <header class="section-intro section-intro--offset">
          <p class="section-eyebrow">
            {{ t('landing.useCasesEyebrow') }}
          </p>
          <h2
            id="use-cases-heading"
            class="section-heading"
          >
            {{ t('landing.useCasesTitle') }}
          </h2>
        </header>
        <ul class="use-case-grid">
          <li
            v-for="item of useCaseItems"
            :key="item.id"
            class="use-case-card"
          >
            <h3 class="use-case-heading">
              {{ item.title }}
            </h3>
            <p class="use-case-desc">
              {{ item.body }}
            </p>
          </li>
        </ul>
      </section>

      <section
        class="section cta-section"
        aria-labelledby="cta-heading"
      >
        <h2
          id="cta-heading"
          class="cta-heading"
        >
          {{ t('landing.ctaTitle') }}
        </h2>
        <p class="cta-desc">
          {{ t('landing.ctaDesc') }}
        </p>
        <router-link
          :to="toLogin"
          class="btn-hero-primary btn-hero-primary--large"
        >
          {{ t('landing.ctaSignIn') }}
        </router-link>
      </section>
    </main>

    <footer class="landing-footer">
      <p class="footer-note">
        {{ t('landing.footerPrivacy') }}
      </p>
      <nav
        class="footer-links"
        :aria-label="t('common.footerNavigation')"
      >
        <router-link
          :to="toLogin"
          class="footer-link"
        >
          {{ t('common.login') }}
        </router-link>
        <router-link
          :to="toPricing"
          class="footer-link"
        >
          {{ t('home.pricing') }}
        </router-link>
      </nav>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import AppLogo from '@/components/AppLogo.vue'
import type { AppLocale } from '@/i18n/locale-resolver'
import { useRouteLocale } from '@/i18n/useRouteLocale'
import { setLocale } from '@/plugins/i18n'

defineOptions({
  name: 'LandingPage',
})

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const locale = useRouteLocale()
const toPricing = computed(() => ({
  name: 'Pricing' as const,
  params: { locale: locale.value },
}))
const toLogin = computed(() => ({
  name: 'Login' as const,
  params: { locale: locale.value },
}))

const featureItems = computed(() => [
  {
    index: '01',
    title: t('landing.featureUploadTitle'),
    body: t('landing.featureUploadDesc'),
  },
  {
    index: '02',
    title: t('landing.featureInsightTitle'),
    body: t('landing.featureInsightDesc'),
  },
  {
    index: '03',
    title: t('landing.featureCitationsTitle'),
    body: t('landing.featureCitationsDesc'),
  },
  {
    index: '04',
    title: t('landing.featureAudioTitle'),
    body: t('landing.featureAudioDesc'),
  },
])

const useCaseItems = computed(() => [
  {
    id: 'study',
    title: t('landing.useCaseStudyTitle'),
    body: t('landing.useCaseStudyDesc'),
  },
  {
    id: 'organize',
    title: t('landing.useCaseOrganizeTitle'),
    body: t('landing.useCaseOrganizeDesc'),
  },
  {
    id: 'create',
    title: t('landing.useCaseCreateTitle'),
    body: t('landing.useCaseCreateDesc'),
  },
])

const MAC_DESKTOP_DOWNLOAD_URL =
  'https://github.com/www6v/notebookLM/releases/download/v0.8.0/NotebookLM_0.1.0_x64.dmg'
const DESKTOP_RELEASES_URL = 'https://github.com/www6v/notebookLM/releases'

function handleDownloadPlatformChange(event: Event) {
  const target = event.target as HTMLSelectElement
  const value = target.value
  if (!value) {
    return
  }
  if (value === 'mac') {
    window.open(MAC_DESKTOP_DOWNLOAD_URL, '_blank', 'noopener,noreferrer')
  } else if (value === 'windows' || value === 'linux') {
    window.open(DESKTOP_RELEASES_URL, '_blank', 'noopener,noreferrer')
  }
  target.value = ''
}

function handleLocaleChange(event: Event) {
  const target = event.target as HTMLSelectElement
  const next = target.value as AppLocale
  if (next !== 'en' && next !== 'zh-CN') {
    return
  }
  if (next === locale.value) {
    return
  }
  setLocale(next)
  router.push({
    name: route.name ?? 'Landing',
    params: { ...route.params, locale: next },
    query: route.query,
    hash: route.hash,
  })
}
</script>

<style scoped>
.landing-page {
  --lp-bg: #0e0c0a;
  --lp-bg-soft: #161311;
  --lp-elevated: rgba(255, 248, 240, 0.04);
  --lp-border: rgba(255, 245, 232, 0.09);
  --lp-border-strong: rgba(255, 245, 232, 0.14);
  --lp-text: #f7f2ea;
  --lp-muted: #a39a8c;
  --lp-accent: #c4a574;
  --lp-accent-dim: #a68452;
  --lp-shadow: 0 28px 80px rgba(12, 8, 4, 0.45);
  --lp-font-display: 'Fraunces', 'Noto Serif SC', Georgia, serif;
  --lp-font-sans: 'Outfit', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
  --home-text: var(--lp-text);
  --home-text-secondary: var(--lp-muted);
  position: relative;
  min-height: 100dvh;
  min-height: 100vh;
  background: var(--lp-bg);
  color: var(--lp-text);
  display: flex;
  flex-direction: column;
  isolation: isolate;
  font-family: var(--lp-font-sans);
}

.skip-link {
  position: absolute;
  left: 12px;
  top: -120px;
  z-index: 100;
  padding: 10px 16px;
  background: var(--lp-text);
  color: var(--lp-bg);
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  border-radius: 8px;
  transition: top 0.15s ease;
}

.skip-link:focus {
  top: 12px;
  outline: 2px solid var(--lp-accent);
  outline-offset: 3px;
}

.landing-stars {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-color: var(--lp-bg);
  background-image:
    radial-gradient(1.5px 1.5px at 10% 20%, rgba(255, 250, 242, 0.55), transparent),
    radial-gradient(1px 1px at 25% 45%, rgba(255, 250, 242, 0.32), transparent),
    radial-gradient(1.5px 1.5px at 40% 12%, rgba(255, 250, 242, 0.42), transparent),
    radial-gradient(1px 1px at 55% 78%, rgba(255, 250, 242, 0.28), transparent),
    radial-gradient(2px 2px at 72% 30%, rgba(255, 250, 242, 0.5), transparent),
    radial-gradient(1px 1px at 88% 65%, rgba(255, 250, 242, 0.22), transparent),
    radial-gradient(1.5px 1.5px at 15% 82%, rgba(255, 250, 242, 0.38), transparent),
    radial-gradient(1px 1px at 33% 8%, rgba(255, 250, 242, 0.2), transparent),
    radial-gradient(1.5px 1.5px at 62% 55%, rgba(255, 250, 242, 0.36), transparent),
    radial-gradient(1px 1px at 95% 22%, rgba(255, 250, 242, 0.26), transparent);
  background-size:
    420px 420px,
    380px 380px,
    520px 520px,
    440px 440px,
    360px 360px,
    480px 480px,
    400px 400px,
    340px 340px,
    460px 460px,
    390px 390px;
  background-position:
    0 0,
    80px 120px,
    200px 40px,
    -40px 200px,
    300px 0,
    120px 280px,
    400px 160px,
    60px 320px,
    240px 100px,
    500px 60px;
}

.landing-atmosphere {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(
      ellipse 70% 55% at 18% 12%,
      rgba(196, 165, 116, 0.07) 0%,
      transparent 55%
    ),
    radial-gradient(
      ellipse 50% 40% at 88% 72%,
      rgba(120, 90, 60, 0.12) 0%,
      transparent 50%
    ),
    radial-gradient(
      circle at 50% 108%,
      rgba(196, 165, 116, 0.06) 0%,
      transparent 42%
    );
}

.landing-grain {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  opacity: 0.055;
  mix-blend-mode: overlay;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}

.landing-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 28px;
  margin: 12px 20px 0;
  max-width: 1280px;
  width: calc(100% - 40px);
  align-self: center;
  background: rgba(14, 12, 10, 0.55);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--lp-border);
  border-radius: 14px;
  box-shadow:
    inset 0 1px 0 rgba(255, 248, 240, 0.06),
    0 18px 48px rgba(8, 5, 2, 0.35);
  position: sticky;
  top: 12px;
  z-index: 10;
}

.landing-header .app-logo {
  cursor: default;
}

.landing-header :deep(.app-logo__text) {
  font-family: var(--lp-font-display);
  font-weight: 600;
  letter-spacing: -0.02em;
  font-size: 21px;
}

.landing-header :deep(.app-logo__icon) {
  color: var(--lp-accent);
}

.landing-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.header-github-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 12px;
  color: rgba(247, 242, 234, 0.88);
  border: 1px solid var(--lp-border-strong);
  border-radius: 10px;
  text-decoration: none;
  flex-shrink: 0;
  transition:
    color 0.22s ease,
    border-color 0.22s ease,
    transform 0.22s ease,
    background 0.22s ease;
}

.header-github-link:hover {
  color: var(--lp-text);
  border-color: rgba(196, 165, 116, 0.45);
  background: rgba(196, 165, 116, 0.06);
}

.header-github-link:active {
  transform: translateY(1px) scale(0.98);
}

.header-github-link:focus-visible {
  outline: 2px solid var(--lp-accent);
  outline-offset: 2px;
}

.header-github-icon {
  display: block;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.header-lang-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.header-lang-select {
  appearance: none;
  -webkit-appearance: none;
  width: max-content;
  max-width: 100%;
  padding: 8px 28px 8px 14px;
  font-size: 14px;
  font-weight: 500;
  font-family: var(--lp-font-sans);
  color: rgba(247, 242, 234, 0.92);
  background-color: transparent;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12' fill='none'%3E%3Cpath d='M3 4.5L6 7.5L9 4.5' stroke='rgba(247,242,234,0.55)' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  border: 1px solid var(--lp-border-strong);
  border-radius: 10px;
  cursor: pointer;
  transition:
    border-color 0.22s ease,
    color 0.22s ease,
    box-shadow 0.22s ease;
}

.header-lang-select:hover {
  border-color: rgba(196, 165, 116, 0.4);
  color: var(--lp-text);
}

.header-lang-select:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px rgba(196, 165, 116, 0.35);
}

.header-lang-select option {
  color: #1a1816;
  background: #f7f2ea;
}

.header-cta {
  display: inline-block;
  padding: 9px 18px;
  background: transparent;
  color: var(--lp-text);
  border: 1px solid var(--lp-border-strong);
  border-radius: 10px;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  transition:
    background 0.22s ease,
    border-color 0.22s ease,
    transform 0.22s ease;
}

.header-cta:hover {
  background: rgba(196, 165, 116, 0.08);
  border-color: rgba(196, 165, 116, 0.45);
  text-decoration: none;
}

.header-cta:active {
  transform: translateY(1px) scale(0.98);
}

.header-cta:focus-visible {
  outline: 2px solid var(--lp-accent);
  outline-offset: 2px;
}

.landing-main {
  position: relative;
  z-index: 1;
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 28px 88px;
  width: 100%;
}

.hero {
  padding: 48px 0 72px;
}

.hero-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 0.85fr);
  gap: 48px;
  align-items: center;
}

.hero-copy {
  text-align: left;
}

.hero-kicker {
  font-size: 14px;
  font-weight: 500;
  font-style: italic;
  letter-spacing: 0.02em;
  color: var(--lp-muted);
  margin: 0 0 16px;
}

.hero-title {
  font-family: var(--lp-font-display);
  font-size: clamp(2.75rem, 5.5vw, 4rem);
  font-weight: 600;
  margin: 0 0 20px;
  letter-spacing: -0.045em;
  line-height: 1.05;
  text-wrap: balance;
}

.hero-title-accent {
  color: var(--lp-accent);
  font-style: italic;
  font-weight: 500;
}

.hero-title-plain {
  color: var(--lp-text);
}

.hero-subtitle {
  font-size: clamp(1.05rem, 1.6vw, 1.2rem);
  font-weight: 400;
  color: var(--lp-muted);
  max-width: 38rem;
  margin: 0 0 32px;
  line-height: 1.7;
  text-wrap: pretty;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px;
}

.btn-hero-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 14px 26px;
  background: var(--lp-accent);
  color: #14110e;
  border-radius: 11px;
  text-decoration: none;
  font-size: 15px;
  font-weight: 600;
  border: 1px solid rgba(20, 17, 14, 0.08);
  box-shadow: var(--lp-shadow);
  transition:
    transform 0.22s ease,
    box-shadow 0.22s ease,
    background 0.22s ease,
    filter 0.22s ease;
}

.btn-hero-primary:hover {
  filter: brightness(1.04);
  text-decoration: none;
  transform: translateY(-2px);
}

.btn-hero-primary:active {
  transform: translateY(0) scale(0.98);
}

.btn-hero-primary:focus-visible {
  outline: 2px solid var(--lp-text);
  outline-offset: 3px;
}

.btn-hero-primary--large {
  padding: 16px 32px;
  font-size: 16px;
  border-radius: 12px;
}

.btn-hero-ghost {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 14px 18px;
  color: var(--lp-text);
  text-decoration: none;
  font-size: 15px;
  font-weight: 500;
  border-radius: 11px;
  border: 1px solid transparent;
  transition:
    color 0.22s ease,
    border-color 0.22s ease,
    background 0.22s ease,
    transform 0.22s ease;
}

.btn-hero-ghost:hover {
  border-color: var(--lp-border-strong);
  background: rgba(255, 248, 240, 0.04);
  text-decoration: none;
}

.btn-hero-ghost:active {
  transform: scale(0.98);
}

.btn-hero-ghost:focus-visible {
  outline: 2px solid var(--lp-accent);
  outline-offset: 2px;
}

.hero-visual {
  position: relative;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
}

.hero-showcase {
  position: relative;
  width: min(100%, 380px);
  aspect-ratio: 1 / 1.05;
  max-height: 360px;
}

.hero-showcase__ambient {
  position: absolute;
  inset: 8% 4% 12%;
  border-radius: 28px;
  background: radial-gradient(
    ellipse 80% 70% at 50% 45%,
    rgba(196, 165, 116, 0.14) 0%,
    transparent 68%
  );
  filter: blur(2px);
  pointer-events: none;
}

.hero-showcase__stack {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-deck-card {
  position: absolute;
  width: 86%;
  height: 78%;
  border-radius: 18px;
  border: 1px solid rgba(255, 245, 232, 0.07);
  background: rgba(22, 19, 16, 0.65);
  box-shadow: 0 24px 48px rgba(6, 4, 2, 0.45);
}

.hero-deck-card--rear {
  transform: rotate(-9deg) translate(-18px, 14px);
  opacity: 0.55;
}

.hero-deck-card--mid {
  width: 88%;
  height: 80%;
  transform: rotate(5deg) translate(14px, -8px);
  opacity: 0.72;
  border-color: rgba(196, 165, 116, 0.1);
}

.hero-panel {
  position: relative;
  width: min(100%, 320px);
  padding: 0;
  border-radius: 20px;
  background: linear-gradient(
    155deg,
    rgba(255, 248, 240, 0.09) 0%,
    rgba(22, 19, 17, 0.55) 45%,
    rgba(14, 12, 10, 0.75) 100%
  );
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 245, 232, 0.12);
  box-shadow:
    inset 0 1px 0 rgba(255, 248, 240, 0.08),
    inset 0 -1px 0 rgba(0, 0, 0, 0.22),
    0 32px 64px rgba(8, 5, 2, 0.5),
    0 0 0 1px rgba(196, 165, 116, 0.06);
  overflow: hidden;
}

.hero-panel__chrome {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 14px 16px 10px;
  border-bottom: 1px solid rgba(255, 245, 232, 0.06);
}

.hero-panel__chrome-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(163, 154, 140, 0.35);
}

.hero-panel__chrome-dot:first-child {
  background: rgba(196, 120, 92, 0.55);
}

.hero-panel__chrome-dot:nth-child(2) {
  background: rgba(196, 165, 116, 0.45);
}

.hero-panel__toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px 14px;
}

.hero-panel__toolbar-pill {
  height: 6px;
  width: 42%;
  border-radius: 4px;
  background: rgba(255, 248, 240, 0.1);
}

.hero-panel__toolbar-pill--short {
  width: 22%;
  opacity: 0.65;
}

.hero-panel__body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 4px 20px 20px;
}

.hero-panel__line {
  display: block;
  height: 7px;
  border-radius: 4px;
  background: rgba(255, 248, 240, 0.08);
  width: 100%;
}

.hero-panel__line--title {
  width: 58%;
  height: 9px;
  background: rgba(255, 248, 240, 0.14);
}

.hero-panel__line--dim {
  opacity: 0.55;
  width: 92%;
}

.hero-panel__line--medium {
  width: 78%;
}

.hero-panel__line--short {
  width: 44%;
  opacity: 0.5;
}

.hero-panel__cite {
  display: flex;
  align-items: stretch;
  gap: 10px;
  padding: 12px 12px;
  margin-top: 4px;
  border-radius: 12px;
  background: rgba(196, 165, 116, 0.1);
  border: 1px solid rgba(196, 165, 116, 0.22);
  box-shadow: inset 0 1px 0 rgba(255, 248, 240, 0.06);
}

.hero-panel__cite-mark {
  width: 3px;
  flex-shrink: 0;
  border-radius: 2px;
  background: linear-gradient(
    180deg,
    rgba(196, 165, 116, 0.95) 0%,
    rgba(166, 132, 82, 0.65) 100%
  );
}

.hero-panel__cite-text {
  flex: 1;
  height: 36px;
  border-radius: 6px;
  background: linear-gradient(
    90deg,
    rgba(255, 248, 240, 0.12) 0%,
    rgba(255, 248, 240, 0.05) 55%,
    rgba(255, 248, 240, 0.09) 100%
  );
}

.hero-panel__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 20px 18px;
  border-top: 1px solid rgba(255, 245, 232, 0.06);
}

.hero-panel__status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.hero-panel__status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(196, 165, 116, 0.85);
  box-shadow: 0 0 12px rgba(196, 165, 116, 0.45);
  animation: hero-panel-pulse 2.4s ease-in-out infinite;
}

.hero-panel__meta {
  flex: 1;
  max-width: 120px;
  height: 6px;
  margin-left: auto;
  border-radius: 4px;
  background: rgba(255, 248, 240, 0.07);
}

@keyframes hero-panel-pulse {
  0%,
  100% {
    opacity: 0.55;
    transform: scale(1);
  }

  50% {
    opacity: 1;
    transform: scale(1.08);
  }
}

@media (prefers-reduced-motion: reduce) {
  .hero-panel__status-dot {
    animation: none;
    opacity: 0.85;
  }
}

.section {
  margin-bottom: 88px;
}

.section-intro {
  max-width: 36rem;
  margin-bottom: 40px;
}

.section-intro--offset {
  margin-left: clamp(0px, 4vw, 48px);
}

.section-eyebrow {
  font-size: 14px;
  font-style: italic;
  font-weight: 500;
  color: var(--lp-muted);
  margin: 0 0 10px;
  letter-spacing: 0.01em;
}

.section-heading {
  font-family: var(--lp-font-display);
  font-size: clamp(1.75rem, 3vw, 2.35rem);
  font-weight: 600;
  letter-spacing: -0.03em;
  line-height: 1.15;
  color: var(--lp-text);
  margin: 0;
  text-wrap: balance;
}

.feature-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.feature-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 28px 36px;
  padding: 36px 0;
  border-top: 1px solid var(--lp-border);
  align-items: start;
}

.feature-row:last-child {
  border-bottom: 1px solid var(--lp-border);
}

.feature-row__index {
  font-family: var(--lp-font-display);
  font-size: 1.5rem;
  font-weight: 500;
  color: rgba(196, 165, 116, 0.55);
  letter-spacing: -0.02em;
  line-height: 1.2;
  padding-top: 4px;
  font-variant-numeric: tabular-nums;
}

.feature-row__title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--lp-text);
  margin: 0 0 10px;
  letter-spacing: -0.02em;
}

.feature-row__desc {
  font-size: 15px;
  color: var(--lp-muted);
  line-height: 1.72;
  margin: 0;
  max-width: 62ch;
  text-wrap: pretty;
}

.use-case-grid {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.use-case-card {
  padding: 28px 30px 32px;
  background: var(--lp-elevated);
  border: 1px solid var(--lp-border);
  border-radius: 16px;
  box-shadow: inset 0 1px 0 rgba(255, 248, 240, 0.05);
  transition:
    border-color 0.22s ease,
    transform 0.22s ease,
    background 0.22s ease;
}

.use-case-card:hover {
  border-color: rgba(196, 165, 116, 0.28);
  background: rgba(255, 248, 240, 0.055);
  transform: translateY(-2px);
}

.use-case-card:nth-child(3) {
  grid-column: 1 / -1;
  max-width: min(100%, 52rem);
  border-radius: 20px;
}

.use-case-heading {
  font-family: var(--lp-font-display);
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--lp-text);
  margin: 0 0 10px;
  letter-spacing: -0.02em;
}

.use-case-desc {
  font-size: 14px;
  color: var(--lp-muted);
  line-height: 1.68;
  margin: 0;
  max-width: 62ch;
  text-wrap: pretty;
}

.cta-section {
  text-align: left;
  padding: 48px 40px 52px;
  background: linear-gradient(
    145deg,
    rgba(255, 248, 240, 0.05) 0%,
    rgba(22, 19, 17, 0.85) 48%,
    rgba(14, 12, 10, 0.95) 100%
  );
  border: 1px solid var(--lp-border);
  border-radius: 22px;
  box-shadow:
    inset 0 1px 0 rgba(255, 248, 240, 0.06),
    0 24px 64px rgba(8, 5, 2, 0.4);
}

.cta-heading {
  font-family: var(--lp-font-display);
  font-size: clamp(1.65rem, 2.8vw, 2.1rem);
  font-weight: 600;
  letter-spacing: -0.03em;
  margin: 0 0 14px;
  color: var(--lp-text);
  text-wrap: balance;
}

.cta-desc {
  font-size: 16px;
  color: var(--lp-muted);
  margin: 0 0 28px;
  max-width: 40rem;
  line-height: 1.68;
  text-wrap: pretty;
}

.landing-footer {
  position: relative;
  z-index: 1;
  padding: 36px 28px 44px;
  margin-top: auto;
  border-top: 1px solid var(--lp-border);
  background: linear-gradient(
    180deg,
    rgba(14, 12, 10, 0.2) 0%,
    rgba(10, 8, 6, 0.92) 100%
  );
  backdrop-filter: blur(12px);
}

.footer-note {
  font-size: 13px;
  color: rgba(163, 154, 140, 0.92);
  margin: 0 auto 16px;
  max-width: 520px;
  text-align: center;
  line-height: 1.55;
  text-wrap: pretty;
}

.footer-links {
  display: flex;
  justify-content: center;
  gap: 28px;
}

.footer-link {
  font-size: 14px;
  color: var(--lp-muted);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.22s ease;
}

.footer-link:hover {
  color: var(--lp-accent);
  text-decoration: none;
}

.footer-link:focus-visible {
  outline: 2px solid var(--lp-accent);
  outline-offset: 3px;
  border-radius: 4px;
}

@media (max-width: 900px) {
  .hero-layout {
    grid-template-columns: 1fr;
    gap: 40px;
  }

  .hero-visual {
    order: -1;
    min-height: 220px;
  }

  .section-intro--offset {
    margin-left: 0;
  }
}

@media (max-width: 640px) {
  .landing-header {
    margin: 8px 12px 0;
    width: calc(100% - 24px);
    padding: 12px 16px;
    border-radius: 12px;
  }

  .landing-main {
    padding: 28px 18px 72px;
  }

  .hero {
    padding: 28px 0 48px;
  }

  .hero-copy {
    text-align: left;
  }

  .hero-kicker {
    font-size: 12px;
  }

  .feature-row {
    grid-template-columns: 1fr;
    gap: 8px;
    padding: 28px 0;
  }

  .feature-row__index {
    font-size: 1.15rem;
  }

  .use-case-grid {
    grid-template-columns: 1fr;
  }

  .use-case-card:nth-child(3) {
    grid-column: auto;
    max-width: none;
  }

  .cta-section {
    padding: 36px 22px 40px;
    border-radius: 18px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .skip-link {
    transition: none;
  }

  .header-github-link,
  .header-cta,
  .btn-hero-primary,
  .btn-hero-ghost,
  .use-case-card {
    transition: none;
  }

  .btn-hero-primary:hover,
  .use-case-card:hover {
    transform: none;
  }
}
</style>
