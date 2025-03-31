<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-header">
        <h2>用户注册</h2>
        <p>欢迎加入校园二手商品交易平台</p>
      </div>
      
      <el-form
        :model="registerForm"
        :rules="registerRules"
        ref="registerFormRef"
        class="register-form"
        @keyup.enter="handleRegister"
      >
        <el-alert
          v-if="registerError"
          :title="errorMessage"
          type="error"
          show-icon
          :closable="false"
          style="margin-bottom: 15px"
        />
        
        <el-form-item prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="用户名"
            prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="email">
          <el-input
            v-model="registerForm.email"
            placeholder="邮箱"
            prefix-icon="Message"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="确认密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item prop="phone">
          <el-input
            v-model="registerForm.phone"
            placeholder="手机号码"
            prefix-icon="Phone"
          />
        </el-form-item>

        <el-form-item prop="nickname">
          <el-input
            v-model="registerForm.nickname"
            placeholder="昵称"
            prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="captcha" class="captcha-item">
          <div class="captcha-container">
            <el-input
              v-model="registerForm.captcha"
              placeholder="验证码"
              class="captcha-input"
            />
            <el-button
              type="primary"
              class="captcha-button"
              :disabled="captchaLoading || captchaCountdown > 0"
              @click="getCaptcha"
            >
              {{ captchaCountdown > 0 ? `${captchaCountdown}秒后重试` : '获取验证码' }}
            </el-button>
          </div>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            class="register-button"
            :loading="loading"
            @click="handleRegister"
          >注册</el-button>
        </el-form-item>
      </el-form>

      <div class="register-footer">
        <p>已有账号？ <router-link to="/auth/login">立即登录</router-link></p>
        <p><router-link to="/">返回首页</router-link></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { User, Message, Lock, Phone } from '@element-plus/icons-vue'
import axios from 'axios'

const router = useRouter()
const userStore = useUserStore()

// 表单引用
const registerFormRef = ref(null)

// 状态
const loading = ref(false)
const registerError = ref(false)
const errorMessage = ref('')
const captchaLoading = ref(false)
const captchaCountdown = ref(0)

// 表单数据
const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  phone: '',
  nickname: '',
  captcha: ''
})

// 验证密码是否一致
const validatePass = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

// 验证手机号
const validatePhone = (rule, value, callback) => {
  if (value === '') {
    callback()
  } else {
    const reg = /^1[3-9]\d{9}$/
    if (!reg.test(value)) {
      callback(new Error('请输入有效的手机号码'))
    } else {
      callback()
    }
  }
}

// 表单验证规则
const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能小于6个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validatePass, trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号码', trigger: 'blur' },
    { validator: validatePhone, trigger: 'blur' }
  ],
  nickname: [
    { required: true, message: '请输入昵称', trigger: 'blur' },
    { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' }
  ],
  captcha: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { min: 4, max: 6, message: '验证码长度不正确', trigger: 'blur' }
  ]
}

// 获取验证码
const getCaptcha = async () => {
  if (!registerForm.phone) {
    ElMessage.warning('请先输入手机号码')
    return
  }

  const phoneReg = /^1[3-9]\d{9}$/
  if (!phoneReg.test(registerForm.phone)) {
    ElMessage.warning('请输入有效的手机号码')
    return
  }

  captchaLoading.value = true
  try {
    const response = await axios.post('/api/auth/captcha', {
      phone: registerForm.phone
    })

    if (response.data.success) {
      ElMessage.success('验证码已发送，请注意查收')
      // 开始倒计时
      captchaCountdown.value = 60
      const timer = setInterval(() => {
        captchaCountdown.value--
        if (captchaCountdown.value <= 0) {
          clearInterval(timer)
        }
      }, 1000)
    } else {
      ElMessage.error(response.data.message || '验证码发送失败')
    }
  } catch (error) {
    console.error('获取验证码失败:', error)
    ElMessage.error('获取验证码失败，请稍后再试')
  } finally {
    captchaLoading.value = false
  }
}

// 注册处理
const handleRegister = async () => {
  if (!registerFormRef.value) return

  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      registerError.value = false

      try {
        const userData = {
          nickname: registerForm.nickname,
          username: registerForm.username,
          email: registerForm.email,
          password: registerForm.password,
          phone: registerForm.phone,
          captcha: registerForm.captcha
        }

        const result = await userStore.register(userData)

        if (result.success) {
          ElMessage.success('注册成功，请登录')
          router.push('/auth/login')
        } else {
          registerError.value = true
          errorMessage.value = result.message
        }
      } catch (error) {
        console.error('注册失败:', error)
        registerError.value = true
        errorMessage.value = error.response?.data?.message || '注册失败，请稍后再试'
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.register-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.register-container {
  width: 400px;
  padding: 30px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.register-header {
  text-align: center;
  margin-bottom: 30px;
}

.register-header h2 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 10px;
}

.register-header p {
  font-size: 14px;
  color: #909399;
}

.register-form {
  margin-bottom: 20px;
}

.register-button {
  width: 100%;
  padding: 12px 0;
}

.register-footer {
  text-align: center;
  font-size: 14px;
  color: #606266;
}

.register-footer a {
  color: #409eff;
  text-decoration: none;
}

.captcha-container {
  display: flex;
  gap: 10px;
}

.captcha-input {
  flex: 1;
}

.captcha-button {
  width: 120px;
  white-space: nowrap;
}
</style>