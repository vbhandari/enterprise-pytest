export interface Product {
  id: number
  name: string
  description: string | null
  price: number
  stock_quantity: number
  category: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface OrderItem {
  id: number
  product_id: number
  quantity: number
  unit_price: number
  subtotal: number
}

export interface Order {
  id: number
  customer_id: number
  status: string
  subtotal: number
  tax_amount: number
  discount_amount: number
  total: number
  discount_code: string | null
  items: OrderItem[]
  created_at: string
  updated_at: string
}

export interface OrderSummary {
  id: number
  customer_id: number
  status: string
  total: number
  created_at: string
}

export interface Coupon {
  id: number
  code: string
  discount_percent: number
  valid_from: string
  valid_to: string
  max_uses: number
  current_uses: number
  is_active: boolean
  created_at: string
}

export interface AuthResponse {
  access_token: string
}

export interface HealthResponse {
  status: string
  version: string
}

export type OrderStatus = 'created' | 'paid' | 'shipped' | 'delivered' | 'cancelled'
