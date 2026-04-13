<template>
  <v-dialog
    :model-value="modelValue"
    max-width="480"
    persistent
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <v-card class="payment-card">
      <v-card-title class="d-flex align-center justify-space-between">
        <span>订阅 NoteWorks Plus</span>
        <v-btn
          icon
          variant="text"
          size="small"
          @click="handleClose"
        >
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text v-if="step === 'select'">
        <div class="plan-summary mb-4">
          <div class="plan-price">
            ¥{{ (totalAmount / 100).toFixed(0) }}
          </div>
          <v-select
            v-model="durationMonths"
            :items="durationOptions"
            item-title="label"
            item-value="value"
            label="订阅时长"
            density="compact"
            class="mt-2"
          />
        </div>

        <div class="text-subtitle-2 mb-3">
          选择支付方式
        </div>

        <div class="pay-channel-group">
          <v-btn
            :variant="payChannel === 'alipay' ? 'flat' : 'outlined'"
            :color="payChannel === 'alipay' ? 'primary' : undefined"
            class="pay-channel-btn"
            @click="payChannel = 'alipay'"
          >
            <v-icon start>
              mdi-alpha-a-circle
            </v-icon>
            支付宝
          </v-btn>
          <v-btn
            :variant="payChannel === 'wechat' ? 'flat' : 'outlined'"
            :color="payChannel === 'wechat' ? 'success' : undefined"
            class="pay-channel-btn"
            @click="payChannel = 'wechat'"
          >
            <v-icon start>
              mdi-wechat
            </v-icon>
            微信支付
          </v-btn>
        </div>

        <v-btn
          color="primary"
          block
          size="large"
          class="mt-4"
          :loading="creating"
          @click="handleCreateOrder"
        >
          立即支付 ¥{{ (totalAmount / 100).toFixed(0) }}
        </v-btn>
      </v-card-text>

      <v-card-text
        v-else-if="step === 'qrcode'"
        class="text-center"
      >
        <div class="qr-header mb-3">
          <v-icon
            :color="payChannel === 'alipay' ? '#1677FF' : '#07C160'"
            size="24"
          >
            {{ payChannel === 'alipay' ? 'mdi-alpha-a-circle' : 'mdi-wechat' }}
          </v-icon>
          <span class="ml-2 text-body-1">
            {{ payChannel === 'alipay' ? '支付宝' : '微信' }}扫码支付
          </span>
        </div>

        <div class="qr-wrap">
          <QrcodeVue
            :value="qrCodeUrl"
            :size="200"
            level="M"
          />
        </div>

        <div class="text-body-2 text-medium-emphasis mt-3">
          请使用{{ payChannel === 'alipay' ? '支付宝' : '微信' }}扫描二维码完成支付
        </div>
        <div class="text-caption text-medium-emphasis mt-1">
          支付金额：¥{{ (totalAmount / 100).toFixed(0) }}
        </div>

        <v-progress-linear
          v-if="polling"
          indeterminate
          color="primary"
          class="mt-3"
        />
        <div
          v-if="pollTimeout"
          class="text-caption text-error mt-2"
        >
          支付超时，请重新下单
        </div>
      </v-card-text>

      <v-card-text
        v-else-if="step === 'success'"
        class="text-center"
      >
        <v-icon
          color="success"
          size="64"
          class="mb-3"
        >
          mdi-check-circle
        </v-icon>
        <div class="text-h6 mb-2">
          支付成功
        </div>
        <div class="text-body-2 text-medium-emphasis">
          您已成功订阅 NoteWorks Plus，享受更强大的功能！
        </div>
        <v-btn
          color="primary"
          class="mt-4"
          @click="handleClose"
        >
          开始使用
        </v-btn>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted, watch } from 'vue'
import QrcodeVue from 'qrcode.vue'
import { paymentApi } from '@/api/payment'
import { useUserStore } from '@/stores/useUserStore'
import { useSnackbarStore } from '@/stores/useSnackbarStore'

defineOptions({
  name: 'PaymentDialog',
})

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'paid': []
}>()

const userStore = useUserStore()
const snackbar = useSnackbarStore()

const PRICE_PER_MONTH = 9900

const step = ref<'select' | 'qrcode' | 'success'>('select')
const payChannel = ref<'alipay' | 'wechat'>('alipay')
const durationMonths = ref(1)
const creating = ref(false)
const orderId = ref('')
const qrCodeUrl = ref('')
const polling = ref(false)
const pollTimeout = ref(false)
let pollTimer: ReturnType<typeof setInterval> | null = null
let timeoutTimer: ReturnType<typeof setTimeout> | null = null

const durationOptions = [
  { label: '1 个月 — ¥99', value: 1 },
  { label: '3 个月 — ¥297', value: 3 },
  { label: '6 个月 — ¥594', value: 6 },
  { label: '12 个月 — ¥1188', value: 12 },
]

const totalAmount = computed(() => PRICE_PER_MONTH * durationMonths.value)

watch(() => props.modelValue, (open) => {
  if (open) {
    step.value = 'select'
    pollTimeout.value = false
    qrCodeUrl.value = ''
    orderId.value = ''
  } else {
    stopPolling()
  }
})

async function handleCreateOrder() {
  creating.value = true
  try {
    const result = await paymentApi.createOrder({
      pay_channel: payChannel.value,
      duration_months: durationMonths.value,
    })
    orderId.value = result.order_id
    qrCodeUrl.value = result.qr_code_url
    step.value = 'qrcode'
    startPolling()
  } catch {
    snackbar.error('创建订单失败，请重试')
  } finally {
    creating.value = false
  }
}

function startPolling() {
  polling.value = true
  pollTimeout.value = false

  pollTimer = setInterval(async () => {
    try {
      const status = await paymentApi.getOrderStatus(orderId.value)
      if (status.status === 'paid') {
        stopPolling()
        step.value = 'success'
        await userStore.fetchUser()
        emit('paid')
      }
    } catch {
      // polling errors are non-fatal
    }
  }, 3000)

  timeoutTimer = setTimeout(() => {
    pollTimeout.value = true
    stopPolling()
  }, 5 * 60 * 1000)
}

function stopPolling() {
  polling.value = false
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  if (timeoutTimer) {
    clearTimeout(timeoutTimer)
    timeoutTimer = null
  }
}

function handleClose() {
  stopPolling()
  emit('update:modelValue', false)
}

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.payment-card {
  border-radius: 12px;
}

.plan-summary {
  background: rgba(var(--v-theme-primary), 0.06);
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.plan-price {
  font-size: 32px;
  font-weight: 700;
  color: rgb(var(--v-theme-primary));
}

.pay-channel-group {
  display: flex;
  gap: 12px;
}

.pay-channel-btn {
  flex: 1;
}

.qr-header {
  display: flex;
  align-items: center;
  justify-content: center;
}

.qr-wrap {
  display: inline-block;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.08);
}
</style>
