<template>
  <div class="orchard-container">
    <!-- 页面标签 -->
    <div class="page-tag">
      <span class="tag-icon">🗺️</span>
      <span>SmartOrchard · GIS Management</span>
    </div>

    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">果园GIS管理</h1>
        <p class="page-desc">可视化果园地块分布与病害采样点分布，支持地块增删改查与空间数据分析</p>
      </div>
      <div class="header-actions">
        <el-button @click="refreshMap" class="btn-refresh">
          <span>🔄</span>
          刷新地图
        </el-button>
        <el-button type="primary" @click="addOrchardDialogVisible = true" class="btn-add">
          <span>➕</span>
          新增果园地块
        </el-button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧地图区域 -->
      <div class="map-section">
        <div class="section-card map-card">
          <div class="map-header">
            <div class="map-title">
              <span class="title-icon">📍</span>
              <span>果园地块分布图</span>
            </div>
            <div class="map-legend">
              <div class="legend-item">
                <span class="legend-dot healthy"></span>
                <span>健康</span>
              </div>
              <div class="legend-item">
                <span class="legend-dot disease"></span>
                <span>病害</span>
              </div>
            </div>
          </div>
          <div class="map-content">
            <MapContainer
              ref="mapRef"
              :orchardData="orchardData"
              :diseasePointData="diseasePointData"
              @pointClick="handlePointClick"
              @polygonClick="handlePolygonClick"
              @mapClick="handleMapClick"
            />
          </div>
        </div>
      </div>

      <!-- 右侧信息面板 -->
      <div class="info-section">
        <!-- 果园列表 -->
        <div class="section-card orchard-list-card">
          <div class="card-header">
            <span class="card-icon">🌳</span>
            <h3 class="card-title">果园地块列表</h3>
            <el-tag size="small" type="info">{{ orchardData.length }} 个</el-tag>
          </div>
          <div class="orchard-list" v-if="orchardData.length > 0">
            <div
              v-for="item in orchardData"
              :key="item.id"
              class="orchard-item"
              :class="{ active: activeOrchardId === item.id }"
              @click="handleOrchardItemClick(item)"
            >
              <div class="orchard-icon">
                <span>🌲</span>
              </div>
              <div class="orchard-info">
                <div class="orchard-name">{{ item.orchardName }}</div>
                <div class="orchard-meta">
                  <span class="meta-item">{{ item.variety }}</span>
                  <span class="meta-divider">·</span>
                  <span class="meta-item">{{ item.area }}亩</span>
                </div>
              </div>
              <div class="orchard-status" :class="getStatusClass(item.diseaseRate)">
                <span class="status-value">{{ item.diseaseRate }}%</span>
                <span class="status-label">病害率</span>
              </div>
            </div>
          </div>
          <div v-else class="empty-list">
            <span class="empty-icon">🏕️</span>
            <p>暂无果园数据</p>
          </div>
        </div>

        <!-- 选中地块详情 -->
        <div class="section-card detail-card" v-if="activeOrchardInfo">
          <div class="card-header">
            <span class="card-icon">📋</span>
            <h3 class="card-title">地块详情</h3>
          </div>
          <div class="detail-content">
            <div class="detail-header">
              <span class="detail-icon">🌳</span>
              <div class="detail-title">
                <span class="name">{{ activeOrchardInfo.orchardName }}</span>
                <span class="variety">{{ activeOrchardInfo.variety }}</span>
              </div>
            </div>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-icon-small">📐</span>
                <span class="detail-label">种植面积</span>
                <span class="detail-value">{{ activeOrchardInfo.area }} 亩</span>
              </div>
              <div class="detail-item">
                <span class="detail-icon-small">🌱</span>
                <span class="detail-label">树龄</span>
                <span class="detail-value">{{ activeOrchardInfo.age }} 年</span>
              </div>
              <div class="detail-item highlight">
                <span class="detail-icon-small">📊</span>
                <span class="detail-label">病害率</span>
                <span class="detail-value" :class="getStatusClass(activeOrchardInfo.diseaseRate)">
                  {{ activeOrchardInfo.diseaseRate }}%
                </span>
              </div>
              <div class="detail-item">
                <span class="detail-icon-small">📍</span>
                <span class="detail-label">地址</span>
                <span class="detail-value address">{{ activeOrchardInfo.address || '暂无' }}</span>
              </div>
            </div>
            <div class="detail-actions">
              <el-button type="danger" size="small" @click="handleDeleteOrchard" class="btn-delete-orchard">
                <span>🗑️</span>
                删除该果园
              </el-button>
            </div>
          </div>
        </div>

        <!-- 病害统计 -->
        <div class="section-card stats-card">
          <div class="card-header">
            <span class="card-icon">📈</span>
            <h3 class="card-title">
              <span v-if="activeOrchardId && activeOrchardInfo">{{ activeOrchardInfo.orchardName }} - 病害统计</span>
              <span v-else>区域病害统计</span>
            </h3>
          </div>
          
          <!-- 未选择果园时的提示 -->
          <div v-if="!activeOrchardId" class="stats-empty">
            <span class="empty-icon">👆</span>
            <p>请在左侧选择一个果园</p>
            <p class="empty-hint">查看该果园的病害分布情况</p>
          </div>
          
          <!-- 已选择果园，显示统计 -->
          <template v-else>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-icon blue">
                  <span>📍</span>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ filteredDiseaseData.length }}</div>
                  <div class="stat-label">采样点总数</div>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon red">
                  <span>⚠️</span>
                </div>
                <div class="stat-info">
                  <div class="stat-value" style="color: #ef4444;">{{ filteredDiseaseCount }}</div>
                  <div class="stat-label">病害点数量</div>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon yellow">
                  <span>📊</span>
                </div>
                <div class="stat-info">
                  <div class="stat-value" style="color: #f59e0b;">{{ activeOrchardInfo?.diseaseRate || 0 }}%</div>
                  <div class="stat-label">果园发病率</div>
                </div>
              </div>
            </div>
            
            <!-- 病害类型分布（动态） -->
            <div class="disease-distribution" v-if="filteredDiseaseData.length > 0">
              <h4 class="dist-title">
                <span>🍎</span>
                病害类型分布
              </h4>
              <div class="dist-bars">
                <div v-for="item in diseaseTypeStats" :key="item.type" class="dist-item">
                  <span class="dist-name">{{ item.type }}</span>
                  <div class="dist-bar">
                    <div class="dist-fill" :style="{ width: item.percent + '%', background: item.color }"></div>
                  </div>
                  <span class="dist-count">{{ item.count }}处 ({{ item.percent }}%)</span>
                </div>
              </div>
            </div>
            
            <!-- 无病害数据提示 -->
            <div v-else class="no-disease-tip">
              <span>🌿</span>
              <p>该果园暂无病害采样数据</p>
              <p class="tip-sub">前往「病害检测」页面，上传叶片图片并关联此果园</p>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- 新增果园弹窗 -->
    <el-dialog v-model="addOrchardDialogVisible" title="新增果园地块" width="550px" class="add-dialog">
      <div class="dialog-content">
        <div class="dialog-header">
          <span class="dialog-icon">🌳</span>
          <span>添加新果园地块信息</span>
        </div>
        <el-form :model="orchardForm" label-width="100px" class="orchard-form">
          <el-form-item label="果园名称" prop="orchardName">
            <el-input v-model="orchardForm.orchardName" placeholder="请输入果园名称" />
          </el-form-item>
          <el-form-item label="种植品种" prop="variety">
            <el-input v-model="orchardForm.variety" placeholder="请输入种植品种" />
          </el-form-item>
          <el-form-item label="种植面积" prop="area">
            <el-input-number v-model="orchardForm.area" :min="1" placeholder="亩" style="width: 100%;" />
          </el-form-item>
          <el-form-item label="树龄" prop="age">
            <el-input-number v-model="orchardForm.age" :min="1" placeholder="年" style="width: 100%;" />
          </el-form-item>
          <el-form-item label="详细地址" prop="address">
            <el-input v-model="orchardForm.address" type="textarea" :rows="2" placeholder="请输入果园详细地址（可选，用于备注）" />
          </el-form-item>
          <el-form-item label="果园位置" prop="location">
            <div class="location-picker">
              <div class="location-hint">
                <span v-if="!selectedLocation">📍 请在下方地图上点击选择果园位置</span>
                <span v-else class="location-selected">
                  ✅ 已选择位置：{{ selectedLocation[0].toFixed(4) }}, {{ selectedLocation[1].toFixed(4) }}
                </span>
              </div>
              <el-button 
                v-if="!isSelectingLocation" 
                type="primary" 
                size="small" 
                @click="startSelectingLocation"
                class="btn-select-location"
              >
                🗺️ 在地图上选择
              </el-button>
              <el-button 
                v-else 
                type="warning" 
                size="small" 
                @click="cancelSelectingLocation"
                class="btn-cancel-select"
              >
                ❌ 取消选择
              </el-button>
            </div>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="handleDialogClose" class="btn-cancel">取消</el-button>
        <el-button type="primary" @click="submitOrchardForm" :disabled="!selectedLocation" class="btn-submit">
          <span>✅</span>
          确认提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import MapContainer from '@/components/MapContainer.vue'
