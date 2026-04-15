import { createRouter, createWebHistory } from 'vue-router'

// 布局组件
const MainLayout = () => import('@/layout/MainLayout.vue')
// 页面组件
const Landing = () => import('@/views/LandingPage.vue')
const Login = () => import('@/views/Login.vue')
const Register = () => import('@/views/Register.vue')
const Dashboard = () => import('@/views/Dashboard.vue')
const DiseaseDetect = () => import('@/views/DiseaseDetect.vue')
const OrchardMap = () => import('@/views/OrchardMap.vue')
const HistoryData = () => import('@/views/HistoryData.vue')
const DataAnalysis = () => import('@/views/DataAnalysis.vue')
const SystemSetting = () => import('@/views/SystemSetting.vue')

const routes = [
  {
    path: '/',
    redirect: '/landing'
  },
  {
    path: '/landing',
    name: 'Landing',
    component: Landing,
    meta: { title: '欢迎', noAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { title: '系统登录', noAuth: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { title: '账号注册', noAuth: true }
  },
  {
    path: '/app',
    component: MainLayout,
    redirect: '/app/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: { title: '系统首页', icon: 'Odometer' }
      },
      {
        path: 'detect',
        name: 'DiseaseDetect',
        component: DiseaseDetect,
        meta: { title: '病害检测', icon: 'Search' }
      },
      {
        path: 'orchard-map',
        name: 'OrchardMap',
        component: OrchardMap,
        meta: { title: '果园GIS管理', icon: 'MapLocation' }
      },
      {
        path: 'history',
        name: 'HistoryData',
        component: HistoryData,
        meta: { title: '历史数据', icon: 'Document' }
      },
      {
        path: 'analysis',
        name: 'DataAnalysis',
        component: DataAnalysis,
        meta: { title: '数据分析', icon: 'DataAnalysis' }
      },
      {
        path: 'setting',
        name: 'SystemSetting',
        component: SystemSetting,
        meta: { title: '系统设置', icon: 'Setting' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/landing'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫-登录校验
router.beforeEach((to, from, next) => {
  const isLogin = localStorage.getItem('apple-disease-token')
  if (to.meta.requiresAuth && !isLogin) {
    next('/login')
  } else {
    document.title = `${to.meta.title || '首页'} - 苹果叶片病害检测系统`
    next()
  }
})

export default router