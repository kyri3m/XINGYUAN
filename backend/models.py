"""
环境监测采样派单系统 - 数据库模型 + 权限体系 (企业改为文本字段)
"""
from sqlalchemy import create_engine, Column, String, Integer, Float, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone
import os, secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'dispatch.db')}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

ALL_PERMISSIONS = {
    "admin_panel": "管理端入口", "manage_users": "用户管理",
    "manage_tasks": "任务管理", "view_all_tasks": "查看全部任务",
    "view_dispatch": "派单计划", "manage_personnel": "人员管理",
    "do_sampling": "现场采样", "manage_reports": "报告管理", "manage_lab": "实验管理",
}
ROLE_LABELS = {
    "admin": "系统管理员", "field_director": "现场部部长",
    "field_leader": "采样组长", "field_member": "采样组员",
    "report_manager": "报告部负责人", "lab_manager": "实验部负责人",
}
ROLE_TEMPLATES = {
    "admin": {k: True for k in ALL_PERMISSIONS},
    "field_director": {"admin_panel":True,"manage_users":True,"manage_tasks":True,"view_all_tasks":True,"view_dispatch":True,"manage_personnel":True,"do_sampling":False,"manage_reports":False,"manage_lab":False},
    "field_leader": {"admin_panel":True,"manage_users":False,"manage_tasks":False,"view_all_tasks":True,"view_dispatch":True,"manage_personnel":False,"do_sampling":True,"manage_reports":False,"manage_lab":False},
    "field_member": {"admin_panel":False,"manage_users":False,"manage_tasks":False,"view_all_tasks":False,"view_dispatch":False,"manage_personnel":False,"do_sampling":True,"manage_reports":False,"manage_lab":False},
    "report_manager": {"admin_panel":True,"manage_users":False,"manage_tasks":False,"view_all_tasks":True,"view_dispatch":True,"manage_personnel":False,"do_sampling":False,"manage_reports":True,"manage_lab":False},
    "lab_manager": {"admin_panel":True,"manage_users":False,"manage_tasks":False,"view_all_tasks":True,"view_dispatch":True,"manage_personnel":False,"do_sampling":False,"manage_reports":False,"manage_lab":True},
}

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    display_name = Column(String(50), nullable=False)
    role = Column(String(30), nullable=False, default="field_member")
    permissions = Column(JSON, nullable=False, default=dict)
    phone = Column(String(20), default="")
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    sampling_records = relationship("SamplingRecord", back_populates="sampler_user")
    def has_perm(self, perm_key): return True if self.role=="admin" else bool(self.permissions.get(perm_key, False))

class Personnel(Base):
    __tablename__ = "personnel"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    role = Column(String(30), default="采样组员")
    phone = Column(String(30), default="")
    status = Column(String(20), default="active")
    reg_code = Column(String(20), unique=True, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    leader_id = Column(Integer, ForeignKey("personnel.id"), nullable=True)  # 归属组长
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    linked_user = relationship("User", foreign_keys=[user_id])

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    pid = Column(String(50), nullable=False)
    task_name = Column(String(200), default="")
    company = Column(String(200), default="")            # 企业名（纯文本）
    date_start = Column(String(20), nullable=True)
    date_end = Column(String(20), nullable=True)
    planned_hrs = Column(Float, default=0)
    actual_hrs = Column(Float, nullable=True)
    leader_ids = Column(String(200), default="")
    member_ids = Column(String(200), default="")
    testing_items = Column(JSON, default=list)
    project_type = Column(String(50), default="")        # 项目类别: 自行检测/委托检测/比对监测/验收检测
    valid_period = Column(String(20), default="")        # 有效期: 月度/季度/半年度/年度
    contact_person = Column(String(50), default="")      # 项目联系人
    contact_phone = Column(String(30), default="")       # 联系方式
    project_region = Column(String(100), default="")     # 项目地区
    market_manager = Column(String(50), default="")      # 市场经理
    district = Column(String(100), default="")           # 安徽省市区县
    status = Column(String(20), default="pending")
    note = Column(Text, default="")
    cancel_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    sampling_records = relationship("SamplingRecord", back_populates="task_rel")

class SamplingRecord(Base):
    __tablename__ = "sampling_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    sampler_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(String(20), default="")
    ports = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    task_rel = relationship("Task", back_populates="sampling_records")
    sampler_user = relationship("User", back_populates="sampling_records")

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(username="admin", password_hash=pwd_context.hash("admin123"), display_name="系统管理员", role="admin", permissions=ROLE_TEMPLATES["admin"], status="active"))
            db.commit(); print("admin created")
    finally: db.close()
