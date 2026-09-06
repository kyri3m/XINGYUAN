"""sampling API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import secrets
from ..models import get_db, User, Task, SamplingRecord
from ..schemas import SamplingCreate, SamplingOut
from ..auth import hash_password, verify_password, create_access_token, get_current_user, require_perm
from ..services import assigned
router = APIRouter()

@router.get('/api/sampling', response_model=List[SamplingOut])
def list_sampling(task_id: Optional[int]=None, db: Session=Depends(get_db), user: User=Depends(get_current_user)):
    q = db.query(SamplingRecord)
    if task_id:
        q = q.filter(SamplingRecord.task_id == task_id)
    recs = q.order_by(SamplingRecord.id.desc()).all()
    if not user.has_perm('view_all_tasks'):
        recs = [r for r in recs if r.sampler_id == user.id]
    for r in recs:
        r.sampler_name = r.sampler_user.display_name if r.sampler_user else ''
    return recs

@router.post('/api/sampling', response_model=SamplingOut)
def create_sampling(data: SamplingCreate, db: Session=Depends(get_db), user: User=Depends(require_perm('do_sampling'))):
    from datetime import date
    if data.date:
        try:
            date.fromisoformat(data.date)
        except ValueError:
            raise HTTPException(422, '采样日期无效')
    task = db.get(Task, data.task_id)
    if not task:
        raise HTTPException(404, '任务不存在')
    if not user.has_perm('manage_tasks') and (not assigned(task, user, db)):
        raise HTTPException(403, '不能录入他人的采样任务')
    r = SamplingRecord(task_id=data.task_id, sampler_id=user.id, date=data.date or datetime.now(timezone.utc).strftime('%Y-%m-%d'), ports=[p.model_dump() for p in data.ports])
    db.add(r)
    db.commit()
    db.refresh(r)
    r.sampler_name = user.display_name
    return r
