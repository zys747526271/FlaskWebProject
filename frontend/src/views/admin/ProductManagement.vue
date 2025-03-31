<template>
  <div class="product-management">
    <h1 class="page-title">商品管理</h1>
    
    <!-- 搜索和操作栏 -->
    <div class="action-bar">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-input
            v-model="searchQuery"
            placeholder="搜索商品名称/描述"
            clearable
            @clear="fetchProducts"
            @keyup.enter="fetchProducts"
          >
            <template #append>
              <el-button @click="fetchProducts">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="statusFilter" placeholder="状态筛选" clearable @change="fetchProducts">
            <el-option label="全部" value="" />
            <el-option label="已上架" value="active" />
            <el-option label="已下架" value="inactive" />
            <el-option label="待审核" value="pending" />
          </el-select>
        </el-col>
        <el-col :span="14" class="action-buttons">
          <el-button type="primary" @click="handleAddProduct">
            <el-icon><Plus /></el-icon> 添加商品
          </el-button>
          <el-button type="success" :disabled="!selectedProducts.length" @click="handleBatchApprove">
            <el-icon><Check /></el-icon> 批量上架
          </el-button>
          <el-button type="warning" :disabled="!selectedProducts.length" @click="handleBatchReject">
            <el-icon><Close /></el-icon> 批量下架
          </el-button>
          <el-button type="danger" :disabled="!selectedProducts.length" @click="handleBatchDelete">
            <el-icon><Delete /></el-icon> 批量删除
          </el-button>
        </el-col>
      </el-row>
    </div>
    
    <!-- 商品列表 -->
    <el-card shadow="hover" class="product-table-card">
      <el-table
        :data="products"
        style="width: 100%"
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="商品图片" width="100">
          <template #default="scope">
            <el-image 
              style="width: 60px; height: 60px" 
              :src="scope.row.cover_image || 'https://via.placeholder.com/60'"
              fit="cover"
              :preview-src-list="[scope.row.cover_image]"
            >
              <template #error>
                <div class="image-error">
                  <el-icon><Picture /></el-icon>
                </div>
              </template>
            </el-image>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="商品名称" width="180" show-overflow-tooltip />
        <el-table-column prop="price" label="价格" width="100">
          <template #default="scope">
            ¥{{ formatPrice(scope.row.price) }}
          </template>
        </el-table-column>
        <el-table-column prop="stock" label="库存" width="80" />
        <el-table-column prop="category" label="分类" width="120" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="scope">
            <el-button type="primary" size="small" @click="handleEdit(scope.row)">
              编辑
            </el-button>
            <el-button 
              :type="scope.row.status === 'active' ? 'warning' : 'success'"
              size="small"
              @click="handleToggleStatus(scope.row)"
            >
              {{ scope.row.status === 'active' ? '下架' : '上架' }}
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(scope.row)">
              删除
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
    
    <!-- 商品编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑商品' : '添加商品'"
      width="650px"
    >
      <el-form
        :model="productForm"
        :rules="productRules"
        ref="productFormRef"
        label-width="100px"
      >
        <el-form-item label="商品名称" prop="name">
          <el-input v-model="productForm.name" />
        </el-form-item>
        <el-form-item label="商品描述" prop="description">
          <el-input v-model="productForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="价格" prop="price">
              <el-input-number v-model="productForm.price" :precision="2" :step="0.1" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="库存" prop="stock">
              <el-input-number v-model="productForm.stock" :min="0" :step="1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="分类" prop="category">
          <el-select v-model="productForm.category" placeholder="选择分类" style="width: 100%">
            <el-option label="电子产品" value="electronics" />
            <el-option label="图书" value="books" />
            <el-option label="服装" value="clothing" />
            <el-option label="家居" value="home" />
            <el-option label="运动" value="sports" />
            <el-option label="其他" value="others" />
          </el-select>
        </el-form-item>
        <el-form-item label="商品图片" prop="cover_image">
          <el-upload
            class="avatar-uploader"
            action="/api/upload"
            :show-file-list="false"
            :on-success="handleUploadSuccess"
            :before-upload="beforeUpload"
          >
            <img v-if="productForm.cover_image" :src="productForm.cover_image" class="avatar" />
            <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
          </el-upload>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="productForm.status" placeholder="选择状态" style="width: 100%">
            <el-option label="上架" value="active" />
            <el-option label="下架" value="inactive" />
            <el-option label="待审核" value="pending" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitting">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Check, Close, Delete, Picture } from '@element-plus/icons-vue'
