<template>
  <div class="order-detail-page">
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>
    
    <div v-else-if="error" class="error-container">
      <el-empty description="加载订单详情失败">
        <template #description>
          <p>{{ errorMessage }}</p>
        </template>
        <el-button type="primary" @click="fetchOrderDetail">重试</el-button>
        <el-button @click="$router.push('/orders')">返回订单列表</el-button>
      </el-empty>
    </div>
    
    <div v-else class="order-detail-container">
      <div class="page-header">
        <h1 class="page-title">订单详情</h1>
        <el-button @click="$router.push('/orders')">返回订单列表</el-button>
      </div>
      
      <el-card class="order-info-card">
        <template #header>
          <div class="card-header">
            <span>订单信息</span>
            <div class="order-status" :class="'status-' + order.status">
              {{ getStatusText(order.status) }}
            </div>
          </div>
        </template>
        
        <div class="order-info-list">
          <div class="info-item">
            <span class="label">订单编号：</span>
            <span class="value">{{ order.order_number }}</span>
          </div>
          <div class="info-item">
            <span class="label">下单时间：</span>
            <span class="value">{{ formatDate(order.created_at) }}</span>
          </div>
          <div class="info-item">
            <span class="label">支付方式：</span>
            <span class="value">{{ order.payment_method || '未支付' }}</span>
          </div>
          <div class="info-item">
            <span class="label">支付时间：</span>
            <span class="value">{{ order.paid_at ? formatDate(order.paid_at) : '未支付' }}</span>
          </div>
        </div>
      </el-card>
      
      <el-card class="order-products-card">
        <template #header>
          <div class="card-header">
            <span>商品信息</span>
          </div>
        </template>
        
        <div class="order-products">
          <div class="product-header">
            <div class="product-cell product-info-cell">商品信息</div>
            <div class="product-cell">单价</div>
            <div class="product-cell">数量</div>
            <div class="product-cell">小计</div>
          </div>
          
          <div v-for="item in order.items" :key="item.id" class="product-item">
            <div class="product-cell product-info-cell">
              <el-image :src="item.product.image || defaultImage" :alt="item.product.name" class="product-image" />
              <div class="product-details">
                <router-link :to="`/products/${item.product.id}`" class="product-name">{{ item.product.name }}</router-link>
                <div class="product-meta">{{ item.product.description }}</div>
              </div>
            </div>
            <div class="product-cell">¥{{ formatPrice(item.price) }}</div>
            <div class="product-cell">{{ item.quantity }}</div>
            <div class="product-cell">¥{{ formatPrice(item.price * item.quantity) }}</div>
          </div>
        </div>
        
        <div class="order-summary">
          <div class="summary-item">
            <span class="label">商品总价：</span>
            <span class="value">¥{{ formatPrice(order.items_amount) }}</span>
          </div>
          <div class="summary-item">
            <span class="label">运费：</span>
            <span class="value">¥{{ formatPrice(order.shipping_fee) }}</span>
          </div>
          <div class="summary-item total">
            <span class="label">实付款：</span>
            <span class="value">¥{{ formatPrice(order.total_amount) }}</span>
          </div>
        </div>
      </el-card>
      
      <el-card class="shipping-info-card">
        <template #header>
          <div class="card-header">
            <span>收货信息</span>
          </div>
        </template>
        
        <div class="shipping-info">
          <div class="info-item">
            <span class="label">收货人：</span>
            <span class="value">{{ order.address?.name }}</span>
          </div>
          <div class="info-item">
            <span class="label">联系电话：</span>
            <span class="value">{{ order.address?.phone }}</span>
          </div>
          <div class="info-item">
            <span class="label">收货地址：</span>
            <span class="value">{{ formatAddress(order.address) }}</span>
          </div>
        </div>
      </el-card>
      
      <div class="order-actions">
        <el-button 
          v-if="order.status === 'pending'" 
          type="primary" 
          @click="payOrder(order.id)"
        >去支付</el-button>
        
        <el-button 
          v-if="order.status === 'shipped'" 
          type="success" 
          @click="confirmReceive(order.id)"
        >确认收货</el-button>
        
        <el-button 
          v-if="order.status === 'pending'" 
          type="danger" 
          @click="cancelOrder(order.id)"
        >取消订单</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

