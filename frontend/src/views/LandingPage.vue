<template>
  <div class="landing-page">
    <div
      class="landing-stars"
      aria-hidden="true"
    />
    <div
      class="landing-glow"
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

    <main class="landing-main">
      <section class="hero">
        <h2 class="hero-title">
          <span class="hero-title-accent">{{ t('landing.heroTitleAccent') }}</span><span class="hero-title-plain">{{ t('landing.heroTitlePlain') }}</span>
        </h2>
        <p class="hero-subtitle">
          {{ t('landing.heroSubtitle') }}
        </p>
        <div class="hero-actions">
          <router-link
            :to="toLogin"
            class="btn-hero-pill"
          >
            {{ t('landing.getStarted') }}
            <span class="btn-hero-pill-chevron">›</span>
          </router-link>
        </div>
      </section>

      <section class="section features">
        <h3 class="section-title">{{ t('landing.featuresTitle') }}</h3>
        <div class="feature-grid">
          <div class="feature-card">
            <div class="feature-icon">📄</div>
            <h4 class="feature-heading">{{ t('landing.featureUploadTitle') }}</h4>
            <p class="feature-desc">
              {{ t('landing.featureUploadDesc') }}
            </p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">✨</div>
            <h4 class="feature-heading">{{ t('landing.featureInsightTitle') }}</h4>
            <p class="feature-desc">
              {{ t('landing.featureInsightDesc') }}
            </p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">📎</div>
            <h4 class="feature-heading">{{ t('landing.featureCitationsTitle') }}</h4>
            <p class="feature-desc">
              {{ t('landing.featureCitationsDesc') }}
            </p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">🎧</div>
            <h4 class="feature-heading">{{ t('landing.featureAudioTitle') }}</h4>
            <p class="feature-desc">
              {{ t('landing.featureAudioDesc') }}
            </p>
          </div>
        </div>
      </section>

      <section class="section use-cases">
        <h3 class="section-title">{{ t('landing.useCasesTitle') }}</h3>
        <div class="use-case-grid">
          <div class="use-case-card">
            <h4 class="use-case-heading">{{ t('landing.useCaseStudyTitle') }}</h4>
            <p class="use-case-desc">
              {{ t('landing.useCaseStudyDesc') }}
            </p>
          </div>
          <div class="use-case-card">
            <h4 class="use-case-heading">{{ t('landing.useCaseOrganizeTitle') }}</h4>
            <p class="use-case-desc">
              {{ t('landing.useCaseOrganizeDesc') }}
            </p>
          </div>
          <div class="use-case-card">
            <h4 class="use-case-heading">{{ t('landing.useCaseCreateTitle') }}</h4>
            <p class="use-case-desc">
              {{ t('landing.useCaseCreateDesc') }}
            </p>
          </div>
        </div>
      </section>

      <section class="section cta-section">
        <h3 class="section-title">{{ t('landing.ctaTitle') }}</h3>
        <p class="cta-desc">
          {{ t('landing.ctaDesc') }}
        </p>
        <router-link
          :to="toLogin"
          class="btn-hero-pill btn-hero-pill-large"
        >
          {{ t('landing.ctaSignIn') }}
          <span class="btn-hero-pill-chevron">›</span>
        </router-link>
      </section>
    </main>

    <footer class="landing-footer">
      <p class="footer-note">
        {{ t('landing.footerPrivacy') }}
      </p>
      <div class="footer-links">
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
      </div>
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
  --home-bg: #000000;
  --home-surface: rgba(255, 255, 255, 0.05);
  --home-border: rgba(255, 255, 255, 0.12);
  --home-text: #ffffff;
  --home-text-secondary: #d1d5db;
  --home-primary: #facc15;
  --landing-gold: #facc15;
  --landing-gold-dim: #eab308;
  position: relative;
  min-height: 100vh;
  background: var(--home-bg);
  color: var(--home-text);
  display: flex;
  flex-direction: column;
  isolation: isolate;
}

.landing-stars {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-color: #000000;
  background-image:
    radial-gradient(1.5px 1.5px at 10% 20%, rgba(255, 255, 255, 0.9), transparent),
    radial-gradient(1px 1px at 25% 45%, rgba(255, 255, 255, 0.55), transparent),
    radial-gradient(1.5px 1.5px at 40% 12%, rgba(255, 255, 255, 0.75), transparent),
    radial-gradient(1px 1px at 55% 78%, rgba(255, 255, 255, 0.5), transparent),
    radial-gradient(2px 2px at 72% 30%, rgba(255, 255, 255, 0.85), transparent),
    radial-gradient(1px 1px at 88% 65%, rgba(255, 255, 255, 0.45), transparent),
    radial-gradient(1.5px 1.5px at 15% 82%, rgba(255, 255, 255, 0.65), transparent),
    radial-gradient(1px 1px at 33% 8%, rgba(255, 255, 255, 0.4), transparent),
    radial-gradient(1.5px 1.5px at 62% 55%, rgba(255, 255, 255, 0.7), transparent),
    radial-gradient(1px 1px at 95% 22%, rgba(255, 255, 255, 0.55), transparent),
    radial-gradient(1px 1px at 48% 92%, rgba(255, 255, 255, 0.35), transparent),
    radial-gradient(2px 2px at 8% 58%, rgba(255, 253, 240, 0.95), transparent);
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
    390px 390px,
    410px 410px,
    500px 500px;
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
    500px 60px,
    180px 400px,
    20px 80px;
}

