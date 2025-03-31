<template>
  <div class="admin-dashboard">
    <h1 class="page-title">管理控制台</h1>
    
    <!-- 数据概览卡片 -->
    <el-row :gutter="20" class="dashboard-cards">
      <el-col :span="6">
        <el-card shadow="hover" class="data-card">
          <template #header>
            <div class="card-header">
              <el-icon><User /></el-icon>
              <span>用户总数</span>
            </div>
          </template>
          <div class="card-value">{{ stats.userCount || 0 }}</div>
          <div class="card-footer">
            <el-tag size="small" type="info">今日新增: {{ stats.newUserCount || 0 }}</el-tag>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="data-card">
          <template #header>
            <div class="card-header">
              <el-icon><Goods /></el-icon>
              <span>商品总数</span>
            </div>
          </template>
          <div class="card-value">{{ stats.productCount || 0 }}</div>
          <div class="card-footer">
            <el-tag size="small" type="info">今日新增: {{ stats.newProductCount || 0 }}</el-tag>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="data-card">
          <template #header>
            <div class="card-header">
              <el-icon><List /></el-icon>
              <span>订单总数</span>
            </div>
          </template>
          <div class="card-value">{{ stats.orderCount || 0 }}</div>
          <div class="card-footer">
            <el-tag size="small" type="info">今日新增: {{ stats.newOrderCount || 0 }}</el-tag>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="data-card">
          <template #header>
            <div class="card-header">
              <el-icon><Money /></el-icon>
              <span>销售总额</span>
            </div>
          </template>
          <div class="card-value">¥{{ formatPrice(stats.totalSales || 0) }}</div>
          <div class="card-footer">
            <el-tag size="small" type="info">今日销售: ¥{{ formatPrice(stats.todaySales || 0) }}</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 图表区域 -->
    <el-row :gutter="20" class="dashboard-charts">
      <el-col :span="12">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>最近7天销售趋势</span>
            </div>
          </template>
          <div class="chart-container" v-loading="loading.sales">
            <!-- 这里可以集成图表库如ECharts -->
            <div class="chart-placeholder">销售趋势图表</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>商品类别分布</span>
            </div>
          </template>
          <div class="chart-container" v-loading="loading.categories">
            <!-- 这里可以集成图表库如ECharts -->
            <div class="chart-placeholder">类别分布图表</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 最新订单 -->
    <el-card shadow="hover" class="recent-orders-card">
      <template #header>
        <div class="card-header">
          <span>最新订单</span>
          <router-link to="/admin/orders" class="view-more">查看全部</router-link>
        </div>
      </template>
      <div v-loading="loading.orders">
        <el-table :data="recentOrders" style="width: 100%">
          <el-table-column prop="order_number" label="订单编号" width="180" />
          <el-table-column prop="user.username" label="用户" width="120" />
          <el-table-column prop="total_amount" label="金额" width="120">
            <template #default="scope">
              ¥{{ formatPrice(scope.row.total_amount) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="120">
            <template #default="scope">
              <el-tag :type="getStatusType(scope.row.status)">
                {{ getStatusText(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间">
            <template #default="scope">
              {{ formatDate(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="scope">
              <router-link :to="`/admin/orders/${scope.row.id}`">
                <el-button type="text" size="small">查看</el-button>
              </router-link>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  User, Goods, List, Money,
  DataBoard, ShoppingCart, Wallet
} from '@element-plus/icons-vue'
import api from '../../utils/api'

const router = useRouter()

// 加载状态
const loading = reactive({
  stats: false,
  sales: false,
  categories: false,
  orders: false
})

// 统计数据
const stats = reactive({
  userCount: 0,
  newUserCount: 0,
  productCount: 0,
  newProductCount: 0,
  orderCount: 0,
  newOrderCount: 0,
  totalSales: 0,
  todaySales: 0
})

// 最近订单
const recentOrders = ref([])

// 格式化价格
const formatPrice = (price) => {
  return parseFloat(price).toFixed(2)
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
    'shipped': '已发货',
    'completed': '已完成',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

// 获取状态类型
const getStatusType = (status) => {
  const typeMap = {
    'pending': 'warning',
    'paid': 'primary',
    'shipped': 'success',
    'completed': 'success',
    'cancelled': 'info'
  }
  return typeMap[status] || ''
}

// 获取统计数据
const fetchStats = async () => {
  loading.stats = true
  try {
    const response = await api.get('/admin/stats')
    Object.assign(stats, response.data)
  } catch (error) {
    console.error('获取统计数据失败:', error)
    ElMessage.error('获取统计数据失败')
  } finally {
    loading.stats = false
  }
}

// 获取最近订单
const fetchRecentOrders = async () => {
  loading.orders = true
  try {
    const response = await api.get('/admin/orders/recent')
    recentOrders.value = response.data
  } catch (error) {
    console.error('获取最近订单失败:', error)
    ElMessage.error('获取最近订单失败')
  } finally {
    loading.orders = false
  }
}

onMounted(() => {
  fetchStats()
  fetchRecentOrders()
})
</script>

<style lang="scss" scoped>
.admin-dashboard {
  padding: 20px;
}

.page-title {
  margin-bottom: 20px;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.dashboard-cards {
  margin-bottom: 20px;
}

.data-card {
  height: 100%;
  
  .card-header {
    display: flex;
    align-items: center;
    
    .el-icon {
      margin-right: 8px;
      font-size: 18px;
    }
  }
  
  .card-value {
    font-size: 28px;
    font-weight: 600;
    color: #303133;
    margin: 15px 0;
  }
  
  .card-footer {
    margin-top: 10px;
  }
}

.dashboard-charts {
  margin-bottom: 20px;
}

.chart-card {
  margin-bottom: 20px;
  
  .chart-container {
    height: 300px;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  
  .chart-placeholder {
    color: #909399;
    font-size: 14px;
  }
}

.recent-orders-card {
  margin-bottom: 20px;
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .view-more {
      font-size: 14px;
      color: #409EFF;
      text-decoration: none;
      
      &:hover {
        text-decoration: underline;
      }
    }
  }
}
</style>