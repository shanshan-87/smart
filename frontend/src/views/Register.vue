<template>
  <div class="auth-page">
    <!-- 左侧品牌区域 -->
    <div class="auth-left">
      <div class="left-content">
        <div class="left-logo">🍎</div>
        <h1 class="left-title">SmartOrchard</h1>
        <p class="left-sub">苹果叶片病害检测系统</p>
        <ul class="left-features">
          <li>
            <el-icon><Check /></el-icon>
            <span>基于 YOLOv13 深度学习模型</span>
          </li>
          <li>
            <el-icon><Check /></el-icon>
            <span>支持4类苹果叶片病害识别</span>
          </li>
          <li>
            <el-icon><Check /></el-icon>
            <span>检测结果实时可视化输出</span>
          </li>
          <li>
            <el-icon><Check /></el-icon>
            <span>历史数据可追溯可导出</span>
          </li>
        </ul>
        <div class="left-footer">
          <p>塔里木大学 信息工程学院</p>
          <p>计算机科学与技术专业 · 毕业设计</p>
        </div>
      </div>
    </div>

    <!-- 右侧表单区域 -->
    <div class="auth-right">
      <div class="auth-form-box">
        <div class="form-header">
          <h2 class="form-title">注册账号</h2>
          <p class="form-tip">创建账号，开始您的病害检测之旅</p>
        </div>

        <el-form
          ref="registerFormRef"
          :model="registerForm"
          :rules="registerRules"
          class="auth-form"
          size="large"
        >
          <el-form-item prop="username">
            <el-input
              v-model="registerForm.username"
              placeholder="请输入用户名"
              prefix-icon="User"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="请输入密码（至少6位）"
              prefix-icon="Lock"
              show-password
            />
          </el-form-item>
          <el-form-item prop="confirmPassword">
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="请确认密码"
              prefix-icon="Lock"
              show-password
              @keyup.enter="handleRegister"
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              class="submit-btn"
              :loading="loading"
              @click="handleRegister"
            >
              注 册
            </el-button>
          </el-form-item>
        </el-form>

        <div class="form-footer">
          <span>已有账号？</span>
          <el-link type="primary" @click="$router.push('/login')">立即登录</el-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Check } from '@element-plus/icons-vue'
import { api } from '@/api/request'

const router = useRouter()
const registerFormRef = ref()
const loading = ref(false)

const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

// 自定义校验：确认密码
const validateConfirm = (rule, value, callback) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const registerRules = reactive({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' }
  ]
})

const handleRegister = async () => {
  if (!registerFormRef.value) return
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await api.register({
          username: registerForm.username,
          password: registerForm.password
        })
        ElMessage.success('注册成功，请登录')
        router.push('/login')
      } catch (error) {
        console.error('注册失败', error)
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped lang="scss">
.auth-page {
  display: flex;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

.auth-left {
  width: 42%;
  background: linear-gradient(160deg, #1a3c2e 0%, #2d6a4f 50%, #40916c 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    width: 320px;
    height: 320px;
    border-radius: 50%;
    background: rgba(255,255,255,0.05);
    top: -80px;
    right: -80px;
  }
  &::after {
    content: '';
    position: absolute;
    width: 200px;
    height: 200px;
    border-radius: 50%;
    background: rgba(255,255,255,0.04);
    bottom: 60px;
    left: -60px;
  }
}

.left-content {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 40px;

  .left-logo {
    font-size: 72px;
    line-height: 1;
    margin-bottom: 16px;
  }

  .left-title {
    font-size: 32px;
    font-weight: 800;
    color: #fff;
    letter-spacing: 2px;
    margin: 0 0 8px;
  }

  .left-sub {
    font-size: 16px;
    color: rgba(255,255,255,0.7);
    margin: 0 0 40px;
    letter-spacing: 4px;
  }

  .left-features {
    list-style: none;
    padding: 0;
    margin: 0 0 40px;
    text-align: left;

    li {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 0;
      color: rgba(255,255,255,0.85);
      font-size: 15px;
      border-bottom: 1px solid rgba(255,255,255,0.1);

      .el-icon {
        color: #52b788;
        font-size: 16px;
        flex-shrink: 0;
      }
    }
  }

  .left-footer {
    color: rgba(255,255,255,0.45);
    font-size: 12px;
    line-height: 1.8;
    margin-top: 20px;
  }
}

.auth-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f0;
}

.auth-form-box {
  width: 420px;
  background: #fff;
  border-radius: 16px;
  padding: 44px 40px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.08);

  .form-header {
    margin-bottom: 32px;

    .form-title {
      font-size: 26px;
      font-weight: 700;
      color: #1a1a1a;
      margin: 0 0 8px;
    }

    .form-tip {
      font-size: 14px;
      color: #888;
      margin: 0;
    }
  }

  .auth-form {
    .submit-btn {
      width: 100%;
      height: 48px;
      font-size: 16px;
      font-weight: 600;
      letter-spacing: 4px;
      border-radius: 8px;
      background: #1a3c2e;
      border-color: #1a3c2e;

      &:hover, &:focus {
        background: #2d6a4f;
        border-color: #2d6a4f;
      }
    }
  }

  .form-footer {
    text-align: center;
    margin-top: 8px;
    font-size: 14px;
    color: #888;
    display: flex;
    justify-content: center;
    gap: 4px;
  }
}
</style>
