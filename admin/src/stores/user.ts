import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Admin, TokenResponse } from '@/types'
import { post, get } from '@/utils/request'

const TOKEN_KEY = 'cardstore_admin_token'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref<string>(localStorage.getItem(TOKEN_KEY) || '')
  const userInfo = ref<Admin | null>(null)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username || '')
  const nickname = computed(() => userInfo.value?.nickname || userInfo.value?.username || '')
  // 用户头像字母（取昵称或用户名的首字符，支持中英文）
  const avatarLetter = computed(() => {
    const name = userInfo.value?.nickname || userInfo.value?.username || ''
    if (!name) return '?'
    // 取第一个字符（支持中文）
    return name.charAt(0).toUpperCase()
  })

  // 登录
  async function login(username: string, password: string) {
    const res = await post<TokenResponse>('/admin/auth/login', { username, password })
    token.value = res.data.access_token
    localStorage.setItem(TOKEN_KEY, res.data.access_token)
    await fetchUserInfo()
    return res
  }

  // 获取用户信息
  async function fetchUserInfo() {
    if (!token.value) return
    const res = await get<Admin>('/admin/auth/me')
    userInfo.value = res.data
    return res.data
  }

  // 修改密码
  async function changePassword(oldPassword: string, newPassword: string) {
    return post('/admin/auth/password', {
      old_password: oldPassword,
      new_password: newPassword,
    })
  }

  // 登出
  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem(TOKEN_KEY)
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    username,
    nickname,
    avatarLetter,
    login,
    fetchUserInfo,
    changePassword,
    logout,
  }
})
