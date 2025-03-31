<template>
  <div class="product-detail-page">
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>
    
    <div v-else-if="error" class="error-container">
      <el-empty description="加载商品信息失败">
        <template #description>
          <p>{{ errorMessage }}</p>
        </template>
        <el-button type="primary" @click="fetchProductDetail">重试</el-button>
      </el-empty>
    </div>
    
    <div v-else-if="product" class="product-container">
      <!-- 商品基本信息 -->
      <div class="product-main">
        <!-- 商品图片 -->
        <div class="product-gallery">
          <el-carousel v-if="product.images && product.images.length" indicator-position="outside" height="400px">
            <el-carousel-item v-for="(image, index) in product.images" :key="index">
              <el-image :src="image" fit="contain" :preview-src-list="product.images" />
            </el-carousel-item>
          </el-carousel>
          
          <el-image 
            v-else 
            :src="defaultImage" 
            fit="contain"
            style="width: 100%; height: 400px;"
          >
            <template #error>
              <div class="image-error">
                <el-icon><Picture /></el-icon>
                <p>暂无图片</p>
              </div>
            </template>
          </el-image>
        </div>
        
        <!-- 商品信息 -->
        <div class="product-info">
          <h1 class="product-title">{{ product.name }}</h1>
          
          <div class="product-meta">
            <div class="product-id">商品编号: {{ product.quick_id || product.id }}</div>
            <div class="product-views">浏览量: {{ product.views || 0 }}</div>
          </div>
          
          <div class="product-price-container">
            <div class="product-price">
              <span class="price-label">价格:</span>
              <span class="current-price">¥{{ formatPrice(product.price) }}</span>
              <span v-if="product.original_price" class="original-price">¥{{ formatPrice(product.original_price) }}</span>
            </div>
          </div>
          
          <div class="product-quantity">
            <span class="quantity-label">库存:</span>
            <span :class="['quantity-value', product.quantity <= 5 ? 'low-stock' : '']">{{ product.quantity }}</span>
            <span v-if="product.quantity <= 5" class="stock-warning">库存紧张</span>
          </div>
          
          <div class="product-actions">
            <el-input-number v-model="quantity" :min="1" :max="product.quantity" size="large" />
            
            <el-button 
              type="primary" 
              size="large" 
              :disabled="!product.is_available || product.quantity <= 0"
              @click="addToCart"
            >
              <el-icon><ShoppingCart /></el-icon>
              加入购物车
            </el-button>
            
            <el-button 
              type="danger" 
              size="large" 
              :disabled="!product.is_available || product.quantity <= 0"
              @click="buyNow"
            >
              立即购买
            </el-button>
          </div>
          
          <div class="seller-info" v-if="product.seller">
            <div class="seller-title">卖家信息</div>
            <div class="seller-detail">
              <el-avatar :size="40" :src="product.seller.avatar">
                {{ product.seller.username?.substring(0, 1).toUpperCase() || 'U' }}
              </el-avatar>
              <div class="seller-name">{{ product.seller.username }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 商品详情 -->
      <div class="product-detail">
        <el-tabs>
          <el-tab-pane label="商品详情">
            <div class="detail-content">
              <div class="detail-section">
                <h3>商品描述</h3>
                <p v-if="product.description">{{ product.description }}</p>
                <p v-else class="no-content">暂无描述</p>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="用户评价">
            <div class="comments-section">
              <p class="no-content">暂无评价</p>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      
      <!-- 相关推荐 -->
      <div class="related-products" v-if="relatedProducts.length > 0">
        <div class="section-title">
          <h2>相关推荐</h2>
        </div>
        <el-row :gutter="20">
          <el-col :xs="12" :sm="8" :md="6" :lg="4" v-for="item in relatedProducts" :key="item.id">
            <product-card :product="item" />
          </el-col>
        </el-row>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Picture, ShoppingCart } from '@element-plus/icons-vue'
import api from '../../utils/api'
import ProductCard from '../../components/product/ProductCard.vue'
import { useUserStore } from '../../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 状态
const product = ref(null)
const loading = ref(true)
const error = ref(false)
const errorMessage = ref('')
const quantity = ref(1)
const relatedProducts = ref([])

// 默认图片
const defaultImage = 'https://via.placeholder.com/600x400?text=No+Image'

// 格式化价格
const formatPrice = (price) => {
  return parseFloat(price).toFixed(2)
}

// 获取商品详情
const fetchProductDetail = async () => {
  const productId = route.params.id
  if (!productId) {
    error.value = true
    errorMessage.value = '商品ID无效'
    loading.value = false
    return
  }
  
  loading.value = true
  error.value = false
  
  try {
    const response = await api.products.getDetail(productId)
    product.value = response.data
    fetchRelatedProducts()
  } catch (err) {
    console.error('获取商品详情失败:', err)
    error.value = true
    errorMessage.value = err.response?.data?.message || '获取商品详情失败'
  } finally {
    loading.value = false
  }
}