import { api } from '@/api/request'

const mapRef = ref(null)
const addOrchardDialogVisible = ref(false)
const activeOrchardId = ref(null)

// 地图选点相关状态
const isSelectingLocation = ref(false)
const selectedLocation = ref(null)

// 果园地块数据
const orchardData = ref([])

// 病害采样点数据
const diseasePointData = ref([])

// 加载果园数据
const loadOrchardData = async () => {
  try {
    const res = await api.getOrchardList()
    if (res.data) {
      // 后端可能返回数组或对象
      orchardData.value = Array.isArray(res.data) ? res.data : res.data.orchards || []
    }
  } catch (error) {
    console.error('获取果园数据失败', error)
  }
}

// 加载病害空间数据
const loadDiseasePointData = async () => {
  try {
    const res = await api.getDiseaseSpatialData()
    if (res.data) {
      diseasePointData.value = res.data
    }
  } catch (error) {
    console.error('获取病害空间数据失败', error)
  }
}

// 选中的果园详情
const activeOrchardInfo = computed(() => {
  return orchardData.value.find(item => item.id === activeOrchardId.value) || null
})

// 病害类型颜色映射
const diseaseTypeColors = {
  '黑星病': '#1890ff',
  '黑腐病': '#f5222d',
  '锈病': '#faad14',
  '健康叶片': '#52c41a'
}