import api from '../../utils/api'

// 状态变量
const loading = ref(false)
const submitting = ref(false)
const products = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')
const statusFilter = ref('')
const selectedProducts = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const productFormRef = ref(null)

// 商品表单
const productForm = reactive({
  id: null,
  name: '',
  description: '',
  price: 0,
  stock: 0,
  category: '',
  cover_image: '',
  status: 'pending'
})

// 表单验证规则
const productRules = {
  name: [
    { required: true, message: '请输入商品名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入商品描述', trigger: 'blur' }
  ],
  price: [
    { required: true, message: '请输入价格', trigger: 'blur' },
    { type: 'number', min: 0, message: '价格必须大于等于0', trigger: 'blur' }
  ],
  stock: [
    { required: true, message: '请输入库存', trigger: 'blur' },
    { type: 'number', min: 0, message: '库存必须大于等于0', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择分类', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
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
    'active': '已上架',
    'inactive': '已下架',
    'pending': '待审核'
  }
  return statusMap[status] || status
}

// 获取状态类型
const getStatusType = (status) => {
  const typeMap = {
    'active': 'success',
    'inactive': 'info',
    'pending': 'warning'
  }
  return typeMap[status] || ''
}

// 获取商品列表
const fetchProducts = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      per_page: pageSize.value,
      query: searchQuery.value,
      status: statusFilter.value
    }
    const response = await api.products.getList(params)
    products.value = response.items || []
    total.value = response.total || 0
  } catch (error) {
    console.error('获取商品列表失败:', error)
    ElMessage.error('获取商品列表失败')
  } finally {
    loading.value = false
  }
}

// 处理页码变化
const handleCurrentChange = (page) => {
  currentPage.value = page
  fetchProducts()
}

// 处理每页数量变化
const handleSizeChange = (size) => {
  pageSize.value = size
  fetchProducts()
}

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedProducts.value = selection
}

// 添加商品
const handleAddProduct = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

// 编辑商品
const handleEdit = async (row) => {
  isEdit.value = true
  resetForm()
  try {
    // 获取商品详情
    const detail = await api.products.getDetail(row.id)
    Object.assign(productForm, {
      id: detail.id,
      name: detail.name,
      description: detail.description,
      price: detail.price,
      stock: detail.stock,
      category: detail.category,
      cover_image: detail.cover_image,
      status: detail.status
    })
    dialogVisible.value = true
  } catch (error) {
    console.error('获取商品详情失败:', error)
    ElMessage.error('获取商品详情失败')
  }
}

// 切换商品状态
const handleToggleStatus = async (row) => {
  const newStatus = row.status === 'active' ? 'inactive' : 'active'
  try {
    await api.products.update(row.id, { status: newStatus })
    ElMessage.success(`商品已${newStatus === 'active' ? '上架' : '下架'}`)
    fetchProducts()
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败')
  }
}

// 删除商品
const handleDelete = (row) => {
  ElMessageBox.confirm(
    '此操作将永久删除该商品, 是否继续?',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await api.products.delete(row.id)
      ElMessage.success('删除成功')
      fetchProducts()
    } catch (error) {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }).catch(() => {
    ElMessage.info('已取消删除')
  })
}

