<template>
  <div class="landing-page">
    <!-- 顶部导航 -->
    <header class="navbar">
      <div class="navbar-brand">
        <span class="brand-logo">🍎</span>
        <div class="brand-info">
          <span class="brand-name">SmartOrchard</span>
          <span class="brand-sub">苹果叶片病害检测系统</span>
        </div>
      </div>
      <div class="navbar-actions">
        <button class="btn-outline" @click="goLogin">登录</button>
        <button class="btn-primary" @click="goRegister">注册</button>
      </div>
    </header>

    <main class="main-content">
      <!-- Hero 区域 -->
      <section class="hero-section">
        <div class="hero-left">
          <p class="hero-tag">APPLE DISEASE DETECTION BASED ON YOLOv13</p>
          <h1 class="hero-title">苹果叶片病害<br>检测系统</h1>
          <p class="hero-desc">
            本系统面向苹果果园病害精准防控场景，融合 YOLOv13 目标检测网络与工程化前后端流程，
            实现从上传、检测到结果管理的完整闭环。
          </p>

          <!-- 统计卡片 -->
          <div class="stat-cards">
            <div class="stat-card">
              <el-icon class="stat-icon"><Cpu /></el-icon>
              <div>
                <div class="stat-label">识别类别</div>
                <div class="stat-value">4 种病害</div>
              </div>
            </div>
            <div class="stat-card">
              <el-icon class="stat-icon"><Cpu /></el-icon>
              <div>
                <div class="stat-label">核心网络</div>
                <div class="stat-value">YOLOv13</div>
              </div>
            </div>
            <div class="stat-card">
              <el-icon class="stat-icon"><Lightning /></el-icon>
              <div>
                <div class="stat-label">结果反馈</div>
                <div class="stat-value">毫秒级输出</div>
              </div>
            </div>
          </div>
        </div>

        <div class="hero-right">
          <div class="disease-card">
            <div class="disease-card-header">
              <span class="disease-card-title">检测类别（4 类）</span>
              <span class="disease-card-sub">Dataset Labels</span>
            </div>
            <div class="disease-grid">
              <div class="disease-tag" v-for="item in diseaseLabels" :key="item.en">
                <span class="disease-zh">{{ item.zh }}</span>
                <span class="disease-en">{{ item.en }}</span>
              </div>
            </div>
            <p class="disease-tip">
              系统已对上述类别进行统一训练与推理流程支持，模型在苹果叶片数据集上完成精调，便于后续扩展更多病害类型。
            </p>
          </div>
        </div>
      </section>

      <!-- 功能特点 -->
      <section class="features-section">
        <div class="feature-card" v-for="feat in features" :key="feat.title">
          <el-icon class="feat-icon" :size="28"><component :is="feat.icon" /></el-icon>
          <h3 class="feat-title">{{ feat.title }}</h3>
          <p class="feat-desc">{{ feat.desc }}</p>
        </div>
      </section>

      <!-- 系统流程 -->
      <section class="flow-section">
        <h2 class="section-title">系统流程</h2>
        <div class="flow-steps">
          <div class="flow-step" v-for="(step, idx) in flowSteps" :key="idx">
            <div class="step-num">{{ String(idx + 1).padStart(2, '0') }}</div>
            <div class="step-title">{{ step.title }}</div>
            <div class="step-desc">{{ step.desc }}</div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { Picture, Setting, Promotion, Lightning, Cpu } from '@element-plus/icons-vue'

const router = useRouter()

const goLogin = () => {
  router.push('/login')
}

const goRegister = () => {
  router.push('/register')
}

const goSystem = () => {
  const token = localStorage.getItem('apple-disease-token')
  if (token) {
    router.push('/app/dashboard')
  } else {
    router.push('/login')
  }
}

const diseaseLabels = [
  { zh: '黑星病', en: 'Apple Scab' },
  { zh: '黑腐病', en: 'Black Rot' },
  { zh: '锈病', en: 'Cedar Apple Rust' },
  { zh: '健康叶片', en: 'Healthy' },
]

const features = [
  {
    icon: 'Picture',
    title: '多类别病害识别',
    desc: '针对苹果叶片四类常见病害进行自动检测，支持稳定的可视化预测结果与置信度输出。',
  },
  {
    icon: 'Setting',
    title: '深度学习模型驱动',
    desc: '基于 YOLOv13 目标检测网络完成特征提取与定位判别。',
  },
  {
    icon: 'Promotion',
    title: '过程可追溯',
    desc: '检测历史、置信度、时间戳可追溯，便于模型效果分析与持续优化，支持批量导出报告。',
  },
]

const flowSteps = [
  {
    title: '用户认证',
    desc: '登录后进入系统，保障检测记录的个人化管理与数据安全。',
  },
  {
    title: '上传图像',
    desc: '上传苹果叶片样本图像，系统完成预处理并送入 YOLOv13 模型。',
  },
  {
    title: '模型推理',
    desc: '通过 YOLOv13 实时检测病害区域，输出类别标签与置信度。',
  },
  {
    title: '结果管理',
    desc: '查看检测结果与历史记录，支持实验分析与报告一键生成。',
  },
]
</script>

<style scoped lang="scss">
/* ===== 基础变量 ===== */
$primary: #1a3c2e;
$primary-light: #2d6a4f;
$accent: #52b788;
$bg: #f5f5f0;
$card-bg: #ffffff;
$border: #e8e8e0;
$text-main: #1a1a1a;
$text-sub: #555;
$text-muted: #888;

