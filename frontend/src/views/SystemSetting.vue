<template>
  <div class="setting-container">
    <!-- 页面标签 -->
    <div class="page-tag">
      <span class="tag-icon">⚙️</span>
      <span>SmartOrchard · System Admin</span>
    </div>

    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">系统设置</h1>
        <p class="page-desc">管理系统用户、配置参数与个人信息</p>
      </div>
    </div>

    <!-- 功能标签页 -->
    <div class="tab-nav">
      <button
        v-if="isAdmin"
        class="tab-btn"
        :class="{ active: activeTab === 'user' }"
        @click="activeTab = 'user'"
      >
        <span class="tab-icon">👤</span>
        <span>用户管理</span>
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'profile' }"
        @click="activeTab = 'profile'"
      >
        <span class="tab-icon">📝</span>
        <span>个人信息</span>
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'password' }"
        @click="activeTab = 'password'"
      >
        <span class="tab-icon">🔑</span>
        <span>修改密码</span>
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'about' }"
        @click="activeTab = 'about'"
      >
        <span class="tab-icon">ℹ️</span>
        <span>关于系统</span>
      </button>
    </div>

    <!-- 用户管理 -->
    <div v-show="activeTab === 'user'" class="tab-content">
      <!-- 统计卡片 -->
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-icon blue">
            <span>👥</span>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ userStats.total }}</div>
            <div class="stat-label">用户总数</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon green">
            <span>🔐</span>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ userStats.admin }}</div>
            <div class="stat-label">管理员</div>
          </div>
        </div>
      </div>

      <!-- 用户列表卡片 -->
      <div class="section-card">
        <div class="card-header">
          <div class="card-title">
            <span class="card-icon">👥</span>
            <span>用户列表</span>
          </div>
          <el-button type="primary" @click="openCreateDialog" class="btn-add">
            <span>➕</span>
            创建用户
          </el-button>
        </div>

        <el-table :data="userList" v-loading="userLoading" stripe class="user-table">
          <el-table-column prop="id" label="ID" width="80" align="center" />
          <el-table-column prop="username" label="用户名" min-width="120">
            <template #default="{ row }">
              <div class="username-cell">
                <span class="user-avatar">👤</span>
                <span>{{ row.username }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="realName" label="姓名" min-width="120">
            <template #default="{ row }">
              {{ row.realName || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="college" label="学院（果园）" min-width="140">
            <template #default="{ row }">
              {{ row.college || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="major" label="专业" min-width="160">
            <template #default="{ row }">
              {{ row.major || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="createdAt" label="创建时间" width="160" align="center" />
          <el-table-column label="操作" width="140" align="center">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button type="primary" size="small" link @click="openEditDialog(row)">
                  ✏️ 编辑
                </el-button>
                <el-button type="danger" size="small" link @click="handleDeleteUser(row)" :disabled="row.id === currentUserId">
                  🗑️ 删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 个人信息 -->
    <div v-show="activeTab === 'profile'" class="tab-content">
      <div class="section-card profile-card">
        <div class="card-header">
          <div class="card-title">
            <span class="card-icon">📝</span>
            <span>个人信息</span>
          </div>
        </div>
        <el-form
          ref="userFormRef"
          :model="userForm"
          :rules="userRules"
          label-width="120px"
          class="profile-form"
        >
          <el-form-item label="用户名" prop="username">
            <el-input v-model="userForm.username" disabled />
          </el-form-item>
          <el-form-item label="姓名" prop="realName">
            <el-input v-model="userForm.realName" placeholder="请输入真实姓名" />
          </el-form-item>
          <el-form-item label="所属学院（果园）" prop="college">
            <el-input v-model="userForm.college" placeholder="请输入所属学院（果园）" />
          </el-form-item>
          <el-form-item label="专业" prop="major">
            <el-input v-model="userForm.major" placeholder="请输入专业" />
          </el-form-item>
          <el-form-item label="联系邮箱" prop="email">
            <el-input v-model="userForm.email" placeholder="请输入联系邮箱" />
          </el-form-item>
          <el-form-item label="联系电话" prop="phone">
            <el-input v-model="userForm.phone" placeholder="请输入联系电话" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="submitUserForm" class="btn-submit">
              <span>💾</span>
              保存修改
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 修改密码 -->
    <div v-show="activeTab === 'password'" class="tab-content">
      <div class="section-card password-card">
        <div class="card-header">
          <div class="card-title">
            <span class="card-icon">🔑</span>
            <span>修改密码</span>
          </div>
        </div>
        <el-form
          ref="passwordFormRef"
          :model="passwordForm"
          :rules="passwordRules"
          label-width="120px"
          class="password-form"
        >
          <el-form-item label="原密码" prop="oldPassword">
            <el-input v-model="passwordForm.oldPassword" type="password" placeholder="请输入原密码" show-password />
          </el-form-item>
          <el-form-item label="新密码" prop="newPassword">
            <el-input v-model="passwordForm.newPassword" type="password" placeholder="请输入新密码" show-password />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input v-model="passwordForm.confirmPassword" type="password" placeholder="请再次输入新密码" show-password />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="submitPasswordForm" class="btn-submit">
              <span>🔐</span>
              修改密码
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 关于系统 -->
    <div v-show="activeTab === 'about'" class="tab-content">
      <!-- 系统标识区 -->
      <div class="about-banner">
        <div class="about-logo-large">🍎</div>
        <div class="about-title-area">
          <h2>SmartOrchard</h2>
          <p>基于YOLOv13的苹果叶片病害检测系统</p>
          <div class="version-badge">v1.0.0</div>
        </div>
      </div>

      <!-- 核心信息卡片 -->
      <div class="about-grid">
        <div class="about-card info-card">
          <div class="card-icon blue">🎯</div>
          <div class="card-body">
            <h4>核心算法</h4>
            <p>YOLOv13 深度学习模型</p>
            <span class="card-tag">目标检测</span>
          </div>
        </div>
        <div class="about-card info-card">
          <div class="card-icon green">🔧</div>
          <div class="card-body">
            <h4>技术栈</h4>
            <p>Vue 3 + FastAPI</p>
            <span class="card-tag">前后端分离</span>
          </div>
        </div>
        <div class="about-card info-card">
          <div class="card-icon orange">📊</div>
          <div class="card-body">
            <h4>数据存储</h4>
            <p>SQLite + ECharts</p>
            <span class="card-tag">可视化分析</span>
          </div>
        </div>
        <div class="about-card info-card">
          <div class="card-icon purple">🗺️</div>
          <div class="card-body">
            <h4>GIS管理</h4>
            <p>果园空间分布</p>
            <span class="card-tag">精准防控</span>
          </div>
        </div>
      </div>

      <!-- 详细信息表格 -->
      <div class="section-card about-detail-card">
        <div class="card-header">
          <div class="card-title">
            <span class="card-icon">📋</span>
            <span>系统详情</span>
          </div>
        </div>
        <div class="detail-content">
          <div class="detail-row">
            <div class="detail-item">
              <span class="detail-label">系统版本</span>
              <span class="detail-value">v1.0.0</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">核心算法</span>
              <span class="detail-value">YOLOv13</span>
            </div>
          </div>
          <div class="detail-row">
            <div class="detail-item">
              <span class="detail-label">开发框架</span>
              <span class="detail-value">Vue 3 + Element Plus</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">后端框架</span>
              <span class="detail-value">FastAPI + SQLAlchemy</span>
            </div>
          </div>
          <div class="detail-row">
            <div class="detail-item">
              <span class="detail-label">开发单位</span>
              <span class="detail-value">塔里木大学 信息工程学院</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">开发者</span>
              <span class="detail-value">贾云山</span>
            </div>
          </div>
          <div class="detail-row">
            <div class="detail-item">
              <span class="detail-label">指导教师</span>
              <span class="detail-value">谢渠</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">应用场景</span>
              <span class="detail-value">南疆苹果种植产业</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 系统简介 -->
      <div class="section-card about-intro-card">
        <div class="card-header">
          <div class="card-title">
            <span class="card-icon">📖</span>
            <span>系统简介</span>
          </div>
        </div>
        <div class="intro-content">
          <p>本系统针对南疆苹果种植产业的实际痛点，基于YOLOv13深度学习算法开发，实现苹果叶片病害的快速、精准检测。系统支持单张/批量图像检测、病害空间分布GIS管理、历史数据追溯、多维度统计分析等功能。</p>
          <div class="feature-list">
            <div class="feature-item">
              <span class="feature-icon">✓</span>
              <span>支持4种病害类型检测：黑星病、黑腐病、锈病、健康叶片</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">✓</span>
              <span>批量图像处理，提升检测效率</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">✓</span>
              <span>GIS地图可视化果园病害分布</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">✓</span>
              <span>历史数据管理与报告导出</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑用户弹窗 -->
    <el-dialog
      v-model="userDialogVisible"
      :title="isEditMode ? '编辑用户' : '创建用户'"
      width="500px"
      class="user-dialog"
    >
      <el-form
        ref="dialogFormRef"
        :model="dialogForm"
        :rules="dialogRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="dialogForm.username" :disabled="isEditMode" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item :label="isEditMode ? '新密码' : '密码'" prop="password">
          <el-input v-model="dialogForm.password" type="password" show-password :placeholder="isEditMode ? '留空则不修改密码' : '请输入密码'" />
        </el-form-item>
        <el-form-item label="姓名" prop="realName">
          <el-input v-model="dialogForm.realName" placeholder="请输入真实姓名" />
        </el-form-item>
              <el-form-item label="所属学院（果园）" prop="college">
          <el-input v-model="dialogForm.college" placeholder="请输入所属学院（果园）" />
        </el-form-item>
        <el-form-item label="专业" prop="major">
          <el-input v-model="dialogForm.major" placeholder="请输入专业" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userDialogVisible = false" class="btn-cancel">取消</el-button>
        <el-button type="primary" @click="handleSubmitUser" class="btn-confirm">
          {{ isEditMode ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api/request'

// 当前登录用户信息
const currentUserInfo = ref({
  id: null,
  username: 'admin'
})

// 判断是否为管理员（ID为1的用户为管理员）
const isAdmin = computed(() => currentUserInfo.value.id === 1)

// 根据用户角色设置默认标签
const activeTab = ref('profile')

// 用户管理相关
const userList = ref([])
const userLoading = ref(false)
const userStats = reactive({
  total: 0,
  admin: 0
})
const currentUserId = ref(null)

// 弹窗相关
const userDialogVisible = ref(false)
const isEditMode = ref(false)
const dialogFormRef = ref()
const editingUserId = ref(null)

const dialogForm = reactive({
  username: '',
  password: '',
  realName: '',
  college: '',
  major: ''
})

const dialogRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }],
  realName: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }]
}

// 获取当前登录用户信息
const loadCurrentUser = () => {
  const userInfo = JSON.parse(localStorage.getItem('user-info') || '{}')
  currentUserInfo.value = {
    id: userInfo.id || 1,
    username: userInfo.username || 'admin'
  }
  currentUserId.value = currentUserInfo.value.id
  // 管理员默认显示用户管理标签
  if (isAdmin.value) {
    activeTab.value = 'user'
  }
}

// 加载用户列表
const loadUserList = async () => {
  if (!isAdmin.value) return // 非管理员不加载用户列表
  userLoading.value = true
  try {
    const res = await api.getUserList()
    userList.value = res.data?.users || []
    userStats.total = res.data?.total || 0
    userStats.admin = 1 // 管理员数量，默认1个
  } catch (error) {
    console.error('获取用户列表失败', error)
  } finally {
    userLoading.value = false
  }
}

// 打开创建用户弹窗
const openCreateDialog = () => {
  isEditMode.value = false
  editingUserId.value = null
  dialogForm.username = ''
  dialogForm.password = ''
  dialogForm.realName = ''
  dialogForm.college = ''
  dialogForm.major = ''
  userDialogVisible.value = true
}

// 打开编辑用户弹窗
const openEditDialog = (row) => {
  isEditMode.value = true
  editingUserId.value = row.id
  dialogForm.username = row.username
  dialogForm.password = ''
  dialogForm.realName = row.realName || ''
  dialogForm.college = row.college || ''
  dialogForm.major = row.major || ''
  userDialogVisible.value = true
}

// 提交用户表单
const handleSubmitUser = async () => {
  if (!dialogFormRef.value) return
  await dialogFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (isEditMode.value) {
          // 编辑模式
          const data = {
            username: dialogForm.username,
            real_name: dialogForm.realName,
            college: dialogForm.college,
            major: dialogForm.major
          }
          if (dialogForm.password) {
            data.password = dialogForm.password
          }
          await api.updateUser(editingUserId.value, data)
          ElMessage.success('用户信息更新成功')
        } else {
          // 创建模式
          await api.createUser({
            username: dialogForm.username,
            password: dialogForm.password,
            real_name: dialogForm.realName,
            college: dialogForm.college,
            major: dialogForm.major
          })
          ElMessage.success('用户创建成功')
        }
        userDialogVisible.value = false
        loadUserList()
      } catch (error) {
        console.error('操作失败', error)
        ElMessage.error(error.message || '操作失败')
      }
    }
  })
}