// 批量上架
const handleBatchApprove = () => {
  if (selectedProducts.value.length === 0) {
    ElMessage.warning('请选择要上架的商品')
    return
  }
  
  ElMessageBox.confirm(
    `确定要上架选中的 ${selectedProducts.value.length} 个商品吗?`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    }
  ).then(async () => {
    try {
      const productIds = selectedProducts.value.map(product => product.id)
      await api.admin.batchUpdateProductStatus({
        ids: productIds,
        status: 'active'
      })
      ElMessage.success('批量上架成功')
      fetchProducts()
    } catch (error) {
      console.error('批量上架失败:', error)
      ElMessage.error('批量上架失败')
    }
  }).catch(() => {
    ElMessage.info('已取消操作')
  })
}

// 批量下架
const handleBatchReject = () => {
  if (selectedProducts.value.length === 0) {
    ElMessage.warning('请选择要下架的商品')
    return
  }
  
  ElMessageBox.confirm(
    `确定要下架选中的 ${selectedProducts.value.length} 个商品吗?`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    }
  ).then(async () => {
    try {
      const productIds = selectedProducts.value.map(product => product.id)
      await api.admin.batchUpdateProductStatus({
        ids: productIds,
        status: 'inactive'
      })
      ElMessage.success('批量下架成功')
      fetchProducts()
    } catch (error) {
      console.error('批量下架失败:', error)
      ElMessage.error('批量下架失败')
    }
  }).catch(() => {
    ElMessage.info('已取消操作')
  })
}

// 批量删除
const handleBatchDelete = () => {
  if (selectedProducts.value.length === 0) {
    ElMessage.warning('请选择要删除的商品')
    return
  }
  
  ElMessageBox.confirm(
    `此操作将永久删除选中的 ${selectedProducts.value.length} 个商品, 是否继续?`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      const productIds = selectedProducts.value.map(product => product.id)
      // 这里需要后端提供批量删除接口
      // 暂时使用循环单个删除
      for (const id of productIds) {
        await api.products.delete(id)
      }
      ElMessage.success('批量删除成功')
      fetchProducts()
    } catch (error) {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    }
  }).catch(() => {
    ElMessage.info('已取消删除')
  })
}

// 上传前验证
const beforeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('上传文件只能是图片格式!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('上传图片大小不能超过 2MB!')
    return false
  }
  return true
}

// 上传成功回调
const handleUploadSuccess = (response) => {
  productForm.cover_image = response.url
}

// 重置表单
const resetForm = () => {
  if (productFormRef.value) {
    productFormRef.value.resetFields()
  }
  Object.assign(productForm, {
    id: null,
    name: '',
    description: '',
    price: 0,
    stock: 0,
    category: '',
    cover_image: '',
    status: 'pending'
  })
}

// 提交表单
const submitForm = async () => {
  if (!productFormRef.value) return
  
  await productFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (isEdit.value) {
          // 编辑商品
          await api.products.update(productForm.id, {
            name: productForm.name,
            description: productForm.description,
            price: productForm.price,
            stock: productForm.stock,
            category: productForm.category,
            cover_image: productForm.cover_image,
            status: productForm.status
          })
          ElMessage.success('更新成功')
        } else {
          // 添加商品
          await api.products.create({
            name: productForm.name,
            description: productForm.description,
            price: productForm.price,
            stock: productForm.stock,
            category: productForm.category,
            cover_image: productForm.cover_image,
            status: productForm.status
          })
          ElMessage.success('添加成功')
        }
        dialogVisible.value = false
        fetchProducts()
      } catch (error) {
        console.error('操作失败:', error)
        ElMessage.error(error.response?.data?.message || '操作失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

onMounted(() => {
  fetchProducts()
})
</script>

<style lang="scss" scoped>
.product-management {
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

.product-table-card {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.avatar-uploader {
  .avatar {
    width: 178px;
    height: 178px;
    display: block;
    object-fit: cover;
  }
  
  .avatar-uploader-icon {
    font-size: 28px;
    color: #8c939d;
    width: 178px;
    height: 178px;
    text-align: center;
    border: 1px dashed #d9d9d9;
    border-radius: 6px;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
  }
}

.image-error {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  background-color: #f5f7fa;
  color: #909399;
  font-size: 20px;
}
</style>