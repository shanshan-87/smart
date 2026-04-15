<template>
  <div class="map-container" ref="mapRef"></div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  // 地图中心点坐标，默认南疆阿克苏地区（冰糖心核心产区）
  center: {
    type: Array,
    default: () => [41.1687, 80.2613]
  },
  zoom: {
    type: Number,
    default: 12
  },
  // 果园地块数据
  orchardData: {
    type: Array,
    default: () => []
  },
  // 病害采样点数据
  diseasePointData: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['pointClick', 'polygonClick', 'mapClick'])

const mapRef = ref(null)
let mapInstance = null
let polygonLayerGroup = null
let markerLayerGroup = null
let isClickMode = ref(false)  // 是否处于点击选点模式
let tempMarker = null  // 临时标记

// 地图初始化
const initMap = () => {
  if (!mapRef.value) return
  // 初始化地图实例
  mapInstance = L.map(mapRef.value).setView(props.center, props.zoom)
  // 加载高德瓦片底图（国内访问稳定，无偏移）
  L.tileLayer('https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', {
    attribution: '&copy; 高德地图',
    maxZoom: 18,
    minZoom: 3
  }).addTo(mapInstance)

  // 初始化图层组
  polygonLayerGroup = L.layerGroup().addTo(mapInstance)
  markerLayerGroup = L.layerGroup().addTo(mapInstance)

  // 地图点击事件（用于选点模式）
  mapInstance.on('click', (e) => {
    if (isClickMode.value) {
      const latlng = e.latlng
      // 移除之前的临时标记
      if (tempMarker) {
        tempMarker.remove()
      }
      // 添加新的临时标记
      const clickIcon = L.divIcon({
        html: `
          <div style="
            width: 32px;
            height: 32px;
            background: #16a34a;
            border: 3px solid #fff;
            border-radius: 50% 50% 50% 0;
            transform: rotate(-45deg);
            box-shadow: 0 2px 8px rgba(0,0,0,0.4);
            display: flex;
            align-items: center;
            justify-content: center;
          ">
            <span style="transform: rotate(45deg); font-size: 14px;">📍</span>
          </div>
        `,
        className: 'click-marker',
        iconSize: [36, 36],
        iconAnchor: [16, 32]
      })
      tempMarker = L.marker([latlng.lat, latlng.lng], { icon: clickIcon }).addTo(mapInstance)
      // 触发事件给父组件
      emit('mapClick', [latlng.lat, latlng.lng])
    }
  })

  // 渲染初始数据
  renderOrchardPolygon()
  renderDiseaseMarker()
}

// 渲染果园地块多边形
const renderOrchardPolygon = () => {
  if (!polygonLayerGroup || !props.orchardData.length) return
  polygonLayerGroup.clearLayers()

  props.orchardData.forEach(item => {
    const popupContent = `
      <div style="width: 200px;">
        <h4 style="margin: 0 0 8px; font-size: 14px;">${item.orchardName}</h4>
        <p style="margin: 4px 0; font-size: 12px;">种植品种：${item.variety}</p>
        <p style="margin: 4px 0; font-size: 12px;">种植面积：${item.area}亩</p>
        <p style="margin: 4px 0; font-size: 12px;">地址：${item.address || '暂无'}</p>
        <p style="margin: 4px 0; font-size: 12px;">病害发生率：${item.diseaseRate}%</p>
      </div>
    `

    // 判断是单点还是多边形
    if (item.path && item.path.length === 1) {
      // 单点：显示圆形标记
      const center = item.path[0]
      const orchardIcon = L.divIcon({
        html: `
          <div style="
            width: 24px;
            height: 24px;
            background: ${item.color || '#1890ff'};
            border: 3px solid #fff;
            border-radius: 50%;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
          ">
            <span style="font-size: 12px;">🌳</span>
          </div>
        `,
        className: 'orchard-marker',
        iconSize: [28, 28],
        iconAnchor: [14, 14]
      })
      const marker = L.marker(center, { icon: orchardIcon }).addTo(polygonLayerGroup)
      marker.bindPopup(popupContent)
      marker.on('click', () => emit('polygonClick', item))
    } else if (item.path && item.path.length >= 3) {
      // 多边形：显示多边形区域
      const polygon = L.polygon(item.path, {
        color: item.color || '#1890ff',
        fillColor: item.fillColor || 'rgba(24, 144, 255, 0.2)',
        fillOpacity: 0.5,
        weight: 2
      }).addTo(polygonLayerGroup)
      polygon.bindPopup(popupContent)
      polygon.on('click', () => emit('polygonClick', item))
    }
  })
}

// 渲染病害采样点标记
const renderDiseaseMarker = () => {
  if (!markerLayerGroup || !props.diseasePointData.length) return
  markerLayerGroup.clearLayers()

  // 病害严重程度对应图标颜色
  const levelColorMap = {
    '轻度': '#52c41a',
    '中度': '#faad14',
    '重度': '#f5222d'
  }

  props.diseasePointData.forEach(item => {
    // 自定义病害点图标
    const diseaseIcon = L.divIcon({
      html: `<div style="width: 12px; height: 12px; background: ${levelColorMap[item.level] || '#1890ff'}; border-radius: 50%; border: 2px solid #fff; box-shadow: 0 0 4px rgba(0,0,0,0.3);"></div>`,
      className: 'disease-marker',
      iconSize: [16, 16],
      iconAnchor: [8, 8]
    })

    const marker = L.marker(item.coordinate, { icon: diseaseIcon }).addTo(markerLayerGroup)
    // 绑定病害详情弹窗
    marker.bindPopup(`
      <div style="width: 220px;">
        <h4 style="margin: 0 0 8px; font-size: 14px;">病害采样点</h4>
        <p style="margin: 4px 0; font-size: 12px;">病害类型：${item.diseaseType}</p>
        <p style="margin: 4px 0; font-size: 12px;">严重程度：<span style="color: ${levelColorMap[item.level]}">${item.level}</span></p>
        <p style="margin: 4px 0; font-size: 12px;">置信度：${(item.confidence * 100).toFixed(2)}%</p>
        <p style="margin: 4px 0; font-size: 12px;">检测时间：${item.detectTime}</p>
      </div>
    `)
    // 绑定点击事件
    marker.on('click', () => emit('pointClick', item))
  })
}

// 监听数据变化，重新渲染
watch(() => props.orchardData, () => renderOrchardPolygon(), { deep: true })
watch(() => props.diseasePointData, () => renderDiseaseMarker(), { deep: true })

// 组件挂载后初始化地图
onMounted(() => {
  initMap()
})

// 暴露地图实例给父组件
defineExpose({
  getMapInstance: () => mapInstance,
  setMapCenter: (center, zoom) => {
    if (mapInstance) mapInstance.setView(center, zoom || props.zoom)
  },
  refreshMap: () => {
    if (mapInstance) {
      mapInstance.invalidateSize()
      renderOrchardPolygon()
      renderDiseaseMarker()
    }
  },
  // 直接暴露重渲染函数，供父组件精确控制调用时机
  forceRenderPolygon: () => {
    if (mapInstance) renderOrchardPolygon()
  },
  forceRenderMarkers: () => {
    if (mapInstance) renderDiseaseMarker()
  },
  // 设置点击选点模式
  setClickMode: (enabled) => {
    isClickMode.value = enabled
    if (!enabled && tempMarker) {
      tempMarker.remove()
      tempMarker = null
    }
  }
})
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  min-height: 600px;
  border-radius: var(--border-radius);
  overflow: hidden;
}
</style>