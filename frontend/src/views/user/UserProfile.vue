<template>
  <div class="user-profile-page">
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>
    
    <div v-else-if="error" class="error-container">
      <el-empty description="加载用户信息失败">
        <template #description>
          <p>{{ errorMessage }}</p>
        </template>
        <el-button type="primary" @click="fetchUserProfile">重试</el-button>
      </el-empty>
    </div>
    
    <div v-else class="profile-container">
      <h1 class="page-title">个人中心</h1>
      
      <el-tabs v-model="activeTab" class="profile-tabs">
        <!-- 基本信息 -->
        <el-tab-pane label="基本信息" name="basic">
          <el-card class="profile-card">
            <div class="user-avatar">
              <el-avatar :size="100" :src="userInfo.avatar">
                {{ userInfo.username?.substring(0, 1).toUpperCase() || 'U' }}
              </el-avatar>
              <el-button size="small" @click="handleAvatarUpload">更换头像</el-button>
              <input
                type="file"
                ref="avatarInput"
                style="display: none"
                accept="image/*"
                @change="uploadAvatar"
              />
            </div>
            
            <el-form
              :model="userForm"
              :rules="userRules"
              ref="userFormRef"
              label-width="100px"
              class="profile-form"
            >
              <el-form-item label="用户名" prop="username">
                <el-input v-model="userForm.username" disabled />
              </el-form-item>
              
              <el-form-item label="昵称" prop="nickname">
                <el-input v-model="userForm.nickname" />
              </el-form-item>
              
              <el-form-item label="电子邮箱" prop="email">
                <el-input v-model="userForm.email" />
              </el-form-item>
              
              <el-form-item label="手机号码" prop="phone">
                <el-input v-model="userForm.phone" />
              </el-form-item>
              
              <el-form-item label="性别" prop="gender">
                <el-radio-group v-model="userForm.gender">
                  <el-radio label="male">男</el-radio>
                  <el-radio label="female">女</el-radio>
                  <el-radio label="other">其他</el-radio>
                </el-radio-group>
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="updateUserProfile">保存修改</el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-tab-pane>
        
        <!-- 修改密码 -->
        <el-tab-pane label="修改密码" name="password">
          <el-card class="profile-card">
            <el-form
              :model="passwordForm"
              :rules="passwordRules"
              ref="passwordFormRef"
              label-width="100px"
              class="password-form"
            >
              <el-form-item label="当前密码" prop="currentPassword">
                <el-input
                  v-model="passwordForm.currentPassword"
                  type="password"
                  show-password
                />
              </el-form-item>
              
              <el-form-item label="新密码" prop="newPassword">
                <el-input
                  v-model="passwordForm.newPassword"
                  type="password"
                  show-password
                />
              </el-form-item>
              
              <el-form-item label="确认新密码" prop="confirmPassword">
                <el-input
                  v-model="passwordForm.confirmPassword"
                  type="password"
                  show-password
                />
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="updatePassword">修改密码</el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-tab-pane>
        
        <!-- 收货地址 -->
        <el-tab-pane label="收货地址" name="address">
          <el-card class="profile-card">
            <div class="address-header">
              <h3>我的收货地址</h3>
              <el-button type="primary" size="small" @click="showAddressDialog('add')">添加新地址</el-button>
            </div>
            
            <div v-if="addresses.length === 0" class="empty-address">
              <el-empty description="暂无收货地址" />
            </div>
            
            <div v-else class="address-list">
              <el-card
                v-for="address in addresses"
                :key="address.id"
                class="address-item"
                :class="{ 'is-default': address.is_default }"
                shadow="hover"
              >
                <div class="address-content">
                  <div class="address-info">
                    <div class="address-name">
                      <span>{{ address.name }}</span>
                      <span class="address-phone">{{ address.phone }}</span>
                    </div>
                    <div class="address-detail">
                      {{ formatAddress(address) }}
                    </div>
                  </div>
                  
                  <div class="address-actions">
                    <el-tag v-if="address.is_default" type="success" size="small">默认地址</el-tag>
                    <el-button v-else type="text" @click="setDefaultAddress(address.id)">设为默认</el-button>
                    <el-button type="text" @click="showAddressDialog('edit', address)">编辑</el-button>
                    <el-button type="text" @click="deleteAddress(address.id)">删除</el-button>
                  </div>
                </div>
              </el-card>
            </div>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </div>
    
    <!-- 地址编辑对话框 -->
    <el-dialog
      :title="addressDialogType === 'add' ? '添加新地址' : '编辑地址'"
      v-model="addressDialogVisible"
      width="500px"
    >
      <el-form
        :model="addressForm"
        :rules="addressRules"
        ref="addressFormRef"
        label-width="80px"
      >
        <el-form-item label="收货人" prop="name">
          <el-input v-model="addressForm.name" />
        </el-form-item>
        
        <el-form-item label="手机号码" prop="phone">
          <el-input v-model="addressForm.phone" />
        </el-form-item>
        
        <el-form-item label="所在地区" prop="region">
          <el-cascader
            v-model="addressForm.region"
            :options="regions"
            placeholder="请选择省/市/区"
          />
        </el-form-item>
        
        <el-form-item label="详细地址" prop="detail">
          <el-input v-model="addressForm.detail" type="textarea" :rows="3" />
        </el-form-item>
        
        <el-form-item label="邮政编码" prop="zip_code">
          <el-input v-model="addressForm.zip_code" />
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="addressForm.is_default">设为默认收货地址</el-checkbox>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="addressDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveAddress">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

