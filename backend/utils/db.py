from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

# ==============================================
# ✅ 这里我直接改成 根目录，永远不会报错！
# ==============================================
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# OAuth2配置
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# 数据库模型
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    real_name = Column(String, nullable=True)
    college = Column(String, nullable=True)
    major = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

class DetectRecord(Base):
    __tablename__ = "detect_records"
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    result_image_url = Column(String, nullable=False)
    disease_count = Column(Integer, default=0)
    disease_type = Column(String, nullable=True)
    level = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    duration = Column(Integer, nullable=False)
    detect_time = Column(DateTime, default=datetime.now)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 数据来源用户ID，备份到管理员时记录原始用户
    admin_record_id = Column(Integer, nullable=True)  # 对应的管理员表ID，用于关联

# 管理员检测记录汇总表（包含所有用户的检测数据，ID连续递增）
class AdminDetectRecord(Base):
    __tablename__ = "admin_detect_records"
    id = Column(Integer, primary_key=True, index=True)  # 管理员视角的ID，连续递增
    original_record_id = Column(Integer, nullable=False)  # 原用户记录ID
    file_name = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    result_image_url = Column(String, nullable=False)
    disease_count = Column(Integer, default=0)
    disease_type = Column(String, nullable=True)
    level = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    duration = Column(Integer, nullable=False)
    detect_time = Column(DateTime, default=datetime.now)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 来源用户ID

class Orchard(Base):
    __tablename__ = "orchards"
    id = Column(Integer, primary_key=True, index=True)
    orchard_name = Column(String, nullable=False)
    variety = Column(String, nullable=False)
    area = Column(Float, nullable=False)
    age = Column(Integer, nullable=False)
    disease_rate = Column(Float, default=0)
    address = Column(String, nullable=False)
    color = Column(String, default="#1890ff")
    fill_color = Column(String, default="rgba(24, 144, 255, 0.2)")
    path = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 数据来源用户ID

class DiseasePoint(Base):
    __tablename__ = "disease_points"
    id = Column(Integer, primary_key=True, index=True)
    coordinate = Column(JSON, nullable=False)
    disease_type = Column(String, nullable=False)
    level = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)
    detect_time = Column(DateTime, default=datetime.now)
    orchard_id = Column(Integer, ForeignKey("orchards.id"), nullable=False)

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 获取当前用户
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from utils.auth import decode_access_token
    username = decode_access_token(token)
    if username is None:
        raise HTTPException(status_code=401, detail="无效的登录凭证")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user