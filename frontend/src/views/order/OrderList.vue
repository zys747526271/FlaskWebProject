<template>
  <div class="order-list-page">
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>
    
    <div v-else-if="error" class="error-container">
      <el-empty description="加载订单失败">
        <template #description>
          <p>{{ errorMessage }}</p>
        </template>
        <el-button type="primary" @click="fetchOrders">重试</el-button>
      </el-empty>
    </div>
    
    <div v-else-if="orders.length === 0" class="empty-orders">
      <el-empty description="暂无订单">
        <template #description>
          <p>您还没有任何订单</p>
        </template>
        <el-button type="primary" @click="$router.push('/')">去购物</el-button>
      </el-empty>
    </div>
    
    <div v-else class="orders-container">
      <h1 class="page-title">我的订单</h1>
      
      <div class="order-filter">
        <el-select v-model="filterStatus" placeholder="订单状态" clearable @change="fetchOrders">
          <el-option label="全部" value="" />
          <el-option label="待付款" value="pending" />
          <el-option label="待发货" value="paid" />
          <el-option label="待收货" value="shipped" />
          <el-option label="已完成" value="completed" />
          <el-option label="已取消" value="cancelled" />
        </el-select>
        
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          @change="fetchOrders"
        />
      </div>
      
      <div class="orders-list">
        <el-card v-for="order in orders" :key="order.id" class="order-item" shadow="hover">
          <div class="order-header">
            <div class="order-info">
              <span class="order-number">订单号: {{ order.order_number }}</span>
              <span class="order-date">下单时间: {{ formatDate(order.created_at) }}</span>
            </div>
            <div class="order-status" :class="'status-' + order.status">
              {{ getStatusText(order.status) }}
            </div>
          </div>
          
          <div class="order-products">
            <div v-for="item in order.items" :key="item.id" class="product-item">
              <el-image :src="item.product.image || defaultImage" :alt="item.product.name" class="product-image" />
              <div class="product-info">
                <router-link :to="`/products/${item.product.id}`" class="product-name">{{ item.product.name }}</router-link>
                <div class="product-price">¥{{ formatPrice(item.price) }} × {{ item.quantity }}</div>
              </div>
            </div>
          </div>
          
          <div class="order-footer">
            <div class="order-total">
              <span>共 {{ getTotalItems(order) }} 件商品</span>
              <span class="total-price">实付款: <strong>¥{{ formatPrice(order.total_amount) }}</strong></span>
            </div>
            
            <div class="order-actions">
              <el-button 
                v-if="order.status === 'pending'" 
                type="primary" 
                size="small" 
                @click="payOrder(order.id)"
              >去支付</el-button>
              
              <el-button 
                v-if="order.status === 'shipped'" 
                type="success" 
                size="small" 
                @click="confirmReceive(order.id)"
              >确认收货</el-button>
              
              <el-button 
                v-if="order.status === 'pending'" 
                type="danger" 
                size="small" 
                @click="cancelOrder(order.id)"
              >取消订单</el-button>
              
              <el-button 
                type="info" 
                size="small" 
                @click="$router.push(`/orders/${order.id}`)"
              >订单详情</el-button>
            </div>
          </div>
        </el-card>
      </div>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[5, 10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="totalOrders"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

const router = useRouter()
const orders = ref([])
const loading = ref(true)
const error = ref(false)
const errorMessage = ref('')
const filterStatus = ref('')
const dateRange = ref(null)
const currentPage = ref(1)
const pageSize = ref(10)
const totalOrders = ref(0)

// 默认图片
const defaultImage = 'https://via.placeholder.com/100x100?text=No+Image'

// 格式化价格
const formatPrice = (price) => {
  return parseFloat(price).toFixed(2)
}

// 格式化日期
const formatDate = (dateString) => {
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

// 获取订单商品总数
const getTotalItems = (order) => {
  return order.items.reduce((total, item) => total + item.quantity, 0)
}

// 获取订单列表
const fetchOrders = async () => {
  loading.value = true
  error.value = false
  
  try {
    const params = {
      page: currentPage.value,
      limit: pageSize.value,
      status: filterStatus.value || undefined
    }
    
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0].toISOString().split('T')[0]
      params.end_date = dateRange.value[1].toISOString().split('T')[0]
    }
    
    const response = await api.orders.getList(params)
    orders.value = response.items || []
    totalOrders.value = response.total || 0
  } catch (err) {
    console.error('获取订单列表失败:', err)
    error.value = true
    errorMessage.value = err.response?.data?.message || '获取订单列表失败'
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
    fetchOrders()
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
    fetchOrders()
  } catch (err) {
    if (err !== 'cancel') {
      console.error('取消订单失败:', err)
      ElMessage.error(err.response?.data?.message || '取消订单失败')
    }
  }
}

// 处理每页显示数量变化
const handleSizeChange = (val) => {
  pageSize.value = val
  fetchOrders()
}

// 处理页码变化
const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchOrders()
}

// 页面加载时获取订单列表
onMounted(() => {
  fetchOrders()
})
</script>

<style scoped>
.order-list-page {
  padding: 20px;
}

.page-title {
  margin-bottom: 20px;
  font-size: 24px;
  font-weight: 500;
}

.order-filter {
  display: flex;
  margin-bottom: 20px;
  gap: 15px;
}

.orders-list {
  margin-bottom: 20px;
}

.order-item {
  margin-bottom: 15px;
}

.order-header {
  display: flex;
  justify-content: space-between;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 10px;
}

.order-info {
  display: flex;
  gap: 20px;
}

.order-number {
  font-weight: 500;
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

.order-products {
  margin-bottom: 15px;
}

.product-item {
  display: flex;
  padding: 10px 0;
  border-bottom: 1px dashed #ebeef5;
}

.product-image {
  width: 80px;
  height: 80px;
  object-fit: cover;
  margin-right: 15px;
}

.product-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.product-name {
  color: #303133;
  text-decoration: none;
  font-weight: 500;
}

.product-name:hover {
  color: #409eff;
}

.product-price {
  color: #606266;
}

.order-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.order-total {
  display: flex;
  flex-direction: column;
}

.total-price {
  color: #f56c6c;
  font-size: 16px;
  margin-top: 5px;
}

.order-actions {
  display: flex;
  gap: 10px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.loading-container,
.error-container,
.empty-orders {
  padding: 40px 0;
  text-align: center;
}
</style>