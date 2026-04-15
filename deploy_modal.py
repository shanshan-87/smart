"""
SmartOrchard - Modal.com 部署配置
===================================
用法：
  modal deploy modal.py

部署后自动获得公开 URL，如：
  https://your-username--smart-orchard-app.modal.run
"""

import os
import subprocess
import urllib.request
from pathlib import Path

import modal

# ----------------------------------------
# 1. 创建 Modal App
# ----------------------------------------
app = modal.App("smart-orchard")

# ----------------------------------------
# 2. 定义镜像（包含所有依赖）
# ----------------------------------------
# 使用 A100 GPU（免费额度内可用），或 T4 作为备选
# Modal 免费计划：每月 30 小时 GPU
IMAGE = (
    modal.Image.debian_slim(python_version="3.11")
    # PyTorch + CUDA（支持 GPU 推理）
    .pip_install(
        "torch==2.1.0",
        "torchvision==0.16.0",
        index_url="https://download.pytorch.org/whl/cu118",
    )
    # YOLO + 其他依赖
    .pip_install(
        "ultralytics==8.3.0",
        "opencv-python==4.9.0.80",
        "pillow==10.3.0",
        "fastapi==0.110.0",
        "uvicorn[standard]==0.29.0",
        "python-multipart==0.0.9",
        "sqlalchemy==2.0.29",
        "passlib[bcrypt]==1.7.4",
        "python-jose[cryptography]==3.3.0",
        "pydantic==2.12.5",
        "numpy==1.26.4",
    )
)

# ----------------------------------------
# 3. 持久化存储卷（存放数据库、用户上传文件）
# ----------------------------------------
volume = modal.Volume.from_name("smart-orchard-data")

# 字体下载（避免 OpenCV 不支持中文）
FONT_URL = "https://github.com/StellarCN/scp_zh/raw/master/fonts/SimHei.ttf"
FONT_PATH = "/data/fonts/SimHei.ttf"


def download_font():
    """下载黑体字体（如果不存在）"""
    Path("/data/fonts").mkdir(parents=True, exist_ok=True)
    if not os.path.exists(FONT_PATH):
        print("下载 SimHei.ttf 字体...")
        urllib.request.urlretrieve(FONT_URL, FONT_PATH)
        print("字体下载完成！")
    else:
        print("字体已存在，跳过下载。")


# ----------------------------------------
# 4. 懒加载模型（冷启动时只初始化 API）
# ----------------------------------------
# 模型在第一次调用 /detect 时才加载，避免每次重启都下载
_model = None


def get_model():
    global _model
    if _model is None:
        from ultralytics import YOLO

        # 优先使用用户上传的模型文件（持久化卷中）
        model_path = "/data/model/best.pt"
        if os.path.exists(model_path):
            print("加载自定义模型 best.pt ...")
            _model = YOLO(model_path, task="detect")
        else:
            print("未找到 best.pt，使用默认 YOLOv8n 模型...")
            _model = YOLO("yolov8n.pt")
        print("模型加载完成！")
    return _model


