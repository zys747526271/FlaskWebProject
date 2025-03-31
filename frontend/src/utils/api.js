import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    const { response } = error
    
    if (response && response.status === 401) {
      // 未授权，清除token并跳转到登录页
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      window.location.href = '/auth/login'
    }
    
    return Promise.reject(error)
  }
)

// API服务
export default {
  // 用户认证
  auth: {
    login: (data) => api.post('/auth/login', data),
    register: (data) => api.post('/auth/register', data),
    adminLogin: (data) => api.post('/auth/admin/login', data),
    getProfile: () => api.get('/auth/profile'),
    updateProfile: (data) => api.put('/auth/profile', data)
  },
  
  // 商品
  products: {
    getList: (params) => api.get('/products', { params }),
    getDetail: (id) => api.get(`/products/${id}`),
    create: (data) => api.post('/products', data),
    update: (id, data) => api.put(`/products/${id}`, data),
    delete: (id) => api.delete(`/products/${id}`),
    uploadImage: (id, formData) => api.post(`/products/${id}/images`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
    getRecommended: () => api.get('/products/recommended'),
    getHot: () => api.get('/products/hot')
  },
  
  // 购物车
  cart: {
    getItems: () => api.get('/carts/cart'),
    addItem: (data) => api.post('/carts/cart', data),
    updateItem: (id, data) => api.put(`/carts/${id}`, data),
    removeItem: (id) => api.delete(`/carts/${id}`),
    batchRemove: (ids) => api.post('/carts/batch', { ids })
  },
  
  // 订单
  orders: {
    getList: (params) => api.get('/orders', { params }),
    getDetail: (id) => api.get(`/orders/${id}`),
    create: (data) => api.post('/orders', data),
    updateStatus: (id, status) => api.put(`/orders/${id}/status`, { status }),
    delete: (id) => api.delete(`/orders/${id}`)
  },
  
  // 地址
  addresses: {
    getList: () => api.get('/addresses'),
    create: (data) => api.post('/addresses', data),
    update: (id, data) => api.put(`/addresses/${id}`, data),
    delete: (id) => api.delete(`/addresses/${id}`),
    getDefault: () => api.get('/addresses/default'),
    setDefault: (id) => api.put(`/addresses/set-default/${id}`),
    getRegions: () => api.get('/addresses/regions')
  },
  
  // 标签/分类
  tags: {
    getList: (params) => api.get('/tags', { params }),
    getDetail: (id) => api.get(`/tags/${id}`)
  },
  
  // 管理员
  admin: {
    getUsers: (params) => api.get('/admin/users', { params }),
    getUserDetail: (id) => api.get(`/admin/users/${id}`),
    banUser: (id, isBanned) => api.put(`/admin/users/${id}/ban`, { is_banned: isBanned }),
    deleteUser: (id) => api.delete(`/admin/users/${id}`),
    getPendingProducts: () => api.get('/admin/products/pending'),
    batchUpdateProductStatus: (data) => api.put('/admin/products/batch/status', data),
    getUserOrders: (userId) => api.get(`/admin/users/${userId}/orders`),
    resetUserPassword: (userId) => api.post(`/admin/users/${userId}/reset_password`),
    updateUser: (userId, data) => api.put(`/admin/users/${userId}`, data)
  }
}