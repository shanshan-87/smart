<template>
  <div class="detect-container">
    <!-- 页面标签 -->
    <div class="page-tag">
      <span class="tag-icon">🔍</span>
      <span>SmartOrchard · AI Disease Detection</span>
    </div>

    <div class="page-header">
      <h1 class="page-title">苹果叶片病害检测</h1>
      <p class="page-desc">
        上传苹果叶片图像后，系统将基于深度学习模型输出类别预测与置信度分布。建议使用主体清晰、背景干净的样本图，以获得更稳定的识别结果。
      </p>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧上传区域 -->
      <div class="left-section">
        <div class="section-card upload-card">
          <div class="card-header">
            <span class="card-icon">📤</span>
            <h3 class="card-title">图像上传</h3>
          </div>

          <el-tabs v-model="activeTab" type="border-card" class="detect-tabs">
            <!-- 单张检测 -->
            <el-tab-pane label="单张检测" name="single">
              <el-upload
                ref="singleUploadRef"
                class="single-uploader"
                action="#"
                :show-file-list="false"
                :auto-upload="false"
                :on-change="handleSingleFileChange"
                accept="image/jpg,image/jpeg,image/png,image/bmp"
              >
                <div v-if="!singleImageUrl" class="upload-empty">
                  <span class="upload-icon">🖼️</span>
                  <p class="upload-text">点击上传苹果叶片图像</p>
                  <span class="upload-hint">支持 JPG/PNG/JPEG/BMP 格式</span>
                </div>
                <img v-else :src="singleImageUrl" class="upload-image" alt="上传的叶片图像" />
              </el-upload>

              <div class="upload-status" v-if="singleImageUrl">
                <div class="status-item success">
                  <span>✅</span>
                  <span>图像上传成功</span>
                </div>
                <div class="status-item info">
                  <span>💡</span>
                  <span>点击开始检测按钮执行YOLOv13病害识别</span>
                </div>
              </div>

              <div class="orchard-select-wrapper">
                <el-select
                  v-model="selectedOrchardId"
                  placeholder="选择关联果园（可选）"
                  clearable
                  size="large"
                  class="orchard-select"
                >
                  <el-option
                    v-for="item in orchardList"
                    :key="item.id"
                    :label="item.orchardName + ' - ' + item.variety"
                    :value="item.id"
                  >
                    <span>{{ item.orchardName }}</span>
                    <span class="orchard-select-tag">{{ item.variety }}</span>
                  </el-option>
                </el-select>
                <span class="orchard-hint" v-if="selectedOrchardId">
                  检测结果将关联到 {{ getSelectedOrchardName() }}
                </span>
              </div>

              <div class="action-btns">
                <el-button size="large" @click="resetSingleUpload">重新选择</el-button>
                <el-button
                  type="primary"
                  size="large"
                  class="btn-detect"
                  :loading="detectLoading"
                  :disabled="!singleImageUrl"
                  @click="handleSingleDetect"
                >
                  <span>🚀</span>
                  开始检测
                </el-button>
              </div>
            </el-tab-pane>

            <!-- 批量检测 -->
            <el-tab-pane label="批量检测" name="batch">
              <div class="orchard-select-wrapper">
                <el-select
                  v-model="selectedOrchardId"
                  placeholder="选择关联果园（可选）"
                  clearable
                  size="large"
                  class="orchard-select"
                >
                  <el-option
                    v-for="item in orchardList"
                    :key="item.id"
                    :label="item.orchardName + ' - ' + item.variety"
                    :value="item.id"
                  >
                    <span>{{ item.orchardName }}</span>
                    <span class="orchard-select-tag">{{ item.variety }}</span>
                  </el-option>
                </el-select>
              </div>
              
              <el-upload
                ref="batchUploadRef"
                multiple
                action="#"
                :auto-upload="false"
                :on-change="handleBatchFileChange"
                :on-remove="handleBatchFileRemove"
                :file-list="batchFileList"
                accept="image/jpg,image/jpeg,image/png,image/bmp"
              >
                <el-button type="primary" size="large" class="btn-select">
                  <span>📁</span>
                  选择多张图像
                </el-button>
                <template #tip>
                  <div class="upload-tip">
                    支持批量上传JPG/PNG格式图像，单次最多上传20张
                  </div>
                </template>
              </el-upload>

              <div class="batch-preview" v-if="batchImageList.length > 0">
                <div class="preview-header">
                  <span class="preview-icon">🖼️</span>
                  <span>已选择 {{ batchImageList.length }} 张图像</span>
                </div>
                <div class="preview-grid">
                  <el-image
                    v-for="(file, index) in batchImageList"
                    :key="index"
                    :src="file.url"
                    :preview-src-list="batchImageList.map(item => item.url)"
                    fit="cover"
                    class="batch-image"
                  />
                </div>
              </div>

              <div class="action-btns">
                <el-button size="large" @click="resetBatchUpload">清空列表</el-button>
                <el-button
                  type="primary"
                  size="large"
                  class="btn-detect"
                  :loading="batchDetectLoading"
                  :disabled="batchFileList.length === 0"
                  @click="handleBatchDetect"
                >
                  <span>🚀</span>
                  批量检测
                </el-button>
              </div>
            </el-tab-pane>
          </el-tabs>

          <!-- 重置按钮 -->
          <div class="reset-section">
            <el-button @click="resetDetect" type="text" class="btn-reset">
              <span>🔄</span>
              重置检测
            </el-button>
          </div>

          <!-- 底部警告提示 -->
          <div class="warning-tips">
            <div class="tip-item">
              <span class="tip-icon">⚠️</span>
              <span class="tip-text">深度学习模型输出的预测结果仅供辅助参考，不能替代专业农艺诊断。</span>
            </div>
            <div class="tip-item">
              <span class="tip-icon">📷</span>
              <span class="tip-text">识别准确度受图像质量影响较大，建议上传光照均匀、叶片清晰的样本图像。</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧结果区域 -->
      <div class="right-section">
        <div class="section-card result-card">
          <div class="card-header">
            <span class="card-icon">📊</span>
            <h3 class="card-title">检测结果</h3>
          </div>

          <!-- 无结果状态 -->
          <div v-if="activeTab === 'single' && !detectResult" class="result-empty">
            <span class="empty-icon">🔍</span>
            <p class="empty-text">暂无检测结果</p>
            <span class="empty-hint">请上传图像并点击开始检测</span>
          </div>

          <div v-else-if="activeTab === 'batch' && !batchDetectResult" class="result-empty">
            <span class="empty-icon">📋</span>
            <p class="empty-text">暂无批量检测结果</p>
            <span class="empty-hint">请上传多张图像并点击批量检测</span>
          </div>

          <!-- 单张检测结果 -->
          <div v-else-if="activeTab === 'single' && detectResult" class="single-result">
            <div class="result-image-box">
              <img :src="detectResult.resultImageUrl" alt="检测结果图" class="result-image" />
            </div>

            <div class="result-meta">
              <div class="meta-item">
                <span class="meta-icon">🕐</span>
                <span class="meta-label">检测时间</span>
                <span class="meta-value">{{ detectResult.detectTime }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-icon">⚡</span>
                <span class="meta-label">检测耗时</span>
                <span class="meta-value">{{ detectResult.duration }}ms</span>
              </div>
              <div class="meta-item highlight">
                <span class="meta-icon">{{ isHealthy ? '🌿' : '🦠' }}</span>
                <span class="meta-label">{{ isHealthy ? '健康叶片' : '病害数量' }}</span>
                <el-tag :type="isHealthy ? 'success' : 'danger'" size="large">{{ detectResult.diseaseCount }}</el-tag>
              </div>
            </div>

            <div class="disease-list" v-if="detectResult.diseaseList && detectResult.diseaseList.length > 0">
              <h4 class="list-title">
                <span>📋</span>
                病害详情
              </h4>
              <el-table :data="detectResult.diseaseList" stripe size="small">
                <el-table-column prop="className" label="病害类别" width="140" />
                <el-table-column prop="confidence" label="置信度" width="100">
                  <template #default="{ row }">
                    {{ (row.confidence * 100).toFixed(2) }}%
                  </template>
                </el-table-column>
                <el-table-column prop="level" label="严重程度">
                  <template #default="{ row }">
                    <el-tag :type="getLevelType(row.level)">{{ row.level }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="suggestion" label="防治建议" />
              </el-table>
            </div>

            <div class="result-actions">
              <el-button @click="downloadResult" class="btn-action">
                <span>📄</span>
                下载检测报告
              </el-button>
              <el-button type="primary" @click="saveToHistory" class="btn-action primary">
                <span>💾</span>
                保存至历史记录
              </el-button>
            </div>
          </div>

          <!-- 批量检测结果 -->
          <div v-else-if="activeTab === 'batch' && batchDetectResult" class="batch-result">
            <div class="batch-summary">
              <span class="summary-icon">✅</span>
              <span>批量检测完成，共检测 {{ batchDetectResult.totalCount }} 张图像，</span>
              <span class="disease-count">发现病害 {{ batchDetectResult.diseaseTotalCount }} 处</span>
            </div>

            <!-- 批量检测结果图片展示 -->
            <div class="batch-result-images">
              <div class="batch-grid">
                <div v-for="(item, index) in batchDetectResult.list" :key="index" class="batch-result-item" @click="viewBatchDetail(item)">
                  <img :src="item.resultImageUrl" alt="检测结果" class="batch-result-image" />
                  <div class="batch-result-info">
                    <span class="file-name" :title="item.fileName">{{ item.fileName }}</span>
                    <el-tag v-if="item.diseaseCount > 0" type="danger" size="small">{{ item.diseaseCount }}处病害</el-tag>
                    <el-tag v-else type="success" size="small">健康</el-tag>
                  </div>
                </div>
              </div>
            </div>

            <div class="batch-table">
              <el-table :data="batchDetectResult.list" stripe>
                <el-table-column prop="fileName" label="文件名" min-width="150" show-overflow-tooltip />
                <el-table-column prop="diseaseCount" label="病害数量" width="100" align="center">
                  <template #default="{ row }">
                    <el-tag v-if="row.diseaseCount > 0" type="danger" size="small">{{ row.diseaseCount }}</el-tag>
                    <el-tag v-else type="success" size="small">健康</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="duration" label="检测耗时" width="100" align="center">
                  <template #default="{ row }">{{ row.duration }}ms</template>
                </el-table-column>
                <el-table-column label="操作" width="160" align="center">
                  <template #default="{ row }">
                    <el-button size="small" @click="viewBatchDetail(row)">查看详情</el-button>
                    <el-button type="primary" size="small" @click="downloadSingleResult(row)">下载</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div class="batch-actions">
              <el-button type="primary" @click="exportBatchResult" class="btn-action primary">
                <span>📦</span>
                导出全部检测结果
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 批量检测详情弹窗 -->
    <el-dialog v-model="detailDialogVisible" title="检测详情" width="900px" class="detail-dialog">
      <div v-if="currentDetail" class="detail-content">
        <div class="detail-image-box">
          <img :src="currentDetail.resultImageUrl" alt="检测结果" class="detail-image" />
        </div>
        <div class="detail-meta">
          <div class="meta-row">
            <span class="meta-label">文件名</span>
            <span class="meta-value">{{ currentDetail.fileName }}</span>
          </div>
          <div class="meta-row">
            <span class="meta-label">检测耗时</span>
            <span class="meta-value">{{ currentDetail.duration }}ms</span>
          </div>
          <div class="meta-row">
            <span class="meta-label">病害数量</span>
            <el-tag type="danger">{{ currentDetail.diseaseCount }}</el-tag>
          </div>
        </div>
        <div class="detail-disease" v-if="currentDetail.diseaseList">
          <h4><span>📋</span> 病害详情</h4>
          <el-table :data="currentDetail.diseaseList" stripe size="small">
            <el-table-column prop="className" label="病害类别" width="140" />
            <el-table-column prop="confidence" label="置信度" width="100">
              <template #default="{ row }">
                {{ (row.confidence * 100).toFixed(2) }}%
              </template>
            </el-table-column>
            <el-table-column prop="level" label="严重程度">
              <template #default="{ row }">
                <el-tag :type="getLevelType(row.level)">{{ row.level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="suggestion" label="防治建议" />
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="downloadSingleResult(currentDetail)">
          <span>📄</span>
          下载检测结果
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api/request'

// 判断是否为健康叶片
const isHealthy = computed(() => {
  if (!detectResult.value || !detectResult.value.diseaseList) {
    return false
  }
  if (detectResult.value.diseaseList.length === 0) {
    return false
  }
  return detectResult.value.diseaseList.every(item => {
    if (!item.className) return false
    const name = item.className.toString().toLowerCase()
    return name.includes('healthy') || name.includes('健康')
  })
})

// 基础变量
const activeTab = ref('single')
const singleUploadRef = ref()
const batchUploadRef = ref()

// 单张上传相关
const singleImageUrl = ref('')
const singleFile = ref(null)
const detectLoading = ref(false)
const detectResult = ref(null)

// 批量上传相关
const batchFileList = ref([])
const batchImageList = ref([])
const batchDetectLoading = ref(false)
const batchDetectResult = ref(null)

// 详情弹窗相关
const detailDialogVisible = ref(false)
const currentDetail = ref(null)

// 果园关联相关
const orchardList = ref([])
const selectedOrchardId = ref(null)

// 加载果园列表
const loadOrchardList = async () => {
  try {
    const res = await api.getOrchardList()
    if (res.code === 200) {
      // 后端返回的是 { orchards: [...], total: n }
      orchardList.value = res.data?.orchards || res.data || []
    }
  } catch (error) {
    console.error('加载果园列表失败', error)
  }
}

// 获取选中的果园名称
const getSelectedOrchardName = () => {
  const orchard = orchardList.value.find(item => item.id === selectedOrchardId.value)
  return orchard ? orchard.orchardName : ''
}

// 页面加载时获取果园列表
onMounted(() => {
  loadOrchardList()
})

// 单张文件选择
const handleSingleFileChange = (file) => {
  const isImage = file.raw.type.includes('image/')
  if (!isImage) {
    ElMessage.error('请上传图片格式文件')
    return
  }
  singleFile.value = file.raw
  singleImageUrl.value = URL.createObjectURL(file.raw)
  detectResult.value = null
}

// 重置单张上传
const resetSingleUpload = () => {
  singleImageUrl.value = ''
  singleFile.value = null
  detectResult.value = null
  singleUploadRef.value?.clearFiles()
}

// 单张检测执行
const handleSingleDetect = async () => {
  if (!singleFile.value) {
    ElMessage.warning('请先上传叶片图像')
    return
  }
  detectLoading.value = true
  const formData = new FormData()
  formData.append('image', singleFile.value)
  // 添加果园ID参数
  if (selectedOrchardId.value) {
    formData.append('orchard_id', selectedOrchardId.value)
  }

  try {
    const res = await api.singleDetect(formData)
    if (res.code === 200) {
      res.data.resultImageUrl = 'http://127.0.0.1:8000' + res.data.resultImageUrl
      detectResult.value = res.data
      const msg = selectedOrchardId.value 
        ? `检测完成，已添加到果园 ${getSelectedOrchardName()}`
        : '检测完成'
      ElMessage.success(msg)
    } else {
      ElMessage.error(res.message || '检测失败')
    }
  } catch (error) {
    console.error('检测失败', error)
    ElMessage.error('检测失败，请确保后端已启动')
  } finally {
    detectLoading.value = false
  }
}

// 批量文件处理
const handleBatchFileChange = (file, fileList) => {
  batchFileList.value = fileList
  batchImageList.value = fileList.map(item => {
    return {
      name: item.name,
      url: URL.createObjectURL(item.raw)
    }
  })
  batchDetectResult.value = null
}

const handleBatchFileRemove = () => {
  batchDetectResult.value = null
}

// 重置批量上传
const resetBatchUpload = () => {
  batchFileList.value = []
  batchImageList.value = []
  batchDetectResult.value = null
  batchUploadRef.value?.clearFiles()
}

// 批量检测执行
const handleBatchDetect = async () => {
  if (batchFileList.value.length === 0) {
    ElMessage.warning('请先选择要检测的图像')
    return
  }
  batchDetectLoading.value = true
  const formData = new FormData()
  batchFileList.value.forEach(file => {
    formData.append('images', file.raw)
  })
  // 添加果园ID参数
  if (selectedOrchardId.value) {
    formData.append('orchard_id', selectedOrchardId.value)
  }

  try {
    const res = await api.batchDetect(formData)
    if (res.data && res.data.list) {
      res.data.list.forEach(item => {
        if (item.resultImageUrl) {
          item.resultImageUrl = 'http://127.0.0.1:8000' + item.resultImageUrl
        }
      })
    }
    batchDetectResult.value = res.data
    const msg = selectedOrchardId.value 
      ? `批量检测完成，已添加到果园 ${getSelectedOrchardName()}`
      : '批量检测完成'
    ElMessage.success(msg)
  } catch (error) {
    console.error('批量检测失败', error)
    ElMessage.error('批量检测失败：' + (error.message || '请确保后端已启动'))
  } finally {
    batchDetectLoading.value = false
  }
}

// 批量详情查看
const viewBatchDetail = (row) => {
  currentDetail.value = row
  detailDialogVisible.value = true
}

// 严重程度标签样式
const getLevelType = (level) => {
  const typeMap = {
    '健康': 'success',
    '重度': 'danger'
  }
  return typeMap[level] || 'info'
}

// 重置检测
const resetDetect = () => {
  ElMessageBox.confirm('确定要重置当前所有检测内容吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    resetSingleUpload()
    resetBatchUpload()
    ElMessage.success('重置成功')
  })
}

// 下载/保存相关方法
const downloadResult = async () => {
  if (!detectResult.value) {
    ElMessage.warning('暂无检测结果可下载')
    return
  }
  await _doDownload(detectResult.value)
}

const downloadSingleResult = async (row) => {
  if (!row) return
  await _doDownload(row)
}

const _doDownload = async (record) => {
  try {
    if (!record) {
      ElMessage.warning('暂无检测结果')
      return
    }

    ElMessage.info('正在生成检测报告...')

    const reportData = {
      file_name: record.fileName || record.file_name || '未知文件',
      detect_time: record.detectTime || record.detect_time || new Date().toLocaleString(),
      duration: record.duration || 0,
      disease_count: record.diseaseCount || record.disease_count || 0,
      disease_list: record.diseaseList || record.disease_list || [],
      result_image_url: (record.resultImageUrl || record.result_image_url || '').replace('http://127.0.0.1:8000', '')
    }

    const blob = await api.downloadReport(reportData)

    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `病害检测报告_${record.fileName || Date.now()}.html`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)

    ElMessage.success('报告下载成功！用浏览器打开即可查看，也可打印/保存为PDF')
  } catch (err) {
    console.error('下载出错：', err)
    ElMessage.error('下载失败，请确保后端已启动')
  }
}

const saveToHistory = () => {
  ElMessage.success('检测完成后已自动保存至历史记录！可在历史记录页查看')
}

const exportBatchResult = async () => {
  if (!batchDetectResult.value || batchDetectResult.value.list.length === 0) {
    ElMessage.warning('暂无批量检测结果')
    return
  }

  ElMessage.info('正在逐个下载，请稍候...')
  for (const row of batchDetectResult.value.list) {
    await _doDownload(row)
    await new Promise(resolve => setTimeout(resolve, 300))
  }
  ElMessage.success('全部下载完成！')
}
</script>

<style scoped lang="scss">
.detect-container {
  padding: 24px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

// 页面标签
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

  .tag-icon {
    font-size: 16px;
  }
}

// 页面标题
.page-header {
  margin-bottom: 24px;

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
    line-height: 1.6;
  }
}

// 主内容区
.main-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  align-items: start;
}

