import { defineStore } from 'pinia'
import axios from 'axios'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    userInfo: JSON.parse(localStorage.getItem('userInfo') || '{}'),
    isAuthenticated: !!localStorage.getItem('token')
  }),
  
  getters: {
    isAdmin: (state) => state.userInfo.isAdmin === true,
    userId: (state) => state.userInfo.id,
    username: (state) => state.userInfo.nickname || '用户'
  },
  
  actions: {
    async login(credentials) {
      try {
        const response = await axios.post('/api/auth/login', credentials)
        const { token, user } = response.data
        
        // 保存到状态和本地存储
        this.token = token
        this.userInfo = user
        this.isAuthenticated = true
        
        localStorage.setItem('token', token)
        localStorage.setItem('userInfo', JSON.stringify(user))
        
        // 设置axios默认头部
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
        
        return { success: true }
      } catch (error) {
        console.error('登录失败:', error)
        return { 
          success: false, 
          message: error.response?.data?.message || '登录失败，请检查用户名和密码'
        }
      }
    },
    
    async register(userData) {
      try {
        const response = await axios.post('/api/auth/register', userData)
        return { success: true, data: response.data }
      } catch (error) {
        console.error('注册失败:', error)
        return { 
          success: false, 
          message: error.response?.data?.message || '注册失败，请稍后再试'
        }
      }
    },
    
    async adminLogin(credentials) {
      try {
        const response = await axios.post('/api/auth/admin/login', credentials)
        const { token, admin } = response.data
        
        // 保存到状态和本地存储
        this.token = token
        this.userInfo = { ...admin, isAdmin: true }
        this.isAuthenticated = true
        
        localStorage.setItem('token', token)
        localStorage.setItem('userInfo', JSON.stringify(this.userInfo))
        
        // 设置axios默认头部
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
        
        return { success: true }
      } catch (error) {
        console.error('管理员登录失败:', error)
        return { 
          success: false, 
          message: error.response?.data?.message || '登录失败，请检查用户名和密码'
        }
      }
    },
    
    async fetchUserProfile() {
      try {
        const response = await axios.get('/api/users/profile')
        this.userInfo = response.data
        localStorage.setItem('userInfo', JSON.stringify(response.data))
        return { success: true, data: response.data }
      } catch (error) {
        console.error('获取用户信息失败:', error)
        return { success: false, message: '获取用户信息失败' }
      }
    },
    
    logout() {
      // 清除状态
      this.token = ''
      this.userInfo = {}
      this.isAuthenticated = false
      
      // 清除本地存储
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      
      // 清除axios头部
      delete axios.defaults.headers.common['Authorization']
    }
  }
})