const userStore = useUserStore()

// 状态
const loading = ref(true)
const error = ref(false)
const errorMessage = ref('')
const activeTab = ref('basic')

// 用户信息
const userInfo = ref({})
const userForm = ref({
  username: '',
  nickname: '',
  email: '',
  phone: '',
  gender: 'other'
})

// 密码表单
const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 地址相关
const addresses = ref([])
const regions = ref([])
const addressDialogVisible = ref(false)
const addressDialogType = ref('add') // 'add' 或 'edit'
const addressForm = ref({
  id: null,
  name: '',
  phone: '',
  region: [],
  detail: '',
  zip_code: '',
  is_default: false
})

// 表单引用
const userFormRef = ref(null)
const passwordFormRef = ref(null)
const addressFormRef = ref(null)
const avatarInput = ref(null)

// 表单验证规则
const userRules = {
  nickname: [
    { required: true, message: '请输入昵称', trigger: 'blur' },
    { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ]
}

const passwordRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能小于6个字符', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能小于6个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.value.newPassword) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const addressRules = {
  name: [
    { required: true, message: '请输入收货人姓名', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号码', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ],
  region: [
    { required: true, message: '请选择所在地区', trigger: 'change' }
  ],
  detail: [
    { required: true, message: '请输入详细地址', trigger: 'blur' }
  ]
}

// 初始化
onMounted(async () => {
  await fetchUserProfile()
  await fetchAddresses()
  await fetchRegions()
})

// 获取用户信息
const fetchUserProfile = async () => {
  loading.value = true
  error.value = false
  
  try {
    const response = await api.auth.getProfile()
    userInfo.value = response
    
    // 填充表单
    userForm.value = {
      username: response.username,
      nickname: response.nickname || '',
      email: response.email || '',
      phone: response.phone || '',
      gender: response.gender || 'other'
    }
  } catch (err) {
    console.error('获取用户信息失败:', err)
    error.value = true
    errorMessage.value = err.response?.data?.message || '获取用户信息失败'
  } finally {
    loading.value = false
  }
}

// 更新用户信息
const updateUserProfile = async () => {
  if (!userFormRef.value) return
  
  await userFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await api.auth.updateProfile(userForm.value)
        ElMessage.success('个人信息更新成功')
        await fetchUserProfile()
      } catch (err) {
        console.error('更新用户信息失败:', err)
        ElMessage.error(err.response?.data?.message || '更新用户信息失败')
      }
    }
  })
}

// 更新密码
const updatePassword = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await api.auth.updatePassword({
          current_password: passwordForm.value.currentPassword,
          new_password: passwordForm.value.newPassword
        })
        ElMessage.success('密码修改成功')
        passwordForm.value = {
          currentPassword: '',
          newPassword: '',
          confirmPassword: ''
        }
      } catch (err) {
        console.error('修改密码失败:', err)
        ElMessage.error(err.response?.data?.message || '修改密码失败')
      }
    }
  })
}

// 头像上传
const handleAvatarUpload = () => {
  avatarInput.value.click()
}