# ----------------------------------------
# 5. 定义 FastAPI ASGI 应用
# ----------------------------------------
@app.cls(
    image=IMAGE,
    gpu="T4",  # 使用 T4 GPU（免费额度内）
    memory=4096,  # 4GB 内存（YOLO 推理需要）
    volumes={"/data": volume},  # 持久化存储
    timeout=300,  # 单次请求超时 5 分钟
)
class SmartOrchardAPI:
    @modal.enter()
    def start(self):
        """容器启动时执行一次"""
        import sys
        sys.path.insert(0, "/backend")

        # 下载字体
        download_font()

        # 设置环境变量
        os.environ["FONT_PATH"] = FONT_PATH
        os.environ["DATABASE_URL"] = "sqlite:///./app.db"

        # 初始化目录
        os.makedirs("/data/static/uploads", exist_ok=True)
        os.makedirs("/data/static/results", exist_ok=True)
        os.makedirs("/data/model", exist_ok=True)

        print("✅ SmartOrchard 初始化完成！")

    @modal.asgi_app()
    def api(self):
        import fastapi
        from fastapi import FastAPI, UploadFile, File, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import FileResponse
        from pydantic import BaseModel
        from typing import List, Optional
        import cv2
        import numpy as np
        from PIL import Image, ImageDraw, ImageFont
        import uuid
        import shutil
        import time

        app = FastAPI(title="苹果叶片病害检测系统 API", version="1.0.0")

        # CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 静态文件
        app.mount("/static", StaticFiles(directory="/data/static"), name="static")

        # ========== 中文绘制工具 ==========
        def cv2_put_chinese_text(img, text, org, font_size=20, color=(0, 255, 0)):
            img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(img_pil)
            try:
                font = ImageFont.truetype(FONT_PATH, font_size)
            except Exception:
                font = ImageFont.load_default()
            rgb_color = (color[2], color[1], color[0])
            draw.text(org, text, font=font, fill=rgb_color)
            return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

        # ========== 病害映射表 ==========
        DISEASE_MAP = {
            0: {"name": "黑星病", "en_name": "Apple Scab"},
            1: {"name": "黑腐病", "en_name": "Black Rot"},
            2: {"name": "锈病", "en_name": "Cedar Apple Rust"},
            3: {"name": "健康叶片", "en_name": "Healthy"},
        }

        HEAVY_DISEASES = {"黑腐病", "锈病"}  # 重度病害

        def get_level(cls, confidence, area_ratio):
            name = DISEASE_MAP.get(cls, {}).get("name", "未知")
            if name == "健康叶片":
                return "无"
            if name in HEAVY_DISEASES:
                return "重度"
            if confidence > 0.75 or area_ratio > 0.15:
                return "中度"
            return "轻度"

        # ========== API 路由 ==========

        @app.get("/")
        def root():
            return {
                "message": "🍎 SmartOrchard 苹果叶片病害检测系统",
                "version": "1.0.0",
                "docs": "/docs",
            }

        @app.get("/health")
        def health():
            return {"status": "ok"}

        @app.post("/detect")
        async def detect(file: UploadFile = File(...)):
            """上传苹果叶片图片，返回病害检测结果"""
            model = get_model()

            # 保存上传文件
            suffix = os.path.splitext(file.filename)[1] or ".jpg"
            input_path = f"/data/static/uploads/{uuid.uuid4().hex}{suffix}"
            result_path = f"/data/static/results/{uuid.uuid4().hex}_result.jpg"

            with open(input_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            # YOLO 推理
            start_time = time.time()
            results = model(input_path, verbose=False)
            duration_ms = int((time.time() - start_time) * 1000)

            img = cv2.imread(input_path)
            detections = []

            for result in results:
                boxes = result.boxes
                if boxes is None or len(boxes) == 0:
                    # 无检测结果 → 健康
                    cv2_put_chinese_text(img, "未检出病害（健康）", (20, 40), 24, (0, 200, 0))
                    cv2.imwrite(result_path, img)
                    return {
                        "success": True,
                        "image_url": f"/static/uploads/{os.path.basename(input_path)}",
                        "result_image_url": f"/static/results/{os.path.basename(result_path)}",
                        "disease_count": 0,
                        "disease_type": "健康叶片",
                        "disease_types": [],
                        "level": "无",
                        "confidence": 0.0,
                        "duration_ms": duration_ms,
                        "diseases": [],
                    }

                disease_count = len(boxes)
                cls_ids = [int(b.cls) for b in boxes]
                confidences = [float(b.conf) for b in boxes]

                # 统计病害类型
                type_counts = {}
                for cls_id in cls_ids:
                    name = DISEASE_MAP.get(cls_id, {}).get("name", "未知")
                    type_counts[name] = type_counts.get(name, 0) + 1

                primary_cls = cls_ids[0]
                primary_name = DISEASE_MAP.get(primary_cls, {}).get("name", "未知")
                avg_conf = sum(confidences) / len(confidences)
                level = get_level(primary_cls, avg_conf, 0.1)

                # 绘制检测框和标签
                disease_labels = []
                for i, box in enumerate(boxes):
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cls_id = int(box.cls)
                    conf = float(box.conf)
                    name = DISEASE_MAP.get(cls_id, {}).get("name", "未知")

                    # 颜色：重度-红，中度-橙，轻度-黄
                    color_map = {"重度": (0, 0, 255), "中度": (0, 165, 255), "轻度": (0, 255, 255), "无": (0, 200, 0)}
                    lvl = get_level(cls_id, conf, 0.1)
                    color = color_map.get(lvl, (0, 255, 0))

                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                    label = f"{name} {conf:.2f}"
                    cv2_put_chinese_text(img, label, (x1, max(y1 - 8, 20)), 16, color)
                    disease_labels.append({"class": cls_id, "name": name, "confidence": conf})

                # 汇总标签
                summary = f"检测到 {disease_count} 处 | {', '.join(f'{k}×{v}' for k, v in type_counts.items())}"
                cv2_put_chinese_text(img, summary, (10, 30), 18, (255, 255, 255))

                cv2.imwrite(result_path, img)

                return {
                    "success": True,
                    "image_url": f"/static/uploads/{os.path.basename(input_path)}",
                    "result_image_url": f"/static/results/{os.path.basename(result_path)}",
                    "disease_count": disease_count,
                    "disease_type": primary_name,
                    "disease_types": list(type_counts.keys()),
                    "level": level,
                    "confidence": round(avg_conf, 4),
                    "duration_ms": duration_ms,
                    "diseases": disease_labels,
                }

        @app.get("/static/uploads/{filename}")
        def serve_upload(filename: str):
            path = f"/data/static/uploads/{filename}"
            if os.path.exists(path):
                return FileResponse(path)
            raise HTTPException(404, "File not found")

        @app.get("/static/results/{filename}")
        def serve_result(filename: str):
            path = f"/data/static/results/{filename}"
            if os.path.exists(path):
                return FileResponse(path)
            raise HTTPException(404, "File not found")

        return app


# ----------------------------------------
# 6. 本地调试入口
# ----------------------------------------
if __name__ == "__main__":
    with app.run():
        print("Modal app is running!")
