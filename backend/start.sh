#!/bin/bash
# ============================================
# SmartOrchard Backend - 启动脚本
# 用于 Render 部署
# ============================================

set -e  # 遇到错误立即退出

echo "🚀 正在启动 SmartOrchard 后端..."

# —— 下载中文字体（Linux 环境无 simhei.ttf）——
FONT_DIR="/opt/render/project/src/backend/fonts"
FONT_FILE="$FONT_DIR/SimHei.ttf"
mkdir -p "$FONT_DIR"

if [ ! -f "$FONT_FILE" ]; then
    echo "📥 下载中文字体 SimHei.ttf..."
    # 使用清华/中科大开源镜像
    curl -L -o "$FONT_FILE" \
        "https://github.com/StellarCN/scp_zh/raw/master/fonts/SimHei.ttf" \
        || curl -L -o "$FONT_FILE" \
        "https://github.com/misode/misode.github.io/raw/main/public/fonts/simhei.ttf" \
        || echo "⚠️ 字体下载失败，将使用默认字体（可能无法显示中文）"
fi

# —— 创建静态目录（Render 每次部署会清空）——
mkdir -p static/uploads static/results
echo "✅ 静态目录已创建"

# —— 启动 FastAPI —— 
echo "🌐 启动 Uvicorn..."
uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
