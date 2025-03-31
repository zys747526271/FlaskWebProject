<template>
  <div class="main-layout">
    <!-- 顶部导航栏 -->
    <header class="header">
      <div class="container">
        <div class="logo">
          <router-link to="/">
            <h1>二手交易平台</h1>
          </router-link>
        </div>
        
        <div class="search-bar">
          <el-input
            v-model="searchQuery"
            placeholder="搜索商品"
            class="search-input"
            @keyup.enter="handleSearch"
          >
            <template #append>
              <el-button @click="handleSearch">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
        </div>
        
        <div class="nav-actions">
          <template v-if="userStore.isAuthenticated">
            <router-link to="/cart" class="nav-item">
              <el-badge :value="cartCount" :hidden="cartCount === 0" class="cart-badge">
                <el-icon><ShoppingCart /></el-icon>
              </el-badge>
              购物车
            </router-link>
            <el-dropdown trigger="click">
              <span class="user-dropdown">
                <el-avatar :size="32" :src="userStore.userInfo?.avatar || ''">
                  {{ userStore.userInfo?.username?.substring(0, 1).toUpperCase() || 'U' }}
                </el-avatar>
                <span>{{ userStore.userInfo?.username || '用户' }}</span>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item>
                    <router-link to="/profile">个人中心</router-link>
                  </el-dropdown-item>
                  <el-dropdown-item>
                    <router-link to="/orders">我的订单</router-link>
                  </el-dropdown-item>
                  <el-dropdown-item v-if="userStore.userInfo?.isAdmin">
                    <router-link to="/admin">管理控制台</router-link>
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="handleLogout">
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <router-link to="/auth/login" class="nav-item">登录</router-link>
            <router-link to="/auth/register" class="nav-item register-btn">注册</router-link>
          </template>
        </div>
      </div>
    </header>

    <!-- 主要内容区域 -->
    <main class="main-content">
      <div class="container">
        <router-view />
      </div>
    </main>

    <!-- 页脚 -->
    <footer class="footer">
      <div class="container">
        <div class="footer-content">
          <div class="footer-section">
            <h3>关于我们</h3>
            <p>二手交易平台致力于为用户提供安全、便捷的二手商品交易服务。</p>
          </div>
          <div class="footer-section">
            <h3>联系方式</h3>
            <p>邮箱: support@example.com</p>
            <p>电话: 123-456-7890</p>
          </div>
          <div class="footer-section">
            <h3>帮助中心</h3>
            <ul>
              <li><a href="#">常见问题</a></li>
              <li><a href="#">用户指南</a></li>
              <li><a href="#">隐私政策</a></li>
            </ul>
          </div>
        </div>
        <div class="copyright">
          <p>&copy; {{ new Date().getFullYear() }} 二手交易平台 版权所有</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { Search, ShoppingCart } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '../utils/api'

const router = useRouter()
const userStore = useUserStore()
const searchQuery = ref('')
const cartCount = ref(0)

// 获取购物车数量
const fetchCartCount = async () => {
  if (userStore.isAuthenticated) {
    try {
      const cartData = await api.cart.getItems()
      cartCount.value = cartData.items?.length || 0
    } catch (error) {
      console.error('获取购物车数据失败:', error)
    }
  }
}

// 搜索处理
const handleSearch = () => {
  if (searchQuery.value.trim()) {
    router.push({
      path: '/',
      query: { q: searchQuery.value.trim() }
    })
  }
}

// 退出登录
const handleLogout = () => {
  userStore.logout()
  ElMessage.success('已成功退出登录')
  router.push('/')
}

onMounted(() => {
  fetchCartCount()
})
</script>

<style lang="scss" scoped>
.main-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 15px;
}

.header {
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
  
  .container {
    display: flex;
    align-items: center;
    height: 70px;
  }
  
  .logo {
    margin-right: 30px;
    
    a {
      text-decoration: none;
      color: #409EFF;
      
      h1 {
        font-size: 24px;
        font-weight: 600;
      }
    }
  }
  
  .search-bar {
    flex: 1;
    max-width: 500px;
    margin: 0 20px;
    
    .search-input {
      width: 100%;
    }
  }
  
  .nav-actions {
    display: flex;
    align-items: center;
    
    .nav-item {
      margin-left: 20px;
      text-decoration: none;
      color: #606266;
      display: flex;
      align-items: center;
      
      &:hover {
        color: #409EFF;
      }
      
      .el-icon {
        margin-right: 5px;
      }
    }
    
    .register-btn {
      color: #409EFF;
      font-weight: 500;
    }
    
    .user-dropdown {
      display: flex;
      align-items: center;
      cursor: pointer;
      margin-left: 20px;
      
      .el-avatar {
        margin-right: 8px;
      }
    }
    
    .cart-badge {
      margin-right: 5px;
    }
  }
}

.main-content {
  flex: 1;
  padding: 30px 0;
}

.footer {
  background-color: #f8f9fa;
  padding: 40px 0 20px;
  margin-top: auto;
  
  .footer-content {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    margin-bottom: 30px;
  }
  
  .footer-section {
    flex: 1;
    min-width: 200px;
    margin-bottom: 20px;
    
    h3 {
      font-size: 18px;
      margin-bottom: 15px;
      color: #303133;
    }
    
    p {
      margin-bottom: 10px;
      color: #606266;
    }
    
    ul {
      list-style: none;
      
      li {
        margin-bottom: 8px;
        
        a {
          color: #606266;
          text-decoration: none;
          
          &:hover {
            color: #409EFF;
          }
        }
      }
    }
  }
  
  .copyright {
    text-align: center;
    padding-top: 20px;
    border-top: 1px solid #e4e7ed;
    color: #909399;
  }
}
</style>