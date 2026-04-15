<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="aside-container">
      <div class="logo-box">
        <span class="logo-icon">🍎</span>
        <span class="logo-text">病害检测系统</span>
      </div>
      <el-menu
        :default-active="route.path"
        router
        background-color="#001529"
        text-color="#ffffff"
        active-text-color="#1890ff"
        class="sidebar-menu"
      >
        <el-menu-item v-for="item in menuList" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <!-- 顶部导航栏 -->
      <el-header class="header-container">
        <div class="header-left">
          <el-button class="portal-btn" @click="router.push('/')">
            <span>🏠</span>
            <span>返回门户</span>
          </el-button>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/app/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentPageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <div class="user-info">
              <el-avatar size="small" :icon="UserFilled" />
              <span class="username">{{ currentUser.username }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="setting">⚙️ 个人设置</el-dropdown-item>
                <el-dropdown-item command="switch" divided>🔄 切换账号</el-dropdown-item>
                <el-dropdown-item command="logout">🚪 退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 页面内容区 -->
      <el-main class="main-container">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { UserFilled } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

// 当前登录用户信息
const currentUser = ref({
  id: null,
  username: '管理员',
  real_name: ''
})

// 从localStorage获取用户信息
const loadUserInfo = () => {
  const userInfo = JSON.parse(localStorage.getItem('user-info') || '{}')
  if (userInfo.username) {
    currentUser.value = {
      id: userInfo.id,
      username: userInfo.real_name || userInfo.username,
      real_name: userInfo.real_name || ''
    }
  }
}

// 菜单列表，与路由配置对应
const menuList = ref([
  { path: '/app/dashboard', title: '系统首页', icon: 'Odometer' },
  { path: '/app/detect', title: '病害检测', icon: 'Search' },
  { path: '/app/orchard-map', title: '果园GIS管理', icon: 'MapLocation' },
  { path: '/app/history', title: '历史数据', icon: 'Document' },
  { path: '/app/analysis', title: '数据分析', icon: 'DataAnalysis' },
  { path: '/app/setting', title: '系统设置', icon: 'Setting' }
])

// 当前页面标题
const currentPageTitle = computed(() => {
  const matched = menuList.value.find(item => item.path === route.path)
  return matched ? matched.title : ''
})

// 页面加载时获取用户信息
onMounted(() => {
  loadUserInfo()
})

// 下拉菜单操作
const handleCommand = (command) => {
  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      localStorage.removeItem('apple-disease-token')
      localStorage.removeItem('user-info')
      router.push('/login')
      ElMessage.success('退出登录成功')
    })
  } else if (command === 'setting') {
    router.push('/app/setting')
  } else if (command === 'switch') {
    ElMessageBox.confirm('确定要切换账号吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    }).then(() => {
      localStorage.removeItem('apple-disease-token')
      localStorage.removeItem('user-info')
      router.push('/login')
    })
  } else if (command === 'portal') {
    router.push('/')
  }
}
</script>

<style scoped lang="scss">
.layout-container {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.aside-container {
  background-color: #001529;
  height: 100%;
  display: flex;
  flex-direction: column;

  .logo-box {
    height: 64px;
    display: flex;
    align-items: center;
    padding: 0 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);

    .logo-img {
      width: 32px;
      height: 32px;
      margin-right: 8px;
    }

    .logo-icon {
      font-size: 28px;
      margin-right: 8px;
      line-height: 1;
    }

    .logo-text {
      color: #ffffff;
      font-size: 16px;
      font-weight: 600;
      white-space: nowrap;
    }
  }

  .sidebar-menu {
    border: none;
    flex: 1;
    overflow-y: auto;

    .el-menu-item {
      height: 50px;
      line-height: 50px;
      margin: 4px 0;
      border-radius: 4px;

      &:hover {
        background-color: rgba(24, 144, 255, 0.1);
      }

      &.is-active {
        background-color: var(--primary-color);
        color: #ffffff;
      }
    }
  }
}

.header-container {
  background: #ffffff;
  border-bottom: 1px solid var(--border-color);
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;

  .header-left {
    display: flex;
    align-items: center;
    gap: 20px;

    .portal-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 16px;
      background: #16a34a;
      border-color: #16a34a;
      color: #fff;
      border-radius: 6px;
      font-size: 14px;
      transition: all 0.2s;

      &:hover {
        background: #15803d;
        border-color: #15803d;
      }
    }
  }

  .header-right {
    .user-info {
      display: flex;
      align-items: center;
      cursor: pointer;

      .username {
        margin-left: 8px;
        font-size: 14px;
      }
    }
  }
}

.main-container {
  padding: 0;
  background-color: var(--bg-color);
  overflow-y: auto;
}
</style>