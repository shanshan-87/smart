<template>
  <div class="dashboard-container">
    <!-- Hero 横幅区域 -->
    <section class="hero-banner">
      <div class="hero-left">
        <div class="hero-tag">
          <span class="tag-icon">🍎</span>
          <span>SmartOrchard · AI Disease Detection</span>
        </div>
        <h1 class="hero-title">苹果叶片病害检测工作台</h1>
        <p class="hero-desc">
          基于深度学习的高精度苹果叶片病害识别系统，支持黑星病、黑腐病、锈病等常见病害的智能检测与分类。
        </p>
        <div class="hero-actions">
          <el-button type="primary" size="large" class="btn-primary" @click="$router.push('/app/detect')">
            开始检测
          </el-button>
          <el-button size="large" class="btn-default" @click="$router.push('/app/history')">
            查看历史
          </el-button>
        </div>
      </div>

      <div class="hero-right">
        <div class="disease-panel">
          <div class="panel-header">
            <div class="panel-title">
              <span class="panel-icon">📊</span>
              <span>数据集识别类别</span>
            </div>
            <span class="panel-count">4 labels</span>
          </div>
          <div class="disease-grid">
            <div class="disease-card" v-for="item in diseaseList" :key="item.name">
              <div class="disease-name">{{ item.name }}</div>
              <div class="disease-en">{{ item.en }}</div>
              <div class="disease-tag" :style="{ background: item.tagBg, color: item.tagColor }">
                {{ item.tag }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 统计卡片 -->
    <section class="stats-row">
      <div class="stat-card">
        <div class="stat-icon icon-blue">
          <span>📁</span>
        </div>
        <div class="stat-info">
          <div class="stat-label">类别覆盖</div>
          <div class="stat-value">4 种病害</div>
          <div class="stat-desc">覆盖核心病害类型</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon icon-green">
          <span>🤖</span>
        </div>
        <div class="stat-info">
          <div class="stat-label">模型架构</div>
          <div class="stat-value">YOLOv13</div>
          <div class="stat-desc">深层特征提取 + 目标检测</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon icon-yellow">
          <span>⚡</span>
        </div>
        <div class="stat-info">
          <div class="stat-label">识别响应</div>
          <div class="stat-value">毫秒级</div>
          <div class="stat-desc">快速返回检测结果</div>
        </div>
      </div>
    </section>

    <!-- 底部区域：左侧实验流程 + 右侧最新记录 -->
    <section class="bottom-section">
      <div class="left-column">
        <!-- 实验流程卡片 -->
        <div class="section-card">
          <h3 class="section-title">
            <span>🔬</span>
            实验流程
          </h3>
          <div class="flow-steps">
            <div class="flow-step">
              <span class="step-num">01</span>
              <span class="step-text">上传苹果叶片样本图像，系统自动完成数据预处理</span>
            </div>
            <div class="flow-step">
              <span class="step-num">02</span>
              <span class="step-text">深度网络提取纹理、形态和颜色等关键特征</span>
            </div>
            <div class="flow-step">
              <span class="step-num">03</span>
              <span class="step-text">输出病害类别预测及置信度，支持可视化展示</span>
            </div>
            <div class="flow-step">
              <span class="step-num">04</span>
              <span class="step-text">识别记录自动沉淀到历史，便于复盘分析</span>
            </div>
          </div>
        </div>
      </div>

      <div class="right-column">
        <!-- 最新检测记录 -->
        <div class="section-card">
          <h3 class="section-title">
            <span>📋</span>
            最新检测记录
            <el-tag size="small" type="info" class="record-count">{{ latestRecordList.length }} 条</el-tag>
          </h3>
          <div v-if="latestRecordList.length === 0" class="empty-records">
            <span class="empty-icon">📭</span>
            <p>暂无检测记录</p>
          </div>
          <div v-else class="record-list">
            <div class="record-item" v-for="item in latestRecordList" :key="item.id" @click="viewRecordDetail(item)">
              <div class="record-icon" :class="item.diseaseCount > 0 ? 'danger' : 'safe'">
                <span v-if="item.diseaseCount > 0">⚠️</span>
                <span v-else>✅</span>
              </div>
              <div class="record-info">
                <div class="record-name">{{ item.fileName }}</div>
                <div class="record-time">{{ item.detectTime }}</div>
              </div>
              <div class="record-tag" :class="item.diseaseCount > 0 ? 'danger' : 'safe'">
                {{ item.diseaseCount > 0 ? `${item.diseaseCount}处病害` : '无病害' }}
              </div>
            </div>
          </div>
          <el-button class="view-all-btn" text @click="$router.push('/app/history')">
            查看全部识别历史 →
          </el-button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/api/request'

// 病害类别数据
const diseaseList = [
  { name: '黑星病', en: 'Apple Scab', tag: '真菌性', tagBg: 'rgba(24,144,255,0.1)', tagColor: '#1890ff' },
  { name: '黑腐病', en: 'Black Rot', tag: '真菌性', tagBg: 'rgba(245,34,45,0.1)', tagColor: '#f5222d' },
  { name: '锈病', en: 'Cedar Apple Rust', tag: '真菌性', tagBg: 'rgba(250,173,20,0.1)', tagColor: '#faad14' },
  { name: '健康叶片', en: 'Healthy', tag: '正常', tagBg: 'rgba(82,196,26,0.1)', tagColor: '#52c41a' },
]

// 最新检测记录
const latestRecordList = ref([])

// 点击查看记录详情，跳转到历史页面
const viewRecordDetail = (item) => {
  // 保存要查看的记录ID到localStorage，历史页面会自动打开详情弹窗
  localStorage.setItem('pending-detail-id', item.id.toString())
  // 跳转到历史页面
  window.location.href = '/app/history'
}

// 加载最新记录
const loadLatestRecords = async () => {
  try {
    const res = await api.getHistoryList({ page: 1, size: 100 })
    if (res.data && res.data.records) {
      const sorted = [...res.data.records].sort((a, b) => b.id - a.id)
      latestRecordList.value = sorted.slice(0, 5).map(item => ({
        id: item.id,
        fileName: item.fileName,
        detectTime: item.detectTime,
        diseaseCount: item.diseaseCount || 0
      }))
    }
  } catch (error) {
    console.error('获取最新记录失败', error)
  }
}

onMounted(() => {
  loadLatestRecords()
})
</script>

<style scoped lang="scss">
.dashboard-container {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

// Hero 横幅
.hero-banner {
  background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 50%, #ecfdf5 100%);
  border-radius: 16px;
  padding: 36px;
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 32px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.hero-left {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 16px;

  .hero-tag {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(8px);
    border: 1px solid #e5e7eb;
    border-radius: 24px;
    padding: 8px 16px;
    font-size: 13px;
    color: #666;
    width: fit-content;
    font-weight: 500;

    .tag-icon {
      font-size: 16px;
    }
  }

  .hero-title {
    font-size: 34px;
    font-weight: 800;
    color: #1a1a1a;
    margin: 0;
    line-height: 1.2;
    letter-spacing: -0.5px;
  }

  .hero-desc {
    font-size: 15px;
    color: #666;
    line-height: 1.7;
    margin: 0;
    max-width: 480px;
  }

  .hero-actions {
    display: flex;
    gap: 12px;
    margin-top: 8px;

    .btn-primary {
      background: #16a34a;
      border-color: #16a34a;
      border-radius: 8px;
      padding: 12px 28px;
      font-weight: 600;
      transition: all 0.2s;

      &:hover {
        background: #15803d;
        border-color: #15803d;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(22, 163, 74, 0.3);
      }
    }

    .btn-default {
      border-radius: 8px;
      padding: 12px 28px;
      font-weight: 600;
      border-color: #d1d5db;
      color: #666;
      transition: all 0.2s;

      &:hover {
        border-color: #16a34a;
        color: #16a34a;
      }
    }
  }
}

// 右侧病害面板
.hero-right {
  .disease-panel {
    background: #ffffff;
    border-radius: 14px;
    padding: 22px;
    border: 1px solid #e5e7eb;
    height: 100%;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);

    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 18px;

      .panel-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 15px;
        font-weight: 700;
        color: #1a1a1a;

        .panel-icon {
          font-size: 18px;
        }
      }

      .panel-count {
        font-size: 12px;
        color: #999;
        background: #f3f4f6;
        padding: 4px 10px;
        border-radius: 12px;
      }
    }

    .disease-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;

      .disease-card {
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 14px;
        background: #fafafa;
        transition: all 0.2s;

        &:hover {
          border-color: #16a34a;
          box-shadow: 0 2px 8px rgba(22, 163, 74, 0.1);
          transform: translateY(-2px);
        }

        .disease-name {
          font-size: 14px;
          font-weight: 700;
          color: #1a1a1a;
          margin-bottom: 4px;
        }

        .disease-en {
          font-size: 11px;
          color: #999;
          margin-bottom: 8px;
        }

        .disease-tag {
          display: inline-block;
          font-size: 10px;
          padding: 2px 8px;
          border-radius: 8px;
          font-weight: 500;
        }
      }
    }
  }
}

