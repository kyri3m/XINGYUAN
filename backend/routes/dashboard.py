"""dashboard API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import secrets
from ..models import get_db, User, Personnel, Task
from ..auth import hash_password, verify_password, create_access_token, get_current_user, require_perm
from ..services import assigned
from .tasks import _et
router = APIRouter()

@router.get('/api/dashboard')
def dashboard(db: Session=Depends(get_db), user: User=Depends(get_current_user)):
    all_t = db.query(Task).all()
    if not user.has_perm('view_all_tasks'):
        lp = db.query(Personnel).filter(Personnel.user_id == user.id).first()
        ps = str(lp.id) if lp else None
        all_t = [t for t in all_t if assigned(t, user, db)]
    today = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d')
    now = datetime.now(timezone(timedelta(hours=8)))
    wd = now.weekday()
    ws = (now - timedelta(days=wd)).strftime('%Y-%m-%d')
    we = (now + timedelta(days=6 - wd)).strftime('%Y-%m-%d')
    tt = [t for t in all_t if t.date_start and t.date_end and (t.date_start <= today <= t.date_end)][:20]
    tg = {}
    for t in tt:
        lids = [x.strip() for x in (t.leader_ids or '').split(',') if x.strip()]
        for lid in lids:
            ld = db.query(Personnel).filter(Personnel.id == int(lid)).first()
            ln = ld.name if ld else lid
            if ln not in tg:
                tg[ln] = []
            tg[ln].append(_et(t, db))
    wt = [t for t in all_t if t.date_start and t.date_end and (t.date_start <= we) and (t.date_end >= ws)]
    wg = {}
    for t in wt:
        lids = [x.strip() for x in (t.leader_ids or '').split(',') if x.strip()]
        for lid in lids:
            ld = db.query(Personnel).filter(Personnel.id == int(lid)).first()
            ln = ld.name if ld else lid
            if ln not in wg:
                wg[ln] = {'pending': 0, 'progress': 0, 'done': 0, 'abnormal': 0, 'total': 0}
            wg[ln][t.status if t.status in ['pending', 'progress', 'done', 'abnormal'] else 'pending'] += 1
            wg[ln]['total'] += 1
    ym = now.strftime('%Y-%m')
    yq = str(now.year) + '-Q' + str((now.month - 1) // 3 + 1)
    yy = str(now.year)

    def _pm(t):
        ds = t.date_start or ''
        return {'monthly': ds.startswith(ym) or (not ds and '月度' in (t.valid_period or '')), 'quarterly': (not ds and '季度' in (t.valid_period or '')) or ds[:7] >= yy + '-' + str((int(yq[-1]) - 1) * 3 + 1).zfill(2) and ds[:7] <= yy + '-' + str(int(yq[-1]) * 3).zfill(2), 'yearly': ds.startswith(yy) or (not ds and '年度' in (t.valid_period or ''))}
    ms = {'pending': 0, 'progress': 0, 'done': 0, 'total': 0}
    qs = {'pending': 0, 'progress': 0, 'done': 0, 'total': 0}
    ys = {'pending': 0, 'progress': 0, 'done': 0, 'total': 0}
    for t in all_t:
        p = _pm(t)
        for k, v in [('monthly', ms), ('quarterly', qs), ('yearly', ys)]:
            if p[k]:
                v['total'] += 1
                v['pending'] += 1 if t.status == 'pending' else 0
                v['progress'] += 1 if t.status == 'progress' else 0
                v['done'] += 1 if t.status == 'done' else 0
    return {'total': len(all_t), 'pending': sum((1 for t in all_t if t.status == 'pending')), 'progress': sum((1 for t in all_t if t.status == 'progress')), 'done': sum((1 for t in all_t if t.status == 'done')), 'today_tasks': tg, 'week_tasks': wg, 'week_dates': {'start': ws, 'end': we}, 'periods': {'monthly': ms, 'quarterly': qs, 'yearly': ys}}

