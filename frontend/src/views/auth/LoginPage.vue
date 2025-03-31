<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h2>用户登录</h2>
        <p>欢迎回到校园二手商品交易平台</p>
      </div>
      
      <el-form
        :model="loginForm"
        :rules="loginRules"
        ref="loginFormRef"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-alert
          v-if="loginError"
          :title="errorMessage"
          type="error"
          show-icon
          :closable="false"
          style="margin-bottom: 15px"
        />

        <el-form-item prop="phone">
          <el-input
            v-model="loginForm.phone"
            placeholder="手机号"
            prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <div class="form-options">
          <el-checkbox v-model="rememberMe">记住我</el-checkbox>
          <el-button type="text" @click="forgotPassword">忘记密码？</el-button>
        </div>

        <el-form-item>
          <el-button
            type="primary"
            class="login-button"
            :loading="loading"
            @click="handleLogin"
          >登录</el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <p>还没有账号？ <router-link to="/auth/register">立即注册</router-link></p>
        <p><router-link to="/">返回首页</router-link></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const route = useRoute()

const loginFormRef = ref(null)
const loading = ref(false)
const loginError = ref(false)
const errorMessage = ref('')
const rememberMe = ref(false)

const loginForm = reactive({
  phone: '',
  password: ''
})

const loginRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能小于6个字符', trigger: 'blur' }
  ]
}

onMounted(() => {
  const rememberedPhone = localStorage.getItem('rememberedPhone')
  if (rememberedPhone) {
    loginForm.phone = rememberedPhone
    rememberMe.value = true
  }
})

const handleLogin = async () => {
  if (!loginFormRef.value) return

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      loginError.value = false

      try {
        const response = await axios.post('/api/auth/login', {
          phone: loginForm.phone,
          password: loginForm.password
        })

        if (response.data.success) {
          localStorage.setItem('token', response.data.data.token)
          if (rememberMe.value) {
            localStorage.setItem('rememberedPhone', loginForm.phone)
          } else {
            localStorage.removeItem('rememberedPhone')
          }

          ElMessage.success('登录成功')
          const redirectPath = route.query.redirect || '/'
          router.push(redirectPath)
        } else {
          loginError.value = true
          errorMessage.value = response.data.message
        }
      } catch (error) {
        console.error('登录失败:', error)
        loginError.value = true
        errorMessage.value = error.response?.data?.message || '登录失败，请稍后再试'
      } finally {
        loading.value = false
      }
    }
  })
}

const forgotPassword = () => {
  ElMessage.info('请联系管理员重置密码')
}

axios.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, error => Promise.reject(error))
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.login-container {
  width: 400px;
  padding: 30px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 10px;
}

.login-header p {
  font-size: 14px;
  color: #909399;
}

.login-form {
  margin-bottom: 20px;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.login-button {
  width: 100%;
  padding: 12px 0;
}

.login-footer {
  text-align: center;
  font-size: 14px;
  color: #606266;
}

.login-footer a {
  color: #409eff;
  text-decoration: none;
}
</style>