// 统计卡片行
.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 22px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
    transform: translateY(-2px);
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    flex-shrink: 0;

    &.icon-blue {
      background: rgba(24, 144, 255, 0.1);
    }
    &.icon-green {
      background: rgba(22, 163, 74, 0.1);
    }
    &.icon-yellow {
      background: rgba(250, 173, 20, 0.1);
    }
  }

  .stat-info {
    flex: 1;

    .stat-label {
      font-size: 13px;
      color: #888;
      margin-bottom: 4px;
      font-weight: 500;
    }

    .stat-value {
      font-size: 22px;
      font-weight: 800;
      color: #1a1a1a;
      margin-bottom: 4px;
    }

    .stat-desc {
      font-size: 12px;
      color: #aaa;
    }
  }
}

// 底部区域
.bottom-section {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 20px;
  align-items: start;
}

.section-card {
  background: #ffffff;
  border-radius: 14px;
  padding: 24px;
  border: 1px solid #e5e7eb;
}

.section-title {
  font-size: 16px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 18px;
  display: flex;
  align-items: center;
  gap: 8px;

  span {
    font-size: 18px;
  }

  .record-count {
    margin-left: auto;
    font-weight: normal;
    background: #f3f4f6;
    border: none;
  }
}

// 流程步骤
.flow-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;

  .flow-step {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 16px;
    background: #fafafa;
    border-radius: 10px;
    border: 1px solid #f0f0eb;
    transition: all 0.2s;

    &:hover {
      background: #f0fdf4;
      border-color: #bbf7d0;
    }

    .step-num {
      font-size: 13px;
      font-weight: 800;
      color: #16a34a;
      min-width: 28px;
      height: 28px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(22, 163, 74, 0.1);
      border-radius: 6px;
    }

    .step-text {
      font-size: 13px;
      color: #666;
      line-height: 1.5;
    }
  }
}