// 删除用户
const handleDeleteUser = (row) => {
  ElMessageBox.confirm(`确定要删除用户「${row.username}」吗？删除后无法恢复！`, '警告', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await api.deleteUser(row.id)
      ElMessage.success('用户删除成功')
      loadUserList()
    } catch (error) {
      console.error('删除失败', error)
      ElMessage.error(error.message || '删除失败')
    }
  }).catch(() => {})
}

// 个人信息表单
const userFormRef = ref()
const userForm = reactive({
  username: '',
  realName: '',
  college: '',
  major: '',
  email: '',
  phone: ''
})
const userRules = reactive({
  realName: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  email: [{ type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }]
})

// 加载当前用户信息
const loadUserInfo = async () => {
  try {
    const res = await api.getUserInfo()
    if (res.data) {
      userForm.username = res.data.username || ''
      userForm.realName = res.data.real_name || ''
      userForm.college = res.data.college || ''
      userForm.major = res.data.major || ''
      userForm.email = res.data.email || ''
      userForm.phone = res.data.phone || ''
    }
  } catch (error) {
    console.error('获取用户信息失败', error)
  }
}

// 提交个人信息修改
const submitUserForm = async () => {
  if (!userFormRef.value) return
  await userFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await api.updateUserInfo({
          real_name: userForm.realName,
          college: userForm.college,
          major: userForm.major,
          email: userForm.email,
          phone: userForm.phone
        })
        ElMessage.success('个人信息修改成功')
        // 更新localStorage中的用户信息
        const userInfo = JSON.parse(localStorage.getItem('user-info') || '{}')
        userInfo.real_name = userForm.realName
        localStorage.setItem('user-info', JSON.stringify(userInfo))
      } catch (error) {
        console.error('更新失败', error)
        ElMessage.error(error.message || '更新失败')
      }
    }
  })
}