const uploadAvatar = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  const formData = new FormData()
  formData.append('avatar', file)
  
  try {
    await api.auth.uploadAvatar(formData)
    ElMessage.success('头像上传成功')
    await fetchUserProfile()
  } catch (err) {
    console.error('头像上传失败:', err)
    ElMessage.error(err.response?.data?.message || '头像上传失败')
  } finally {
    // 清空文件输入框，以便再次选择同一文件时触发change事件
    event.target.value = ''
  }
}

// 获取地址列表
const fetchAddresses = async () => {
  try {
    const response = await api.addresses.getList()
    addresses.value = response || []
  } catch (err) {
    console.error('获取地址列表失败:', err)
    ElMessage.error('获取地址列表失败')
  }
}

// 获取地区数据
const fetchRegions = async () => {
  try {
    const response = await api.addresses.getRegions()
    regions.value = response || []
  } catch (err) {
    console.error('获取地区数据失败:', err)
  }
}

// 格式化地址
const formatAddress = (address) => {
  const regionNames = address.region_names || []
  return [...regionNames, address.detail].filter(Boolean).join(' ')
}

// 显示地址对话框
const showAddressDialog = (type, address = null) => {
  addressDialogType.value = type
  addressDialogVisible.value = true
  
  if (type === 'add') {
    addressForm.value = {
      id: null,
      name: '',
      phone: '',
      region: [],
      detail: '',
      zip_code: '',
      is_default: false
    }
  } else if (type === 'edit' && address) {
    addressForm.value = {
      id: address.id,
      name: address.name,
      phone: address.phone,
      region: address.region || [],
      detail: address.detail,
      zip_code: address.zip_code || '',
      is_default: address.is_default
    }
  }
}

// 保存地址
const saveAddress = async () => {
  if (!addressFormRef.value) return
  
  await addressFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const data = {
          name: addressForm.value.name,
          phone: addressForm.value.phone,
          region: addressForm.value.region,
          detail: addressForm.value.detail,
          zip_code: addressForm.value.zip_code,
          is_default: addressForm.value.is_default
        }
        
        if (addressDialogType.value === 'add') {
          await api.addresses.create(data)
          ElMessage.success('添加地址成功')
        } else {
          await api.addresses.update(addressForm.value.id, data)
          ElMessage.success('更新地址成功')
        }
        
        addressDialogVisible.value = false
        await fetchAddresses()
      } catch (err) {
        console.error('保存地址失败:', err)
        ElMessage.error(err.response?.data?.message || '保存地址失败')
      }
    }
  })
}

// 设置默认地址
const setDefaultAddress = async (id) => {
  try {
    await api.addresses.setDefault(id)
    ElMessage.success('设置默认地址成功')
    await fetchAddresses()
  } catch (err) {
    console.error('设置默认地址失败:', err)
    ElMessage.error(err.response?.data?.message || '设置默认地址失败')
  }
}

// 删除地址
const deleteAddress = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个地址吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.addresses.delete(id)
    ElMessage.success('删除地址成功')
    await fetchAddresses()
  } catch (err) {
    if (err !== 'cancel') {
      console.error('删除地址失败:', err)
      ElMessage.error(err.response?.data?.message || '删除地址失败')
    }
  }
}
</script>

<style scoped>
.user-profile-page {
  padding: 20px 0;
}

.page-title {
  margin-bottom: 20px;
  font-size: 24px;
  font-weight: 500;
  color: #333;
}

.profile-tabs {
  margin-top: 20px;
}

.profile-card {
  margin-bottom: 20px;
}

.user-avatar {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 30px;
}

.user-avatar .el-button {
  margin-top: 10px;
}

.profile-form,
.password-form {
  max-width: 500px;
}

.address-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.address-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.address-item {
  position: relative;
  border: 1px solid #ebeef5;
}

.address-item.is-default {
  border-color: #67c23a;
}

.address-content {
  display: flex;
  justify-content: space-between;
}

.address-info {
  flex: 1;
}

.address-name {
  font-weight: bold;
  margin-bottom: 5px;
}

.address-phone {
  margin-left: 10px;
  color: #606266;
}

.address-detail {
  color: #606266;
  line-height: 1.5;
}

.address-actions {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
}

.empty-address {
  padding: 30px 0;
}

.loading-container,
.error-container {
  padding: 50px 0;
  text-align: center;
}
</style>