// 通用卡片
.section-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 24px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.03);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0eb;

  .card-icon {
    font-size: 22px;
  }

  .card-title {
    font-size: 18px;
    font-weight: 700;
    color: #1a1a1a;
    margin: 0;
  }
}

// 上传卡片
.upload-card {
  .detect-tabs {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: none;

    :deep(.el-tabs__header) {
      margin: 0;
    }
  }
}

.single-uploader {
  width: 100%;

  .upload-empty {
    width: 100%;
    height: 260px;
    border: 2px dashed #d1d5db;
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    cursor: pointer;
    transition: all 0.3s ease;
    background: #fafafa;

    &:hover {
      border-color: #16a34a;
      background: #f0fdf4;
    }

    .upload-icon {
      font-size: 56px;
      margin-bottom: 12px;
      opacity: 0.6;
    }

    .upload-text {
      font-size: 16px;
      font-weight: 600;
      color: #1a1a1a;
      margin: 0 0 8px;
    }

    .upload-hint {
      font-size: 13px;
      color: #888;
    }
  }

  .upload-image {
    width: 100%;
    max-height: 260px;
    object-fit: contain;
    border-radius: 12px;
  }
}

.upload-status {
  margin: 16px 0;
  display: flex;
  flex-direction: column;
  gap: 8px;

  .status-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 13px;

    &.success {
      background: #f0fdf4;
      color: #16a34a;
    }

    &.info {
      background: #f0f9ff;
      color: #1890ff;
    }
  }
}

