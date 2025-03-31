<template>
  <div class="product-card" @click="navigateToDetail">
    <div class="product-image">
      <el-image 
        :src="product.image_url || defaultImage" 
        fit="cover"
        :preview-src-list="[product.image_url]"
        :initial-index="0"
        alt="商品图片"
        loading="lazy"
      >
        <template #error>
          <div class="image-error">
            <el-icon><Picture /></el-icon>
          </div>
        </template>
      </el-image>
      <div v-if="product.discount" class="discount-tag">{{ product.discount }}折</div>
    </div>
    
    <div class="product-info">
      <h3 class="product-title" :title="product.name">{{ product.name }}</h3>
      <p class="product-description" :title="product.description">{{ product.description }}</p>
      
      <div class="product-meta">
        <div class="product-price">
          <span class="current-price">¥{{ formatPrice(product.price) }}</span>
          <span v-if="product.original_price" class="original-price">¥{{ formatPrice(product.original_price) }}</span>
        </div>
        <div class="product-stats">
          <span class="sales">销量 {{ product.sales || 0 }}</span>
        </div>
      </div>
      
      <div class="product-tags" v-if="product.tags && product.tags.length">
        <el-tag 
          v-for="tag in product.tags" 
          :key="tag.id" 
          size="small" 
          effect="plain"
          class="product-tag"
        >
          {{ tag.name }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { Picture } from '@element-plus/icons-vue'

// 组件属性
const props = defineProps({
  product: {
    type: Object,
    required: true
  }
})

const router = useRouter()
const defaultImage = 'https://via.placeholder.com/300x300?text=No+Image'

// 格式化价格
const formatPrice = (price) => {
  return parseFloat(price).toFixed(2)
}

// 跳转到商品详情页
const navigateToDetail = () => {
  router.push(`/products/${props.product.id}`)
}
</script>

<style lang="scss" scoped>
.product-card {
  background-color: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  margin-bottom: 20px;
  cursor: pointer;
  height: 100%;
  display: flex;
  flex-direction: column;
  
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
  }
  
  .product-image {
    position: relative;
    height: 200px;
    overflow: hidden;
    
    .el-image {
      width: 100%;
      height: 100%;
    }
    
    .image-error {
      display: flex;
      justify-content: center;
      align-items: center;
      width: 100%;
      height: 100%;
      background-color: #f5f7fa;
      color: #909399;
      
      .el-icon {
        font-size: 30px;
      }
    }
    
    .discount-tag {
      position: absolute;
      top: 10px;
      right: 10px;
      background-color: #f56c6c;
      color: #fff;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: bold;
    }
  }
  
  .product-info {
    padding: 15px;
    flex: 1;
    display: flex;
    flex-direction: column;
    
    .product-title {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 8px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .product-description {
      font-size: 14px;
      color: #606266;
      margin: 0 0 10px;
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      line-height: 1.5;
      height: 42px;
    }
    
    .product-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
      margin-top: auto;
      
      .product-price {
        .current-price {
          font-size: 18px;
          font-weight: bold;
          color: #f56c6c;
        }
        
        .original-price {
          font-size: 14px;
          color: #909399;
          text-decoration: line-through;
          margin-left: 5px;
        }
      }
      
      .product-stats {
        font-size: 12px;
        color: #909399;
      }
    }
    
    .product-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
      
      .product-tag {
        margin-right: 5px;
      }
    }
  }
}
</style>