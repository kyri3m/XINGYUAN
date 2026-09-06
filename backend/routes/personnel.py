"""personnel API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import secrets
from ..models import get_db, User, Personnel, Task, ROLE_TEMPLATES
from ..schemas import PersonnelCreate, PersonnelUpdate, PersonnelOut
from ..auth import hash_password, verify_password, create_access_token, get_current_user, require_perm
from ..services import validate_person
router = APIRouter()

def _ep(p, db):
    p.has_account = p.user_id is not None
    linked = db.get(User, p.user_id) if p.user_id else None
    p.account_username = linked.username if linked else None
    if p.leader_id:
        leader = db.query(Personnel).filter(Personnel.id == p.leader_id).first()
        p.leader_name = leader.name if leader else None
    else:
        p.leader_name = None
    return p

@router.get('/api/personnel', response_model=List[PersonnelOut])
def list_personnel(search: Optional[str]=None, db: Session=Depends(get_db), _: User=Depends(get_current_user)):
    q = db.query(Personnel)
    if search:
        q = q.filter(or_(Personnel.name.contains(search), Personnel.phone.contains(search)))
    result = [PersonnelOut.model_validate(_ep(p, db)) for p in q.order_by(Personnel.id).all()]
    if not _.has_perm('manage_personnel'):
        for item in result:
            item.reg_code = None
    return result

@router.post('/api/personnel', response_model=PersonnelOut)
def create_personnel(data: PersonnelCreate, db: Session=Depends(get_db), _: User=Depends(require_perm('manage_personnel'))):
    validate_person(data.model_dump(), db)
    while True:
        c = secrets.token_hex(4).upper()[:8]
        if not db.query(Personnel).filter(Personnel.reg_code == c).first():
            break
    p = Personnel(name=data.name, role=data.role, phone=data.phone, leader_id=data.leader_id, reg_code=c)
    db.add(p)
    db.commit()
    db.refresh(p)
    return _ep(p, db)

@router.put('/api/personnel/{pid}', response_model=PersonnelOut)
def update_personnel(pid: int, data: PersonnelUpdate, db: Session=Depends(get_db), _: User=Depends(require_perm('manage_personnel'))):
    p = db.query(Personnel).filter(Personnel.id == pid).first()
    if not p:
        raise HTTPException(404, '不存在')
    values = data.model_dump(exclude_unset=True)
    account = db.get(User, p.user_id) if p.user_id else None
    if account:
        changing_access = any(key in values and values[key] != getattr(p, key) for key in ('role', 'status'))
        if changing_access and (account.role == 'admin' or account.id == _.id):
            raise HTTPException(403, '不能通过人员资料更改管理员或自己的账号权限，请使用用户管理')
    validate_person(data.model_dump(exclude_unset=True), db, p)
    previous_role = p.role
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    if p.user_id:
        account = db.get(User, p.user_id)
        if account:
            if 'status' in values:
                account.status = p.status
            if previous_role != p.role:
                account.role = {'采样组长': 'field_leader', '采样组员': 'field_member'}.get(p.role, p.role)
                account.permissions = ROLE_TEMPLATES[account.role]
    db.commit()
    db.refresh(p)
    return _ep(p, db)

@router.delete('/api/personnel/{pid}')
def delete_personnel(pid: int, db: Session=Depends(get_db), _: User=Depends(require_perm('manage_personnel'))):
    p = db.query(Personnel).filter(Personnel.id == pid).first()
    if not p:
        raise HTTPException(404, '不存在')
    from ..services import ids
    if any((str(pid) in ids(t.leader_ids) | ids(t.member_ids) for t in db.query(Task).all())):
        raise HTTPException(409, '人员已关联任务，请先调整派单')
    if db.query(Personnel).filter(Personnel.leader_id == pid).first():
        raise HTTPException(409, '请先调整下属组员')
    db.delete(p)
    db.commit()
    return {'ok': True}

@router.post('/api/personnel/{pid}/regenerate-code')
def regen_code(pid: int, db: Session=Depends(get_db), _: User=Depends(require_perm('manage_personnel'))):
    p = db.query(Personnel).filter(Personnel.id == pid).first()
    if not p:
        raise HTTPException(404, '不存在')
    if p.user_id:
        raise HTTPException(400, '已注册')
    while True:
        c = secrets.token_hex(4).upper()[:8]
        if not db.query(Personnel).filter(Personnel.reg_code == c).first():
            break
    p.reg_code = c
    db.commit()
    return {'reg_code': c}

@router.get('/api/personnel/members/{leader_id}')
def get_members(leader_id: int, db: Session=Depends(get_db), _: User=Depends(get_current_user)):
    """获取某组长的所有下属组员"""
    members = db.query(Personnel).filter(Personnel.leader_id == leader_id, Personnel.status == 'active').all()
    return [{'id': m.id, 'name': m.name, 'role': m.role} for m in members]