const route = useRoute()
const router = useRouter()
const order = ref({})
const loading = ref(true)
const error = ref(false)
const errorMessage = ref('')

// 默认图片
const defaultImage = 'https://via.placeholder.com/100x100?text=No+Image'

// 格式化价格
const formatPrice = (price) => {
  return parseFloat(price || 0).toFixed(2)
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    'pending': '待付款',
    'paid': '待发货',
    'shipped': '待收货',
    'completed': '已完成',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

// 格式化地址
const formatAddress = (address) => {
  if (!address) return ''
  return `${address.province} ${address.city} ${address.district} ${address.detail}`
}

// 获取订单详情
const fetchOrderDetail = async () => {
  const orderId = route.params.id
  if (!orderId) {
    error.value = true
    errorMessage.value = '订单ID无效'
    loading.value = false
    return
  }
  
  loading.value = true
  error.value = false
  
  try {
    const response = await api.orders.getDetail(orderId)
    order.value = response.data || {}
  } catch (err) {
    console.error('获取订单详情失败:', err)
    error.value = true
    errorMessage.value = err.response?.data?.message || '获取订单详情失败'
  } finally {
    loading.value = false
  }
}

// 支付订单
const payOrder = async (orderId) => {
  try {
    // 这里应该跳转到支付页面或调用支付接口
    ElMessage.info('支付功能尚未实现，请联系管理员')
    // 实际项目中应该跳转到支付页面
    // router.push(`/payment/${orderId}`)
  } catch (err) {
    console.error('支付订单失败:', err)
    ElMessage.error(err.response?.data?.message || '支付订单失败')
  }
}

// 确认收货
const confirmReceive = async (orderId) => {
  try {
    await ElMessageBox.confirm('确认已收到商品吗？', '确认收货', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.orders.updateStatus(orderId, 'completed')
    ElMessage.success('确认收货成功')
    fetchOrderDetail()
  } catch (err) {
    if (err !== 'cancel') {
      console.error('确认收货失败:', err)
      ElMessage.error(err.response?.data?.message || '确认收货失败')
    }
  }
}

// 取消订单
const cancelOrder = async (orderId) => {
  try {
    await ElMessageBox.confirm('确定要取消该订单吗？', '取消订单', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.orders.updateStatus(orderId, 'cancelled')
    ElMessage.success('订单已取消')
    fetchOrderDetail()
  } catch (err) {
    if (err !== 'cancel') {
      console.error('取消订单失败:', err)
      ElMessage.error(err.response?.data?.message || '取消订单失败')
    }
  }
}

// 页面加载时获取订单详情
onMounted(() => {
  fetchOrderDetail()
})
</script>

<style scoped>
.order-detail-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
}

.order-info-card,
.order-products-card,
.shipping-info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.order-status {
  font-weight: 500;
}

.status-pending {
  color: #e6a23c;
}

.status-paid {
  color: #409eff;
}

.status-shipped {
  color: #67c23a;
}

.status-completed {
  color: #67c23a;
}

.status-cancelled {
  color: #f56c6c;
}

.order-info-list,
.shipping-info {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.info-item {
  display: flex;
}

.label {
  color: #606266;
  margin-right: 10px;
}

.value {
  color: #303133;
  font-weight: 500;
}

.order-products {
  margin-bottom: 20px;
}

.product-header {
  display: flex;
  background-color: #f5f7fa;
  padding: 10px 0;
  font-weight: 500;
}

.product-item {
  display: flex;
  padding: 15px 0;
  border-bottom: 1px solid #ebeef5;
}

.product-cell {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.product-info-cell {
  flex: 3;
  justify-content: flex-start;
}

.product-image {
  width: 80px;
  height: 80px;
  object-fit: cover;
  margin-right: 15px;
}

.product-details {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.product-name {
  color: #303133;
  text-decoration: none;
  font-weight: 500;
  margin-bottom: 5px;
}

.product-name:hover {
  color: #409eff;
}

.product-meta {
  color: #909399;
  font-size: 12px;
}

.order-summary {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  padding-top: 20px;
}

.summary-item {
  margin-bottom: 10px;
}

.summary-item.total {
  font-size: 18px;
  color: #f56c6c;
}

.order-actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 30px;
}

.loading-container,
.error-container {
  padding: 40px 0;
  text-align: center;
}
</style>