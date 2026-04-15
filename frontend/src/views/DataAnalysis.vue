<template>
  <div class="analysis-container">
    <!-- 页面标签 -->
    <div class="page-tag">
      <span class="tag-icon">📊</span>
      <span>SmartOrchard · Data Analysis</span>
    </div>

    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">病害数据分析</h1>
        <p class="page-desc">多维度统计分析苹果叶片病害检测数据，洞察病害发展趋势与分布规律</p>
      </div>
      <div class="header-actions">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          @change="handleDateChange"
          class="date-picker"
        />
        <el-button type="primary" @click="refreshData" class="btn-refresh">
          <span>🔄</span>
          刷新数据
        </el-button>
      </div>
    </div>

    <!-- 核心指标卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon blue">
          <span>📊</span>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ analysisData.totalCount }}</div>
          <div class="stat-label">总检测样本</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon red">
          <span>🦠</span>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ analysisData.diseaseRate }}%</div>
          <div class="stat-label">病害样本占比</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green">
          <span>🎯</span>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ analysisData.avgAccuracy }}%</div>
          <div class="stat-label">平均识别精度</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon yellow">
          <span>🌳</span>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ analysisData.orchardCount || 0 }}</div>
          <div class="stat-label">覆盖果园数</div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-grid">
      <!-- 第一行：两个图表 -->
      <div class="chart-row">
        <!-- 病害类型分布环形图 -->
        <div class="section-card chart-card">
          <div class="card-header">
            <span class="card-icon">🍎</span>
            <h3 class="card-title">病害类型分布统计（4类）</h3>
          </div>
          <div ref="doughnutChartRef" class="chart-content"></div>
        </div>

        <!-- 病害严重程度占比 -->
        <div class="section-card chart-card">
          <div class="card-header">
            <span class="card-icon">📈</span>
            <h3 class="card-title">病害严重程度占比</h3>
          </div>
          <div ref="levelPieChartRef" class="chart-content"></div>
        </div>
      </div>

      <!-- 第二行：两个图表 -->
      <div class="chart-row">
        <!-- 月度病害趋势图 -->
        <div class="section-card chart-card">
          <div class="card-header">
            <span class="card-icon">📉</span>
            <h3 class="card-title">月度病害发生趋势</h3>
          </div>
          <div ref="trendLineChartRef" class="chart-content"></div>
        </div>

        <!-- 病害类型严重程度分布 -->
        <div class="section-card chart-card">
          <div class="card-header">
            <span class="card-icon">📊</span>
            <h3 class="card-title">各病害类型统计情况</h3>
          </div>
          <div ref="diseaseLevelChartRef" class="chart-content"></div>
        </div>
      </div>

      <!-- 第三行：全宽图表 -->
      <div class="chart-full">
        <div class="section-card chart-card">
          <div class="card-header">
            <span class="card-icon">🤖</span>
            <h3 class="card-title">YOLO系列模型性能对比</h3>
          </div>
          <div ref="modelCompareChartRef" class="chart-content-wide"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { api } from '@/api/request'

const dateRange = ref([])

// 图表DOM引用
const doughnutChartRef = ref(null)
const levelPieChartRef = ref(null)
const trendLineChartRef = ref(null)
const diseaseLevelChartRef = ref(null)
const modelCompareChartRef = ref(null)

// 图表实例
let doughnutInstance = null
let levelPieInstance = null
let trendLineInstance = null
let diseaseLevelInstance = null
let modelCompareInstance = null

// 分析统计数据
const analysisData = reactive({
  totalCount: 0,
  diseaseRate: 0,
  avgAccuracy: 0
})

// 图表数据
const chartData = reactive({
  diseaseTypeStats: [],
  diseaseLevelStats: [],
  levelStats: { 重度: 0, 健康: 0 },
  monthlyStats: []
})

// 病害类型颜色
const diseaseColors = {
  '黑星病': '#1890ff',
  '黑腐病': '#52c41a',
  '锈病': '#faad14',
  '健康叶片': '#13c2c2'
}

