<template>
  <div class="pricing-page">
    <header class="pricing-header">
      <div class="header-left">
        <AppLogo
          class="logo-link"
          @click="goHome"
        />
      </div>
      <div class="header-right">
        <template v-if="userStore.isLoggedIn">
          <v-btn
            variant="text"
            @click="goSettings"
          >
            <v-icon size="20">mdi-cog</v-icon>
            <span class="header-btn-label">{{ t('pricing.settings') }}</span>
          </v-btn>
          <v-btn
            variant="text"
            icon
            @click="handleLogout"
          >
            <v-icon size="20">mdi-logout</v-icon>
          </v-btn>
        </template>
        <v-btn
          v-else
          color="primary"
          @click="goLogin"
        >
          {{ t('pricing.login') }}
        </v-btn>
      </div>
    </header>

    <main class="pricing-main">
      <div class="pricing-hero">
        <h2 class="pricing-title">{{ t('pricing.title') }}</h2>
        <p class="pricing-subtitle">
          {{ t('pricing.subtitle') }}
        </p>
        <div class="pricing-actions">
          <v-btn
            color="primary"
            size="large"
            @click="goHome"
          >
            {{ t('pricing.getStarted') }}
          </v-btn>
          <v-btn
            size="large"
            variant="outlined"
            color="primary"
            class="btn-outline"
            @click="handleTalkToSales"
          >
            {{ t('pricing.contactSales') }}
          </v-btn>
        </div>
      </div>

      <div class="pricing-table-wrap">
        <table class="pricing-table">
          <thead>
            <tr>
              <th class="th-feature" />
              <th class="th-plan">{{ t('pricing.free') }}</th>
              <th class="th-plan th-plan--highlight">{{ t('pricing.plus') }}</th>
              <th class="th-plan">{{ t('pricing.enterprise') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="td-feature">{{ t('pricing.rowFee') }}</td>
              <td class="td-cell">{{ t('pricing.freePrice') }}</td>
              <td class="td-cell td-cell--highlight">
                {{ t('pricing.plusMonthly') }}
                <span class="cell-note">{{ t('pricing.plusStudentNote') }}</span>
              </td>
              <td class="td-cell">
                <a
                  href="#"
                  class="table-link"
                  @click.prevent="handleTalkToSales"
                >
                  {{ t('pricing.enterpriseNegotiate') }}
                </a>
              </td>
            </tr>
            <tr>
              <td class="td-feature">{{ t('pricing.rowNotebooks') }}</td>
              <td class="td-cell">
                {{ t('pricing.notebooksUpTo', { count: 20 }) }}
              </td>
              <td class="td-cell td-cell--highlight">
                {{ t('pricing.notebooksUpTo', { count: 200 }) }}
              </td>
              <td class="td-cell">{{ t('pricing.customOnDemand') }}</td>
            </tr>
            <tr>
              <td class="td-feature">{{ t('pricing.rowSources') }}</td>
              <td class="td-cell">{{ t('pricing.sourcesCount', { count: 30 }) }}</td>
              <td class="td-cell td-cell--highlight">
                {{ t('pricing.sourcesCount', { count: 50 }) }}
              </td>
              <td class="td-cell">{{ t('pricing.customOnDemand') }}</td>
            </tr>
            <tr>
              <td class="td-feature">{{ t('pricing.rowDailyChats') }}</td>
              <td class="td-cell">{{ t('pricing.dailyQuota', { count: 50 }) }}</td>
              <td class="td-cell td-cell--highlight">
                {{ t('pricing.dailyQuota', { count: 200 }) }}
              </td>
              <td class="td-cell">{{ t('pricing.customOnDemand') }}</td>
            </tr>
            <tr>
              <td class="td-feature">{{ t('pricing.rowModels') }}</td>
              <td class="td-cell">{{ t('pricing.modelDefaultOnly') }}</td>
              <td class="td-cell td-cell--highlight">{{ t('pricing.modelAll') }}</td>
              <td class="td-cell">{{ t('pricing.customOnDemand') }}</td>
            </tr>
            <tr>
              <td class="td-feature">{{ t('pricing.rowDailyAudio') }}</td>
              <td class="td-cell">{{ t('pricing.dailyQuota', { count: 3 }) }}</td>
              <td class="td-cell td-cell--highlight">
                {{ t('pricing.dailyQuota', { count: 20 }) }}
              </td>
              <td class="td-cell">{{ t('pricing.customOnDemand') }}</td>
            </tr>
            <tr>
              <td class="td-feature">{{ t('pricing.rowChatApi') }}</td>
              <td class="td-cell">
                <v-icon
                  class="icon-check"
                  :aria-label="t('pricing.a11yIncluded')"
                >
                  mdi-check
                </v-icon>
              </td>
              <td class="td-cell td-cell--highlight">
                <v-icon
                  class="icon-check"
                  :aria-label="t('pricing.a11yIncluded')"
                >
                  mdi-check
                </v-icon>
              </td>
              <td class="td-cell">
                <v-icon
                  class="icon-check"
                  :aria-label="t('pricing.a11yIncluded')"
                >
                  mdi-check
                </v-icon>
              </td>
            </tr>
            <tr>
              <td class="td-feature">{{ t('pricing.rowLogsExport') }}</td>
              <td class="td-cell">
                <v-icon
                  class="icon-check"
                  :aria-label="t('pricing.a11yIncluded')"
                >
                  mdi-check
                </v-icon>
              </td>
              <td class="td-cell td-cell--highlight">
                <v-icon
                  class="icon-check"
                  :aria-label="t('pricing.a11yIncluded')"
                >
                  mdi-check
                </v-icon>
              </td>
              <td class="td-cell">
                <v-icon
                  class="icon-check"
                  :aria-label="t('pricing.a11yIncluded')"
                >
                  mdi-check
                </v-icon>
              </td>
            </tr>
            <tr>
              <td class="td-feature">{{ t('pricing.rowCustomShare') }}</td>
              <td class="td-cell">
                <v-icon
                  class="icon-cross"
                  :aria-label="t('pricing.a11yNotIncluded')"
                >
                  mdi-close
                </v-icon>
              </td>
              <td class="td-cell td-cell--highlight">
                <v-icon
                  class="icon-check"
                  :aria-label="t('pricing.a11yIncluded')"
                >
                  mdi-check
                </v-icon>
              </td>
              <td class="td-cell">
                <v-icon
                  class="icon-check"
                  :aria-label="t('pricing.a11yIncluded')"
                >
                  mdi-check
                </v-icon>
              </td>
            </tr>
            <tr class="tr-action">
              <td class="td-feature" />
              <td class="td-cell">
                <v-btn
                  variant="outlined"
                  size="small"
                  @click="goHome"
                >
                  {{ t('pricing.useFree') }}
                </v-btn>
              </td>
              <td class="td-cell td-cell--highlight">
                <v-btn
                  v-if="userStore.isPaid"
                  variant="tonal"
                  color="success"
                  size="small"
                  disabled
                >
                  {{ t('pricing.currentPlan') }}
                </v-btn>
                <v-btn
                  v-else
                  color="primary"
                  size="small"
                  @click="handleSubscribe"
                >
                  {{ t('pricing.subscribeNow') }}
                </v-btn>
              </td>
              <td class="td-cell">
                <v-btn
                  variant="outlined"
                  size="small"
                  @click="handleTalkToSales"
                >
                  {{ t('pricing.contactSalesShort') }}
                </v-btn>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>

    <PaymentDialog
      v-model="showPaymentDialog"
      @paid="onPaid"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useRouteLocale } from '@/i18n/useRouteLocale'
import { useI18n } from 'vue-i18n'
import AppLogo from '@/components/AppLogo.vue'
import PaymentDialog from '@/components/PaymentDialog.vue'
import { useUserStore } from '@/stores/useUserStore'
import { useSnackbarStore } from '@/stores/useSnackbarStore'

defineOptions({
  name: 'PricingPage',
})

const router = useRouter()
const locale = useRouteLocale()
const { t } = useI18n()
const userStore = useUserStore()
const snackbar = useSnackbarStore()

const showPaymentDialog = ref(false)

function goHome() {
  router.push({ name: 'Home', params: { locale: locale.value } })
}

function goSettings() {
  router.push({ name: 'Settings', params: { locale: locale.value } })
}

function goLogin() {
  router.push({ name: 'Login', params: { locale: locale.value } })
}

function handleLogout() {
  userStore.logout()
  goLogin()
}

function handleTalkToSales() {
  snackbar.info(t('pricing.snackContactSales'))
}

function handleSubscribe() {
  if (!userStore.isLoggedIn) {
    goLogin()
    return
  }
  showPaymentDialog.value = true
}

function onPaid() {
  snackbar.success(t('pricing.snackSubscribeSuccess'))
}
</script>

<style scoped>
.pricing-page {
  min-height: 100vh;
  background: var(--home-bg);
  color: var(--home-text);
}

.pricing-header {
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

.header-left .logo-link {
  cursor: pointer;
}

.header-left .logo-link:hover {
  opacity: 0.9;
}

.header-right {
  display: flex;
  gap: 4px;
  align-items: center;
}

.header-btn-label {
  margin-left: 4px;
}

.pricing-main {
  max-width: 960px;
  margin: 0 auto;
  padding: 48px 24px 64px;
}

.pricing-hero {
  text-align: center;
  margin-bottom: 48px;
}

.pricing-title {
  font-size: 32px;
  font-weight: 700;
  color: var(--home-text);
  margin-bottom: 12px;
}

.pricing-subtitle {
  font-size: 16px;
  color: var(--home-text-secondary);
  margin-bottom: 24px;
}

.pricing-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.btn-outline {
  background: var(--home-surface);
  border: 1px solid var(--home-primary);
  color: var(--home-primary);
}

.pricing-table-wrap {
  background: var(--home-surface);
  border: 1px solid var(--home-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.pricing-table {
  width: 100%;
  border-collapse: collapse;
}

.pricing-table th,
.pricing-table td {
  padding: 16px 20px;
  text-align: left;
  border-bottom: 1px solid var(--home-border);
  vertical-align: middle;
}

.pricing-table thead th {
  font-size: 15px;
  font-weight: 600;
  color: var(--home-text);
  background: var(--home-surface);
}

.pricing-table tbody tr:last-child td {
  border-bottom: none;
}

.th-feature {
  width: 28%;
  min-width: 180px;
}

.th-plan {
  width: 24%;
  text-align: center;
}

.th-plan--highlight {
  background: rgba(66, 133, 244, 0.06);
}

.td-feature {
  font-size: 14px;
  color: var(--home-text);
  font-weight: 500;
}

.td-cell {
  font-size: 14px;
  color: var(--home-text-secondary);
  text-align: center;
}

.td-cell--highlight {
  background: rgba(66, 133, 244, 0.06);
  color: var(--home-text);
}

.cell-note {
  display: block;
  font-size: 12px;
  color: var(--home-text-secondary);
  margin-top: 4px;
}

.table-link {
  color: var(--home-primary);
  text-decoration: none;
}

.table-link:hover {
  text-decoration: underline;
}

.icon-check {
  color: #34a853;
  font-size: 20px;
}

.icon-cross {
  color: var(--home-text-secondary);
  font-size: 18px;
  opacity: 0.7;
}

.tr-action td {
  padding-top: 20px;
  padding-bottom: 20px;
}
</style>
