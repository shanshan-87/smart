from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ultralytics import YOLO
import cv2
import numpy as np
import os
import uuid
from datetime import datetime, date
from typing import List, Optional
from PIL import Image, ImageDraw, ImageFont

# -------------------------------------------------------
# 中文文字绘制工具（OpenCV 不支持中文，改用 PIL 绘制后转回）
# -------------------------------------------------------
# 字体路径：优先使用 Render Linux 环境的字体，回退到 Windows
# 生产环境会下载 SimHei.ttf 到 backend/fonts/
_FONT_PATH = os.environ.get("FONT_PATH",
    r"/opt/render/project/src/backend/fonts/SimHei.ttf"
    if os.path.exists("/opt/render/project/src/backend/fonts/SimHei.ttf")
    else r"C:\Windows\Fonts\simhei.ttf")

def cv2_put_chinese_text(img: np.ndarray, text: str, org: tuple,
                          font_size: int = 20, color: tuple = (0, 255, 0),
                          thickness: int = 2) -> np.ndarray:
    """
    在 OpenCV 图像上绘制中文文字。
    - img: BGR numpy 数组
    - text: 要绘制的字符串（支持中文）
    - org: 文字左上角坐标 (x, y)
    - font_size: 字号
    - color: BGR 颜色元组
    - thickness: 仅占位兼容参数，PIL 通过 font_size 控制粗细
    """
    # OpenCV BGR → PIL RGB
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    try:
        font = ImageFont.truetype(_FONT_PATH, font_size)
    except Exception:
        font = ImageFont.load_default()
    # PIL 颜色是 RGB
    rgb_color = (color[2], color[1], color[0])
    draw.text(org, text, font=font, fill=rgb_color)
    # PIL RGB → OpenCV BGR
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

# 导入工具模块
from utils.auth import create_access_token, verify_password, get_password_hash
from utils.db import get_db, Base, engine, User, DetectRecord, AdminDetectRecord, Orchard, DiseasePoint, get_current_user
from pydantic import BaseModel

# 初始化FastAPI应用
app = FastAPI(title="苹果叶片病害检测系统API", version="1.0.0")

# 配置CORS跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录（自动创建，不用手动建）
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/results", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 初始化数据库
Base.metadata.create_all(bind=engine)

# 检查并添加缺失的列
try:
    from sqlalchemy import text
    with engine.connect() as conn:
        # detect_records 表
        result = conn.execute(text("PRAGMA table_info(detect_records)"))
        columns = [row[1] for row in result.fetchall()]
        if 'source_user_id' not in columns:
            conn.execute(text("ALTER TABLE detect_records ADD COLUMN source_user_id INTEGER REFERENCES users(id)"))
            conn.commit()
            print("✅ 数据库已更新：detect_records 添加 source_user_id 字段")
        if 'admin_record_id' not in columns:
            conn.execute(text("ALTER TABLE detect_records ADD COLUMN admin_record_id INTEGER"))
            conn.commit()
            print("✅ 数据库已更新：detect_records 添加 admin_record_id 字段")

        # 创建 admin_detect_records 表（如果不存在）
        result_admin = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='admin_detect_records'"))
        if not result_admin.fetchone():
            conn.execute(text("""
                CREATE TABLE admin_detect_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_record_id INTEGER NOT NULL,
                    file_name VARCHAR NOT NULL,
                    image_url VARCHAR NOT NULL,
                    result_image_url VARCHAR NOT NULL,
                    disease_count INTEGER DEFAULT 0,
                    disease_type VARCHAR,
                    level VARCHAR,
                    confidence FLOAT,
                    duration INTEGER NOT NULL,
                    detect_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER REFERENCES users(id) NOT NULL
                )
            """))
            conn.commit()
            print("✅ 数据库已更新：创建 admin_detect_records 表")

        # orchards 表 - user_id
        result2 = conn.execute(text("PRAGMA table_info(orchards)"))
        orchard_columns = [row[1] for row in result2.fetchall()]
        if 'user_id' not in orchard_columns:
            conn.execute(text("ALTER TABLE orchards ADD COLUMN user_id INTEGER REFERENCES users(id) DEFAULT 1"))
            conn.commit()
            print("✅ 数据库已更新：orchards 添加 user_id 字段")
        if 'source_user_id' not in orchard_columns:
            conn.execute(text("ALTER TABLE orchards ADD COLUMN source_user_id INTEGER REFERENCES users(id)"))
            conn.commit()
            print("✅ 数据库已更新：orchards 添加 source_user_id 字段")
except Exception as e:
    print(f"⚠️ 数据库更新提示: {e}")

# ==============================================
# ✅ 加载你的 YOLOv13 best.pt 模型
# ==============================================
MODEL_PATH = "model/best.pt"
if os.path.exists(MODEL_PATH):
    model = YOLO(MODEL_PATH, task="detect")
    print("✅ YOLOv13 模型加载成功！")
else:
    # 兜底方案：如果没有你的模型，自动下载官方轻量模型
    print("⚠️  未找到 model/best.pt，正在加载官方 YOLOv8n 模型...")
    model = YOLO("yolov13n.pt")
    print("✅ 官方模型加载成功！")

# ==============================================
# 数据同步函数：将用户数据实时备份到管理员汇总表
# ==============================================
def sync_record_to_admin(db: Session, record: DetectRecord, original_user_id: int):
    """
    将普通用户的检测记录同步到管理员汇总表（AdminDetectRecord）
    - record: 原始检测记录
    - original_user_id: 原始用户ID（创建记录的用户）
    - AdminDetectRecord的ID是连续递增的
    """
    # 只有普通用户才需要同步，管理员不需要同步给自己
    if original_user_id == 1:
        return  # 管理员自己的数据不需要再同步

    # 检查管理员用户是否存在
    admin_user = db.query(User).filter(User.id == 1).first()
    if not admin_user:
        print("⚠️ 管理员用户不存在，跳过数据同步")
        return

    # 创建一条新记录同步到管理员汇总表
    admin_record = AdminDetectRecord(
        original_record_id=record.id,  # 保留原记录ID用于关联
        file_name=record.file_name,
        image_url=record.image_url,
        result_image_url=record.result_image_url,
        disease_count=record.disease_count,
        disease_type=record.disease_type,
        level=record.level,
        confidence=record.confidence,
        duration=record.duration,
        detect_time=record.detect_time,
        user_id=original_user_id  # 记录原始数据来源用户
    )
    db.add(admin_record)
    # 不单独commit，由调用方统一commit

# 病害类别与防治建议映射（与YOLOv13模型输出完全匹配，共4类）
# 对应 PlantVillage 苹果病害数据集标准分类
DISEASE_MAP = {
    0: {
        "name": "黑星病",
        "en_name": "Apple Scab",
        "suggestion": "喷施10%苯醚甲环唑水分散粒剂2000倍液，10天一次，连续2-3次；萌芽前全园喷5波美度石硫合剂；合理修剪保证通风透光，秋冬清除病叶病果集中烧毁",
        "detail": "苹果产区核心病害，危害叶片和果实。叶片出现黑褐色圆形病斑，造成提前脱落；果实染病后龟裂畸形，丧失商品价值，多雨高湿季节极易爆发。"
    },
    1: {
        "name": "黑腐病",
        "en_name": "Black Rot",
        "suggestion": "喷施43%戊唑醇悬浮剂3000倍液，7-10天一次；发病初期可用80%代森锰锌可湿性粉剂800倍液交替喷施；增施有机肥增强树势，及时清除病果病枝",
        "detail": "危害叶片、果实和枝条。叶片形成边缘紫色、中心褐色的'蛙眼状'病斑；果实染病后褐色腐烂，最终全果僵化，高温高湿环境下发病严重。"
    },
    2: {
        "name": "锈病",
        "en_name": "Cedar Apple Rust",
        "suggestion": "喷施25%三唑酮可湿性粉剂2000倍液，展叶期10天一次连续2-3次；清除果园周边5公里内桧柏、雪松等转主寄主；发病后可用12.5%烯唑醇可湿性粉剂2500倍液",
        "detail": "典型转主寄生病害，需通过桧柏/雪松完成生活史。叶片出现橙黄色圆形病斑，后期长出黄褐色毛状孢子器，严重时大量早落叶，春季多雨年份发病极重。"
    },
    3: {
        "name": "健康叶片",
        "en_name": "Healthy",
        "suggestion": "叶片无病害，做好日常水肥管理、合理修剪通风，维持树体健康即可",
        "detail": "叶片无任何病原菌侵染，生长状态良好，无需病害防治处理。"
    }
}