.btn-select {
  width: 100%;
  height: 48px;
  font-size: 15px;
  background: #16a34a;
  border-color: #16a34a;

  &:hover {
    background: #15803d;
    border-color: #15803d;
  }
}

.upload-tip {
  margin-top: 12px;
  font-size: 13px;
  color: #888;
}

.batch-preview {
  margin-top: 16px;
  background: #fafafa;
  border-radius: 12px;
  padding: 16px;

  .preview-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    font-size: 14px;
    color: #666;

    .preview-icon {
      font-size: 18px;
    }
  }

  .preview-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
    gap: 8px;

    .batch-image {
      width: 80px;
      height: 80px;
      border-radius: 8px;
      cursor: pointer;
      object-fit: cover;
      border: 2px solid transparent;
      transition: all 0.2s;

      &:hover {
        border-color: #16a34a;
        transform: scale(1.05);
      }
    }
  }
}

// 果园选择
.orchard-select-wrapper {
  margin-bottom: 16px;
  
  .orchard-select {
    width: 100%;
  }
  
  .orchard-select-tag {
    float: right;
    color: #999;
    font-size: 12px;
  }
  
  .orchard-hint {
    display: block;
    margin-top: 6px;
    font-size: 12px;
    color: #16a34a;
  }
}

.action-btns {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;

  .btn-detect {
    background: #16a34a;
    border-color: #16a34a;
    padding: 12px 28px;
    font-weight: 600;
    transition: all 0.2s;

    &:hover:not(:disabled) {
      background: #15803d;
      border-color: #15803d;
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(22, 163, 74, 0.3);
    }

    &:disabled {
      background: #d1d5db;
      border-color: #d1d5db;
    }
  }
}