// 当前选中果园的病害数据（过滤后的）
const filteredDiseaseData = computed(() => {
  if (!activeOrchardId.value) return []
  return diseasePointData.value.filter(item => item.orchardId === activeOrchardId.value)
})

// 过滤后的病害点数量（排除健康）
const filteredDiseaseCount = computed(() => {
  return filteredDiseaseData.value.filter(item => item.diseaseType !== '健康叶片').length
})

// 病害类型分布统计
const diseaseTypeStats = computed(() => {
  const data = filteredDiseaseData.value
  if (data.length === 0) return []
  
  // 统计各病害类型数量
  const counts = {}
  data.forEach(item => {
    const type = item.diseaseType || '未知'
    counts[type] = (counts[type] || 0) + 1
  })
  
  // 转换为百分比
  const total = data.length
  return Object.entries(counts).map(([type, count]) => ({
    type,
    count,
    percent: Math.round((count / total) * 100),
    color: diseaseTypeColors[type] || '#999'
  })).sort((a, b) => b.count - a.count)
})

// 获取状态样式类
const getStatusClass = (rate) => {
  if (rate > 20) return 'danger'
  if (rate > 10) return 'warning'
  return 'safe'
}

// 地图事件回调
const handlePointClick = (item) => {
  activeOrchardId.value = item.orchardId
}

