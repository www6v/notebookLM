<template>
  <div class="pricing-page">
    <header class="pricing-header">
      <div class="header-left">
        <h1
          class="logo"
          @click="router.push('/')"
        >
          NotebookLM
        </h1>
      </div>
      <div class="header-right">
        <template v-if="userStore.isLoggedIn">
          <el-button
            text
            @click="router.push('/settings')"
          >
            <el-icon size="20">
              <Setting />
            </el-icon>
            <span class="header-btn-label">设置</span>
          </el-button>
          <el-button
            text
            @click="handleLogout"
          >
            <el-icon size="20">
              <SwitchButton />
            </el-icon>
          </el-button>
        </template>
        <el-button
          v-else
          type="primary"
          @click="router.push('/login')"
        >
          登录
        </el-button>
      </div>
    </header>

    <main class="pricing-main">
      <div class="pricing-hero">
        <h2 class="pricing-title">定价</h2>
        <p class="pricing-subtitle">
          面向个人创作者、团队与企业的方案，按需选择
        </p>
        <div class="pricing-actions">
          <el-button
            type="primary"
            size="large"
            @click="router.push('/')"
          >
            立即开始
          </el-button>
          <el-button
            size="large"
            class="btn-outline"
            @click="handleTalkToSales"
          >
            联系销售
          </el-button>
        </div>
      </div>

      <div class="pricing-table-wrap">
        <table class="pricing-table">
          <thead>
            <tr>
              <th class="th-feature" />
              <th class="th-plan">免费版</th>
              <th class="th-plan th-plan--highlight">NotebookLM Plus</th>
              <th class="th-plan">企业版</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="td-feature">月费 / 平台费用</td>
              <td class="td-cell">免费</td>
              <td class="td-cell td-cell--highlight">
                ¥99/月
                <span class="cell-note">学生 ¥49/月</span>
              </td>
              <td class="td-cell">
                <a
                  href="#"
                  class="table-link"
                  @click.prevent="handleTalkToSales"
                >
                  批量优惠，联系洽谈 →
                </a>
              </td>
            </tr>
            <tr>
              <td class="td-feature">笔记本数量</td>
              <td class="td-cell">最多 100 个</td>
              <td class="td-cell td-cell--highlight">最多 500 个</td>
              <td class="td-cell">按需定制</td>
            </tr>
            <tr>
              <td class="td-feature">每笔记本来源数</td>
              <td class="td-cell">50 个</td>
              <td class="td-cell td-cell--highlight">300 个</td>
              <td class="td-cell">按需定制</td>
            </tr>
            <tr>
              <td class="td-feature">每日对话次数</td>
              <td class="td-cell">50 次</td>
              <td class="td-cell td-cell--highlight">500 次</td>
              <td class="td-cell">按需定制</td>
            </tr>
            <tr>
              <td class="td-feature">每日音频生成</td>
              <td class="td-cell">3 次</td>
              <td class="td-cell td-cell--highlight">20 次</td>
              <td class="td-cell">按需定制</td>
            </tr>
            <tr>
              <td class="td-feature">聊天与 API 访问</td>
              <td class="td-cell">
                <el-icon class="icon-check">
                  <Check />
                </el-icon>
              </td>
              <td class="td-cell td-cell--highlight">
                <el-icon class="icon-check">
                  <Check />
                </el-icon>
              </td>
              <td class="td-cell">
                <el-icon class="icon-check">
                  <Check />
                </el-icon>
              </td>
            </tr>
            <tr>
              <td class="td-feature">活动日志与导出</td>
              <td class="td-cell">
                <el-icon class="icon-check">
                  <Check />
                </el-icon>
              </td>
              <td class="td-cell td-cell--highlight">
                <el-icon class="icon-check">
                  <Check />
                </el-icon>
              </td>
              <td class="td-cell">
                <el-icon class="icon-check">
                  <Check />
                </el-icon>
              </td>
            </tr>
            <tr>
              <td class="td-feature">自定义回复风格与高级分享</td>
              <td class="td-cell">
                <el-icon class="icon-cross">
                  <Close />
                </el-icon>
              </td>
              <td class="td-cell td-cell--highlight">
                <el-icon class="icon-check">
                  <Check />
                </el-icon>
              </td>
              <td class="td-cell">
                <el-icon class="icon-check">
                  <Check />
                </el-icon>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Setting, SwitchButton, Check, Close } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/useUserStore'

defineOptions({
  name: 'PricingPage',
})

const router = useRouter()
const userStore = useUserStore()

function handleLogout() {
  userStore.logout()
  router.push('/login')
}

function handleTalkToSales() {
  ElMessage.info('请联系客服获取企业方案与报价')
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

.header-left .logo {
  font-size: 22px;
  font-weight: 700;
  color: var(--home-primary);
  cursor: pointer;
}

.header-left .logo:hover {
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

.btn-outline:hover {
  background: rgba(66, 133, 244, 0.08);
  border-color: var(--home-primary);
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
</style>