.reset-section {
  margin-top: 16px;
  text-align: center;

  .btn-reset {
    color: #888;
    font-size: 13px;

    &:hover {
      color: #16a34a;
    }
  }
}

// 底部警告提示
.warning-tips {
  margin-top: 24px;
  padding: 16px;
  background: #fefce8;
  border: 1px dashed #fbbf24;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;

  .tip-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-size: 13px;
    color: #92400e;
    line-height: 1.6;

    .tip-icon {
      font-size: 16px;
      flex-shrink: 0;
      margin-top: 2px;
    }

    .tip-text {
      flex: 1;
    }
  }
}

// 结果区域
.result-card {
  min-height: 600px;
}

.result-empty {
  height: 400px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: #fafafa;
  border-radius: 12px;

  .empty-icon {
    font-size: 64px;
    opacity: 0.5;
    margin-bottom: 16px;
  }

  .empty-text {
    font-size: 18px;
    font-weight: 600;
    color: #1a1a1a;
    margin: 0 0 8px;
  }

  .empty-hint {
    font-size: 14px;
    color: #888;
  }
}

// 单张检测结果
.single-result {
  .result-image-box {
    width: 100%;
    margin-bottom: 20px;

    .result-image {
      width: 100%;
      max-height: 280px;
      object-fit: contain;
      border-radius: 12px;
      border: 1px solid #e5e7eb;
    }
  }

  .result-meta {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 20px;

    .meta-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
      padding: 14px;
      background: #fafafa;
      border-radius: 10px;
      text-align: center;

      &.highlight {
        background: #fef2f2;
      }

      .meta-icon {
        font-size: 20px;
      }

      .meta-label {
        font-size: 12px;
        color: #888;
      }

      .meta-value {
        font-size: 14px;
        font-weight: 600;
        color: #1a1a1a;
      }
    }
  }

  .disease-list {
    .list-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 15px;
      font-weight: 700;
      color: #1a1a1a;
      margin: 0 0 12px;
    }
  }

  .result-actions {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
    gap: 12px;

    .btn-action {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 12px 20px;
      border-radius: 8px;
      font-weight: 500;
      transition: all 0.2s;

      &.primary {
        background: #16a34a;
        border-color: #16a34a;
        color: #fff;

        &:hover {
          background: #15803d;
          border-color: #15803d;
        }
      }
    }
  }
}

