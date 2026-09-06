"""tasks API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import secrets
from ..models import get_db, User, Personnel, Task
from ..schemas import TaskCreate, TaskUpdate, TaskOut
from ..auth import hash_password, verify_password, create_access_token, get_current_user, require_perm
from ..services import assigned, validate_task
router = APIRouter()

def _et(task, db):
    if 'personnel_names' not in db.info:
        db.info['personnel_names'] = {str(p.id): p.name for p in db.query(Personnel).all()}
    def _names(s):
        if not s:
            return ''
        ids = [x.strip() for x in s.split(',') if x.strip()]
        return '、'.join(db.info['personnel_names'].get(i, i) for i in ids)
    task.leader_names = _names(task.leader_ids)
    task.member_names = _names(task.member_ids)
    return task

@router.get('/api/tasks', response_model=List[TaskOut])
def list_tasks(status: Optional[str]=None, search: Optional[str]=None, month: Optional[str]=None, leader_id: Optional[int]=None, db: Session=Depends(get_db), user: User=Depends(get_current_user)):
    q = db.query(Task)
    if status:
        q = q.filter(Task.status == status)
    if month:
        from datetime import date
        from calendar import monthrange
        try:
            first = date.fromisoformat(month + '-01')
            if first.strftime('%Y-%m') != month: raise ValueError()
        except ValueError:
            raise HTTPException(422, '月份格式必须为 YYYY-MM')
        last = f'{month}-{monthrange(first.year, first.month)[1]:02}'
        q = q.filter(or_(Task.date_start == None, Task.date_start <= last)).filter(or_(Task.date_end == None, Task.date_end >= month + '-01'))
    if leader_id:
        q = q.filter(or_(Task.leader_ids == str(leader_id), Task.leader_ids.like(f'{leader_id},%'), Task.leader_ids.like(f'%,{leader_id},%'), Task.leader_ids.like(f'%,{leader_id}')))
    if search:
        q = q.filter(or_(Task.pid.contains(search), Task.task_name.contains(search), Task.company.contains(search)))
    tasks = q.order_by(Task.id.desc()).all()
    if not user.has_perm('view_all_tasks'):
        tasks = [t for t in tasks if assigned(t, user, db)]
    return [_et(t, db) for t in tasks]

@router.post('/api/tasks', response_model=TaskOut)
def create_task(data: TaskCreate, db: Session=Depends(get_db), _: User=Depends(require_perm('manage_tasks'))):
    validate_task(data.model_dump(), db)
    t = Task(**data.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return _et(t, db)

@router.put('/api/tasks/{tid}', response_model=TaskOut)
def update_task(tid: int, data: TaskUpdate, db: Session=Depends(get_db), user: User=Depends(get_current_user)):
    t = db.query(Task).filter(Task.id == tid).first()
    if not t:
        raise HTTPException(404, '不存在')
    values = data.model_dump(exclude_unset=True)
    if not user.has_perm('manage_tasks'):
        if not user.has_perm('do_sampling') or not assigned(t, user, db, leader_only=True):
            raise HTTPException(403, '只有负责该任务的组长或管理员可操作')
        if set(values) - {'status', 'cancel_reason', 'actual_hrs'} or values.get('status') not in {'done', 'abnormal', 'cancelled'}:
            raise HTTPException(403, '组长仅可更新任务执行结果')
    validate_task(values, db, t)
    if values.get('status') in {'done', 'progress', 'pending'}:
        values['cancel_reason'] = None
    for k, v in values.items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return _et(t, db)

@router.delete('/api/tasks/{tid}')
def delete_task(tid: int, db: Session=Depends(get_db), _: User=Depends(require_perm('manage_tasks'))):
    t = db.query(Task).filter(Task.id == tid).first()
    if not t:
        raise HTTPException(404, '不存在')
    if t.sampling_records:
        raise HTTPException(409, '任务已有采样记录，不能删除')
    db.delete(t)
    db.commit()
    return {'ok': True}
