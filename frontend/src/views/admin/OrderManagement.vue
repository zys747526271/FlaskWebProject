<template>
  <div class="order-management">
    <h1 class="page-title">订单管理</h1>
    
    <!-- 搜索和操作栏 -->
    <div class="action-bar">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-input
            v-model="searchQuery"
            placeholder="搜索订单号/用户名"
            clearable
            @clear="fetchOrders"
            @keyup.enter="fetchOrders"
          >
            <template #append>
              <el-button @click="fetchOrders">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="statusFilter" placeholder="状态筛选" clearable @change="fetchOrders">
            <el-option label="全部" value="" />
            <el-option label="待付款" value="pending" />
            <el-option label="待发货" value="paid" />
            <el-option label="已发货" value="shipped" />
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-col>
        <el-col :span="14" class="action-buttons">
          <el-button type="success" :disabled="!selectedOrders.length" @click="handleBatchShip">
            <el-icon><Van /></el-icon> 批量发货
          </el-button>
          <el-button type="warning" :disabled="!selectedOrders.length" @click="handleBatchCancel">
            <el-icon><Close /></el-icon> 批量取消
          </el-button>
        </el-col>
      </el-row>
    </div>
    
    <!-- 订单列表 -->
    <el-card shadow="hover" class="order-table-card">
      <el-table
        :data="orders"
        style="width: 100%"
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="order_number" label="订单编号" width="180" />
        <el-table-column prop="user.username" label="用户" width="120" />
        <el-table-column prop="total_amount" label="金额" width="100">
          <template #default="scope">
            ¥{{ formatPrice(scope.row.total_amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="item_count" label="商品数量" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="payment_method" label="支付方式" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="scope">
            <el-button type="primary" size="small" @click="handleViewDetail(scope.row)">
              查看
            </el-button>
            <el-button 
              v-if="scope.row.status === 'paid'"
              type="success" 
              size="small" 
              @click="handleShip(scope.row)"
            >
              发货
            </el-button>
            <el-button 
              v-if="['pending', 'paid'].includes(scope.row.status)"
              type="warning" 
              size="small" 
              @click="handleCancel(scope.row)"
            >
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    
    <!-- 发货对话框 -->
    <el-dialog
      v-model="shipDialogVisible"
      title="订单发货"
      width="500px"
    >
      <el-form
        :model="shipForm"
        :rules="shipRules"
        ref="shipFormRef"
        label-width="100px"
      >
        <el-form-item label="物流公司" prop="shipping_company">
          <el-select v-model="shipForm.shipping_company" placeholder="选择物流公司" style="width: 100%">
            <el-option label="顺丰速运" value="SF" />
            <el-option label="中通快递" value="ZTO" />
            <el-option label="圆通速递" value="YTO" />
            <el-option label="韵达快递" value="YD" />
            <el-option label="申通快递" value="STO" />
            <el-option label="京东物流" value="JD" />
            <el-option label="其他" value="OTHER" />
          </el-select>
        </el-form-item>
        <el-form-item label="物流单号" prop="tracking_number">
          <el-input v-model="shipForm.tracking_number" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="shipForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="shipDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitShipForm" :loading="submitting">
            确定发货
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Van, Close } from '@element-plus/icons-vue'
import api from '../../utils/api'

const router = useRouter()

// 状态变量
const loading = ref(false)
const submitting = ref(false)
const orders = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')
const statusFilter = ref('')
const selectedOrders = ref([])
const shipDialogVisible = ref(false)
const shipFormRef = ref(null)

// 发货表单
const shipForm = reactive({
  order_id: null,
  shipping_company: '',
  tracking_number: '',
  remark: ''
})

// 发货表单验证规则
const shipRules = {
  shipping_company: [
    { required: true, message: '请选择物流公司', trigger: 'change' }
  ],
  tracking_number: [
    { required: true, message: '请输入物流单号', trigger: 'blur' }
  ]
}

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

// 获取订单列表
const fetchOrders = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      per_page: pageSize.value,
      query: searchQuery.value,
      status: statusFilter.value
    }
    const response = await api.orders.getList(params)
    orders.value = response.items || []
    total.value = response.total || 0
  } catch (error) {
    console.error('获取订单列表失败:', error)
    ElMessage.error('获取订单列表失败')
  } finally {
    loading.value = false
  }
}