// 最新记录
.empty-records {
  text-align: center;
  padding: 40px 0;

  .empty-icon {
    font-size: 48px;
    opacity: 0.5;
  }

  p {
    margin: 12px 0 0;
    font-size: 14px;
    color: #bbb;
  }
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.record-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 10px;
  background: #fafafa;
  transition: all 0.2s;

  &:hover {
    background: #f5f5f5;
  }

  .record-icon {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: 16px;

    &.danger {
      background: rgba(245, 34, 45, 0.1);
    }

    &.safe {
      background: rgba(22, 163, 74, 0.1);
    }
  }

  .record-info {
    flex: 1;
    min-width: 0;

    .record-name {
      font-size: 13px;
      color: #1a1a1a;
      margin: 0 0 2px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      font-weight: 500;
    }

    .record-time {
      font-size: 11px;
      color: #aaa;
      margin: 0;
    }
  }

  .record-tag {
    font-size: 11px;
    padding: 4px 10px;
    border-radius: 8px;
    flex-shrink: 0;
    font-weight: 500;

    &.danger {
      background: #fef2f2;
      color: #ef4444;
    }

    &.safe {
      background: #f0fdf4;
      color: #16a34a;
    }
  }
}

.view-all-btn {
  width: 100%;
  justify-content: center;
  color: #666;
  font-weight: 500;
  padding: 12px;
  border-radius: 8px;
  transition: all 0.2s;

  &:hover {
    background: #f0fdf4;
    color: #16a34a;
  }
}
</style>
