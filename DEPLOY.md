# 🚀 SmartOrchard 部署指南

## 项目信息

| 项目 | 技术栈 |
|------|--------|
| 后端 | FastAPI + PyTorch + YOLO + SQLite |
| 前端 | Vue 3 + Vite + Element Plus + ECharts |

---

## ✅ 方案一：Modal.com 完全免费部署（推荐，无需信用卡）

### 亮点

| 项目 | 说明 |
|------|------|
| 费用 | **完全免费**，无需信用卡 |
| GPU | T4 GPU（支持 YOLO 推理） |
| 冷启动 | ~10 秒 |
| 免费额度 | 每月 30 小时 GPU 时长 |

### Step 1：本地安装 Modal CLI

```bash
pip install modal
modal auth login
```

> 用 GitHub 账号登录授权即可，无需信用卡

### Step 2：推送最新代码到 GitHub

```bash
cd D:\Smart
git add modal.py requirements-modal.txt
git commit -m "feat: 添加 Modal 部署配置"
git push origin master
```

### Step 3：一键部署

```bash
cd D:\Smart
modal deploy modal.py
```

等待 3~5 分钟（首次需安装 PyTorch + YOLO），完成后显示：

```
App 'smart-orchard' deployed at:
https://your-username--smart-orchard-api.modal.run
```

这就是你的**后端公开链接**！

### Step 4：配置前端

1. 打开 `frontend/src/api/request.js`
2. 将 `baseURL` 改为你的 Modal URL，例如：

```js
const service = axios.create({
  baseURL: 'https://your-name--smart-orchard-api.modal.run',
  timeout: 30000,
})
```

3. 部署前端到 Vercel（免费）：
```bash
cd frontend
npm install
npm run build
```

### 额度说明

- 每月 30 小时 GPU（YOLO 推理很省时，足够展示用）
- 15 分钟无请求容器休眠
- 数据存储在 Modal Volume 中（持久化）

### 上传自定义模型（可选）

如果你有训练好的 `best.pt`，上传到 Volume：

```bash
modal volume put smart-orchard-data model/best.pt /model/best.pt
```

---

## 方案二：Render 免费部署（需要信用卡）

> ⚠️ 需要绑定信用卡才能部署

### 1. Fork / 推送代码到 GitHub

确保 GitHub 仓库包含以下结构：

```
smart/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── start.sh          ← 启动脚本（字体下载 + uvicorn）
│   ├── render.yaml       ← 部署配置
│   ├── utils/
│   ├── static/
│   └── app.db
├── frontend/
│   ├── src/
│   ├── vite.config.js
│   └── package.json
└── README.md
```

### 2. 部署后端（Render Web Service）

**Step 1：** 访问 [https://render.com](https://render.com)，用 GitHub 登录

**Step 2：** 点击 **New + → Web Service**

**Step 3：** 选择 `smart` 仓库

**Step 4：** 填写配置：

| 配置项 | 值 |
|--------|-----|
| **Name** | `smart-orchard-backend` |
| **Language** | `Python 3.11` |
| **Branch** | `master` |
| **Root Directory** | `backend` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `bash start.sh` |
| **Instance Type** | `Free` |

**Step 5：** 添加环境变量（Environment → Variables）：

| Key | Value |
|-----|-------|
| `SECRET_KEY` | `your-random-secret-key-here` |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` |
| `DATABASE_URL` | `sqlite:///./app.db` |
| `ENVIRONMENT` | `production` |

**Step 6：** 点击 **Create Web Service**

等待 5~10 分钟构建完成（PyTorch + YOLO 首次安装较慢）。

部署成功后，访问：`https://smart-orchard-backend.onrender.com/docs`

> ⚠️ 免费版 15 分钟无活动会休眠，首次访问需等待 30~60 秒唤醒。

### 3. 部署前端（Vercel 免费）

**Step 1：** 访问 [https://vercel.com](https://vercel.com)，用 GitHub 登录

**Step 2：** 点击 **Add New → Project**，导入 `smart` 仓库

**Step 3：** 配置：

| 配置项 | 值 |
|--------|-----|
| **Framework Preset** | `Vite` |
| **Root Directory** | `./frontend` |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |
| **Environment Variables** | `VITE_API_URL` = `https://smart-orchard-backend.onrender.com` |

**Step 4：** 修改 `frontend/vite.config.js`，在生产环境使用绝对 URL：

```js
// vite.config.js
export default defineConfig({
  plugins: [vue()],
  resolve: { alias: { '@': resolve(__dirname, 'src') } },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || '')
  }
})
```

**Step 5：** 修改 `frontend/src/api/request.js`，支持生产环境绝对 URL：

```js
const service = axios.create({
  baseURL: import.meta.env.VITE_API_URL
    ? import.meta.env.VITE_API_URL.replace(/\/$/, '') + '/api'
    : '/api',
  timeout: 30000,
})
```

### 4. 访问部署结果

- 🌐 **前端地址**：`https://smart-frontend.vercel.app`（或你设置的域名）
- 🔧 **后端 API**：`https://smart-orchard-backend.onrender.com`
- 📖 **API 文档**：`https://smart-orchard-backend.onrender.com/docs`

---

## 方案三：Railway 付费部署（$5/月）

Railway 比 Render 更简单，支持直接部署目录，无需改目录结构：

**Step 1：** 安装 [Railway CLI](https://docs.railway.app/getting-started)

```bash
npm install -g @railway/cli
railway login
```

**Step 2：** 在 `backend` 目录部署

```bash
cd D:\Smart\backend
railway init
railway up
```

Railway 会自动识别 Python 项目，运行 `pip install -r requirements.txt`。

**Step 3：** 添加环境变量

```bash
railway variables set SECRET_KEY "your-secret-key"
railway variables set ENVIRONMENT "production"
```

**Step 4：** 获取部署 URL，填入 Vercel 前端的 `VITE_API_URL`

---

## ⚠️ 注意事项

### 免费版 Render 的限制

| 限制项 | 说明 |
|--------|------|
| **冷启动休眠** | 15 分钟无活动后，下次访问等待 30~60 秒唤醒 |
| **750 小时/月** | 两个免费实例（后端 + 前端）共用 |
| **休眠不影响数据** | SQLite 数据库在磁盘上不受休眠影响 |
| **磁盘限制** | 免费版 512MB，注意模型文件大小 |

### 常见问题

**Q：API 返回 500 错误？**
> 检查 Render 后端日志，看是否是字体下载失败或 YOLO 模型路径错误。

**Q：检测速度很慢？**
> 冷启动时 YOLO 加载需要 ~20 秒，之后每次推理约 2~5 秒，属于正常现象。

**Q：图片上传失败？**
> 检查后端 `static/uploads` 目录是否创建成功，可通过 Render Shell 手动创建。

---

## 🔧 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev
```

打开 http://localhost:3000
