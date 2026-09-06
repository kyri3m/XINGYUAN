"""users API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import secrets
from ..models import get_db, User, Personnel, ROLE_TEMPLATES, ROLE_LABELS, ALL_PERMISSIONS
from ..schemas import UserCreate, UserUpdate, UserOut
from ..auth import hash_password, verify_password, create_access_token, get_current_user, require_perm
router = APIRouter()

def validate_access(data, actor, current=None):
    values = data.model_dump(exclude_unset=True)
    role = values.get('role', current.role if current else 'field_member')
    if role not in ROLE_TEMPLATES:
        raise HTTPException(422, '角色无效')
    permissions = values.get('permissions')
    if permissions is None:
        permissions = current.permissions if current else ROLE_TEMPLATES[role]
    if set(permissions) - ALL_PERMISSIONS.keys():
        raise HTTPException(422, '权限名称无效')
    if actor.role != 'admin':
        if role == 'admin' or (current and current.role == 'admin'):
            raise HTTPException(403, '只有系统管理员可管理管理员账号')
        if any((enabled and (not actor.has_perm(key)) for key, enabled in permissions.items())):
            raise HTTPException(403, '不能授予自己不具备的权限')
    if current and current.id == actor.id:
        if values.get('status', 'active') != 'active' or role != current.role or permissions != current.permissions:
            raise HTTPException(409, '不能更改自己的角色、权限或停用自己')

@router.get('/api/users', response_model=List[UserOut])
def list_users(db: Session=Depends(get_db), _: User=Depends(require_perm('manage_users'))):
    return db.query(User).order_by(User.id).all()

@router.post('/api/users', response_model=UserOut)
def create_user(data: UserCreate, db: Session=Depends(get_db), _: User=Depends(require_perm('manage_users'))):
    validate_access(data, _)
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(400, '用户名已存在')
    u = User(username=data.username, password_hash=hash_password(data.password), display_name=data.display_name, role=data.role, phone=data.phone, status='active')
    u.permissions = data.permissions if data.permissions is not None else ROLE_TEMPLATES.get(data.role, {})
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

@router.put('/api/users/{uid}', response_model=UserOut)
def update_user(uid: int, data: UserUpdate, db: Session=Depends(get_db), _: User=Depends(require_perm('manage_users'))):
    u = db.query(User).filter(User.id == uid).first()
    if not u:
        raise HTTPException(404, '不存在')
    validate_access(data, _, u)
    d = data.model_dump(exclude_unset=True)
    if d.get('password'):
        d['password_hash'] = hash_password(d.pop('password'))
    else:
        d.pop('password', None)
    for k, v in d.items():
        if v is not None:
            setattr(u, k, v)
    if 'status' in d:
        for person in db.query(Personnel).filter(Personnel.user_id == uid).all():
            person.status = u.status
    db.commit()
    db.refresh(u)
    return u

@router.delete('/api/users/{uid}')
def delete_user(uid: int, db: Session=Depends(get_db), cur: User=Depends(require_perm('manage_users'))):
    if cur.id == uid:
        raise HTTPException(400, '不能删除自己')
    u = db.query(User).filter(User.id == uid).first()
    if not u:
        raise HTTPException(404, '不存在')
    if u.role == 'admin' and cur.role != 'admin':
        raise HTTPException(403, '只有系统管理员可删除管理员')
    if u.sampling_records:
        raise HTTPException(409, '用户已有采样记录，请停用账号而非删除')
    p = db.query(Personnel).filter(Personnel.user_id == uid).first()
    if p:
        p.user_id = None
    db.delete(u)
    db.commit()
    return {'ok': True}