// 加载统计数据
const loadStatistics = async () => {
  try {
    const params = {
      start_date: dateRange.value?.[0] || undefined,
      end_date: dateRange.value?.[1] || undefined
    }
    const res = await api.getStatisticsData(params)
    if (res.data) {
      analysisData.totalCount = res.data.totalCount || 0
      analysisData.diseaseRate = res.data.diseaseRate || 0
      analysisData.avgAccuracy = res.data.accuracy || 0
    }
  } catch (error) {
    console.error('获取统计数据失败', error)
  }
}

// 加载图表数据
const loadChartData = async () => {
  try {
    const params = {
      start_date: dateRange.value?.[0] || undefined,
      end_date: dateRange.value?.[1] || undefined
    }
    const res = await api.getChartStatistics(params)
    if (res.data) {
      chartData.diseaseTypeStats = res.data.diseaseTypeStats || []
      chartData.diseaseLevelStats = res.data.diseaseLevelStats || []
      chartData.levelStats = res.data.levelStats || { 重度: 0, 健康: 0 }
      chartData.monthlyStats = res.data.monthlyStats || []
      updateAllCharts()
    }
  } catch (error) {
    console.error('获取图表数据失败', error)
  }
}

// 更新所有图表
const updateAllCharts = () => {
  updateDoughnutChart()
  updateLevelPieChart()
  updateTrendLineChart()
  updateDiseaseLevelChart()
}

// 更新病害类型环形图
const updateDoughnutChart = () => {
  if (!doughnutInstance) return
  const diseaseData = chartData.diseaseTypeStats.map(item => ({
    name: item.name,
    value: item.count || 0,
    itemStyle: { color: diseaseColors[item.name] || '#1890ff' }
  }))
  const hasData = diseaseData.some(d => d.value > 0)
  doughnutInstance.setOption({
    series: [{
      data: hasData ? diseaseData : [{ name: '暂无数据', value: 1, itemStyle: { color: '#d9d9d9' } }]
    }]
  })
}

// 更新严重程度饼图
const updateLevelPieChart = () => {
  if (!levelPieInstance) return
  const levelData = [
    { name: '健康', value: chartData.levelStats['健康'] || 0, itemStyle: { color: '#52c41a' } },
    { name: '重度', value: chartData.levelStats['重度'] || 0, itemStyle: { color: '#f5222d' } }
  ]
  const filtered = levelData.filter(item => item.value > 0)
  levelPieInstance.setOption({
    series: [{
      data: filtered.length > 0 ? filtered : [{ name: '暂无数据', value: 1, itemStyle: { color: '#d9d9d9' } }]
    }]
  })
}

// 更新月度趋势图
const updateTrendLineChart = () => {
  if (!trendLineInstance) return
  trendLineInstance.setOption({
    xAxis: { data: chartData.monthlyStats.map(item => item.month) },
    series: [
      { name: '总检测数', data: chartData.monthlyStats.map(item => item.total || 0) },
      { name: '病害数', data: chartData.monthlyStats.map(item => item.disease || 0) }
    ]
  })
}

// 更新病害类型严重程度分布图
const updateDiseaseLevelChart = () => {
  if (!diseaseLevelInstance) return
  // 颜色数组：蓝、紫、红
  const colors = ['#1890ff', '#722ed1', '#f5222d']
  
  // 获取每种病害的数量
  const scabCount = chartData.diseaseLevelStats.find(s => s.disease === '黑星病')?.['重度'] || 0
  const rotCount = chartData.diseaseLevelStats.find(s => s.disease === '黑腐病')?.['重度'] || 0
  const rustCount = chartData.diseaseLevelStats.find(s => s.disease === '锈病')?.['重度'] || 0
  
  diseaseLevelInstance.setOption({
    xAxis: { data: ['黑星病', '黑腐病', '锈病'] },
    series: [{
      name: '发病数量',
      type: 'bar',
      data: [
        { value: scabCount, itemStyle: { color: colors[0] } },
        { value: rotCount, itemStyle: { color: colors[1] } },
        { value: rustCount, itemStyle: { color: colors[2] } }
      ],
      barMaxWidth: 80,
      label: { show: true, position: 'top' }
    }]
  })
}

