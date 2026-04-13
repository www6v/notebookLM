import client from './client'

export interface CreateOrderParams {
  pay_channel: 'alipay' | 'wechat'
  duration_months: number
}

export interface CreateOrderResult {
  order_id: string
  out_trade_no: string
  qr_code_url: string
  amount: number
  pay_channel: string
}

export interface OrderStatus {
  order_id: string
  status: string
  pay_channel: string
  amount: number
  paid_at: string | null
  created_at: string
}

export const paymentApi = {
  createOrder: async (params: CreateOrderParams): Promise<CreateOrderResult> => {
    const { data } = await client.post('/payment/create', params)
    return data
  },

  getOrderStatus: async (orderId: string): Promise<OrderStatus> => {
    const { data } = await client.get(`/payment/status/${orderId}`)
    return data
  },
}