const handlePolygonClick = (item) => {
  activeOrchardId.value = item.id
}

// 处理地图点击事件（选点模式）
const handleMapClick = (coords) => {
  selectedLocation.value = coords
  isSelectingLocation.value = false
  mapRef.value?.setClickMode(false)
  ElMessage.success(`已选择位置：${coords[0].toFixed(4)}, ${coords[1].toFixed(4)}`)
}

// 开始选择位置
const startSelectingLocation = () => {
  isSelectingLocation.value = true
  mapRef.value?.setClickMode(true)
  ElMessage.info('请在地图上点击选择果园位置')
}

// 取消选择位置
const cancelSelectingLocation = () => {
  isSelectingLocation.value = false
  selectedLocation.value = null
  mapRef.value?.setClickMode(false)
}

// 弹窗关闭时重置状态
const handleDialogClose = () => {
  addOrchardDialogVisible.value = false
  cancelSelectingLocation()
}

const handleOrchardItemClick = (item) => {
  activeOrchardId.value = item.id
  mapRef.value?.setMapCenter(item.path?.[0] || [39.9, 116.4], 14)
}

// 地图刷新
const refreshMap = () => {
  mapRef.value?.refreshMap()
  loadOrchardData()
  loadDiseasePointData()
  ElMessage.success('地图刷新成功')
}

// 删除果园
const handleDeleteOrchard = () => {
  if (!activeOrchardId.value) return

  ElMessageBox.confirm(
    `确定要删除「${activeOrchardInfo.value?.orchardName}」吗？删除后无法恢复！`,
    '确认删除',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await api.deleteOrchard(activeOrchardId.value)
      // 从列表中移除
      orchardData.value = orchardData.value.filter(item => item.id !== activeOrchardId.value)
      // 同时移除关联的病害采样点数据（避免地图残留）
      diseasePointData.value = diseasePointData.value.filter(item => item.orchardId !== activeOrchardId.value)
      activeOrchardId.value = null
      ElMessage.success('删除成功')
      // 直接触发地图重渲染，确保标点立即清除
      mapRef.value?.forceRenderPolygon()
      mapRef.value?.forceRenderMarkers()
    } catch (error) {
      console.error('删除失败', error)
      ElMessage.error('删除失败')
    }
  }).catch(() => {
    // 用户取消
  })
}

// 新增果园表单
const orchardForm = reactive({
  orchardName: '',
  variety: '',
  area: 1,
  age: 1,
  address: ''
})

// 提交新增果园
const submitOrchardForm = async () => {
  if (!orchardForm.orchardName) {
    ElMessage.warning('请输入果园名称')
    return
  }
  if (!selectedLocation.value) {
    ElMessage.warning('请先在地图上选择果园位置')
    return
  }

  try {
    // 使用用户在地图上选择的位置
    const coords = selectedLocation.value
    const formData = {
      ...orchardForm,
      path: [coords]  // 使用用户选择的坐标
    }

    const res = await api.addOrchard(formData)
    if (res.data) {
      orchardData.value.push(res.data)
      addOrchardDialogVisible.value = false
      ElMessage.success('新增果园成功')
      // 重置表单
      Object.keys(orchardForm).forEach(key => {
        orchardForm[key] = key === 'area' || key === 'age' ? 1 : ''
      })
      selectedLocation.value = null
      // 刷新地图，定位到新果园
      mapRef.value?.setMapCenter(coords, 14)
      mapRef.value?.refreshMap()
    }
  } catch (error) {
    ElMessage.error('新增果园失败：' + (error.message || '请确保后端已启动'))
  }
}

onMounted(() => {
  loadOrchardData()
  loadDiseasePointData()
})
</script>