# 严重程度判断
# 病害类别：0-黑星病, 1-黑腐病, 2-锈病, 3-健康叶片
def get_disease_level(cls: int, confidence: float, area_ratio: float):
    if cls == 3:  # 健康叶片
        return "健康"
    # 锈病和黑腐病：直接标记为重度（严重病害）
    if cls in (1, 2):  # 1-黑腐病, 2-锈病
        return "重度"
    # 黑星病：根据置信度和面积比例判断
    if cls == 0:  # 黑星病
        if confidence > 0.85 and area_ratio > 0.08:
            return "重度"
        else:
            return "健康"
    # 默认返回健康
    return "健康"

# Pydantic模型
class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    real_name: Optional[str] = None
    college: Optional[str] = None
    major: Optional[str] = None

class OrchardCreate(BaseModel):
    orchardName: str
    variety: str
    area: float
    age: int
    address: str
    diseaseRate: Optional[float] = 0
    color: Optional[str] = "#1890ff"
    fillColor: Optional[str] = "rgba(24, 144, 255, 0.2)"
    # 默认path使用 [lat, lon] 格式（Leaflet标准格式），即南疆阿克苏地区坐标
    path: Optional[list] = [[41.17, 80.26], [41.17, 80.27], [41.16, 80.27], [41.16, 80.26]]

# 登录接口
@app.post("/auth/login", summary="用户登录")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    access_token = create_access_token(data={"sub": user.username})
    return {
        "code": 200,
        "message": "登录成功",
        "data": {
            "token": access_token,
            "user_info": {
                "id": user.id,
                "username": user.username,
                "real_name": user.real_name,
                "college": user.college,
                "major": user.major
            }
        }
    }

# 注册接口
class RegisterRequest(BaseModel):
    username: str
    password: str

@app.post("/auth/register", summary="用户注册")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 创建新用户
    new_user = User(
        username=request.username,
        hashed_password=get_password_hash(request.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "code": 200,
        "message": "注册成功",
        "data": {
            "id": new_user.id,
            "username": new_user.username
        }
    }

# 获取当前用户信息
@app.get("/auth/userinfo", summary="获取当前用户信息")
def get_userinfo(current_user: User = Depends(get_current_user)):
    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "real_name": current_user.real_name,
            "college": current_user.college,
            "major": current_user.major,
            "email": current_user.email,
            "phone": current_user.phone
        }
    }

# 更新当前用户信息
class UserInfoUpdate(BaseModel):
    real_name: Optional[str] = None
    college: Optional[str] = None
    major: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