// 获取相关推荐商品
const fetchRelatedProducts = async () => {
  if (!product.value || !product.value.tag_id) return
  
  try {
    const response = await api.products.getList({
      category_id: product.value.tag_id,
      limit: 6,
      exclude_id: product.value.id
    })
    relatedProducts.value = response.items || []
  } catch (err) {
    console.error('获取相关商品失败:', err)
  }
}

// 添加到购物车
const addToCart = async () => {
  if (!userStore.isAuthenticated) {
    ElMessage.warning('请先登录')
    router.push('/auth/login')
    return
  }
  
  try {
    await api.cart.addItem({
      product_id: product.value.id,
      quantity: quantity.value
    })
    ElMessage.success('已添加到购物车')
  } catch (err) {
    console.error('添加到购物车失败:', err)
    ElMessage.error(err.response?.data?.message || '添加到购物车失败')
  }
}

// 立即购买
const buyNow = async () => {
  if (!userStore.isAuthenticated) {
    ElMessage.warning('请先登录')
    router.push('/auth/login')
    return
  }
  
  try {
    await api.cart.addItem({
      product_id: product.value.id,
      quantity: quantity.value
    })
    router.push('/cart')
  } catch (err) {
    console.error('添加到购物车失败:', err)
    ElMessage.error(err.response?.data?.message || '操作失败')
  }
}

onMounted(() => {
  fetchProductDetail()
})
</script>

<style lang="scss" scoped>
.product-detail-page {
  padding: 20px 0;
}

.loading-container,
.error-container {
  min-height: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.product-container {
  .product-main {
    display: flex;
    margin-bottom: 30px;
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
    overflow: hidden;
    
    @media (max-width: 768px) {
      flex-direction: column;
    }
  }
  
  .product-gallery {
    width: 50%;
    padding: 20px;
    
    @media (max-width: 768px) {
      width: 100%;
    }
    
    .image-error {
      height: 400px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      color: #909399;
      background-color: #f5f7fa;
      
      .el-icon {
        font-size: 48px;
        margin-bottom: 10px;
      }
    }
  }
  
  .product-info {
    width: 50%;
    padding: 30px;
    display: flex;
    flex-direction: column;
    
    @media (max-width: 768px) {
      width: 100%;
    }
    
    .product-title {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 15px;
    }
    
    .product-meta {
      display: flex;
      justify-content: space-between;
      color: #909399;
      font-size: 14px;
      margin-bottom: 20px;
    }
    
    .product-price-container {
      background-color: #f8f9fa;
      padding: 15px;
      border-radius: 4px;
      margin-bottom: 20px;
      
      .product-price {
        display: flex;
        align-items: baseline;
        
        .price-label {
          font-size: 14px;
          color: #606266;
          margin-right: 10px;
        }
        
        .current-price {
          font-size: 28px;
          font-weight: 600;
          color: #f56c6c;
        }
        
        .original-price {
          font-size: 16px;
          color: #909399;
          text-decoration: line-through;
          margin-left: 10px;
        }
      }
    }
    
    .product-quantity {
      margin-bottom: 30px;
      
      .quantity-label {
        font-size: 14px;
        color: #606266;
        margin-right: 10px;
      }
      
      .quantity-value {
        font-size: 16px;
        font-weight: 500;
        color: #303133;
        
        &.low-stock {
          color: #e6a23c;
        }
      }
      
      .stock-warning {
        font-size: 12px;
        color: #e6a23c;
        margin-left: 10px;
      }
    }
    
    .product-actions {
      display: flex;
      gap: 15px;
      margin-bottom: 30px;
      
      @media (max-width: 576px) {
        flex-direction: column;
      }
    }
    
    .seller-info {
      margin-top: auto;
      border-top: 1px solid #ebeef5;
      padding-top: 20px;
      
      .seller-title {
        font-size: 16px;
        font-weight: 500;
        color: #303133;
        margin-bottom: 10px;
      }
      
      .seller-detail {
        display: flex;
        align-items: center;
        
        .seller-name {
          margin-left: 10px;
          font-size: 14px;
          color: #606266;
        }
      }
    }
  }
  
  .product-detail {
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
    padding: 20px;
    margin-bottom: 30px;
    
    .detail-section {
      margin-bottom: 20px;
      
      h3 {
        font-size: 18px;
        font-weight: 500;
        color: #303133;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 1px solid #ebeef5;
      }
      
      p {
        font-size: 14px;
        color: #606266;
        line-height: 1.6;
        white-space: pre-wrap;
      }
    }
    
    .no-content {
      color: #909399;
      font-style: italic;
      text-align: center;
      padding: 30px 0;
    }
  }
  
  .related-products {
    margin-top: 30px;
    
    .section-title {
      margin-bottom: 20px;
      
      h2 {
        font-size: 20px;
        font-weight: 600;
        color: #303133;
        position: relative;
        padding-left: 15px;
        
        &::before {
          content: '';
          position: absolute;
          left: 0;
          top: 50%;
          transform: translateY(-50%);
          width: 4px;
          height: 18px;
          background-color: #409EFF;
          border-radius: 2px;
        }
      }
    }
  }
}
</style>