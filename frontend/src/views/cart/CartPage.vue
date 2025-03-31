<template>
  <div class="cart-page">
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>
    
    <div v-else-if="error" class="error-container">
      <el-empty description="加载购物车失败">
        <template #description>
          <p>{{ errorMessage }}</p>
        </template>
        <el-button type="primary" @click="fetchCartItems">重试</el-button>
      </el-empty>
    </div>
    
    <div v-else-if="cartItems.length === 0" class="empty-cart">
      <el-empty description="购物车为空">
        <template #description>
          <p>您的购物车还没有商品</p>
        </template>
        <el-button type="primary" @click="$router.push('/')">去购物</el-button>
      </el-empty>
    </div>
    
    <div v-else class="cart-container">
      <h1 class="page-title">我的购物车</h1>
      
      <div class="cart-header">
        <el-checkbox v-model="allSelected" @change="handleSelectAll">全选</el-checkbox>
        <div class="header-item">商品信息</div>
        <div class="header-item">单价</div>
        <div class="header-item">数量</div>
        <div class="header-item">金额</div>
        <div class="header-item">操作</div>
      </div>
      
      <div class="cart-items">
        <div v-for="item in cartItems" :key="item.id" class="cart-item">
          <el-checkbox v-model="item.selected" @change="updateSelectedState" />
          
          <div class="item-info">
            <el-image :src="item.product.image || defaultImage" :alt="item.product.name" class="item-image" />
            <div class="item-details">
              <router-link :to="`/product/${item.product.id}`" class="item-name">{{ item.product.name }}</router-link>
              <div class="item-meta">{{ item.product.description }}</div>
            </div>
          </div>
          
          <div class="item-price">¥{{ formatPrice(item.product.price) }}</div>
          
          <div class="item-quantity">
            <el-input-number 
              v-model="item.quantity" 
              :min="1" 
              :max="99"
              @change="(val) => updateItemQuantity(item.id, val)" 
            />
          </div>
          
          <div class="item-subtotal">¥{{ formatPrice(item.product.price * item.quantity) }}</div>
          
          <div class="item-actions">
            <el-button type="danger" size="small" @click="removeCartItem(item.id)">删除</el-button>
          </div>
        </div>
      </div>
      
      <div class="cart-footer">
        <div class="footer-left">
          <el-checkbox v-model="allSelected" @change="handleSelectAll">全选</el-checkbox>
          <el-button size="small" @click="batchRemoveItems">批量删除</el-button>
        </div>
        
        <div class="footer-right">
          <div class="total-info">
            <span>已选择 {{ selectedCount }} 件商品</span>
            <span class="total-price">合计: <strong>¥{{ formatPrice(totalPrice) }}</strong></span>
          </div>
          <el-button type="primary" size="large" @click="checkout" :disabled="selectedCount === 0">结算</el-button>
        </div>
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
const cartItems = ref([])
const loading = ref(true)
const error = ref(false)
const errorMessage = ref('')

// 默认图片
const defaultImage = 'https://via.placeholder.com/100x100?text=No+Image'

// 格式化价格
const formatPrice = (price) => {
  return parseFloat(price).toFixed(2)
}

// 全选状态
const allSelected = computed({
  get: () => {
    return cartItems.value.length > 0 && cartItems.value.every(item => item.selected)
  },
  set: (value) => {
    cartItems.value.forEach(item => item.selected = value)
  }
})

// 已选商品数量
const selectedCount = computed(() => {
  return cartItems.value.filter(item => item.selected).length
})

// 总价
const totalPrice = computed(() => {
  return cartItems.value
    .filter(item => item.selected)
    .reduce((total, item) => total + (item.product.price * item.quantity), 0)
})

// 获取购物车商品
const fetchCartItems = async () => {
  loading.value = true
  error.value = false
  
  try {
    const response = await api.cart.getItems()
    cartItems.value = (response.items || []).map(item => ({
      ...item,
      selected: true
    }))
  } catch (err) {
    console.error('获取购物车失败:', err)
    error.value = true
    errorMessage.value = err.response?.data?.message || '获取购物车失败'
  } finally {
    loading.value = false
  }
}

// 更新商品数量
const updateItemQuantity = async (itemId, quantity) => {
  try {
    await api.cart.updateItem(itemId, { quantity })
    ElMessage.success('数量已更新')
  } catch (err) {
    console.error('更新数量失败:', err)
    ElMessage.error(err.response?.data?.message || '更新数量失败')
    // 恢复原来的数量
    fetchCartItems()
  }
}

// 删除购物车商品
const removeCartItem = async (itemId) => {
  try {
    await ElMessageBox.confirm('确定要从购物车中删除该商品吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.cart.removeItem(itemId)
    ElMessage.success('商品已从购物车中删除')
    // 重新获取购物车列表
    fetchCartItems()
  } catch (err) {
    if (err !== 'cancel') {
      console.error('删除商品失败:', err)
      ElMessage.error(err.response?.data?.message || '删除商品失败')
    }
  }
}

// 批量删除选中商品
const batchRemoveItems = async () => {
  const selectedItems = cartItems.value.filter(item => item.selected)
  
  if (selectedItems.length === 0) {
    ElMessage.warning('请先选择要删除的商品')
    return
  }
  
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedItems.length} 件商品吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const ids = selectedItems.map(item => item.id)
    await api.cart.batchRemove(ids)
    ElMessage.success('选中商品已删除')
    // 重新获取购物车列表
    fetchCartItems()
  } catch (err) {
    if (err !== 'cancel') {
      console.error('批量删除失败:', err)
      ElMessage.error(err.response?.data?.message || '批量删除失败')
    }
  }
}

// 全选/取消全选
const handleSelectAll = (val) => {
  cartItems.value.forEach(item => item.selected = val)
}

// 更新选中状态
const updateSelectedState = () => {
  // 这个函数只是为了触发计算属性的更新
}

// 结算
const checkout = () => {
  const selectedItems = cartItems.value.filter(item => item.selected)
  
  if (selectedItems.length === 0) {
    ElMessage.warning('请先选择要结算的商品')
    return
  }
  
  // 跳转到结算页面
  router.push('/checkout')
}

onMounted(() => {
  fetchCartItems()
})
</script>

<style scoped>
.cart-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  margin-bottom: 20px;
  color: #333;
}

.loading-container,
.error-container,
.empty-cart {
  padding: 40px 0;
  text-align: center;
}

.cart-header {
  display: grid;
  grid-template-columns: 80px 3fr 1fr 1fr 1fr 1fr;
  padding: 15px 0;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 10px;
  text-align: center;
  font-weight: bold;
}

.cart-item {
  display: grid;
  grid-template-columns: 80px 3fr 1fr 1fr 1fr 1fr;
  padding: 20px 0;
  border-bottom: 1px solid #ebeef5;
  align-items: center;
  text-align: center;
}

.item-info {
  display: flex;
  align-items: center;
  text-align: left;
}

.item-image {
  width: 80px;
  height: 80px;
  object-fit: cover;
  margin-right: 15px;
}

.item-name {
  color: #333;
  text-decoration: none;
  font-weight: 500;
  margin-bottom: 5px;
  display: block;
}

.item-name:hover {
  color: #409eff;
}

.item-meta {
  color: #909399;
  font-size: 12px;
}

.item-price,
.item-subtotal {
  color: #f56c6c;
  font-weight: 500;
}

.cart-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
  margin-top: 20px;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.total-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 5px;
}

.total-price {
  font-size: 18px;
}

.total-price strong {
  color: #f56c6c;
  font-size: 24px;
}
</style>