import { defineStore } from 'pinia'
import { request } from '@/utils/api'
import router from '@/router'
import { ElMessage } from 'element-plus'

interface User {
  id: string
  email: string
  nickname: string | null
}

interface AuthState {
  user: User | null
  token: string | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')!) : null,
    token: localStorage.getItem('token')
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    userEmail: (state) => state.user?.email || ''
  },

  actions: {
    async login(email: string, password: string) {
      try {
        const response = await request.post<{
          access_token: string
          token_type: string
          user: User
        }>('/auth/login', { email, password })

        this.token = response.access_token
        this.user = response.user

        localStorage.setItem('token', response.access_token)
        localStorage.setItem('user', JSON.stringify(response.user))

        ElMessage.success('登录成功')
        router.push('/')
      } catch (error) {
        throw error
      }
    },

    async register(email: string, password: string, nickname?: string) {
      try {
        const response = await request.post<{
          access_token: string
          token_type: string
          user: User
        }>('/auth/register', { email, password, nickname })

        this.token = response.access_token
        this.user = response.user

        localStorage.setItem('token', response.access_token)
        localStorage.setItem('user', JSON.stringify(response.user))

        ElMessage.success('注册成功')
        router.push('/')
      } catch (error) {
        throw error
      }
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      router.push('/login')
    },

    async getUserInfo() {
      try {
        const user = await request.get<User>('/auth/me')
        this.user = user
        localStorage.setItem('user', JSON.stringify(user))
      } catch (error) {
        this.logout()
        throw error
      }
    }
  }
})