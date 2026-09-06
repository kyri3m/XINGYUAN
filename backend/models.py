"""Persistent domain models; existing SQLite tables are preserved."""
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import os
from .database import Base, engine, SessionLocal, get_db
from .permissions import ALL_PERMISSIONS, ROLE_LABELS, ROLE_TEMPLATES

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    display_name = Column(String(50), nullable=False)
    role = Column(String(30), nullable=False, default='field_member')
    permissions = Column(JSON, nullable=False, default=dict)
    phone = Column(String(20), default='')
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    sampling_records = relationship('SamplingRecord', back_populates='sampler_user')

    def has_perm(self, perm_key):
        return True if self.role == 'admin' else bool(self.permissions.get(perm_key, False))

class Personnel(Base):
    __tablename__ = 'personnel'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    role = Column(String(30), default='采样组员')
    phone = Column(String(30), default='')
    status = Column(String(20), default='active')
    reg_code = Column(String(20), unique=True, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    leader_id = Column(Integer, ForeignKey('personnel.id'), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    linked_user = relationship('User', foreign_keys=[user_id])

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    pid = Column(String(50), nullable=False)
    task_name = Column(String(200), default='')
    company = Column(String(200), default='')
    date_start = Column(String(20), nullable=True)
    date_end = Column(String(20), nullable=True)
    planned_hrs = Column(Float, default=0)
    actual_hrs = Column(Float, nullable=True)
    leader_ids = Column(String(200), default='')
    member_ids = Column(String(200), default='')
    testing_items = Column(JSON, default=list)
    project_type = Column(String(50), default='')
    valid_period = Column(String(20), default='')
    contact_person = Column(String(50), default='')
    contact_phone = Column(String(30), default='')
    project_region = Column(String(100), default='')
    market_manager = Column(String(50), default='')
    district = Column(String(100), default='')
    status = Column(String(20), default='pending')
    note = Column(Text, default='')
    cancel_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    sampling_records = relationship('SamplingRecord', back_populates='task_rel')

class SamplingRecord(Base):
    __tablename__ = 'sampling_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    sampler_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(String(20), default='')
    ports = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    task_rel = relationship('Task', back_populates='sampling_records')
    sampler_user = relationship('User', back_populates='sampling_records')

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
        if not db.query(User).filter(User.username == 'admin').first():
            db.add(User(username='admin', password_hash=pwd_context.hash(os.getenv('ADMIN_PASSWORD', 'admin123')), display_name='系统管理员', role='admin', permissions=ROLE_TEMPLATES['admin'], status='active'))
            db.commit()
            print('admin created')
    finally:
        db.close()
