// API 响应类型
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

// 分页响应
export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

// 管理员
export interface Admin {
  id: number
  username: string
  nickname: string | null
  email: string | null
  is_active: boolean
  is_superuser: boolean
  last_login_at: string | null
  created_at: string
  updated_at: string
}

// Token 响应
export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

// 平台配置
export interface PlatformConfig {
  id: number
  key: string
  value: string
  description: string | null
  created_at: string
  updated_at: string
}

// 邮件配置
export interface EmailConfig {
  id: number
  smtp_host: string
  smtp_port: number
  smtp_user: string
  smtp_password: string
  from_name: string | null
  from_email: string
  use_tls: boolean
  is_verified: boolean
  created_at: string
  updated_at: string
}

// 公告
export interface Announcement {
  id: number
  title: string
  description: string | null
  content: string
  is_popup: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

// Banner
export interface Banner {
  id: number
  image_url: string
  link_url: string | null
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

// 底部链接
export interface FooterLink {
  id: number
  title: string
  url: string
  link_type: 'agreement' | 'friend_link'
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

// 分类
export interface Category {
  id: number
  name: string
  slug: string
  description: string | null
  icon: string | null
  parent_id: number | null
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

// 支付方式
export interface PaymentMethod {
  id: number
  name: string
  icon: string | null
  fee_type: 'percentage' | 'fixed'
  fee_value: string
  description: string | null
  meta_data: Record<string, unknown>
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

// 商品图片
export interface ProductImage {
  id: number
  image_url: string
  sort_order: number
  is_primary: boolean
}

// 商品标签
export interface ProductTag {
  id: number
  key: string
  value: string
}

// 商品介绍
export interface ProductIntro {
  id: number
  title: string
  content: string
  icon: string | null
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

// 商品
export interface Product {
  id: number
  name: string
  slug: string
  product_type: 'virtual' | 'physical'
  price: string
  stock: number
  is_active: boolean
  sort_order: number
  category: Category | null
  primary_image: string | null
  images: ProductImage[]
  tags: ProductTag[]
  intros: ProductIntro[]
  payment_methods: PaymentMethod[]
  created_at: string
  updated_at: string
}

// 库存项
export interface InventoryItem {
  id: number
  content: string
  is_sold: boolean
  sold_at: string | null
  created_at: string
  updated_at: string
}

// 订单状态
export type OrderStatus = 'pending' | 'paid' | 'processing' | 'completed' | 'cancelled' | 'refunded'

// 订单商品项
export interface OrderItem {
  id: number
  product_id: number
  product_name: string
  product_type: 'virtual' | 'physical'
  quantity: number
  price: string
  subtotal: string
  delivery_content: string | null
  delivered_at: string | null
}

// 订单
export interface Order {
  id: number
  order_no: string
  status: OrderStatus
  email: string
  currency: string
  total_price: string
  payment_method: PaymentMethod | null
  shipping_name: string | null
  shipping_phone: string | null
  shipping_address: string | null
  remark: string | null
  items: OrderItem[]
  created_at: string
  updated_at: string
}

// 订单日志
export interface OrderLog {
  id: number
  action: string
  content: string
  operator: string | null
  created_at: string
}