// 处理页码变化
const handleCurrentChange = (page) => {
  currentPage.value = page
  fetchOrders()
}

// 处理每页数量变化
const handleSizeChange = (size) => {
  pageSize.value = size
  fetchOrders()
}

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedOrders.value = selection
}

// 查看订单详情
const handleViewDetail = (row) => {
  router.push(`/admin/orders/${row.id}`)
}

// 发货
const handleShip = (row) => {
  shipForm.order_id = row.id
  shipForm.shipping_company = ''
  shipForm.tracking_number = ''
  shipForm.remark = ''
  shipDialogVisible.value = true
}

// 提交发货表单
const submitShipForm = async () => {
  if (!shipFormRef.value) return
  
  await shipFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        await api.orders.updateStatus(shipForm.order_id, 'shipped')
        ElMessage.success('订单已发货')
        shipDialogVisible.value = false
        fetchOrders()
      } catch (error) {
        console.error('发货失败:', error)
        ElMessage.error('发货失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

// 取消订单
const handleCancel = (row) => {
  ElMessageBox.confirm(
    '确定要取消该订单吗?',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await api.orders.updateStatus(row.id, 'cancelled')
      ElMessage.success('订单已取消')
      fetchOrders()
    } catch (error) {
      console.error('取消订单失败:', error)
      ElMessage.error('取消订单失败')
    }
  }).catch(() => {
    ElMessage.info('已取消操作')
  })
}

// 批量发货
const handleBatchShip = () => {
  if (selectedOrders.value.length === 0) {
    ElMessage.warning('请选择要发货的订单')
    return
  }
  
  // 检查是否所有选中的订单都是待发货状态
  const invalidOrders = selectedOrders.value.filter(order => order.status !== 'paid')
  if (invalidOrders.length > 0) {
    ElMessage.warning('只能对待发货状态的订单进行发货操作')
    return
  }
  
  ElMessageBox.confirm(
    `确定要批量发货选中的 ${selectedOrders.value.length} 个订单吗?`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    }
  ).then(async () => {
    try {
      const orderIds = selectedOrders.value.map(order => order.id)
      // 这里需要后端提供批量发货接口
      // 暂时使用循环单个发货
      for (const id of orderIds) {
        await api.orders.updateStatus(id, 'shipped')
      }
      ElMessage.success('批量发货成功')
      fetchOrders()
    } catch (error) {
      console.error('批量发货失败:', error)
      ElMessage.error('批量发货失败')
    }
  }).catch(() => {
    ElMessage.info('已取消操作')
  })
}

// 批量取消
const handleBatchCancel = () => {
  if (selectedOrders.value.length === 0) {
    ElMessage.warning('请选择要取消的订单')
    return
  }
  
  // 检查是否所有选中的订单都是可取消状态
  const invalidOrders = selectedOrders.value.filter(order => !['pending', 'paid'].includes(order.status))
  if (invalidOrders.length > 0) {
    ElMessage.warning('只能对待付款或待发货状态的订单进行取消操作')
    return
  }
  
  ElMessageBox.confirm(
    `确定要批量取消选中的 ${selectedOrders.value.length} 个订单吗?`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      const orderIds = selectedOrders.value.map(order => order.id)
      // 这里需要后端提供批量取消接口
      // 暂时使用循环单个取消
      for (const id of orderIds) {
        await api.orders.updateStatus(id, 'cancelled')
      }
      ElMessage.success('批量取消成功')
      fetchOrders()
    } catch (error) {
      console.error('批量取消失败:', error)
      ElMessage.error('批量取消失败')
    }
  }).catch(() => {
    ElMessage.info('已取消操作')
  })
}

onMounted(() => {
  fetchOrders()
})
</script>

<style lang="scss" scoped>
.order-management {
  padding: 20px;
}

.page-title {
  margin-bottom: 20px;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.action-bar {
  margin-bottom: 20px;
  
  .action-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }
}

.order-table-card {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>