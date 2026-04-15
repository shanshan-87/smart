<template>
  <div class="history-container">
    <!-- 页面标签 -->
    <div class="page-tag">
      <span class="tag-icon">📋</span>
      <span>SmartOrchard · Detection Records</span>
    </div>

    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">历史检测数据</h1>
        <p class="page-desc">管理所有苹果叶片病害检测记录，支持查看详情、下载报告、数据导出</p>
      </div>
      <div class="header-actions">
        <el-button @click="handleExport" class="btn-export">
          <span>📤</span>
          导出数据
        </el-button>
        <el-button type="danger" @click="batchDelete" :disabled="selectedList.length === 0" class="btn-delete">
          <span>🗑️</span>
          批量删除
          <el-badge :value="selectedList.length" class="delete-badge" v-if="selectedList.length > 0" />
        </el-button>
      </div>
    </div>

    <!-- 筛选区域 -->
    <div class="section-card filter-card">
      <div class="filter-header">
        <span class="filter-icon">🔍</span>
        <span class="filter-title">数据筛选</span>
      </div>
      <div class="filter-form">
        <div class="filter-group">
          <label class="filter-label">病害类型</label>
          <el-select v-model="filterForm.diseaseType" placeholder="请选择病害类型" clearable class="filter-select">
            <el-option label="全部类型" value="" />
            <el-option label="黑星病 Apple Scab" value="黑星病" />
            <el-option label="黑腐病 Black Rot" value="黑腐病" />
            <el-option label="锈病 Cedar Apple Rust" value="锈病" />
            <el-option label="健康叶片 Healthy" value="健康叶片" />
          </el-select>
        </div>
        <div class="filter-group">
          <label class="filter-label">严重程度</label>
          <el-select v-model="filterForm.level" placeholder="请选择严重程度" clearable class="filter-select">
            <el-option label="全部程度" value="" />
            <el-option label="重度" value="重度" />
            <el-option label="健康" value="健康" />
          </el-select>
        </div>
        <div class="filter-group">
          <label class="filter-label">检测时间</label>
          <el-date-picker
            v-model="filterForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            class="filter-date"
          />
        </div>
        <div class="filter-actions">
          <el-button type="primary" @click="handleFilter" class="btn-search">
            <span>🔍</span>
            查询
          </el-button>
          <el-button @click="resetFilter" class="btn-reset">
            <span>🔄</span>
            重置
          </el-button>
        </div>
      </div>
    </div>

    <!-- 数据统计概览 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon blue">
          <span>📊</span>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ statsData.totalCount }}</div>
          <div class="stat-label">检测记录总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green">
          <span>🌿</span>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ statsData.healthyCount }}</div>
          <div class="stat-label">健康叶片数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon red">
          <span>🦠</span>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ statsData.diseaseCount }}</div>
          <div class="stat-label">病害检测数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon yellow">
          <span>⚡</span>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ statsData.avgDuration }}ms</div>
          <div class="stat-label">平均检测耗时</div>
        </div>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="section-card table-card">
        <div class="table-header">
        <div class="table-title">
          <span class="table-icon">📋</span>
          <span>检测记录列表</span>
        </div>
        <div class="table-actions">
          <div class="table-info" v-if="tableData.length > 0">
            <span>共 {{ pagination.total }} 条记录</span>
          </div>
          <el-button-group class="sort-btn">
            <el-button :type="sortOrder === 'desc' ? 'primary' : ''" @click="setSortOrder('desc')">
              🔽 降序
            </el-button>
            <el-button :type="sortOrder === 'asc' ? 'primary' : ''" @click="setSortOrder('asc')">
              🔼 升序
            </el-button>
          </el-button-group>
        </div>
      </div>
      <el-table
        :data="tableData"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        stripe
        class="data-table"
      >
        <el-table-column type="selection" width="50" align="center" />
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="fileName" label="文件名" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="file-name-cell">
              <span class="file-icon">📄</span>
              <span class="file-name">{{ row.fileName }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="检测图像" width="100" align="center">
          <template #default="{ row }">
            <el-image
              :src="row.resultImageUrl"
              fit="cover"
              class="table-image"
              :preview-src-list="[row.resultImageUrl]"
            />
          </template>
        </el-table-column>
        <el-table-column prop="diseaseCount" label="病害数量" width="110" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.diseaseCount > 0" type="danger" class="disease-tag">
              {{ row.diseaseCount }} 处
            </el-tag>
            <el-tag v-else type="success" class="disease-tag">
              🌿 健康
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="diseaseType" label="病害类型" width="120" align="center">
          <template #default="{ row }">
            <span class="disease-type">{{ row.diseaseType || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="level" label="严重程度" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.level)" size="small" class="level-tag">
              {{ row.level || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="confidence" label="置信度" width="100" align="center">
          <template #default="{ row }">
            <div class="confidence-cell" v-if="row.confidence">
              <span class="confidence-value">{{ (row.confidence * 100).toFixed(1) }}%</span>
              <div class="confidence-bar">
                <div class="confidence-fill" :style="{ width: (row.confidence * 100) + '%' }"></div>
              </div>
            </div>
            <span v-else class="no-data">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="检测耗时" width="100" align="center">
          <template #default="{ row }">
            <span class="duration-value">{{ row.duration || 0 }}ms</span>
          </template>
        </el-table-column>
        <el-table-column prop="detectTime" label="检测时间" width="160" align="center">
          <template #default="{ row }">
            <span class="time-value">{{ row.detectTime || '-' }}</span>
          </template>
        </el-table-column>
        <!-- 来源用户列：仅当存在sourceUserId时显示（管理员查看备份记录时） -->
        <el-table-column v-if="hasBackupRecords" prop="sourceUserName" label="来源用户" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.sourceUserName" type="warning" size="small">
              <span>👤</span> {{ row.sourceUserName }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button size="small" @click="viewDetail(row)" class="btn-view">
                <span>👁️</span>
                详情
              </el-button>
              <el-button type="primary" size="small" @click="downloadReport(row)" class="btn-download">
                <span>📥</span>
                下载
              </el-button>
              <el-button type="danger" size="small" @click="handleDelete(row)" class="btn-remove">
                <span>🗑️</span>
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageChange"
          @current-change="handlePageChange"
          class="custom-pagination"
        />
      </div>
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailDialogVisible" title="检测详情" width="900px" class="detail-dialog">
      <div v-if="currentDetail" class="detail-content">
        <div class="detail-header">
          <span class="detail-icon">🔍</span>
          <div class="detail-title">
            <span class="title">检测详情</span>
            <span class="subtitle">{{ currentDetail.fileName }}</span>
          </div>
        </div>
        <div class="detail-image-box">
          <img :src="currentDetail.resultImageUrl" alt="检测结果" class="detail-image" />
        </div>
        <div class="detail-meta">
          <div class="meta-item">
            <span class="meta-icon">📄</span>
            <span class="meta-label">文件名</span>
            <span class="meta-value">{{ currentDetail.fileName }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-icon">⏱️</span>
            <span class="meta-label">检测耗时</span>
            <span class="meta-value">{{ currentDetail.duration }}ms</span>
          </div>
          <div class="meta-item">
            <span class="meta-icon">🕐</span>
            <span class="meta-label">检测时间</span>
            <span class="meta-value">{{ currentDetail.detectTime }}</span>
          </div>
          <div class="meta-item highlight">
            <span class="meta-icon">🦠</span>
            <span class="meta-label">病害数量</span>
            <el-tag type="danger" size="large">{{ currentDetail.diseaseCount }} 处</el-tag>
          </div>
        </div>
        <div class="detail-disease" v-if="currentDetail.diseaseList && currentDetail.diseaseList.length > 0">
          <h4 class="disease-title">
            <span>📋</span>
            病害详情列表
          </h4>
          <el-table :data="currentDetail.diseaseList" stripe class="disease-table">
            <el-table-column prop="className" label="病害类别" width="160" />
            <el-table-column prop="confidence" label="置信度" width="120">
              <template #default="{ row }">
                <div class="conf-progress">
                  <span class="conf-value">{{ (row.confidence * 100).toFixed(1) }}%</span>
                  <el-progress :percentage="(row.confidence * 100)" :show-text="false" :stroke-width="6" />
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="level" label="严重程度" width="100">
              <template #default="{ row }">
                <el-tag :type="getLevelType(row.level)" size="small">{{ row.level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="suggestion" label="防治建议" />
          </el-table>
        </div>
        <div class="detail-empty" v-else>
          <span class="empty-icon">🌿</span>
          <p>未检测到病害，叶片健康</p>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false" class="btn-cancel">关闭</el-button>
        <el-button type="primary" @click="downloadReport(currentDetail)" class="btn-confirm">
          <span>📥</span>
          下载检测报告
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api/request'

const loading = ref(false)
const detailDialogVisible = ref(false)
const currentDetail = ref(null)
const selectedList = ref([])

// 是否有备份记录（用于显示来源用户列）
const hasBackupRecords = ref(false)

// 检查是否有备份记录
const checkBackupRecords = (records) => {
  hasBackupRecords.value = records.some(record => record.sourceUserId)
}

// 检查是否有待查看的详情记录ID（从Dashboard跳转过来）
const checkPendingDetail = () => {
  const pendingId = localStorage.getItem('pending-detail-id')
  if (pendingId) {
    localStorage.removeItem('pending-detail-id')
    const id = parseInt(pendingId)
    // 查找对应的记录并打开详情
    const record = tableData.value.find(r => r.id === id)
    if (record) {
      viewDetail(record)
    } else {
      // 如果当前页没有，尝试从API获取
      fetchDetailAndOpen(id)
    }
  }
}

// 从API获取详情并打开
const fetchDetailAndOpen = async (recordId) => {
  try {
    const res = await api.getHistoryDetail(parseInt(recordId))
    if (res.data) {
      currentDetail.value = {
        ...res.data,
        imageUrl: res.data.imageUrl ? 'http://127.0.0.1:8000' + res.data.imageUrl : '',
        resultImageUrl: res.data.resultImageUrl ? 'http://127.0.0.1:8000' + res.data.resultImageUrl : ''
      }
      detailDialogVisible.value = true
    }
  } catch (error) {
    console.error('获取详情失败', error)
  }
}

// 筛选表单
const filterForm = reactive({
  diseaseType: '',
  level: '',
  dateRange: []
})

// 分页配置
const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

// 表格数据
const tableData = ref([])

// 统计数据（基于全部筛选数据）
const statsData = reactive({
  totalCount: 0,
  healthyCount: 0,
  diseaseCount: 0,
  avgDuration: 0
})

// 排序方式
const sortOrder = ref('desc')

// 设置排序方式
const setSortOrder = (order) => {
  sortOrder.value = order
  pagination.currentPage = 1
  getTableData()
}

// 数据库维护定时器（每5分钟整理一次ID）
let maintainTimer = null
const startMaintainTimer = () => {
  // 页面加载时先执行一次
  runDatabaseMaintain()
  // 每5分钟执行一次
  maintainTimer = setInterval(() => {
    runDatabaseMaintain()
  }, 5 * 60 * 1000) // 5分钟
}

// 执行数据库维护
const runDatabaseMaintain = async () => {
  try {
    const res = await api.maintainDatabase()
    if (res.code === 200 && res.data && res.data.updated > 0) {
      console.log(`数据库维护完成，更新了 ${res.data.updated} 条记录`)
      // 维护完成后刷新列表
      getTableData()
    }
  } catch (error) {
    // 忽略维护错误（可能是权限问题或没有数据）
    // console.error('数据库维护失败', error)
  }
}

// 获取统计数据（使用后端专门的统计接口）
const loadStatsData = async () => {
  try {
    const params = {
      start_date: filterForm.dateRange?.[0] || undefined,
      end_date: filterForm.dateRange?.[1] || undefined
    }
    const res = await api.getStatisticsData(params)
    const data = res.data || {}

    // 直接使用后端返回的统计数据
    statsData.totalCount = data.totalCount || 0
    statsData.diseaseCount = data.diseaseCount || 0
    statsData.healthyCount = data.healthyCount || 0

    // 平均耗时需要单独从历史记录获取
    const listParams = {
      page: 1,
      size: 10000,
      disease_type: filterForm.diseaseType || undefined,
      level: filterForm.level || undefined,
      start_date: filterForm.dateRange?.[0] || undefined,
      end_date: filterForm.dateRange?.[1] || undefined
    }
    const listRes = await api.getHistoryList(listParams)
    const allRecords = listRes.data?.records || []

    // 计算平均耗时
    if (allRecords.length > 0) {
      const totalDuration = allRecords.reduce((sum, item) => sum + (item.duration || 0), 0)
      statsData.avgDuration = Math.round(totalDuration / allRecords.length)
    } else {
      statsData.avgDuration = 0
    }
  } catch (error) {
    console.error('获取统计数据失败', error)
  }
}


// 严重程度标签类型
const getLevelType = (level) => {
  const typeMap = { '健康': 'success', '重度': 'danger' }
  return typeMap[level] || 'info'
}

// 表格多选
const handleSelectionChange = (selection) => {
  selectedList.value = selection
}

// 筛选查询
const handleFilter = () => {
  pagination.currentPage = 1
  getTableData()
  loadStatsData()
}

// 重置筛选
const resetFilter = () => {
  Object.keys(filterForm).forEach(key => {
    filterForm[key] = key === 'dateRange' ? [] : ''
  })
  pagination.currentPage = 1
  getTableData()
  loadStatsData()
}

// 分页变化
const handlePageChange = () => {
  getTableData()
}

// 获取表格数据
const getTableData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.currentPage,
      size: pagination.pageSize,
      disease_type: filterForm.diseaseType || undefined,
      level: filterForm.level || undefined,
      start_date: filterForm.dateRange?.[0] || undefined,
      end_date: filterForm.dateRange?.[1] || undefined,
      sort_order: sortOrder.value
    }
    const res = await api.getHistoryList(params)
    tableData.value = (res.data?.records || []).map(item => ({
      ...item,
      imageUrl: item.imageUrl ? 'http://127.0.0.1:8000' + item.imageUrl : '',
      resultImageUrl: item.resultImageUrl ? 'http://127.0.0.1:8000' + item.resultImageUrl : ''
    }))
    pagination.total = res.data?.total || 0

    // 检查是否有备份记录（用于显示来源用户列）
    checkBackupRecords(res.data?.records || [])

    // 检查是否有待查看的详情记录（从Dashboard跳转过来）
    checkPendingDetail()
  } catch (error) {
    console.error('获取数据失败', error)
  } finally {
    loading.value = false
  }
}

// 查看详情
const viewDetail = async (row) => {
  try {
    const res = await api.getHistoryDetail(row.id)
    currentDetail.value = {
      ...row,
      ...res.data,
      imageUrl: row.imageUrl || (res.data.imageUrl ? 'http://127.0.0.1:8000' + res.data.imageUrl : ''),
      resultImageUrl: row.resultImageUrl || (res.data.resultImageUrl ? 'http://127.0.0.1:8000' + res.data.resultImageUrl : '')
    }
    detailDialogVisible.value = true
  } catch (error) {
    console.error('获取详情失败', error)
    ElMessage.error('获取详情失败')
  }
}

// 下载报告
const downloadReport = async (row) => {
  try {
    ElMessage.info('正在生成检测报告...')
    
    // 获取完整详情（包含diseaseList）
    const detailRes = await api.getHistoryDetail(row.id)
    const detail = detailRes.data || {}
    
    const reportData = {
      file_name: detail.fileName || row.fileName || '未知文件',
      detect_time: detail.detectTime || row.detectTime || '',
      duration: detail.duration || row.duration || 0,
      disease_count: detail.diseaseCount || row.diseaseCount || 0,
      disease_list: detail.diseaseList || [],
      result_image_url: (detail.resultImageUrl || row.resultImageUrl || '').replace('http://127.0.0.1:8000', '')
    }
    const blob = await api.downloadReport(reportData)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `病害检测报告_${row.fileName || Date.now()}.html`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    ElMessage.success('报告下载成功！')
  } catch (error) {
    console.error('下载失败', error)
    ElMessage.error('下载失败，请确保后端已启动')
  }
}

// 单条删除
const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除「${row.fileName}」的检测记录吗？删除后无法恢复！`, '警告', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await api.deleteHistory(row.id)
      tableData.value = tableData.value.filter(item => item.id !== row.id)
      pagination.total = Math.max(0, pagination.total - 1)
      ElMessage.success('删除成功')
      loadStatsData()
    } catch (error) {
      console.error('删除失败', error)
      ElMessage.error('删除失败')
    }
  })
}

// 批量删除
const batchDelete = () => {
  if (selectedList.value.length === 0) {
    ElMessage.warning('请先选择要删除的记录')
    return
  }
  ElMessageBox.confirm(`确定要删除选中的 ${selectedList.value.length} 条记录吗？删除后无法恢复！`, '警告', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const ids = selectedList.value.map(item => item.id)
      await Promise.all(ids.map(id => api.deleteHistory(id)))
      tableData.value = tableData.value.filter(item => !ids.includes(item.id))
      pagination.total = Math.max(0, pagination.total - ids.length)
      selectedList.value = []
      ElMessage.success('批量删除成功')
      loadStatsData()
    } catch (error) {
      console.error('批量删除失败', error)
      ElMessage.error('批量删除失败')
    }
  })
}

// 导出数据
const handleExport = async () => {
  try {
    ElMessage.info('正在导出，请稍候...')
    const params = {
      disease_type: filterForm.diseaseType || undefined,
      level: filterForm.level || undefined,
      start_date: filterForm.dateRange?.[0] || undefined,
      end_date: filterForm.dateRange?.[1] || undefined
    }
    const blob = await api.exportHistory(params)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `病害检测记录_${new Date().toLocaleDateString().replace(/\//g, '-')}.csv`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    ElMessage.success('导出成功！')
  } catch (error) {
    console.error('导出失败', error)
    ElMessage.error('导出失败，请确保后端已启动')
  }
}

onMounted(() => {
  getTableData()
  loadStatsData()
  startMaintainTimer()  // 启动数据库维护定时器
})

// 组件卸载时清除定时器
onUnmounted(() => {
  if (maintainTimer) {
    clearInterval(maintainTimer)
    maintainTimer = null
  }
})
</script>

<style scoped lang="scss">
.history-container {
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

    .btn-export, .btn-delete {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 10px 18px;
      border-radius: 8px;
      font-weight: 500;
      transition: all 0.2s;
    }

    .btn-export:hover {
      border-color: #16a34a;
      color: #16a34a;
    }

    .btn-delete {
      position: relative;
      &:hover {
        background: #fef2f2;
        border-color: #ef4444;
        color: #ef4444;
      }
    }

    .delete-badge {
      position: absolute;
      top: -8px;
      right: -8px;
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

.filter-card {
  margin-bottom: 20px;

  .filter-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 18px;
    padding-bottom: 14px;
    border-bottom: 1px solid #f0f0eb;

    .filter-icon { font-size: 18px; }
    .filter-title {
      font-size: 15px;
      font-weight: 700;
      color: #1a1a1a;
    }
  }

  .filter-form {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    align-items: flex-end;

    .filter-group {
      display: flex;
      flex-direction: column;
      gap: 6px;

      .filter-label {
        font-size: 13px;
        color: #666;
        font-weight: 500;
      }

      .filter-select { width: 180px; }
      .filter-date { width: 280px; }
    }

    .filter-actions {
      display: flex;
      gap: 10px;

      .btn-search {
        display: flex;
        align-items: center;
        gap: 6px;
        background: #16a34a;
        border-color: #16a34a;
        &:hover {
          background: #15803d;
          border-color: #15803d;
        }
      }

      .btn-reset {
        display: flex;
        align-items: center;
        gap: 6px;
      }
    }
  }
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;

  .stat-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 18px;
    display: flex;
    align-items: center;
    gap: 14px;
    border: 1px solid #e5e7eb;
    transition: all 0.2s;

    &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
      transform: translateY(-2px);
    }

    .stat-icon {
      width: 44px;
      height: 44px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      flex-shrink: 0;

      &.blue { background: rgba(24, 144, 255, 0.1); }
      &.green { background: rgba(22, 163, 74, 0.1); }
      &.red { background: rgba(239, 68, 68, 0.1); }
      &.yellow { background: rgba(245, 158, 11, 0.1); }
    }

    .stat-info {
      .stat-value {
        font-size: 22px;
        font-weight: 800;
        color: #1a1a1a;
      }
      .stat-label {
        font-size: 12px;
        color: #888;
        margin-top: 2px;
      }
    }
  }
}

.table-card {
  .table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
    padding-bottom: 14px;
    border-bottom: 1px solid #f0f0eb;

    .table-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 15px;
      font-weight: 700;
      color: #1a1a1a;
      .table-icon { font-size: 18px; }
    }

    .table-actions {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .table-info {
      font-size: 13px;
      color: #888;
    }

    .sort-btn {
      .el-button {
        padding: 6px 12px;
        font-size: 12px;
      }
    }
  }

  .file-name-cell {
    display: flex;
    align-items: center;
    gap: 8px;
    .file-icon { font-size: 16px; }
    .file-name { font-size: 13px; color: #1a1a1a; }
  }

  .table-image {
    width: 60px;
    height: 40px;
    border-radius: 6px;
    object-fit: cover;
    border: 1px solid #e5e7eb;
  }

  .confidence-cell {
    .confidence-value {
      font-size: 13px;
      font-weight: 600;
      color: #1a1a1a;
      display: block;
      margin-bottom: 4px;
    }
    .confidence-bar {
      width: 60px;
      height: 4px;
      background: #f0f0eb;
      border-radius: 2px;
      overflow: hidden;
      .confidence-fill {
        height: 100%;
        background: linear-gradient(90deg, #16a34a, #52c41a);
        border-radius: 2px;
      }
    }
  }

  .action-btns {
    display: flex;
    gap: 6px;
    .btn-view, .btn-download, .btn-remove {
      display: flex;
      align-items: center;
      justify-content: center;
      min-width: 32px;
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 12px;
      transition: all 0.2s;
    }
    .btn-remove:hover {
      background: #fef2f2;
      color: #ef4444;
    }
  }
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  .custom-pagination :deep(.el-pager li) {
    border-radius: 6px;
    &.is-active { background: #16a34a; }
  }
}

.detail-dialog {
  .detail-content {
    .detail-header {
      display: flex;
      align-items: center;
      gap: 14px;
      margin-bottom: 20px;
      padding: 16px;
      background: #f0fdf4;
      border-radius: 12px;
      .detail-icon { font-size: 28px; }
      .detail-title {
        .title {
          display: block;
          font-size: 18px;
          font-weight: 700;
          color: #1a1a1a;
        }
        .subtitle { font-size: 13px; color: #666; }
      }
    }

    .detail-image-box {
      width: 100%;
      text-align: center;
      margin-bottom: 20px;
      .detail-image {
        max-width: 100%;
        max-height: 350px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
      }
    }

    .detail-meta {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin-bottom: 20px;

      .meta-item {
        display: flex;
        flex-direction: column;
        gap: 6px;
        padding: 14px;
        background: #fafafa;
        border-radius: 10px;
        text-align: center;
        &.highlight { background: #fef2f2; }
        .meta-icon { font-size: 18px; }
        .meta-label { font-size: 11px; color: #888; }
        .meta-value { font-size: 14px; font-weight: 600; color: #1a1a1a; }
      }
    }

    .detail-disease {
      .disease-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 15px;
        font-weight: 700;
        color: #1a1a1a;
        margin: 0 0 14px;
      }
      .conf-progress {
        display: flex;
        flex-direction: column;
        gap: 4px;
        .conf-value { font-size: 13px; font-weight: 600; }
      }
    }

    .detail-empty {
      text-align: center;
      padding: 40px;
      background: #f0fdf4;
      border-radius: 12px;
      .empty-icon { font-size: 48px; }
      p { margin: 12px 0 0; font-size: 14px; color: #16a34a; }
    }
  }

  :deep(.el-dialog__footer) {
    .btn-cancel { border-radius: 8px; }
    .btn-confirm {
      display: flex;
      align-items: center;
      gap: 6px;
      background: #16a34a;
      border-color: #16a34a;
      border-radius: 8px;
      &:hover { background: #15803d; border-color: #15803d; }
    }
  }
}
</style>
