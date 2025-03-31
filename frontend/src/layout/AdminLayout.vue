<template>
  <div class="admin-layout">
    <!-- 侧边栏 -->
    <div class="sidebar" :class="{ 'collapsed': isCollapsed }">
      <div class="logo">
        <h1 v-if="!isCollapsed">管理控制台</h1>
        <el-icon v-else><Monitor /></el-icon>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        :collapse="isCollapsed"
        :collapse-transition="false"
        router
      >
        <el-menu-item index="/admin">
          <el-icon><DataBoard /></el-icon>
          <template #title>控制面板</template>
        </el-menu-item>
        
        <el-menu-item index="/admin/users">
          <el-icon><User /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
        
        <el-menu-item index="/admin/products">
          <el-icon><Goods /></el-icon>
          <template #title>商品管理</template>
        </el-menu-item>
        
        <el-menu-item index="/admin/orders">
          <el-icon><List /></el-icon>
          <template #title>订单管理</template>
        </el-menu-item>
      </el-menu>
      
      <div class="sidebar-footer">
        <el-tooltip
          :content="isCollapsed ? '展开菜单' : '收起菜单'"
          placement="right"
        >
          <el-button
            type="text"
            class="collapse-btn"
            @click="toggleCollapse"
          >
            <el-icon>
              <component :is="isCollapsed ? 'Expand' : 'Fold'"></component>
            </el-icon>
          </el-button>
        </el-tooltip>
      </div>
    </div>
    
    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 顶部导航栏 -->
      <header class="header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/admin' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentRoute.meta.title">
              {{ currentRoute.meta.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <el-dropdown trigger="click">
            <span class="user-dropdown">
              <el-avatar :size="32" :src="userStore.userInfo?.avatar || ''">
                {{ userStore.userInfo?.username?.substring(0, 1).toUpperCase() || 'A' }}
              </el-avatar>
              <span>{{ userStore.userInfo?.username || '管理员' }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>
                  <router-link to="/">返回前台</router-link>
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>
      
      <!-- 内容区域 -->
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'
import {
  Monitor, DataBoard, User, Goods, List,
  Fold, Expand, ArrowDown
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 侧边栏折叠状态
const isCollapsed = ref(false)

// 当前路由
const currentRoute = computed(() => route)

// 当前激活的菜单项
const activeMenu = computed(() => {
  return route.path
})

// 切换侧边栏折叠状态
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

// 退出登录
const handleLogout = () => {
  userStore.logout()
  ElMessage.success('已成功退出登录')
  router.push('/auth/login')
}

// 检查管理员权限
onMounted(() => {
  if (!userStore.isAuthenticated || !userStore.userInfo?.isAdmin) {
    ElMessage.error('您没有管理员权限')
    router.push('/auth/login')
  }
})

// 监听路由变化，检查权限
watch(
  () => route.path,
  (newPath) => {
    if (newPath.startsWith('/admin') && (!userStore.isAuthenticated || !userStore.userInfo?.isAdmin)) {
      ElMessage.error('您没有管理员权限')
      router.push('/auth/login')
    }
  }
)
</script>

<style lang="scss" scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 240px;
  background-color: #304156;
  color: #fff;
  transition: width 0.3s;
  display: flex;
  flex-direction: column;
  
  &.collapsed {
    width: 64px;
  }
  
  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 20px;
    background-color: #263445;
    
    h1 {
      font-size: 18px;
      font-weight: 600;
      color: #fff;
      margin: 0;
      white-space: nowrap;
    }
    
    .el-icon {
      font-size: 24px;
    }
  }
  
  .sidebar-menu {
    flex: 1;
    border-right: none;
    background-color: transparent;
    
    :deep(.el-menu-item) {
      color: #bfcbd9;
      
      &.is-active {
        color: #409EFF;
        background-color: #263445;
      }
      
      &:hover {
        background-color: #263445;
      }
    }
  }
  
  .sidebar-footer {
    padding: 10px;
    display: flex;
    justify-content: center;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    
    .collapse-btn {
      color: #bfcbd9;
      
      &:hover {
        color: #fff;
      }
    }
  }
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #f0f2f5;
  
  .header {
    height: 60px;
    background-color: #fff;
    box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    
    .header-left {
      display: flex;
      align-items: center;
    }
    
    .header-right {
      .user-dropdown {
        display: flex;
        align-items: center;
        cursor: pointer;
        
        .el-avatar {
          margin-right: 8px;
        }
        
        .el-icon {
          margin-left: 5px;
          font-size: 12px;
        }
      }
    }
  }
  
  .content {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
  }
}
</style>