// 初始化环形图
const initDoughnutChart = () => {
  if (!doughnutChartRef.value) return
  doughnutInstance = echarts.init(doughnutChartRef.value)
  doughnutInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}个样本 ({d}%)' },
    legend: { orient: 'vertical', left: 'left', top: 'center' },
    series: [{
      name: '病害类型',
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['65%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}: {d}%' },
      emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
      data: [{ name: '加载中...', value: 1, itemStyle: { color: '#e8e8e8' } }]
    }]
  })
}

// 初始化饼图
const initLevelPieChart = () => {
  if (!levelPieChartRef.value) return
  levelPieInstance = echarts.init(levelPieChartRef.value)
  levelPieInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      name: '严重程度',
      type: 'pie',
      radius: '70%',
      itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
      data: [{ name: '加载中...', value: 1, itemStyle: { color: '#e8e8e8' } }]
    }]
  })
}

// 初始化趋势图
const initTrendLineChart = () => {
  if (!trendLineChartRef.value) return
  trendLineInstance = echarts.init(trendLineChartRef.value)
  trendLineInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['总检测数', '病害数'], top: 0 },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: [] },
    yAxis: { type: 'value', name: '数量' },
    series: [
      {
        name: '总检测数', type: 'line', smooth: true, data: [],
        lineStyle: { width: 3, color: '#16a34a' },
        itemStyle: { color: '#16a34a' },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(22,163,74,0.3)' },
          { offset: 1, color: 'rgba(22,163,74,0.05)' }
        ])}
      },
      {
        name: '病害数', type: 'line', smooth: true, data: [],
        lineStyle: { width: 3, color: '#f5222d' },
        itemStyle: { color: '#f5222d' },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(245,34,45,0.3)' },
          { offset: 1, color: 'rgba(245,34,45,0.05)' }
        ])}
      }
    ]
  })
}

// 初始化病害严重程度分布图
const initDiseaseLevelChart = () => {
  if (!diseaseLevelChartRef.value) return
  diseaseLevelInstance = echarts.init(diseaseLevelChartRef.value)
  diseaseLevelInstance.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { show: false },
    grid: { left: '10%', right: '10%', bottom: '10%', containLabel: true },
    xAxis: { type: 'category', data: ['黑星病', '黑腐病', '锈病'] },
    yAxis: { type: 'value', name: '数量' },
    series: [{
      name: '发病数量',
      type: 'bar',
      data: [],
      barMaxWidth: 80,
      label: { show: true, position: 'top' }
    }]
  })
}

// 初始化模型对比图
const initModelCompareChart = () => {
  if (!modelCompareChartRef.value) return
  modelCompareInstance = echarts.init(modelCompareChartRef.value)
  modelCompareInstance.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: function(params) {
        let result = params[0].axisValue + '<br/>'
        params.forEach(item => {
          const unit = item.seriesName === '参数量(MB)' ? 'MB' : (item.seriesName === '检测速度(FPS)' ? 'FPS' : '%')
          result += item.marker + item.seriesName + ': ' + item.value + unit + '<br/>'
        })
        return result
      }
    },
    legend: { data: ['mAP@0.5(%)', '检测速度(FPS)', '参数量(MB)'], top: 0 },
    grid: { left: '3%', right: '60px', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: ['YOLOv5n', 'YOLOv8n', 'YOLOv10n', 'YOLOv11n', 'YOLOv13'] },
    yAxis: [
      { type: 'value', name: 'mAP@0.5 / FPS', position: 'left', min: 0, max: 120 },
      { type: 'value', name: '参数量(MB)', position: 'right', min: 0, max: 10 }
    ],
    series: [
      {
        name: 'mAP@0.5(%)',
        type: 'bar', yAxisIndex: 0,
        data: [28.0, 37.3, 38.5, 39.5, 96.8],
        itemStyle: { color: '#16a34a', borderRadius: [4, 4, 0, 0] }, barMaxWidth: 40
      },
      {
        name: '检测速度(FPS)',
        type: 'bar', yAxisIndex: 0,
        data: [45, 80, 112, 100, 85],
        itemStyle: { color: '#1890ff', borderRadius: [4, 4, 0, 0] }, barMaxWidth: 40
      },
      {
        name: '参数量(MB)',
        type: 'line', yAxisIndex: 1,
        data: [1.9, 3.2, 2.3, 2.6, 5.8],
        lineStyle: { width: 3, color: '#f5222d' },
        itemStyle: { color: '#f5222d' },
        symbol: 'circle', symbolSize: 8
      }
    ]
  })
}

