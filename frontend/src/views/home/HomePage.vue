<template>
  <div class="home-page">
    <!-- 轮播图 -->
    <div class="banner-section">
      <el-carousel height="400px" indicator-position="outside">
        <el-carousel-item v-for="(banner, index) in banners" :key="index">
          <div class="banner-item" :style="{ backgroundImage: `url(${banner.image})` }">
            <div class="banner-content">
              <h2>{{ banner.title }}</h2>
              <p>{{ banner.description }}</p>
              <el-button type="primary" @click="navigateTo(banner.link)">查看详情</el-button>
            </div>
          </div>
        </el-carousel-item>
      </el-carousel>
    </div>
    
    <!-- 分类导航 -->
    <div class="category-section">
      <div class="section-title">
        <h2>商品分类</h2>
      </div>
      <div class="category-list">
        <div v-for="category in categories" :key="category.id" class="category-item" @click="filterByCategory(category.id)">
          <el-icon>
            <component :is="category.icon"></component>
          </el-icon>
          <span>{{ category.name }}</span>
        </div>
      </div>
    </div>
    
    <!-- 推荐商品 -->
    <div class="recommended-section">
      <div class="section-title">
        <h2>推荐商品</h2>
        <router-link to="/" class="view-more">查看更多</router-link>
      </div>
      <el-row :gutter="20" v-loading="loading.recommended">
        <el-col :xs="12" :sm="8" :md="6" :lg="4" v-for="product in recommendedProducts" :key="product.id">
          <product-card :product="product" />
        </el-col>
      </el-row>
    </div>
    
    <!-- 热门商品 -->
    <div class="hot-section">
      <div class="section-title">
        <h2>热门商品</h2>
        <router-link to="/" class="view-more">查看更多</router-link>
      </div>
      <el-row :gutter="20" v-loading="loading.hot">
        <el-col :xs="12" :sm="8" :md="6" :lg="4" v-for="product in hotProducts" :key="product.id">
          <product-card :product="product" />
        </el-col>
      </el-row>
    </div>
    
    <!-- 最新上架 -->
    <div class="latest-section">
      <div class="section-title">
        <h2>最新上架</h2>
        <router-link to="/" class="view-more">查看更多</router-link>
      </div>
      <el-row :gutter="20" v-loading="loading.latest">
        <el-col :xs="12" :sm="8" :md="6" :lg="4" v-for="product in latestProducts" :key="product.id">
          <product-card :product="product" />
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Goods, ShoppingBag, Bicycle, Basketball, 
  Suitcase, Notebook, Camera, Headset
} from '@element-plus/icons-vue'
import api from '../../utils/api'
import ProductCard from '../../components/product/ProductCard.vue'

const route = useRoute()
const router = useRouter()

// 状态
const loading = ref({
  recommended: false,
  hot: false,
  latest: false
})

// 轮播图数据
const banners = ref([
  {
    title: '二手交易平台',
    description: '安全、便捷的二手商品交易服务',
    image: 'https://via.placeholder.com/1200x400/409EFF/FFFFFF?text=二手交易平台',
    link: '/'
  },
  {
    title: '特价商品',
    description: '限时特价，低至5折',
    image: 'https://via.placeholder.com/1200x400/67C23A/FFFFFF?text=特价商品',
    link: '/'
  },
  {
    title: '新品上架',
    description: '每日更新，好物不断',
    image: 'https://via.placeholder.com/1200x400/E6A23C/FFFFFF?text=新品上架',
    link: '/'
  }
])

// 分类数据
const categories = ref([
  { id: 1, name: '电子产品', icon: 'Goods' },
  { id: 2, name: '服装鞋包', icon: 'ShoppingBag' },
  { id: 3, name: '运动户外', icon: 'Basketball' },
  { id: 4, name: '图书音像', icon: 'Notebook' },
  { id: 5, name: '生活用品', icon: 'Suitcase' },
  { id: 6, name: '交通工具', icon: 'Bicycle' },
  { id: 7, name: '数码设备', icon: 'Camera' },
  { id: 8, name: '其他', icon: 'Headset' }
])

// 商品数据
const recommendedProducts = ref([])
const hotProducts = ref([])
const latestProducts = ref([])

// 获取推荐商品
const fetchRecommendedProducts = async () => {
  loading.value.recommended = true
  try {
    const data = await api.products.getRecommended()
    recommendedProducts.value = data.products || []
  } catch (error) {
    console.error('获取推荐商品失败:', error)
    ElMessage.error('获取推荐商品失败')
  } finally {
    loading.value.recommended = false
  }
}

// 获取热门商品
const fetchHotProducts = async () => {
  loading.value.hot = true
  try {
    const data = await api.products.getHot()
    hotProducts.value = data.products || []
  } catch (error) {
    console.error('获取热门商品失败:', error)
    ElMessage.error('获取热门商品失败')
  } finally {
    loading.value.hot = false
  }
}

// 获取最新商品
const fetchLatestProducts = async () => {
  loading.value.latest = true
  try {
    const data = await api.products.getList({ sort: 'created_at', order: 'desc', limit: 6 })
    latestProducts.value = data.products || []
  } catch (error) {
    console.error('获取最新商品失败:', error)
    ElMessage.error('获取最新商品失败')
  } finally {
    loading.value.latest = false
  }
}

// 按分类筛选
const filterByCategory = (categoryId) => {
  router.push({
    path: '/',
    query: { category: categoryId }
  })
}

// 导航到指定链接
const navigateTo = (link) => {
  router.push(link)
}

// 生命周期钩子
onMounted(() => {
  fetchRecommendedProducts()
  fetchHotProducts()
  fetchLatestProducts()
})
</script>

<style lang="scss" scoped>
.home-page {
  .banner-section {
    margin-bottom: 40px;
    
    .banner-item {
      height: 100%;
      background-size: cover;
      background-position: center;
      display: flex;
      align-items: center;
      padding: 0 50px;
      
      .banner-content {
        max-width: 500px;
        color: #fff;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
        
        h2 {
          font-size: 32px;
          margin-bottom: 15px;
        }
        
        p {
          font-size: 18px;
          margin-bottom: 20px;
        }
      }
    }
  }
  
  .section-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h2 {
      font-size: 24px;
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
        height: 20px;
        background-color: #409EFF;
        border-radius: 2px;
      }
    }
    
    .view-more {
      color: #909399;
      text-decoration: none;
      
      &:hover {
        color: #409EFF;
      }
    }
  }
  
  .category-section {
    margin-bottom: 40px;
    
    .category-list {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      
      .category-item {
        width: calc(25% - 15px);
        background-color: #fff;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
        
        @media (max-width: 768px) {
          width: calc(50% - 10px);
        }
        
        &:hover {
          transform: translateY(-5px);
          box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }
        
        .el-icon {
          font-size: 30px;
          color: #409EFF;
          margin-bottom: 10px;
        }
        
        span {
          display: block;
          font-size: 16px;
          color: #303133;
        }
      }
    }
  }
  
  .recommended-section,
  .hot-section,
  .latest-section {
    margin-bottom: 40px;
  }
}
</style>