<style scoped lang="scss">
.orchard-container {
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

// 页面头部
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
      line-height: 1.6;
    }
  }

  .header-actions {
    display: flex;
    gap: 12px;

    .btn-refresh {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 10px 18px;
      border-radius: 8px;
      font-weight: 500;
      transition: all 0.2s;

      &:hover {
        border-color: #16a34a;
        color: #16a34a;
      }
    }

    .btn-add {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 10px 20px;
      background: #16a34a;
      border-color: #16a34a;
      border-radius: 8px;
      font-weight: 600;
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

// 主内容区
.main-content {
  display: grid;
  grid-template-columns: 1fr 380px;
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
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid #f0f0eb;

  .card-icon {
    font-size: 20px;
  }

  .card-title {
    font-size: 16px;
    font-weight: 700;
    color: #1a1a1a;
    margin: 0;
    flex: 1;
  }
}

// 地图区域
.map-section {
  .map-card {
    padding: 0;
    overflow: hidden;

    .map-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 20px;
      border-bottom: 1px solid #f0f0eb;

      .map-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 15px;
        font-weight: 700;
        color: #1a1a1a;

        .title-icon {
          font-size: 18px;
        }
      }

      .map-legend {
        display: flex;
        gap: 16px;

        .legend-item {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: #666;

          .legend-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;

            &.healthy {
              background: #52c41a;
            }

            &.disease {
              background: #f5222d;
            }
          }
        }
      }
    }

    .map-content {
      height: 600px;
    }
  }
}

// 右侧信息面板
.info-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