// 修改密码表单
const passwordFormRef = ref()
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})
const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}
const passwordRules = reactive({
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
})

const submitPasswordForm = async () => {
  if (!passwordFormRef.value) return
  await passwordFormRef.value.validate((valid) => {
    if (valid) {
      ElMessage.success('密码修改成功，请重新登录')
      passwordFormRef.value?.resetFields()
    }
  })
}

onMounted(() => {
  loadCurrentUser()
  loadUserInfo()
  loadUserList()
})
</script>

<style scoped lang="scss">
.setting-container {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

// 页面标签
.page-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #fff;
  border-radius: 20px;
  font-size: 13px;
  color: #666;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  width: fit-content;

  .tag-icon {
    font-size: 16px;
  }
}

// 页面头部
.page-header {
  .header-left {
    .page-title {
      font-size: 24px;
      font-weight: 700;
      color: #1a1a1a;
      margin: 0 0 4px;
    }

    .page-desc {
      font-size: 14px;
      color: #888;
      margin: 0;
    }
  }
}

// 功能标签页
.tab-nav {
  display: flex;
  gap: 12px;
  background: #fff;
  padding: 8px;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);

  .tab-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    border: none;
    background: transparent;
    border-radius: 8px;
    font-size: 14px;
    color: #666;
    cursor: pointer;
    transition: all 0.2s;

    .tab-icon {
      font-size: 16px;
    }

    &:hover {
      background: #f5f7fa;
    }

    &.active {
      background: #16a34a;
      color: #fff;
    }
  }
}

