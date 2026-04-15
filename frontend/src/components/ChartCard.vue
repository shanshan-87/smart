<template>
  <div class="chart-card" :style="{ background: bgColor }">
    <div class="card-left">
      <p class="card-label">{{ label }}</p>
      <h3 class="card-value">{{ value }}</h3>
      <div class="card-trend" :class="trendType">
        <el-icon v-if="trendType === 'up'"><Top /></el-icon>
        <el-icon v-else><Bottom /></el-icon>
        <span>{{ trendValue }}</span>
      </div>
    </div>
    <div class="card-right">
      <div class="icon-box" :style="{ background: iconBg }">
        <el-icon :size="iconSize"><component :is="icon" /></el-icon>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Top, Bottom } from '@element-plus/icons-vue'

const props = defineProps({
  label: {
    type: String,
    default: '统计项'
  },
  value: {
    type: [String, Number],
    default: 0
  },
  trendType: {
    type: String,
    default: 'up', // up上升 / down下降
    validator: (value) => ['up', 'down'].includes(value)
  },
  trendValue: {
    type: String,
    default: '0%'
  },
  icon: {
    type: String,
    default: 'DataBoard'
  },
  iconSize: {
    type: Number,
    default: 24
  },
  bgColor: {
    type: String,
    default: '#ffffff'
  },
  iconBg: {
    type: String,
    default: 'rgba(24, 144, 255, 0.1)'
  }
})
</script>

<style scoped lang="scss">
.chart-card {
  width: 100%;
  padding: 20px;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 6px 16px 0 rgba(0, 0, 0, 0.12);
  }

  .card-left {
    .card-label {
      font-size: 14px;
      color: var(--text-secondary);
      margin-bottom: 8px;
    }

    .card-value {
      font-size: 28px;
      font-weight: 700;
      color: var(--text-main);
      margin-bottom: 8px;
      line-height: 1;
    }

    .card-trend {
      display: flex;
      align-items: center;
      font-size: 12px;

      &.up {
        color: var(--secondary-color);
      }

      &.down {
        color: var(--danger-color);
      }

      .el-icon {
        margin-right: 4px;
      }
    }
  }

  .card-right {
    .icon-box {
      width: 56px;
      height: 56px;
      border-radius: 12px;
      display: flex;
      justify-content: center;
      align-items: center;
      color: var(--primary-color);
    }
  }
}
</style>