// 日期变化回调
const handleDateChange = () => {
  loadStatistics()
  loadChartData()
}

// 刷新数据
const refreshData = () => {
  loadStatistics()
  loadChartData()
  ElMessage.success('数据刷新成功')
}

// 窗口大小变化重绘
const resizeCharts = () => {
  doughnutInstance?.resize()
  levelPieInstance?.resize()
  trendLineInstance?.resize()
  diseaseLevelInstance?.resize()
  modelCompareInstance?.resize()
}

onMounted(async () => {
  initDoughnutChart()
  initLevelPieChart()
  initTrendLineChart()
  initDiseaseLevelChart()
  initModelCompareChart()
  await Promise.all([loadStatistics(), loadChartData()])
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts)
  doughnutInstance?.dispose()
  levelPieInstance?.dispose()
  trendLineInstance?.dispose()
  diseaseLevelInstance?.dispose()
  modelCompareInstance?.dispose()
})
</script>

<style scoped lang="scss">
.analysis-container {
  padding: 24px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
  border: 1px solid #e5e7eb;
  border-radius: 24px;
  padding: 8px 16px;
  font-size: 13px;
  color: #666;
  font-weight: 500;
  margin-bottom: 16px;
  .tag-icon { font-size: 16px; }
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;

  .header-left {
    .page-title {
      font-size: 28px;
      font-weight: 800;
      color: #1a1a1a;
      margin: 0 0 8px;
      letter-spacing: -0.5px;
    }
    .page-desc {
      font-size: 14px;
      color: #666;
      margin: 0;
    }
  }

  .header-actions {
    display: flex;
    gap: 12px;
    align-items: center;

    .date-picker {
      border-radius: 8px;
    }

    .btn-refresh {
      display: flex;
      align-items: center;
      gap: 6px;
      background: #16a34a;
      border-color: #16a34a;
      border-radius: 8px;
      font-weight: 500;
      padding: 10px 18px;
      transition: all 0.2s;

      &:hover {
        background: #15803d;
        border-color: #15803d;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(22, 163, 74, 0.3);
      }
    }
  }
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;

  .stat-card {
    background: #ffffff;
    border-radius: 14px;
    padding: 22px;
    display: flex;
    align-items: center;
    gap: 16px;
    border: 1px solid #e5e7eb;
    transition: all 0.2s;

    &:hover {
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
      transform: translateY(-2px);
    }

    .stat-icon {
      width: 52px;
      height: 52px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      flex-shrink: 0;

      &.blue { background: rgba(24, 144, 255, 0.1); }
      &.red { background: rgba(239, 68, 68, 0.1); }
      &.green { background: rgba(22, 163, 74, 0.1); }
      &.yellow { background: rgba(245, 158, 11, 0.1); }
    }

    .stat-info {
      .stat-value {
        font-size: 26px;
        font-weight: 800;
        color: #1a1a1a;
        line-height: 1.2;
      }
      .stat-label {
        font-size: 13px;
        color: #888;
        margin-top: 4px;
      }
    }
  }
}

.section-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 24px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.03);
}

.charts-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.chart-card {
  .card-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
    padding-bottom: 14px;
    border-bottom: 1px solid #f0f0eb;

    .card-icon { font-size: 20px; }

    .card-title {
      font-size: 16px;
      font-weight: 700;
      color: #1a1a1a;
      margin: 0;
    }
  }

  .chart-content {
    width: 100%;
    height: 300px;
  }

  .chart-content-wide {
    width: 100%;
    height: 320px;
  }
}

.chart-full {
  width: 100%;
}
</style>