.landing-page {
  min-height: 100vh;
  background: $bg;
  background-image:
    linear-gradient(rgba(0,0,0,.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,0,0,.04) 1px, transparent 1px);
  background-size: 40px 40px;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* ===== 导航 ===== */
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 48px;
  height: 64px;
  background: rgba(245, 245, 240, 0.92);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid $border;
  position: sticky;
  top: 0;
  z-index: 100;

  .navbar-brand {
    display: flex;
    align-items: center;
    gap: 10px;

    .brand-logo {
      font-size: 28px;
      line-height: 1;
    }

    .brand-info {
      display: flex;
      flex-direction: column;

      .brand-name {
        font-size: 17px;
        font-weight: 700;
        color: $primary;
        line-height: 1.2;
      }

      .brand-sub {
        font-size: 11px;
        color: $text-muted;
        line-height: 1.4;
      }
    }
  }

  .navbar-actions {
    display: flex;
    gap: 12px;
  }
}

/* ===== 按钮 ===== */
.btn-primary {
  background: $primary;
  color: #fff;
  border: 2px solid $primary;
  border-radius: 8px;
  padding: 8px 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;

  &:hover { background: $primary-light; border-color: $primary-light; }

  &.btn-lg {
    padding: 12px 28px;
    font-size: 16px;
    border-radius: 10px;
  }
}

.btn-outline {
  background: transparent;
  color: $primary;
  border: 2px solid $primary;
  border-radius: 8px;
  padding: 8px 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;

  &:hover { background: rgba($primary, 0.06); }

  &.btn-lg {
    padding: 12px 28px;
    font-size: 16px;
    border-radius: 10px;
  }
}

/* ===== 主内容 ===== */
.main-content {
  max-width: 1280px;
  margin: 0 auto;
  padding: 40px 48px 80px;
  display: flex;
  flex-direction: column;
  gap: 40px;
}

/* ===== Hero ===== */
.hero-section {
  display: grid;
  grid-template-columns: 1fr 440px;
  gap: 32px;
  background: $card-bg;
  border: 1px solid $border;
  border-radius: 16px;
  padding: 48px 40px;
  box-shadow: 0 2px 16px rgba(0,0,0,.06);
}

.hero-left {
  display: flex;
  flex-direction: column;
  gap: 20px;

  .hero-tag {
    font-size: 12px;
    font-weight: 600;
    color: $accent;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin: 0;
  }

  .hero-title {
    font-size: 52px;
    font-weight: 800;
    color: $text-main;
    line-height: 1.15;
    margin: 0;
  }

  .hero-desc {
    font-size: 15px;
    color: $text-sub;
    line-height: 1.8;
    margin: 0;
    max-width: 560px;
  }

  .hero-btns {
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
  }
}

/* 统计卡片 */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 8px;

  .stat-card {
    border: 1px solid $border;
    border-radius: 10px;
    padding: 14px 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    background: #fafaf8;

    .stat-icon {
      color: $primary-light;
      font-size: 20px;
      flex-shrink: 0;
    }

    .stat-label {
      font-size: 12px;
      color: $text-muted;
      line-height: 1.4;
    }

    .stat-value {
      font-size: 16px;
      font-weight: 700;
      color: $text-main;
      line-height: 1.4;
    }
  }
}

/* 病害类别卡片 */
.disease-card {
  border: 1px solid $border;
  border-radius: 12px;
  padding: 24px;
  background: #fafaf8;
  height: 100%;
  box-sizing: border-box;

  .disease-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    .disease-card-title {
      font-size: 16px;
      font-weight: 700;
      color: $text-main;
    }

    .disease-card-sub {
      font-size: 12px;
      color: $text-muted;
    }
  }

  .disease-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 20px;

    .disease-tag {
      border: 1px solid $border;
      border-radius: 8px;
      padding: 14px 16px;
      background: $card-bg;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      transition: box-shadow 0.2s;

      &:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,.1);
      }

      .disease-zh {
        font-size: 16px;
        font-weight: 600;
        color: $text-main;
      }

      .disease-en {
        font-size: 11px;
        color: $text-muted;
      }
    }
  }

  .disease-tip {
    font-size: 13px;
    color: $text-muted;
    line-height: 1.7;
    margin: 0;
    border-top: 1px solid $border;
    padding-top: 16px;
  }
}

/* ===== 功能特点 ===== */
.features-section {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;

  .feature-card {
    background: $card-bg;
    border: 1px solid $border;
    border-radius: 12px;
    padding: 28px 24px;
    box-shadow: 0 1px 6px rgba(0,0,0,.04);
    transition: box-shadow 0.2s;

    &:hover {
      box-shadow: 0 4px 20px rgba(0,0,0,.1);
    }

    .feat-icon {
      color: $primary-light;
      margin-bottom: 14px;
    }

    .feat-title {
      font-size: 18px;
      font-weight: 700;
      color: $text-main;
      margin: 0 0 10px;
    }

    .feat-desc {
      font-size: 14px;
      color: $text-sub;
      line-height: 1.75;
      margin: 0;
    }
  }
}

/* ===== 系统流程 ===== */
.flow-section {
  background: $card-bg;
  border: 1px solid $border;
  border-radius: 12px;
  padding: 36px 40px;
  box-shadow: 0 1px 6px rgba(0,0,0,.04);

  .section-title {
    font-size: 22px;
    font-weight: 700;
    color: $text-main;
    margin: 0 0 28px;
  }

  .flow-steps {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;

    .flow-step {
      border: 1px solid $border;
      border-radius: 10px;
      padding: 20px 18px;
      background: #fafaf8;

      .step-num {
        font-size: 22px;
        font-weight: 800;
        color: $accent;
        margin-bottom: 10px;
      }

      .step-title {
        font-size: 16px;
        font-weight: 700;
        color: $text-main;
        margin-bottom: 8px;
      }

      .step-desc {
        font-size: 13px;
        color: $text-sub;
        line-height: 1.7;
      }
    }
  }
}
</style>
