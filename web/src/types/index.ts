// API 响应类型
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

// 分页数据
export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
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
  children?: Category[]
}

// 商品标签
export interface ProductTag {
  id: number
  key: string
  value: string
}

// 商品图片
export interface ProductImage {
  id: number
  image_url: string
  sort_order: number
  is_primary: boolean
}

// 商品介绍
export interface ProductIntro {
  id: number
  title: string
  content: string
  icon: string | null
  sort_order: number
  is_active: boolean
}

// 支付方式
export interface PaymentMethod {
  id: number
  name: string
  icon: string | null
  fee_type: 'percentage' | 'fixed'
  fee_value: string
  description: string | null
}

// 商品列表项
export interface ProductListItem {
  id: number
  name: string
  slug: string
  product_type: 'virtual' | 'physical'
  price: string
  stock: number
  is_active: boolean
  category: Category | null
  primary_image: string | null
  tags: ProductTag[]
}

// 商品详情
export interface ProductDetail extends ProductListItem {
  images: ProductImage[]
  intros: ProductIntro[]
  payment_methods: PaymentMethod[]
  sort_order: number
  created_at: string
  updated_at: string
}

// 标签分组
export interface TagGroup {
  key: string
  values: string[]
}

// Banner
export interface Banner {
  id: number
  image_url: string
  link_url: string | null
  sort_order: number
}

// 公告
export interface Announcement {
  id: number
  title: string
  description: string | null
  content?: string
  is_popup: boolean
  created_at: string
}

// 底部链接
export interface FooterLink {
  id: number
  title: string
  url: string
  link_type: 'agreement' | 'friend_link'
  sort_order: number
}

// 购物车商品
export interface CartItem {
  product: ProductListItem
  quantity: number
}

// 订单商品
export interface OrderItemCreate {
  product_id: number
  quantity: number
}

// 创建订单
export interface OrderCreate {
  email: string
  items: OrderItemCreate[]
  payment_method_id: number
  currency: string
  shipping_name?: string
  shipping_phone?: string
  shipping_address?: string
  remark?: string
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
  delivery_content?: string
  delivered_at?: string
}

// 订单列表项
export interface OrderListItem {
  id: number
  order_no: string
  status: OrderStatus
  email: string
  currency: string
  total_price: string
  created_at: string
  // 收货信息（实体商品）
  shipping_name: string | null
  shipping_phone: string | null
  shipping_address: string | null
}

// 订单详情
export interface OrderDetail extends OrderListItem {
  paid_at: string | null
  payment_method_id: number | null
  shipping_name: string | null
  shipping_phone: string | null
  shipping_address: string | null
  remark: string | null
  updated_at: string
  items: OrderItem[]
}

// 本地存储的订单记录
export interface LocalOrderRecord {
  order_no: string
  email: string
  total_price: string
  status: OrderStatus
  created_at: string
}

// 站点配置
export interface SiteConfig {
  site_name: string
  site_description: string
  site_logo?: string
  site_favicon?: string
  currency: string
  currency_symbol: string
  contact_info?: string
}

// 支付初始化响应
export interface PaymentInitResponse {
  payment_url: string | null
  payment_data: PaymentData
  expires_in: number
}

// 支付数据（TRC20）
export interface PaymentData {
  wallet_address?: string
  amount?: string
  original_amount?: string
  network?: string
  currency?: string
  qr_content?: string
  [key: string]: unknown
}

// 支付状态响应
export interface PaymentStatusResponse {
  order_no: string
  status: 'pending' | 'paid' | 'completed' | 'cancelled' | 'expired'
  order_status: string
  paid_at: string | null
}
