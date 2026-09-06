"""auth routes API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import secrets
from ..models import get_db, User, Personnel, ROLE_TEMPLATES, ROLE_LABELS, ALL_PERMISSIONS
from ..schemas import LoginRequest, RegisterRequest, TokenResponse, PasswordChange
from ..auth import hash_password, verify_password, create_access_token, get_current_user, require_perm
router = APIRouter()

@router.post('/api/auth/login', response_model=TokenResponse)
def login(req: LoginRequest, db: Session=Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, '用户名或密码错误')
    if user.status != 'active':
        raise HTTPException(403, '账号已被停用')
    return TokenResponse(access_token=create_access_token({'sub': str(user.id)}), user={'id': user.id, 'username': user.username, 'display_name': user.display_name, 'role': user.role, 'role_label': ROLE_LABELS.get(user.role, user.role), 'permissions': user.permissions})

@router.get('/api/auth/me')
def me(user: User=Depends(get_current_user)):
    return {'id': user.id, 'username': user.username, 'display_name': user.display_name, 'role': user.role, 'role_label': ROLE_LABELS.get(user.role, user.role), 'permissions': user.permissions, 'phone': user.phone, 'status': user.status}

@router.post('/api/auth/register')
def register(req: RegisterRequest, db: Session=Depends(get_db)):
    p = db.query(Personnel).filter(Personnel.reg_code == req.reg_code).first()
    if not p:
        raise HTTPException(400, '注册码无效')
    if p.status != 'active':
        raise HTTPException(403, '该人员已停用')
    if p.user_id:
        raise HTTPException(400, '已注册')
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(400, '用户名已存在')
    u = User(username=req.username, password_hash=hash_password(req.password), display_name=p.name, role={'采样组长': 'field_leader', '采样组员': 'field_member'}.get(p.role, p.role), permissions=ROLE_TEMPLATES.get({'采样组长': 'field_leader', '采样组员': 'field_member'}.get(p.role, p.role), {}), phone=p.phone or '', status='active')
    db.add(u)
    db.flush()
    p.user_id = u.id
    db.commit()
    return {'ok': True, 'message': f'注册成功，欢迎 {u.display_name}'}

@router.get('/api/meta/permissions')
def meta(_: User=Depends(get_current_user)):
    return {'permissions': [{'key': k, 'label': v} for k, v in ALL_PERMISSIONS.items()], 'roles': [{'key': k, 'label': v} for k, v in ROLE_LABELS.items()], 'templates': ROLE_TEMPLATES}

@router.post('/api/auth/password')
def change_password(data: PasswordChange, db: Session=Depends(get_db), user: User=Depends(get_current_user)):
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(400, '当前密码不正确')
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {'ok': True}