@app.put("/auth/userinfo", summary="更新当前用户信息")
def update_userinfo(
    data: UserInfoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if data.real_name is not None:
        current_user.real_name = data.real_name
    if data.college is not None:
        current_user.college = data.college
    if data.major is not None:
        current_user.major = data.major
    if data.email is not None:
        current_user.email = data.email
    if data.phone is not None:
        current_user.phone = data.phone

    db.commit()
    return {
        "code": 200,
        "message": "个人信息更新成功"
    }

# 单张图像检测接口（支持果园关联）
@app.post("/detect/single", summary="单张苹果叶片病害检测")
def single_detect(
    image: UploadFile = File(...),
    orchard_id: Optional[int] = Form(None),  # 果园ID，可选参数
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 校验文件格式
    if not image.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
        raise HTTPException(status_code=400, detail="仅支持JPG/PNG/BMP格式的图片")
    
    # 验证果园归属（如果提供了果园ID）：管理员可选任意果园，普通用户只能选自己的
    orchard = None
    if orchard_id:
        if current_user.username == "admin":
            orchard = db.query(Orchard).filter(Orchard.id == orchard_id).first()
        else:
            orchard = db.query(Orchard).filter(
                Orchard.id == orchard_id,
                Orchard.user_id == current_user.id
            ).first()
        if not orchard:
            raise HTTPException(status_code=404, detail="果园不存在或无权限")
    
    # 保存上传的图片
    file_ext = image.filename.split('.')[-1]
    file_name = f"{uuid.uuid4().hex}.{file_ext}"
    upload_path = f"static/uploads/{file_name}"
    with open(upload_path, "wb") as f:
        f.write(image.file.read())
    
    # 读取图像
    img = cv2.imread(upload_path)
    img_height, img_width = img.shape[:2]
    start_time = datetime.now()
    
    # YOLO模型推理
    results = model(img, conf=0.5, iou=0.45)
    end_time = datetime.now()
    duration = int((end_time - start_time).total_seconds() * 1000)
    
    # 处理检测结果
    disease_list = []
    result_img = img.copy()
    
    for r in results:
        boxes = r.boxes
        for box in boxes:
            # 获取检测框信息
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            
            # 计算病害区域占比
            box_area = (x2 - x1) * (y2 - y1)
            img_area = img_width * img_height
            area_ratio = box_area / img_area
            
            # 获取病害信息
            disease_info = DISEASE_MAP.get(cls, {"name": f"未知病害{cls}", "en_name": "Unknown", "suggestion": "请咨询专业植保人员", "detail": "暂无详细信息"})
            level = get_disease_level(cls, conf, area_ratio)
            
            # 绘制检测框
            color = (0, 0, 255) if level == "重度" else (0, 165, 255) if level == "中度" else (0, 255, 0)
            cv2.rectangle(result_img, (x1, y1), (x2, y2), color, 2)
            label_text = f"{disease_info['name']} {conf:.2f}"
            text_y = max(y1 - 22, 2)  # 防止文字超出图像顶部
            result_img = cv2_put_chinese_text(result_img, label_text, (x1, text_y), font_size=20, color=color)
            
            # 保存病害详情
            disease_list.append({
                "className": disease_info["name"],
                "enName": disease_info["en_name"],
                "confidence": conf,
                "level": level,
                "suggestion": disease_info["suggestion"],
                "detail": disease_info["detail"],
                "bbox": [x1, y1, x2, y2]
            })
    
    # 保存结果图片
    result_file_name = f"result_{file_name}"
    result_path = f"static/results/{result_file_name}"
    cv2.imwrite(result_path, result_img)
    
    # 保存检测记录到数据库
    if disease_list:
        has_severe = any(d["level"] == "重度" for d in disease_list)
        overall_level = "重度" if has_severe else "健康"
    else:
        overall_level = "无"
    detect_record = DetectRecord(
        file_name=image.filename,
        image_url=f"/static/uploads/{file_name}",
        result_image_url=f"/static/results/{result_file_name}",
        disease_count=len(disease_list),
        disease_type="、".join([d["className"] for d in disease_list]) if disease_list else "无",
        level=overall_level,
        confidence=max([d["confidence"] for d in disease_list]) if disease_list else None,
        duration=duration,
        detect_time=datetime.now(),
        user_id=current_user.id
    )
    db.add(detect_record)
    db.commit()

    # 同步数据到管理员账户
    sync_record_to_admin(db, detect_record, current_user.id)
    db.commit()

    # 如果指定了果园，生成病害点数据（基于果园中心点生成采样点）
    disease_points_created = 0
    if orchard:
        orchard_path = orchard.path
        # 计算果园中心点
        if orchard_path and len(orchard_path) > 0:
            # 支持单点 [lat, lon] 或多边形 [[[lat,lon], [lat,lon], ...]]
            if len(orchard_path) == 1:
                center_lat, center_lon = orchard_path[0][0], orchard_path[0][1]
            else:
                # 多边形：计算所有顶点的平均中心
                lats = [p[0] for p in orchard_path]
                lons = [p[1] for p in orchard_path]
                center_lat, center_lon = sum(lats) / len(lats), sum(lons) / len(lons)
            
            # 为每个检测结果创建一个病害点记录（含健康叶片，用于统计分母）
            if disease_list:
                for disease in disease_list:
                    disease_point = DiseasePoint(
                        coordinate=[center_lat + (np.random.random() - 0.5) * 0.001, 
                                   center_lon + (np.random.random() - 0.5) * 0.001],  # 在果园中心附近随机分布
                        disease_type=disease["className"],
                        level=disease["level"],
                        confidence=disease["confidence"],
                        detect_time=datetime.now(),
                        orchard_id=orchard_id
                    )
                    db.add(disease_point)
                    if disease["className"] != "健康叶片":
                        disease_points_created += 1
            else:
                # 没有检测结果，记录一个健康采样点
                disease_point = DiseasePoint(
                    coordinate=[center_lat + (np.random.random() - 0.5) * 0.001,
                               center_lon + (np.random.random() - 0.5) * 0.001],
                    disease_type="健康叶片",
                    level="无",
                    confidence=None,
                    detect_time=datetime.now(),
                    orchard_id=orchard_id
                )
                db.add(disease_point)
            
            # 先提交病害点数据，再统计计算病害率
            db.commit()
            
            # 更新果园的病害率：病害点数 / 总采样点数 × 100%
            total_points = db.query(DiseasePoint).filter(DiseasePoint.orchard_id == orchard_id).count()
            disease_points_total = db.query(DiseasePoint).filter(
                DiseasePoint.orchard_id == orchard_id,
                DiseasePoint.disease_type != "健康叶片"
            ).count()
            orchard.disease_rate = min(100, round(disease_points_total / total_points * 100, 1)) if total_points > 0 else 0
            
            db.commit()

    db.refresh(detect_record)

    # 返回结果
    return {
        "code": 200,
        "message": f"检测完成，{'已添加到果园' if disease_points_created > 0 else '未关联果园'}",
        "data": {
            "id": detect_record.id,
            "resultImageUrl": detect_record.result_image_url,
            "detectTime": detect_record.detect_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": detect_record.duration,
            "diseaseCount": detect_record.disease_count,
            "diseaseList": disease_list,
            "orchardId": orchard_id,
            "diseasePointsCreated": disease_points_created,
            "updatedDiseaseRate": orchard.disease_rate if orchard else None
        }
    }

# 批量检测接口（支持果园关联）
@app.post("/detect/batch", summary="批量苹果叶片病害检测")
def batch_detect(
    images: List[UploadFile] = File(...),
    orchard_id: Optional[int] = Form(None),  # 果园ID，可选参数
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 验证果园归属：管理员可选任意果园，普通用户只能选自己的
    orchard = None
    if orchard_id:
        if current_user.username == "admin":
            orchard = db.query(Orchard).filter(Orchard.id == orchard_id).first()
        else:
            orchard = db.query(Orchard).filter(
                Orchard.id == orchard_id,
                Orchard.user_id == current_user.id
            ).first()
        if not orchard:
            raise HTTPException(status_code=404, detail="果园不存在或无权限")
    
    result_list = []
    total_count = len(images)
    disease_total_count = 0
    disease_points_created = 0
    
    # 获取果园中心点（如果指定了果园）
    center_lat, center_lon = None, None
    if orchard and orchard.path:
        if len(orchard.path) == 1:
            center_lat, center_lon = orchard.path[0][0], orchard.path[0][1]
        else:
            lats = [p[0] for p in orchard.path]
            lons = [p[1] for p in orchard.path]
            center_lat, center_lon = sum(lats) / len(lats), sum(lons) / len(lons)
    
    for idx, image in enumerate(images):
        if not image.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            continue
        
        file_ext = image.filename.split('.')[-1]
        file_name = f"{uuid.uuid4().hex}.{file_ext}"
        upload_path = f"static/uploads/{file_name}"
        with open(upload_path, "wb") as f:
            f.write(image.file.read())
        
        img = cv2.imread(upload_path)
        img_height, img_width = img.shape[:2]
        start_time = datetime.now()
        results = model(img, conf=0.5, iou=0.45)
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds() * 1000)
        
        disease_list = []
        result_img = img.copy()
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                box_area = (x2 - x1) * (y2 - y1)
                img_area = img_width * img_height
                area_ratio = box_area / img_area
                
                disease_info = DISEASE_MAP.get(cls, {"name": f"未知病害{cls}", "en_name": "Unknown", "suggestion": "请咨询专业植保人员", "detail": "暂无详细信息"})
                level = get_disease_level(cls, conf, area_ratio)
                
                color = (0, 0, 255) if level == "重度" else (0, 165, 255) if level == "中度" else (0, 255, 0)
                cv2.rectangle(result_img, (x1, y1), (x2, y2), color, 2)
                label_text = f"{disease_info['name']} {conf:.2f}"
                text_y = max(y1 - 22, 2)  # 防止文字超出图像顶部
                result_img = cv2_put_chinese_text(result_img, label_text, (x1, text_y), font_size=20, color=color)
                
                disease_list.append({
                    "className": disease_info["name"],
                    "enName": disease_info["en_name"],
                    "confidence": conf,
                    "level": level,
                    "suggestion": disease_info["suggestion"],
                    "detail": disease_info["detail"],
                    "bbox": [x1, y1, x2, y2]
                })
        
        result_file_name = f"result_{file_name}"
        result_path = f"static/results/{result_file_name}"
        cv2.imwrite(result_path, result_img)
        
        if disease_list:
            has_severe = any(d["level"] == "重度" for d in disease_list)
            overall_level = "重度" if has_severe else "健康"
        else:
            overall_level = "无"
        
        detect_record = DetectRecord(
            file_name=image.filename,
            image_url=f"/static/uploads/{file_name}",
            result_image_url=f"/static/results/{result_file_name}",
            disease_count=len(disease_list),
            disease_type="、".join([d["className"] for d in disease_list]) if disease_list else "无",
            level=overall_level,
            confidence=max([d["confidence"] for d in disease_list]) if disease_list else None,
            duration=duration,
            detect_time=datetime.now(),
            user_id=current_user.id
        )
        db.add(detect_record)
        db.commit()

        # 同步数据到管理员账户
        sync_record_to_admin(db, detect_record, current_user.id)
        db.commit()

        # 如果指定了果园，生成病害点数据（含健康，用于统计分母）
        if orchard and center_lat and center_lon and disease_list:
            for disease in disease_list:
                # 每张图片在中心点附近生成一个随机位置
                offset = idx * 0.0005  # 每张图片错开一点位置
                disease_point = DiseasePoint(
                    coordinate=[center_lat + offset + (np.random.random() - 0.5) * 0.001, 
                               center_lon + (np.random.random() - 0.5) * 0.001],
                    disease_type=disease["className"],
                    level=disease["level"],
                    confidence=disease["confidence"],
                    detect_time=datetime.now(),
                    orchard_id=orchard_id
                )
                db.add(disease_point)
                if disease["className"] != "健康叶片":
                    disease_points_created += 1
        
        db.refresh(detect_record)
        disease_total_count += len(disease_list)
        result_list.append({
            "id": detect_record.id,
            "fileName": image.filename,
            "resultImageUrl": detect_record.result_image_url,
            "duration": detect_record.duration,
            "diseaseCount": detect_record.disease_count,
            "diseaseList": disease_list
        })
    
    # 更新果园病害率：病害点数 / 总采样点数 × 100%
    if orchard:
        db.commit()  # 先提交本批病害点
        total_points = db.query(DiseasePoint).filter(DiseasePoint.orchard_id == orchard_id).count()
        disease_points_total = db.query(DiseasePoint).filter(
            DiseasePoint.orchard_id == orchard_id,
            DiseasePoint.disease_type != "健康叶片"
        ).count()
        orchard.disease_rate = min(100, round(disease_points_total / total_points * 100, 1)) if total_points > 0 else 0
        db.commit()
    
    return {
        "code": 200,
        "message": f"批量检测完成，{'已添加到果园' if disease_points_created > 0 else '未关联果园'}",
        "data": {
            "totalCount": total_count,
            "diseaseTotalCount": disease_total_count,
            "list": result_list,
            "orchardId": orchard_id,
            "diseasePointsCreated": disease_points_created,
            "updatedDiseaseRate": orchard.disease_rate if orchard else None
        }
    }

# 历史记录列表接口
@app.get("/history/list", summary="获取检测历史记录列表")
def get_history_list(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=10000),
    disease_type: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    sort_order: Optional[str] = Query("desc", description="排序方式: asc升序, desc降序"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 管理员从AdminDetectRecord表查询（汇总所有用户数据）
    # 普通用户从DetectRecord表查询
    is_admin = current_user.username == "admin"
    
    if is_admin:
        # 管理员查询管理员汇总表
        query = db.query(AdminDetectRecord)
    else:
        # 普通用户查询自己的表
        query = db.query(DetectRecord).filter(DetectRecord.user_id == current_user.id)
    
    # 筛选条件
    if disease_type:
        if is_admin:
            query = query.filter(AdminDetectRecord.disease_type.like(f"%{disease_type}%"))
        else:
            query = query.filter(DetectRecord.disease_type.like(f"%{disease_type}%"))
    if level:
        if is_admin:
            query = query.filter(AdminDetectRecord.level == level)
        else:
            query = query.filter(DetectRecord.level == level)
    if start_date:
        if is_admin:
            query = query.filter(AdminDetectRecord.detect_time >= start_date)
        else:
            query = query.filter(DetectRecord.detect_time >= start_date)
    if end_date:
        if is_admin:
            query = query.filter(AdminDetectRecord.detect_time <= end_date)
        else:
            query = query.filter(DetectRecord.detect_time <= end_date)
    
    # 排序（根据sort_order参数）
    sort_column = AdminDetectRecord.id if is_admin else DetectRecord.id
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    # 分页
    total = query.count()
    records = query.offset((page-1)*size).limit(size).all()
    
    # 格式化返回
    record_list = []
    # 获取所有用户名映射
    all_users = {u.id: u.username for u in db.query(User).all()}
    for record in records:
        if is_admin:
            # 管理员表
            record_list.append({
                "id": record.id,  # 管理员表ID（连续递增）
                "originalRecordId": record.original_record_id,  # 原用户记录ID
                "fileName": record.file_name,
                "imageUrl": record.image_url,
                "resultImageUrl": record.result_image_url,
                "diseaseCount": record.disease_count,
                "diseaseType": record.disease_type,
                "level": record.level,
                "confidence": record.confidence,
                "duration": record.duration,
                "detectTime": record.detect_time.strftime("%Y-%m-%d %H:%M:%S"),
                "sourceUserId": record.user_id,  # 来源用户ID
                "sourceUserName": all_users.get(record.user_id)  # 来源用户名
            })
        else:
            record_list.append({
                "id": record.id,
                "fileName": record.file_name,
                "imageUrl": record.image_url,
                "resultImageUrl": record.result_image_url,
                "diseaseCount": record.disease_count,
                "diseaseType": record.disease_type,
                "level": record.level,
                "confidence": record.confidence,
                "duration": record.duration,
                "detectTime": record.detect_time.strftime("%Y-%m-%d %H:%M:%S"),
                "sourceUserId": record.source_user_id,
                "sourceUserName": all_users.get(record.source_user_id) if record.source_user_id else None
            })
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "total": total,
            "records": record_list,
            "page": page,
            "size": size
        }
    }

# 导出历史检测数据（CSV格式）- 注意：这个接口必须在 /history/{record_id} 之前，否则 "export" 会被当作 record_id 处理
@app.get("/history/export", summary="导出检测历史记录CSV")
def export_history(
    disease_type: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    sort_order: Optional[str] = Query("asc", description="排序方式: asc升序, desc降序"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    import csv, io
    # 管理员从AdminDetectRecord表导出，普通用户从DetectRecord表导出
    is_admin = current_user.username == "admin"
    if is_admin:
        query = db.query(AdminDetectRecord)
    else:
        query = db.query(DetectRecord).filter(DetectRecord.user_id == current_user.id)
    
    if disease_type:
        if is_admin:
            query = query.filter(AdminDetectRecord.disease_type.like(f"%{disease_type}%"))
        else:
            query = query.filter(DetectRecord.disease_type.like(f"%{disease_type}%"))
    if level:
        if is_admin:
            query = query.filter(AdminDetectRecord.level == level)
        else:
            query = query.filter(DetectRecord.level == level)
    if start_date:
        if is_admin:
            query = query.filter(AdminDetectRecord.detect_time >= start_date)
        else:
            query = query.filter(DetectRecord.detect_time >= start_date)
    if end_date:
        if is_admin:
            query = query.filter(AdminDetectRecord.detect_time <= end_date)
        else:
            query = query.filter(DetectRecord.detect_time <= end_date)

    sort_column = AdminDetectRecord.id if is_admin else DetectRecord.id
    if sort_order == "asc":
        records = query.order_by(sort_column.asc()).all()
    else:
        records = query.order_by(sort_column.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["编号", "文件名", "病害类型", "病害数量", "严重程度", "置信度", "检测耗时(ms)", "检测时间"])
    for r in records:
        writer.writerow([
            r.id,
            r.file_name,
            r.disease_type or "无",
            r.disease_count,
            r.level or "无",
            f"{r.confidence * 100:.2f}%" if r.confidence else "-",
            r.duration,
            r.detect_time.strftime("%Y-%m-%d %H:%M:%S")
        ])

    from urllib.parse import quote
    filename = quote("病害检测记录.csv")
    from fastapi.responses import Response
    return Response(
        content=output.getvalue().encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{filename}"}
    )

# 查看历史记录详情（含完整病害列表）- 必须在 /history/export 之后定义
@app.get("/history/{record_id}", summary="查看历史记录详情")
def get_history_detail(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    is_admin = current_user.username == "admin"

    if is_admin:
        # 管理员：先从 admin_detect_records 表查（record_id 是该表的 id）
        admin_record = db.query(AdminDetectRecord).filter(
            AdminDetectRecord.id == record_id
        ).first()
        if not admin_record:
            raise HTTPException(status_code=404, detail="记录不存在")
        # 用 admin_record 的字段构建返回数据
        disease_type = admin_record.disease_type
        record_data = {
            "id": admin_record.id,
            "fileName": admin_record.file_name,
            "imageUrl": admin_record.image_url,
            "resultImageUrl": admin_record.result_image_url,
            "diseaseCount": admin_record.disease_count,
            "diseaseType": disease_type,
            "level": admin_record.level,
            "confidence": admin_record.confidence,
            "duration": admin_record.duration,
            "detectTime": admin_record.detect_time.strftime("%Y-%m-%d %H:%M:%S") if admin_record.detect_time else "-",
            "sourceUserId": admin_record.user_id,
        }
        confidence = admin_record.confidence
        level = admin_record.level
    else:
        # 普通用户：只能查自己的记录
        record = db.query(DetectRecord).filter(
            DetectRecord.id == record_id,
            DetectRecord.user_id == current_user.id
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")
        disease_type = record.disease_type
        record_data = {
            "id": record.id,
            "fileName": record.file_name,
            "imageUrl": record.image_url,
            "resultImageUrl": record.result_image_url,
            "diseaseCount": record.disease_count,
            "diseaseType": disease_type,
            "level": record.level,
            "confidence": record.confidence,
            "duration": record.duration,
            "detectTime": record.detect_time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        confidence = record.confidence
        level = record.level

    # 从 disease_type 字符串解析病害名，构建完整详情
    name_to_info = {v["name"]: v for v in DISEASE_MAP.values()}
    disease_list = []
    if disease_type and disease_type != "无":
        for dname in [n.strip() for n in disease_type.split("、")]:
            info = name_to_info.get(dname, {"en_name": "-", "detail": "-", "suggestion": "请咨询专业植保人员"})
            disease_list.append({
                "className": dname,
                "enName": info.get("en_name", "-"),
                "confidence": confidence,
                "level": level or "无",
                "suggestion": info.get("suggestion", "请咨询专业植保人员"),
                "detail": info.get("detail", "-")
            })

    record_data["diseaseList"] = disease_list

    return {
        "code": 200,
        "data": record_data
    }

# 删除历史记录接口
@app.delete("/history/{record_id}", summary="删除检测历史记录")
def delete_history(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 管理员可以删除所有记录，普通用户只能删除自己的记录
    if current_user.username == "admin":
        # 管理员视图的ID是AdminDetectRecord的ID，通过original_record_id关联DetectRecord
        admin_record = db.query(AdminDetectRecord).filter(AdminDetectRecord.id == record_id).first()
        if not admin_record:
            raise HTTPException(status_code=404, detail="记录不存在或无权删除")
        # 用original_record_id找到并删除原始记录
        record = db.query(DetectRecord).filter(DetectRecord.id == admin_record.original_record_id).first()
        if record:
            db.delete(record)
        db.delete(admin_record)
    else:
        record = db.query(DetectRecord).filter(
            DetectRecord.id == record_id,
            DetectRecord.user_id == current_user.id
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在或无权删除")
        # 同时删除AdminDetectRecord中对应的记录
        admin_record = db.query(AdminDetectRecord).filter(
            AdminDetectRecord.original_record_id == record.id
        ).first()
        if admin_record:
            db.delete(admin_record)
        db.delete(record)
    db.commit()
    return {
        "code": 200,
        "message": "删除成功"
    }


# 下载检测结果图片接口
@app.get("/download/{record_id}", summary="下载检测结果图片")
def download_result_image(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    is_admin = current_user.username == "admin"
    if is_admin:
        # 管理员从 admin_detect_records 表查
        record = db.query(AdminDetectRecord).filter(AdminDetectRecord.id == record_id).first()
    else:
        # 普通用户只能下载自己的
        record = db.query(DetectRecord).filter(
            DetectRecord.id == record_id,
            DetectRecord.user_id == current_user.id
        ).first()

    if not record:
        raise HTTPException(status_code=404, detail="检测记录不存在")

    # 把接口返回的url，转换成本地文件路径
    # 比如 /static/results/xxx.jpg → static/results/xxx.jpg
    file_local_path = record.result_image_url.lstrip("/")

    # 校验文件是否存在
    if not os.path.exists(file_local_path):
        raise HTTPException(status_code=404, detail="结果图片文件不存在")

    # 返回文件下载响应
    return FileResponse(
        path=file_local_path,
        filename=f"病害检测结果_{record.file_name}",  # 下载到本地的文件名
        media_type="image/jpeg"
    )

# 下载检测报告（HTML格式，含病害详情+防治建议）
@app.get("/report/{record_id}", summary="下载检测报告HTML")
def download_report(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from fastapi.responses import HTMLResponse
    import base64, json as _json

    is_admin = current_user.username == "admin"
    if is_admin:
        # 管理员从 admin_detect_records 表查
        record = db.query(AdminDetectRecord).filter(AdminDetectRecord.id == record_id).first()
    else:
        record = db.query(DetectRecord).filter(
            DetectRecord.id == record_id,
            DetectRecord.user_id == current_user.id
        ).first()
    if not record:
        raise HTTPException(status_code=404, detail="检测记录不存在")

    # 读取结果图片并转为base64嵌入HTML
    img_path = record.result_image_url.lstrip("/")
    img_b64 = ""
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

    # 读取病害详情（存在 disease_type 字段，需重新推断详情）
    # 从 DISEASE_MAP 中根据病害名匹配详情
    name_to_info = {v["name"]: v for v in DISEASE_MAP.values()}


    # 解析 disease_type 字段里记录的病害名列表，过滤掉健康叶片
    disease_names = [n.strip() for n in record.disease_type.split("、")] if record.disease_type and record.disease_type != "无" else []
    # 过滤掉健康叶片，只展示真实病害
    disease_names = [n for n in disease_names if n not in ("健康叶片", "Healthy")]

    # 构造病害详情行
    disease_rows_html = ""
    for dname in disease_names:
        info = name_to_info.get(dname, {"en_name": "-", "detail": "-", "suggestion": "-"})
        disease_rows_html += f"""
        <tr>
            <td><strong>{dname}</strong><br><small style="color:#888">{info.get('en_name','-')}</small></td>
            <td>{info.get('detail','-')}</td>
            <td>{info.get('suggestion','-')}</td>
        </tr>"""

    if not disease_rows_html:
        # 没有真实病害 → 显示健康提示
        disease_rows_html = '<tr><td colspan="3" style="text-align:center;color:green;font-weight:bold;">✅ 未检测到病害，叶片健康</td></tr>'

    level_color = {"重度": "#ff4d4f", "中度": "#faad14", "轻度": "#52c41a", "健康": "#52c41a", "无": "#999"}.get(record.level or "无", "#999")
    confidence_str = f"{record.confidence * 100:.2f}%" if record.confidence else "-"
    detect_time_str = record.detect_time.strftime("%Y年%m月%d日 %H:%M:%S") if record.detect_time else "-"

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>苹果叶片病害检测报告</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: "Microsoft YaHei", "SimHei", Arial, sans-serif; background: #f5f7fa; color: #333; }}
  .report-wrap {{ max-width: 900px; margin: 30px auto; background: #fff; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.10); overflow: hidden; }}
  .report-header {{ background: linear-gradient(135deg, #1a7f37 0%, #2d9e50 100%); color: #fff; padding: 32px 40px; }}
  .report-header h1 {{ font-size: 24px; font-weight: 700; margin-bottom: 6px; }}
  .report-header p {{ font-size: 13px; opacity: 0.85; }}
  .report-body {{ padding: 32px 40px; }}
  .section-title {{ font-size: 16px; font-weight: 700; color: #1a7f37; border-left: 4px solid #1a7f37; padding-left: 10px; margin: 28px 0 16px; }}
  .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 8px; }}
  .info-item {{ background: #f9fafb; border-radius: 8px; padding: 12px 16px; }}
  .info-item label {{ font-size: 12px; color: #888; display: block; margin-bottom: 4px; }}
  .info-item span {{ font-size: 15px; font-weight: 600; color: #222; }}
  .level-badge {{ display: inline-block; padding: 2px 12px; border-radius: 20px; color: #fff; font-size: 13px; font-weight: bold; background: {level_color}; }}
  .result-img {{ width: 100%; max-height: 420px; object-fit: contain; border-radius: 8px; border: 1px solid #e8e8e8; display: block; margin: 0 auto; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 4px; }}
  th {{ background: #f0f7f0; color: #1a7f37; font-weight: 700; padding: 10px 14px; text-align: left; border-bottom: 2px solid #d9f0d9; }}
  td {{ padding: 12px 14px; border-bottom: 1px solid #f0f0f0; vertical-align: top; line-height: 1.6; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #fafff8; }}
  .report-footer {{ background: #f9fafb; border-top: 1px solid #eee; padding: 18px 40px; text-align: center; color: #aaa; font-size: 12px; }}
  @media print {{
    body {{ background: #fff; }}
    .report-wrap {{ box-shadow: none; margin: 0; }}
    .print-btn {{ display: none; }}
  }}
  .print-btn {{ display: block; margin: 0 auto 0; text-align: center; padding: 10px 32px; background: #1a7f37; color: #fff; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; margin-top: 20px; }}
</style>
</head>
<body>
<div class="report-wrap">
  <div class="report-header">
    <h1>🍎 苹果叶片病害检测报告</h1>
    <p>基于YOLOv13深度学习模型 · 塔里木大学信息工程学院 · 智慧果园病害检测系统</p>
  </div>
  <div class="report-body">

    <div class="section-title">基本信息</div>
    <div class="info-grid">
      <div class="info-item"><label>原始文件名</label><span>{record.file_name}</span></div>
      <div class="info-item"><label>检测时间</label><span>{detect_time_str}</span></div>
      <div class="info-item"><label>检测耗时</label><span>{record.duration} ms</span></div>
      <div class="info-item"><label>检测到病害数</label><span>{record.disease_count} 处</span></div>
      <div class="info-item"><label>病害类型</label><span>{record.disease_type or "无"}</span></div>
      <div class="info-item"><label>综合严重程度</label><span><em class="level-badge">{record.level or "无"}</em></span></div>
      <div class="info-item"><label>最高置信度</label><span>{confidence_str}</span></div>
      <div class="info-item"><label>检测模型</label><span>YOLOv13（自训练苹果病害模型）</span></div>
    </div>

    <div class="section-title">检测结果图</div>
    <img class="result-img" src="data:image/jpeg;base64,{img_b64}" alt="检测结果图" />

    <div class="section-title">病害详情与防治建议</div>
    <table>
      <thead>
        <tr>
          <th style="width:160px">病害名称</th>
          <th style="width:280px">病害描述</th>
          <th>防治建议</th>
        </tr>
      </thead>
      <tbody>
        {disease_rows_html}
      </tbody>
    </table>

    <button class="print-btn" onclick="window.print()">🖨️ 打印 / 保存为 PDF</button>

  </div>
  <div class="report-footer">
    本报告由苹果叶片病害检测系统自动生成 · 仅供参考，实际防治请结合田间专业诊断
  </div>
</div>
</body>
</html>"""

    from fastapi.responses import Response
    return Response(
        content=html_content.encode("utf-8"),
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="病害检测报告_{record.id}.html"'}
    )


# 直接从检测结果数据生成报告（不依赖数据库 id，前端直接 POST 检测结果）
class ReportGenerateRequest(BaseModel):
    # 前端发送 snake_case：file_name, disease_count, disease_list, result_image_url
    file_name: str = "未知文件"
    detect_time: str = ""
    duration: int = 0
    disease_count: int = 0
    disease_list: list = []
    result_image_url: str = ""

@app.post("/report/generate", summary="根据检测结果直接生成HTML报告")
def generate_report(
    data: ReportGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    import base64
    from fastapi.responses import Response

    # 读取结果图片转 base64
    img_b64 = ""
    if data.result_image_url:
        img_path = data.result_image_url.lstrip("/")
        # 兼容带域名的完整 URL，只取路径部分
        if img_path.startswith("http"):
            from urllib.parse import urlparse
            img_path = urlparse(data.result_image_url).path.lstrip("/")
        if os.path.exists(img_path):
            with open(img_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")

    name_to_info = {v["name"]: v for v in DISEASE_MAP.values()}

    # 构造病害详情行（从传入的 disease_list 直接拿，数据最准）
    # 过滤掉健康叶片，只展示真实病害
    disease_rows_html = ""
    seen = set()
    for d in data.disease_list:
        dname = d.get("className", "")
        # 跳过健康叶片（不是病害，无需展示在病害详情表中）
        if dname in ("健康叶片", "Healthy") or dname in seen:
            continue
        seen.add(dname)
        info = name_to_info.get(dname, {"en_name": "-", "detail": d.get("detail", "-"), "suggestion": d.get("suggestion", "-")})
        level = d.get("level", "-")
        conf = d.get("confidence", 0)
        level_td_color = {"重度": "#ff4d4f", "中度": "#faad14", "轻度": "#52c41a", "无": "#52c41a"}.get(level, "#999")
        disease_rows_html += f"""
        <tr>
            <td><strong>{dname}</strong><br><small style="color:#888">{info.get('en_name','-')}</small><br>
            <span style="display:inline-block;padding:1px 8px;border-radius:10px;background:{level_td_color};color:#fff;font-size:12px;margin-top:3px">{level}</span>
            <span style="color:#888;font-size:12px;margin-left:6px">置信度: {conf*100:.1f}%</span></td>
            <td>{info.get('detail', d.get('detail', '-'))}</td>
            <td>{info.get('suggestion', d.get('suggestion', '-'))}</td>
        </tr>"""

    if not disease_rows_html:
        disease_rows_html = '<tr><td colspan="3" style="text-align:center;color:green;font-weight:bold;padding:20px">✅ 未检测到病害，叶片健康</td></tr>'

    # 整体严重程度
    # 只取真实病害的level（过滤掉"健康"、"无"等非病害等级），避免 ValueError
    levels = [
        d.get("level", "无") for d in data.disease_list
        if d.get("level") in ("轻度", "中度", "重度")
    ]
    if levels:
        overall_level = max(levels, key=["轻度", "中度", "重度"].index)
    else:
        # 没有病害等级 → 看是否有健康叶片
        has_healthy = any(d.get("className") in ("健康叶片", "Healthy") for d in data.disease_list)
        overall_level = "健康" if (data.disease_list and has_healthy) else ("健康" if data.disease_list else "无")

    level_color = {"重度": "#ff4d4f", "中度": "#faad14", "轻度": "#52c41a", "健康": "#52c41a", "无": "#999"}.get(overall_level, "#999")
    max_conf = max([d.get("confidence", 0) for d in data.disease_list], default=0)
    confidence_str = f"{max_conf * 100:.2f}%" if max_conf else "-"

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>苹果叶片病害检测报告</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: "Microsoft YaHei", "SimHei", Arial, sans-serif; background: #f5f7fa; color: #333; }}
  .report-wrap {{ max-width: 900px; margin: 30px auto; background: #fff; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.10); overflow: hidden; }}
  .report-header {{ background: linear-gradient(135deg, #1a7f37 0%, #2d9e50 100%); color: #fff; padding: 32px 40px; }}
  .report-header h1 {{ font-size: 24px; font-weight: 700; margin-bottom: 6px; }}
  .report-header p {{ font-size: 13px; opacity: 0.85; }}
  .report-body {{ padding: 32px 40px; }}
  .section-title {{ font-size: 16px; font-weight: 700; color: #1a7f37; border-left: 4px solid #1a7f37; padding-left: 10px; margin: 28px 0 16px; }}
  .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 8px; }}
  .info-item {{ background: #f9fafb; border-radius: 8px; padding: 12px 16px; }}
  .info-item label {{ font-size: 12px; color: #888; display: block; margin-bottom: 4px; }}
  .info-item span {{ font-size: 15px; font-weight: 600; color: #222; }}
  .level-badge {{ display: inline-block; padding: 2px 12px; border-radius: 20px; color: #fff; font-size: 13px; font-weight: bold; background: {level_color}; }}
  .result-img {{ width: 100%; max-height: 420px; object-fit: contain; border-radius: 8px; border: 1px solid #e8e8e8; display: block; margin: 0 auto; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 4px; }}
  th {{ background: #f0f7f0; color: #1a7f37; font-weight: 700; padding: 10px 14px; text-align: left; border-bottom: 2px solid #d9f0d9; }}
  td {{ padding: 12px 14px; border-bottom: 1px solid #f0f0f0; vertical-align: top; line-height: 1.6; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #fafff8; }}
  .report-footer {{ background: #f9fafb; border-top: 1px solid #eee; padding: 18px 40px; text-align: center; color: #aaa; font-size: 12px; }}
  @media print {{
    body {{ background: #fff; }}
    .report-wrap {{ box-shadow: none; margin: 0; }}
    .print-btn {{ display: none; }}
  }}
  .print-btn {{ display: block; margin: 20px auto 0; text-align: center; padding: 10px 32px; background: #1a7f37; color: #fff; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; }}
</style>
</head>
<body>
<div class="report-wrap">
  <div class="report-header">
    <h1>🍎 苹果叶片病害检测报告</h1>
    <p>基于YOLOv13深度学习模型 · 塔里木大学信息工程学院 · 智慧果园病害检测系统</p>
  </div>
  <div class="report-body">
    <div class="section-title">基本信息</div>
    <div class="info-grid">
      <div class="info-item"><label>原始文件名</label><span>{data.file_name}</span></div>
      <div class="info-item"><label>检测时间</label><span>{data.detect_time or '-'}</span></div>
      <div class="info-item"><label>检测耗时</label><span>{data.duration} ms</span></div>
      <div class="info-item"><label>检测到病害数</label><span>{data.disease_count} 处</span></div>
      <div class="info-item"><label>综合严重程度</label><span><em class="level-badge">{overall_level}</em></span></div>
      <div class="info-item"><label>最高置信度</label><span>{confidence_str}</span></div>
      <div class="info-item"><label>检测用户</label><span>{current_user.username}</span></div>
      <div class="info-item"><label>检测模型</label><span>YOLOv13（苹果病害专项模型）</span></div>
    </div>

    <div class="section-title">检测结果图</div>
    {'<img class="result-img" src="data:image/jpeg;base64,' + img_b64 + '" alt="检测结果图" />' if img_b64 else '<p style="color:#999;text-align:center;padding:20px">（结果图片未找到）</p>'}

    <div class="section-title">病害详情与防治建议</div>
    <table>
      <thead>
        <tr>
          <th style="width:200px">病害名称 / 严重程度</th>
          <th style="width:260px">病害描述</th>
          <th>防治建议</th>
        </tr>
      </thead>
      <tbody>
        {disease_rows_html}
      </tbody>
    </table>

    <button class="print-btn" onclick="window.print()">🖨️ 打印 / 保存为 PDF</button>
  </div>
  <div class="report-footer">
    本报告由苹果叶片病害检测系统自动生成 · 仅供参考，实际防治请结合田间专业诊断
  </div>
</div>
</body>
</html>"""

    from urllib.parse import quote
    encoded_name = quote('病害检测报告.html')
    return Response(
        content=html_content.encode("utf-8"),
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_name}"}
    )


@app.get("/orchard/list", summary="获取果园列表")
def get_orchard_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 管理员看到所有果园，普通用户只看自己和同步过来的果园
    if current_user.username == "admin":
        orchards = db.query(Orchard).all()
    else:
        orchards = db.query(Orchard).filter(
            (Orchard.user_id == current_user.id) | (Orchard.source_user_id == current_user.id)
        ).all()

    # 获取所有用户名映射
    all_users = {u.id: u.username for u in db.query(User).all()}





    orchard_list = []
    for orchard in orchards:
        # 动态统计该果园的真实病害率（从DiseasePoint实时计算）
        total_points = db.query(DiseasePoint).filter(DiseasePoint.orchard_id == orchard.id).count()
        disease_points = db.query(DiseasePoint).filter(
            DiseasePoint.orchard_id == orchard.id,
            DiseasePoint.disease_type != "健康叶片"
        ).count()
        
        if total_points > 0:
            # 有采样数据，动态计算
            real_disease_rate = min(100, round(disease_points / total_points * 100, 1))
        else:
            # 无采样数据，使用数据库存储值
            real_disease_rate = orchard.disease_rate or 0
        
        # 如果计算值与数据库值不一致，同步更新数据库
        if real_disease_rate != orchard.disease_rate:
            orchard.disease_rate = real_disease_rate
        
        orchard_list.append({
            "id": orchard.id,
            "orchardName": orchard.orchard_name,
            "variety": orchard.variety,
            "area": orchard.area,
            "age": orchard.age,
            "diseaseRate": real_disease_rate,
            "address": orchard.address,
            "color": orchard.color,
            "fillColor": orchard.fill_color,
            "path": orchard.path,
            "sourceUserId": orchard.source_user_id,
            "sourceUserName": all_users.get(orchard.source_user_id) if orchard.source_user_id else None
        })
    
    db.commit()  # 保存病害率更新

    # 如果是管理员，还返回果园总数
    total_count = db.query(Orchard).count()

    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "orchards": orchard_list,
            "total": total_count
        }
    }





@app.post("/orchard/add", summary="新增果园地块")
def add_orchard(
    data: OrchardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    orchard = Orchard(
        orchard_name=data.orchardName,
        variety=data.variety,
        area=data.area,
        age=data.age,
        address=data.address,
        disease_rate=data.diseaseRate or 0,
        color=data.color or "#1890ff",
        fill_color=data.fillColor or "rgba(24, 144, 255, 0.2)",
        path=data.path or [[39.9, 116.4]],  # 默认使用 [lat, lon] 格式
        user_id=current_user.id,
        source_user_id=current_user.id if current_user.id != 1 else None
    )
    db.add(orchard)
    db.commit()

    # 同步到管理员（如果当前用户不是管理员）
    if current_user.id != 1:
        admin_orchard = Orchard(
            orchard_name=data.orchardName,
            variety=data.variety,
            area=data.area,
            age=data.age,
            address=data.address,
            disease_rate=data.diseaseRate or 0,
            color=data.color or "#1890ff",
            fill_color=data.fillColor or "rgba(24, 144, 255, 0.2)",
            path=data.path or [[39.9, 116.4]],  # 默认使用 [lat, lon] 格式
            user_id=1,  # 管理员ID
            source_user_id=current_user.id  # 记录来源
        )
        db.add(admin_orchard)
        db.commit()

    db.refresh(orchard)

    return {
        "code": 200,
        "message": "新增成功",
        "data": {
            "id": orchard.id,
            "orchardName": orchard.orchard_name,
            "variety": orchard.variety,
            "area": orchard.area,
            "age": orchard.age,
            "diseaseRate": orchard.disease_rate,
            "address": orchard.address,
            "color": orchard.color,
            "fillColor": orchard.fill_color,
            "path": orchard.path
        }
    }

# 删除果园地块接口
@app.delete("/orchard/{orchard_id}", summary="删除果园地块")
def delete_orchard(
    orchard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 查询果园：管理员可删除所有果园，普通用户只能删除自己的
    if current_user.username == "admin":
        orchard = db.query(Orchard).filter(Orchard.id == orchard_id).first()
    else:
        orchard = db.query(Orchard).filter(
            Orchard.id == orchard_id,
            (Orchard.user_id == current_user.id) | (Orchard.source_user_id == current_user.id)
        ).first()
    if not orchard:
        raise HTTPException(status_code=404, detail="果园不存在或无权删除")
    
    # 先删除关联的病害点数据（避免外键约束错误）
    db.query(DiseasePoint).filter(DiseasePoint.orchard_id == orchard_id).delete()
    
    # 再删除果园本身
    db.delete(orchard)
    db.commit()
    return {"code": 200, "message": "删除成功"}

# 病害空间数据接口
@app.get("/disease/spatial", summary="获取病害空间分布数据")
def get_disease_spatial_data(
    orchard_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(DiseasePoint)
    if orchard_id:
        query = query.filter(DiseasePoint.orchard_id == orchard_id)
    
    points = query.all()
    point_list = []
    for point in points:
        point_list.append({
            "id": point.id,
            "coordinate": point.coordinate,
            "diseaseType": point.disease_type,
            "level": point.level,
            "confidence": point.confidence,
            "detectTime": point.detect_time.strftime("%Y-%m-%d %H:%M:%S"),
            "orchardId": point.orchard_id
        })
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": point_list
    }

# 统计数据接口
@app.get("/statistics/data", summary="获取统计数据")
def get_statistics_data(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 管理员从AdminDetectRecord表查询（汇总所有用户数据），普通用户查自己的DetectRecord
    is_admin = current_user.username == "admin"
    
    if is_admin:
        query = db.query(AdminDetectRecord)
    else:
        query = db.query(DetectRecord).filter(DetectRecord.user_id == current_user.id)
    
    if start_date:
        if is_admin:
            query = query.filter(AdminDetectRecord.detect_time >= start_date)
        else:
            query = query.filter(DetectRecord.detect_time >= start_date)
    if end_date:
        if is_admin:
            query = query.filter(AdminDetectRecord.detect_time <= end_date)
        else:
            query = query.filter(DetectRecord.detect_time <= end_date)
    
    total_count = query.count()
    
    # 统计病害检测数（disease_type 包含黑星病/黑腐病/锈病）
    if is_admin:
        disease_count = query.filter(
            (AdminDetectRecord.disease_type.like("%黑星病%")) |
            (AdminDetectRecord.disease_type.like("%黑腐病%")) |
            (AdminDetectRecord.disease_type.like("%锈病%"))
        ).count()
        healthy_count = query.filter(
            AdminDetectRecord.disease_type.like("%健康叶片%")
        ).count()
    else:
        disease_count = query.filter(
            (DetectRecord.disease_type.like("%黑星病%")) |
            (DetectRecord.disease_type.like("%黑腐病%")) |
            (DetectRecord.disease_type.like("%锈病%"))
        ).count()
        healthy_count = query.filter(
            DetectRecord.disease_type.like("%健康叶片%")
        ).count()
    
    disease_rate = round((disease_count / total_count * 100), 2) if total_count > 0 else 0

    # 获取果园数量（管理员看到所有，普通用户看自己的）
    if current_user.username == "admin":
        orchard_count = db.query(Orchard).count()
    else:
        orchard_count = db.query(Orchard).filter(
            (Orchard.user_id == current_user.id) | (Orchard.source_user_id == current_user.id)
        ).count()

    # 计算平均精度
    from sqlalchemy import func
    if is_admin:
        avg_accuracy = db.query(func.avg(AdminDetectRecord.confidence)).filter(AdminDetectRecord.confidence.isnot(None)).scalar()
    else:
        avg_accuracy = db.query(func.avg(DetectRecord.confidence)).filter(DetectRecord.confidence.isnot(None)).scalar()
    avg_accuracy = round(avg_accuracy * 100, 2) if avg_accuracy else 0
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "totalCount": total_count,
            "diseaseCount": disease_count,
            "healthyCount": healthy_count,
            "diseaseRate": disease_rate,
            "accuracy": avg_accuracy,
            "orchardCount": orchard_count
        }
    }

# 图表统计数据接口（返回病害类型分布、严重程度、月度趋势）
@app.get("/statistics/chart", summary="获取图表统计数据")
def get_chart_statistics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy import func
    # 管理员从AdminDetectRecord表查询（汇总所有用户数据），普通用户查自己的DetectRecord
    is_admin = current_user.username == "admin"
    
    if is_admin:
        query = db.query(AdminDetectRecord)
    else:
        query = db.query(DetectRecord).filter(DetectRecord.user_id == current_user.id)
    
    if start_date:
        if is_admin:
            query = query.filter(AdminDetectRecord.detect_time >= start_date)
        else:
            query = query.filter(DetectRecord.detect_time >= start_date)
    if end_date:
        if is_admin:
            query = query.filter(AdminDetectRecord.detect_time <= end_date)
        else:
            query = query.filter(DetectRecord.detect_time <= end_date)
    
    # 1. 病害类型分布（4类：黑星病、黑腐病、锈病、健康叶片）
    disease_type_stats = []
    for disease_id, disease_info in DISEASE_MAP.items():
        if is_admin:
            count = query.filter(AdminDetectRecord.disease_type.like(f"%{disease_info['name']}%")).count()
        else:
            count = query.filter(DetectRecord.disease_type.like(f"%{disease_info['name']}%")).count()
        disease_type_stats.append({
            "name": disease_info["name"],
            "count": count
        })
    
    # 2. 每个病害类型的严重程度分布（用于柱状图）
    # 横坐标：3种病害类型（排除健康叶片），每个病害有2个堆叠柱（重度、健康）
    disease_level_stats = []
    for disease_id, disease_info in DISEASE_MAP.items():
        # 跳过健康叶片（没有严重程度）
        if disease_id == 3:  # Healthy
            continue
        disease_name = disease_info["name"]
        # 该病害类型下各种严重程度的数量
        if is_admin:
            severe_count = query.filter(
                AdminDetectRecord.disease_type.like(f"%{disease_name}%"),
                AdminDetectRecord.level == "重度"
            ).count()
            healthy_count = query.filter(
                AdminDetectRecord.disease_type.like(f"%{disease_name}%"),
                AdminDetectRecord.level == "健康"
            ).count()
        else:
            severe_count = query.filter(
                DetectRecord.disease_type.like(f"%{disease_name}%"),
                DetectRecord.level == "重度"
            ).count()
            healthy_count = query.filter(
                DetectRecord.disease_type.like(f"%{disease_name}%"),
                DetectRecord.level == "健康"
            ).count()
        disease_level_stats.append({
            "disease": disease_name,
            "重度": severe_count,
            "健康": healthy_count
        })
    
    # 3. 严重程度总体分布（重度、健康）
    if is_admin:
        level_stats = {
            "重度": query.filter(AdminDetectRecord.level == "重度").count(),
            "健康": query.filter(AdminDetectRecord.level == "健康").count()
        }
    else:
        level_stats = {
            "重度": query.filter(DetectRecord.level == "重度").count(),
            "健康": query.filter(DetectRecord.level == "健康").count()
        }
    
    # 4. 月度趋势（最近6个月）
    monthly_stats = []
    from datetime import timedelta
    now = datetime.now()
    for i in range(5, -1, -1):
        # 计算每月的起始和结束日期
        month_start = datetime(now.year, now.month, 1) - timedelta(days=30 * i)
        if month_start.month == 12:
            month_end = datetime(month_start.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = datetime(month_start.year, month_start.month + 1, 1) - timedelta(days=1)
        
        month_label = month_start.strftime("%m月")
        
        # 该月总检测数
        if is_admin:
            month_total = query.filter(
                AdminDetectRecord.detect_time >= month_start,
                AdminDetectRecord.detect_time <= month_end
            ).count()
            # 该月病害数（排除健康叶片）
            month_disease = query.filter(
                AdminDetectRecord.detect_time >= month_start,
                AdminDetectRecord.detect_time <= month_end,
                AdminDetectRecord.disease_type != "健康叶片"
            ).count()
        else:
            month_total = query.filter(
                DetectRecord.detect_time >= month_start,
                DetectRecord.detect_time <= month_end
            ).count()
            month_disease = query.filter(
                DetectRecord.detect_time >= month_start,
                DetectRecord.detect_time <= month_end,
                DetectRecord.disease_type != "健康叶片"
            ).count()
        
        monthly_stats.append({
            "month": month_label,
            "total": month_total,
            "disease": month_disease
        })
    
    return {
        "code": 200,
        "data": {
            "diseaseTypeStats": disease_type_stats,
            "diseaseLevelStats": disease_level_stats,
            "levelStats": level_stats,
            "monthlyStats": monthly_stats
        }
    }

# ==============================================
# 用户管理接口
# ==============================================

# 获取用户列表
@app.get("/users/list", summary="获取用户列表")
def get_user_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    users = db.query(User).order_by(User.id.asc()).all()
    user_list = []
    for user in users:
        user_list.append({
            "id": user.id,
            "username": user.username,
            "realName": user.real_name,
            "college": user.college,
            "major": user.major,
            "email": user.email,
            "phone": user.phone,
            "createdAt": user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else "-"
        })
    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "total": len(user_list),
            "users": user_list
        }
    }

# ==============================================
# 数据库维护接口
# ==============================================

@app.post("/admin/maintain", summary="整理数据库ID（仅管理员）")
def maintain_database(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """整理数据库：将所有历史检测记录迁移到AdminDetectRecord表"""
    # 仅管理员可以执行
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可以执行此操作")

    try:
        from sqlalchemy import text

        # 迁移所有用户的历史记录到AdminDetectRecord表
        all_records = db.query(DetectRecord).order_by(DetectRecord.id.asc()).all()

        migrated_count = 0
        skipped_count = 0
        
        for record in all_records:
            # 检查是否已存在对应的AdminDetectRecord
            existing = db.query(AdminDetectRecord).filter(
                AdminDetectRecord.original_record_id == record.id
            ).first()
            
            if not existing:
                admin_record = AdminDetectRecord(
                    original_record_id=record.id,
                    file_name=record.file_name,
                    image_url=record.image_url,
                    result_image_url=record.result_image_url,
                    disease_count=record.disease_count,
                    disease_type=record.disease_type,
                    level=record.level,
                    confidence=record.confidence,
                    duration=record.duration,
                    detect_time=record.detect_time,
                    user_id=record.user_id  # 保留原始用户ID
                )
                db.add(admin_record)
                migrated_count += 1
            else:
                skipped_count += 1
        
        db.commit()

        # 重置SQLite自增计数器
        try:
            with engine.connect() as conn:
                conn.execute(text("DELETE FROM sqlite_sequence WHERE name='admin_detect_records'"))
                conn.commit()
        except Exception:
            pass  # 如果表不存在就忽略

        return {
            "code": 200,
            "message": f"数据迁移完成，新增迁移 {migrated_count} 条记录，跳过 {skipped_count} 条已存在的记录",
            "data": {"migrated": migrated_count, "skipped": skipped_count}
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"整理失败: {str(e)}")

# 创建用户
@app.post("/users/create", summary="创建新用户")
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    new_user = User(
        username=data.username,
        hashed_password=get_password_hash(data.password),
        real_name=data.real_name,
        college=data.college,
        major=data.major
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "code": 200,
        "message": "用户创建成功",
        "data": {
            "id": new_user.id,
            "username": new_user.username
        }
    }

# 更新用户信息
@app.put("/users/{user_id}", summary="更新用户信息")
def update_user(
    user_id: int,
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 如果修改用户名，检查是否重复
    if data.username != user.username:
        existing = db.query(User).filter(User.username == data.username, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="用户名已存在")
        user.username = data.username
    
    # 如果传了新密码，更新密码
    if data.password:
        user.hashed_password = get_password_hash(data.password)
    
    if data.real_name is not None:
        user.real_name = data.real_name
    if data.college is not None:
        user.college = data.college
    if data.major is not None:
        user.major = data.major
    
    db.commit()
    
    return {
        "code": 200,
        "message": "用户信息更新成功"
    }

# 删除用户
@app.delete("/users/{user_id}", summary="删除用户")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 不允许删除自己
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除当前登录账号")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查该用户是否有检测记录
    records = db.query(DetectRecord).filter(DetectRecord.user_id == user_id).count()
    if records > 0:
        raise HTTPException(status_code=400, detail=f"该用户有{records}条检测记录，无法删除")
    
    db.delete(user)
    db.commit()
    
    return {
        "code": 200,
        "message": "用户删除成功"
    }

# 初始化管理员账号
@app.on_event("startup")
def init_admin_user():
    db = next(get_db())
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        admin_user = User(
            username="admin",
            hashed_password=get_password_hash("123456"),
            real_name="贾云山",
            college="信息工程学院",
            major="计算机科学与技术"
        )
        db.add(admin_user)
        db.commit()
        print("✅ 初始化管理员账号成功！账号：admin 密码：123456")
    db.close()

# 启动服务
if __name__ == "__main__":
    import uvicorn
    print("🚀 正在启动后端服务...")
    uvicorn.run(app, host="0.0.0.0", port=8000)