// 统计卡片行
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;

  .stat-card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);

    .stat-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;

      &.blue {
        background: rgba(24, 144, 255, 0.1);
      }

      &.green {
        background: rgba(82, 196, 26, 0.1);
      }

      &.red {
        background: rgba(245, 34, 45, 0.1);
      }

      &.yellow {
        background: rgba(250, 173, 20, 0.1);
      }
    }

    .stat-info {
      .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: #1a1a1a;
        line-height: 1.2;
      }

      .stat-label {
        font-size: 13px;
        color: #888;
        margin-top: 2px;
      }
    }
  }
}

// 内容卡片
.section-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  overflow: hidden;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid #f0f0f0;

    .card-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 16px;
      font-weight: 600;
      color: #1a1a1a;

      .card-icon {
        font-size: 18px;
      }
    }

    .btn-add {
      display: flex;
      align-items: center;
      gap: 6px;
      background: #16a34a;
      border-color: #16a34a;
      color: #fff;
      border-radius: 8px;

      &:hover {
        background: #15803d;
        border-color: #15803d;
      }
    }
  }
}

// 用户表格
.user-table {
  padding: 0 20px 20px;

  .username-cell {
    display: flex;
    align-items: center;
    gap: 8px;

    .user-avatar {
      font-size: 20px;
    }
  }

  .action-buttons {
    display: flex;
    gap: 8px;
    justify-content: center;
  }
}