// 批量检测结果
.batch-result {
  .batch-summary {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 14px 16px;
    background: #f0fdf4;
    border-radius: 10px;
    font-size: 14px;
    color: #1a1a1a;
    margin-bottom: 20px;

    .summary-icon {
      font-size: 18px;
    }

    .disease-count {
      font-weight: 700;
      color: #ef4444;
    }
  }

  .batch-result-images {
    margin-bottom: 16px;

    .batch-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      gap: 12px;

      .batch-result-item {
        cursor: pointer;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        overflow: hidden;
        transition: all 0.2s;

        &:hover {
          border-color: #16a34a;
          box-shadow: 0 4px 12px rgba(22, 163, 74, 0.15);
          transform: translateY(-2px);
        }

        .batch-result-image {
          width: 100%;
          height: 100px;
          object-fit: cover;
        }

        .batch-result-info {
          padding: 10px;
          background: #fafafa;

          .file-name {
            display: block;
            font-size: 12px;
            color: #1a1a1a;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-bottom: 6px;
          }
        }
      }
    }
  }

  .batch-table {
    margin-bottom: 16px;
  }

  .batch-actions {
    display: flex;
    justify-content: flex-end;

    .btn-action.primary {
      background: #16a34a;
      border-color: #16a34a;
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 12px 24px;

      &:hover {
        background: #15803d;
        border-color: #15803d;
      }
    }
  }
}

// 详情弹窗
.detail-dialog {
  :deep(.el-dialog__body) {
    padding: 24px;
  }

  .detail-content {
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
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin-bottom: 20px;

      .meta-row {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 12px;
        background: #fafafa;
        border-radius: 8px;

        .meta-label {
          font-size: 12px;
          color: #888;
        }

        .meta-value {
          font-size: 14px;
          font-weight: 600;
          color: #1a1a1a;
        }
      }
    }

    .detail-disease {
      h4 {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 15px;
        font-weight: 700;
        color: #1a1a1a;
        margin: 0 0 12px;
      }
    }
  }
}
</style>
