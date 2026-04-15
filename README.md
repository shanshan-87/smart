# 🌳 智慧果园苹果叶片病害检测系统

> SmartOrchard - Apple Leaf Disease Detection System

基于深度学习的苹果叶片病害智能检测系统，支持单张/批量图像检测、历史记录管理、数据可视化分析和果园GIS管理。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![Vue.js](https://img.shields.io/badge/Vue.js-3.x-42b883.svg)
![YOLOv13](https://img.shields.io/badge/YOLOv13-Detection-orange.svg)

---

## 📋 项目概述

本系统是一个面向智慧农业的苹果叶片病害检测平台，采用YOLOv13深度学习模型实现对苹果叶片的病害自动识别，支持黑星病、黑腐病、锈病等常见病害的检测，并提供完整的数据管理和可视化分析功能。

### 🔬 核心功能

| 功能模块 | 描述 |
|---------|------|
| 📷 **病害检测** | 单张/批量图像上传，YOLOv13模型实时推理，返回病害类型、位置、置信度 |
| 📊 **数据分析** | 病害类型统计、严重程度分布、月度趋势图表展示 |
| 📜 **历史记录** | 检测记录查询、筛选、导出PDF报告 |
| 🗺️ **果园GIS** | 果园位置标注、病害分布热力图、多果园对比分析 |
| 👤 **用户管理** | 角色权限控制、管理员/普通用户数据隔离 |

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Frontend)                       │
│                   Vue 3 + Element Plus + ECharts             │
├─────────────────────────────────────────────────────────────┤
│                        后端 (Backend)                        │
│                    FastAPI + SQLAlchemy                      │
├─────────────────────────────────────────────────────────────┤
│                      模型层 (Model)                          │
│                     YOLOv13 目标检测                         │
└─────────────────────────────────────────────────────────────┘
```

### 后端技术栈

| 技术 | 说明 |
|-----|------|
| **FastAPI** | 高性能异步Web框架 |
| **SQLAlchemy** | ORM数据库操作 |
| **SQLite** | 轻量级数据库 |
| **Ultralytics YOLO** | 深度学习目标检测 |

### 前端技术栈

| 技术 | 说明 |
|-----|------|
| **Vue 3** | 渐进式JavaScript框架 |
| **Vite** | 新一代前端构建工具 |
| **Element Plus** | Vue 3 UI组件库 |
| **ECharts** | 数据可视化图表库 |
| **Vue Router** | 前端路由管理 |
| **Axios** | HTTP请求库 |
| **Leaflet** | 地图可视化库 |

---

## 📁 项目结构

```
SmartOrchard-AppleDiseaseDetection1/
├── backend/                      # 后端服务
│   ├── main.py                   # 主应用入口 (FastAPI)
│   ├── requirements.txt          # Python依赖
│   ├── app.db                    # SQLite数据库
│   ├── model/                    # 模型文件目录
│   │   └── best.pt               # YOLOv13训练模型
│   ├── static/                   # 静态文件
│   │   ├── uploads/              # 上传图片
│   │   └── results/              # 检测结果图片
│   ├── utils/                    # 工具模块
│   │   ├── db.py                 # 数据库模型
│   │   └── auth.py               # 认证工具
│   └── ultralytics/              # YOLO框架
│
├── frontend/                     # 前端应用
│   ├── src/
│   │   ├── main.js               # Vue入口
│   │   ├── App.vue               # 根组件
│   │   ├── api/                  # API接口封装
│   │   ├── assets/               # 静态资源
│   │   ├── components/           # 公共组件
│   │   ├── layout/               # 布局组件
│   │   ├── router/               # 路由配置
│   │   └── views/                # 页面组件
│   │       ├── LandingPage.vue   # 首页/落地页
│   │       ├── Login.vue         # 登录页
│   │       ├── Register.vue      # 注册页
│   │       ├── Dashboard.vue     # 系统首页
│   │       ├── DiseaseDetect.vue # 病害检测
│   │       ├── HistoryData.vue   # 历史记录
│   │       ├── DataAnalysis.vue  # 数据分析
│   │       ├── OrchardMap.vue    # 果园GIS
│   │       └── SystemSetting.vue # 系统设置
│   └── package.json
│
├── static/                       # 全局静态文件
├── README.md                     # 项目文档
└── 启动后端.bat                   # Windows启动脚本
```

---

## 🦠 病害类型

本系统可检测以下4类苹果叶片状态：

| 病害ID | 中文名称 | 英文名称 | 特征描述 |
|:------:|---------|---------|---------|
| 0 | 黑星病 | Apple Scab | 叶片出现黑褐色圆形病斑 |
| 1 | 黑腐病 | Black Rot | 叶片形成"蛙眼状"病斑 |
| 2 | 锈病 | Cedar Apple Rust | 叶片出现橙黄色圆形病斑 |
| 3 | 健康叶片 | Healthy | 无病害侵染 |

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 1. 后端部署

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
# 或双击 启动后端.bat
```

后端服务地址: `http://localhost:8000`

### 2. 前端部署

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 开发模式运行
npm run dev

# 生产环境打包
npm run build
```

前端访问地址: `http://localhost:5173`

### 3. 访问系统

1. 打开浏览器访问 `http://localhost:5173`
2. 使用默认账号登录：
   - 管理员账号: `admin` / `admin123`
   - 普通用户: 注册后登录

---

## 📐 接口文档

启动后端后访问API文档：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 核心接口

| 方法 | 路径 | 说明 |
|-----|------|------|
| POST | `/auth/login` | 用户登录 |
| POST | `/auth/register` | 用户注册 |
| POST | `/detect/single` | 单张图片检测 |
| POST | `/detect/batch` | 批量图片检测 |
| GET | `/history/list` | 检测历史记录 |
| GET | `/statistics/data` | 统计数据 |
| GET | `/statistics/chart` | 图表数据 |
| GET | `/orchard/list` | 果园列表 |
| POST | `/orchard/add` | 添加果园 |
| POST | `/report/generate` | 生成检测报告 |

---

## 🗄️ 数据库设计

### 用户表 (users)

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | INTEGER | 主键 |
| username | VARCHAR | 用户名 |
| hashed_password | VARCHAR | 加密密码 |
| real_name | VARCHAR | 真实姓名 |
| college | VARCHAR | 学院 |
| major | VARCHAR | 专业 |

### 检测记录表 (detect_records)

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | INTEGER | 主键 |
| file_name | VARCHAR | 文件名 |
| image_url | VARCHAR | 原图URL |
| result_image_url | VARCHAR | 结果图URL |
| disease_count | INTEGER | 病害数量 |
| disease_type | VARCHAR | 病害类型 |
| level | VARCHAR | 严重程度 |
| confidence | FLOAT | 置信度 |
| duration | INTEGER | 检测耗时(ms) |
| detect_time | DATETIME | 检测时间 |

### 管理员汇总表 (admin_detect_records)

同步所有用户的检测记录，供管理员统一管理。

### 果园表 (orchards)

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | INTEGER | 主键 |
| name | VARCHAR | 果园名称 |
| location | VARCHAR | 地址 |
| path | VARCHAR | 地图坐标 |
| disease_rate | FLOAT | 病害率 |
| total_points | INTEGER | 采样点数 |
| disease_points | INTEGER | 病害点数 |

### 采样点表 (disease_points)

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | INTEGER | 主键 |
| orchard_id | INTEGER | 所属果园 |
| detect_record_id | INTEGER | 检测记录ID |
| disease_type | VARCHAR | 病害类型 |
| lat | FLOAT | 纬度 |
| lon | FLOAT | 经度 |

---

## 📊 数据分析指标

### 统计指标

- **检测记录总数**: 所有检测次数
- **病害检出数**: 检出病害的记录数
- **健康叶片数**: 无病害的记录数
- **平均置信度**: 模型预测置信度均值
- **果园总数**: 管理的果园数量

### 图表类型

| 图表 | 描述 |
|-----|------|
| 环形图 | 病害类型分布（黑星病/黑腐病/锈病/健康） |
| 柱状图 | 各病害类型发病数量对比 |
| 折线图 | 月度病害发生趋势 |
| 饼图 | 病害严重程度分布（重度/健康） |

---

## 🔧 系统配置

### 管理员功能

1. **数据管理**: 查看所有用户的检测记录
2. **用户管理**: 创建/编辑用户账号
3. **数据库维护**: 清理孤立数据
4. **系统设置**: 修改果园名称、联系方式

### 普通用户功能

1. **病害检测**: 上传图片进行检测
2. **历史记录**: 查看个人检测历史
3. **果园管理**: 添加和管理自己的果园
4. **报告导出**: 导出PDF检测报告

---

## 📝 开发说明

### 添加新用户

```python
# 通过API创建
POST /users/create
{
    "username": "newuser",
    "password": "password123",
    "real_name": "张三",
    "college": "农学院",
    "major": "植物保护"
}
```

### 更新检测模型

将新的 `.pt` 模型文件放入 `backend/model/` 目录，命名为 `best.pt`，重启后端即可自动加载。

### 自定义病害类型

在 `backend/main.py` 的 `DISEASE_MAP` 字典中添加新的病害类型：

```python
4: {
    "name": "新病害名称",
    "en_name": "New Disease",
    "suggestion": "防治建议...",
    "detail": "病害详情..."
}
```

---

## 📄 许可证

本项目仅供学习和研究使用。

---

## 👨‍💻 作者

智慧果园病害检测系统开发团队

---

## 🙏 致谢

- [Ultralytics](https://github.com/ultralytics/ultralytics) - YOLO目标检测框架
- [PlantVillage](https://plantvillage.org/) - 苹果病害数据集
- [Vue.js](https://vuejs.org/) - 前端框架
- [FastAPI](https://fastapi.tiangolo.com/) - 后端框架