.landing-glow {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(
      ellipse 55% 45% at 50% 42%,
      rgba(255, 255, 255, 0.07) 0%,
      transparent 55%
    ),
    radial-gradient(
      circle at 50% 48%,
      rgba(250, 204, 21, 0.04) 0%,
      transparent 42%
    );
}

.landing-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 28px;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  position: sticky;
  top: 0;
  z-index: 10;
}

.landing-header .app-logo {
  cursor: default;
}

.landing-header :deep(.app-logo__text) {
  font-family:
    Georgia,
    'Times New Roman',
    'Noto Serif SC',
    serif;
  font-weight: 600;
  letter-spacing: 0.03em;
  color: #ffffff;
}

.landing-header :deep(.app-logo__icon) {
  color: #ffffff;
}

.landing-header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-github-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 7px 12px;
  color: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 999px;
  text-decoration: none;
  flex-shrink: 0;
}

.header-github-link:hover {
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.45);
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
  color: rgba(255, 255, 255, 0.9);
  background-color: transparent;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12' fill='none'%3E%3Cpath d='M3 4.5L6 7.5L9 4.5' stroke='rgba(255,255,255,0.65)' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 999px;
  cursor: pointer;
}

.header-lang-select:hover {
  border-color: rgba(255, 255, 255, 0.45);
  color: #ffffff;
}

.header-lang-select:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(250, 204, 21, 0.35);
}

.header-lang-select option {
  color: #111111;
  background: #ffffff;
}

.header-link {
  color: rgba(255, 255, 255, 0.75);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  padding: 8px 16px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 999px;
  background: transparent;
}

.header-link:hover {
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.45);
  text-decoration: none;
}

.header-cta {
  display: inline-block;
  padding: 8px 20px;
  background: transparent;
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 999px;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
}

.header-cta:hover {
  background: rgba(255, 255, 255, 0.08);
  text-decoration: none;
}

.landing-main {
  position: relative;
  z-index: 1;
  flex: 1;
  max-width: 1080px;
  margin: 0 auto;
  padding: 48px 24px 64px;
  width: 100%;
}

.hero {
  text-align: center;
  padding: 56px 0 72px;
}

.hero-title {
  font-size: clamp(2.5rem, 6vw, 3.75rem);
  font-weight: 700;
  margin: 0 0 24px;
  letter-spacing: -0.03em;
  line-height: 1.15;
  font-family:
    system-ui,
    -apple-system,
    'Segoe UI',
    'PingFang SC',
    'Microsoft YaHei',
    sans-serif;
}

.hero-title-accent {
  color: var(--landing-gold);
}

.hero-title-plain {
  color: #ffffff;
}

.hero-subtitle {
  font-size: clamp(1.0625rem, 2vw, 1.25rem);
  color: var(--home-text-secondary);
  max-width: 640px;
  margin: 0 auto 36px;
  line-height: 1.65;
  font-weight: 400;
}

.hero-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.btn-hero-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 14px 32px;
  background: #ffffff;
  color: #000000;
  border-radius: 999px;
  text-decoration: none;
  font-size: 16px;
  font-weight: 700;
  border: none;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.btn-hero-pill:hover {
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.2), 0 12px 40px rgba(0, 0, 0, 0.35);
  text-decoration: none;
  transform: translateY(-1px);
}

.btn-hero-pill-chevron {
  font-size: 1.15em;
  line-height: 1;
  opacity: 0.85;
}

.btn-hero-pill-large {
  padding: 16px 36px;
  font-size: 17px;
}

.section {
  margin-bottom: 64px;
}

.section-title {
  font-size: clamp(1.5rem, 3vw, 1.875rem);
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 32px;
  text-align: center;
  letter-spacing: -0.02em;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 28px 32px;
}

.feature-card {
  display: flex;
  flex-direction: column;
  min-height: 240px;
  padding: 32px 36px;
  background: var(--home-surface);
  border: 1px solid var(--home-border);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(8px);
}

.feature-icon {
  font-size: 40px;
  margin-bottom: 16px;
  line-height: 1;
}

.feature-heading {
  font-size: 20px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 12px;
}

.feature-desc {
  font-size: 15px;
  color: var(--home-text-secondary);
  line-height: 1.65;
  flex: 1;
}

@media (max-width: 640px) {
  .feature-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .feature-card {
    min-height: 0;
    padding: 24px;
  }
}

.use-case-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 24px;
}

.use-case-card {
  padding: 24px;
  background: var(--home-surface);
  border: 1px solid var(--home-border);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(8px);
}

.use-case-heading {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 8px;
}

.use-case-desc {
  font-size: 14px;
  color: var(--home-text-secondary);
  line-height: 1.6;
}

.cta-section {
  text-align: center;
  padding: 48px 24px;
  background: var(--home-surface);
  border: 1px solid var(--home-border);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(10px);
}

.cta-desc {
  font-size: 17px;
  color: var(--home-text-secondary);
  margin-bottom: 28px;
  max-width: 520px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.65;
}

.landing-footer {
  position: relative;
  z-index: 1;
  padding: 28px 24px;
  text-align: center;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(10px);
}

.footer-note {
  font-size: 13px;
  color: rgba(209, 213, 219, 0.85);
  margin-bottom: 12px;
}

.footer-links {
  display: flex;
  justify-content: center;
  gap: 24px;
}

.footer-link {
  font-size: 14px;
  color: var(--landing-gold);
  text-decoration: none;
  font-weight: 500;
}

.footer-link:hover {
  color: var(--landing-gold-dim);
  text-decoration: underline;
}
</style>