// 果园列表卡片
.orchard-list-card {
  .orchard-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-height: 320px;
    overflow-y: auto;

    .orchard-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px;
      border-radius: 10px;
      background: #fafafa;
      border: 1px solid transparent;
      cursor: pointer;
      transition: all 0.2s;

      &:hover {
        background: #f0fdf4;
        border-color: #bbf7d0;
      }

      &.active {
        background: #f0fdf4;
        border-color: #16a34a;
        box-shadow: 0 2px 8px rgba(22, 163, 74, 0.1);
      }

      .orchard-icon {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        background: rgba(22, 163, 74, 0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        flex-shrink: 0;
      }

      .orchard-info {
        flex: 1;
        min-width: 0;

        .orchard-name {
          font-size: 14px;
          font-weight: 600;
          color: #1a1a1a;
          margin-bottom: 4px;
        }

        .orchard-meta {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 12px;
          color: #888;

          .meta-divider {
            color: #ccc;
          }
        }
      }

      .orchard-status {
        text-align: center;
        padding: 6px 10px;
        border-radius: 8px;
        min-width: 52px;

        &.safe {
          background: #f0fdf4;
          .status-value { color: #16a34a; }
          .status-label { color: #52c41a; }
        }

        &.warning {
          background: #fef9c3;
          .status-value { color: #ca8a04; }
          .status-label { color: #a16207; }
        }

        &.danger {
          background: #fef2f2;
          .status-value { color: #ef4444; }
          .status-label { color: #dc2626; }
        }

        .status-value {
          display: block;
          font-size: 14px;
          font-weight: 700;
        }

        .status-label {
          display: block;
          font-size: 10px;
        }
      }
    }
  }

  .empty-list {
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
}

// 地块详情卡片
.detail-card {
  .detail-content {
    .detail-header {
      display: flex;
      align-items: center;
      gap: 14px;
      margin-bottom: 20px;
      padding-bottom: 16px;
      border-bottom: 1px dashed #e5e7eb;

      .detail-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        background: linear-gradient(135deg, #16a34a, #52c41a);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
      }

      .detail-title {
        .name {
          display: block;
          font-size: 18px;
          font-weight: 700;
          color: #1a1a1a;
          margin-bottom: 4px;
        }

        .variety {
          font-size: 13px;
          color: #888;
        }
      }
    }

    .detail-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;

      .detail-item {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 12px;
        background: #fafafa;
        border-radius: 10px;

        &.highlight {
          background: #fef2f2;
        }

        .detail-icon-small {
          font-size: 14px;
          margin-bottom: 4px;
        }

        .detail-label {
          font-size: 11px;
          color: #888;
        }

        .detail-value {
          font-size: 14px;
          font-weight: 600;
          color: #1a1a1a;

          &.danger { color: #ef4444; }
          &.warning { color: #f59e0b; }
          &.safe { color: #16a34a; }

          &.address {
            font-size: 12px;
            font-weight: normal;
            color: #666;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
        }
      }
    }

    .detail-actions {
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px dashed #e5e7eb;
      text-align: center;

      .btn-delete-orchard {
        background: #fef2f2;
        border-color: #fecaca;
        color: #ef4444;
        &:hover {
          background: #ef4444;
          border-color: #ef4444;
          color: #fff;
        }
      }
    }
  }
}

// 统计空状态
.stats-empty {
  text-align: center;
  padding: 30px 20px;
  
  .empty-icon {
    font-size: 40px;
    display: block;
    margin-bottom: 12px;
  }
  
  p {
    margin: 8px 0;
    color: #666;
  }
  
  .empty-hint {
    font-size: 12px;
    color: #999;
  }
}

// 无病害提示
.no-disease-tip {
  text-align: center;
  padding: 20px;
  background: #f6ffed;
  border-radius: 8px;
  margin-top: 16px;
  
  span {
    font-size: 32px;
    display: block;
    margin-bottom: 8px;
  }
  
  p {
    margin: 4px 0;
    color: #52c41a;
  }
  
  .tip-sub {
    font-size: 12px;
    color: #999;
  }
}

// 统计卡片
.stats-card {
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 20px;

    .stat-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      padding: 14px;
      background: #fafafa;
      border-radius: 10px;
      text-align: center;

      .stat-icon {
        width: 36px;
        height: 36px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;

        &.blue { background: rgba(24, 144, 255, 0.1); }
        &.red { background: rgba(239, 68, 68, 0.1); }
        &.yellow { background: rgba(245, 158, 11, 0.1); }
      }

      .stat-info {
        .stat-value {
          font-size: 20px;
          font-weight: 800;
          color: #1a1a1a;
        }

        .stat-label {
          font-size: 11px;
          color: #888;
          margin-top: 2px;
        }
      }
    }
  }

  .disease-distribution {
    .dist-title {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      font-weight: 600;
      color: #1a1a1a;
      margin: 0 0 12px;
    }

    .dist-bars {
      display: flex;
      flex-direction: column;
      gap: 10px;

      .dist-item {
        display: flex;
        align-items: center;
        gap: 10px;

        .dist-name {
          width: 60px;
          font-size: 12px;
          color: #666;
        }

        .dist-bar {
          flex: 1;
          height: 8px;
          background: #f0f0eb;
          border-radius: 4px;
          overflow: hidden;

          .dist-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
          }
        }

        .dist-count {
          width: 36px;
          font-size: 12px;
          font-weight: 600;
          color: #1a1a1a;
          text-align: right;
        }
      }
    }
  }
}

// 新增弹窗
.add-dialog {
  .dialog-content {
    .dialog-header {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 12px 16px;
      background: #f0fdf4;
      border-radius: 10px;
      margin-bottom: 20px;
      font-size: 14px;
      color: #16a34a;

      .dialog-icon {
        font-size: 18px;
      }
    }

    .orchard-form {
      :deep(.el-form-item__label) {
        font-weight: 500;
        color: #666;
      }

      .location-picker {
        display: flex;
        flex-direction: column;
        gap: 10px;
        width: 100%;

        .location-hint {
          padding: 10px 12px;
          background: #f5f7fa;
          border-radius: 8px;
          font-size: 13px;
          color: #666;

          .location-selected {
            color: #16a34a;
            font-weight: 500;
          }
        }

        .btn-select-location {
          background: #1890ff;
          border-color: #1890ff;
          &:hover {
            background: #40a9ff;
            border-color: #40a9ff;
          }
        }

        .btn-cancel-select {
          background: #fff7e6;
          border-color: #ffd591;
          color: #fa8c16;
          &:hover {
            background: #ffd591;
            border-color: #ffd591;
            color: #fff;
          }
        }
      }
    }
  }

  :deep(.el-dialog__footer) {
    .btn-cancel {
      border-radius: 8px;
    }

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
</style>