// 个人信息表单
.profile-card, .password-card {
  max-width: 700px;

  .profile-form, .password-form {
    padding: 24px 20px;

    .btn-submit {
      display: flex;
      align-items: center;
      gap: 6px;
      background: #16a34a;
      border-color: #16a34a;
      border-radius: 8px;

      &:hover {
        background: #15803d;
        border-color: #15803d;
      }
    }
  }
}

// 关于系统
.about-banner {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 32px;
  background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%);
  border-radius: 16px;
  margin-bottom: 20px;

  .about-logo-large {
    font-size: 72px;
  }

  .about-title-area {
    h2 {
      font-size: 28px;
      font-weight: 700;
      color: #fff;
      margin: 0 0 8px;
    }

    p {
      font-size: 16px;
      color: rgba(255, 255, 255, 0.9);
      margin: 0 0 12px;
    }

    .version-badge {
      display: inline-block;
      padding: 4px 12px;
      background: rgba(255, 255, 255, 0.2);
      border-radius: 20px;
      font-size: 13px;
      color: #fff;
    }
  }
}

.about-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;

  .about-card {
    background: #fff;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
    transition: transform 0.2s, box-shadow 0.2s;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    .card-icon {
      width: 44px;
      height: 44px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      margin-bottom: 14px;

      &.blue { background: rgba(24, 144, 255, 0.1); }
      &.green { background: rgba(82, 196, 26, 0.1); }
      &.orange { background: rgba(250, 173, 20, 0.1); }
      &.purple { background: rgba(144, 101, 176, 0.1); }
    }

    .card-body {
      h4 {
        font-size: 15px;
        font-weight: 600;
        color: #1a1a1a;
        margin: 0 0 6px;
      }

      p {
        font-size: 13px;
        color: #666;
        margin: 0 0 10px;
      }

      .card-tag {
        display: inline-block;
        padding: 3px 10px;
        background: #f5f7fa;
        border-radius: 4px;
        font-size: 12px;
        color: #888;
      }
    }
  }
}

.about-detail-card, .about-intro-card {
  margin-bottom: 20px;

  .detail-content {
    padding: 20px;

    .detail-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      padding: 14px 0;
      border-bottom: 1px solid #f0f0f0;

      &:last-child {
        border-bottom: none;
      }

      .detail-item {
        display: flex;
        align-items: center;
        gap: 12px;

        .detail-label {
          width: 100px;
          font-size: 14px;
          color: #888;
        }

        .detail-value {
          font-size: 14px;
          color: #1a1a1a;
          font-weight: 500;
        }
      }
    }
  }

  .intro-content {
    padding: 20px;

    p {
      font-size: 14px;
      color: #666;
      line-height: 1.8;
      margin: 0 0 20px;
      text-indent: 2em;
    }

    .feature-list {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;

      .feature-item {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 14px;
        color: #555;

        .feature-icon {
          width: 20px;
          height: 20px;
          background: #16a34a;
          color: #fff;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 12px;
          font-weight: bold;
        }
      }
    }
  }
}

// 弹窗按钮
.user-dialog {
  .btn-cancel {
    border-radius: 8px;
  }

  .btn-confirm {
    background: #16a34a;
    border-color: #16a34a;
    border-radius: 8px;

    &:hover {
      background: #15803d;
      border-color: #15803d;
    }
  }
}
</style>
