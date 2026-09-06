"""Shared task authorization and domain validation."""
from datetime import date
import math
from fastapi import HTTPException
from .models import Personnel, Task

def ids(value):
    return {part.strip() for part in (value or '').split(',') if part.strip()}

def assigned(task, user, db, leader_only=False):
    cache = db.info.setdefault('assigned_people', {})
    if user.id not in cache:
        cache[user.id] = db.query(Personnel).filter(Personnel.user_id == user.id).first()
    person = cache[user.id]
    return bool(person and str(person.id) in (ids(task.leader_ids) | (set() if leader_only else ids(task.member_ids))))

def visible_tasks(user, db):
    tasks = db.query(Task).order_by(Task.id.desc()).all()
    return tasks if user.has_perm('view_all_tasks') else [t for t in tasks if assigned(t, user, db)]

def validate_task(values, db, current=None):
    def value(key, default=None):
        return values.get(key, getattr(current, key, default))
    if not (value('pid', '') or '').strip():
        raise HTTPException(422, '任务编号不能为空')
    duplicate = db.query(Task).filter(Task.pid == value('pid')).first()
    if duplicate and (not current or duplicate.id != current.id):
        raise HTTPException(409, '任务编号已存在')
    status = value('status', 'pending')
    if status not in {'pending', 'progress', 'done', 'cancelled', 'abnormal'}:
        raise HTTPException(422, '无效的任务状态')
    start, end = value('date_start'), value('date_end')
    try:
        if start and date.fromisoformat(start).isoformat() != start: raise ValueError()
        if end and date.fromisoformat(end).isoformat() != end: raise ValueError()
    except (ValueError, TypeError):
        raise HTTPException(422, '请输入有效日期')
    if bool(start) != bool(end) or (start and start > end):
        raise HTTPException(422, '请填写完整日期，结束日期不能早于开始日期')
    for key in ('planned_hrs', 'actual_hrs'):
        if value(key) is not None and (not math.isfinite(value(key)) or value(key) < 0):
            raise HTTPException(422, '工时不能为负数')
    for key in ('leader_ids', 'member_ids'):
        for pid in ids(value(key)):
            if not pid.isdigit() or not db.query(Personnel).filter(Personnel.id == int(pid), Personnel.status == 'active').first():
                raise HTTPException(422, '所选人员不存在或已停用')
    if status == 'progress' and (not start or not ids(value('leader_ids'))):
        raise HTTPException(422, '派单需要采样日期与组长')
    if status in {'cancelled', 'abnormal'} and not value('cancel_reason'):
        raise HTTPException(422, '请填写取消或异常原因')
    if 'testing_items' in values:
        items = values['testing_items']
        if not isinstance(items, list) or any(not isinstance(x, dict) or not isinstance(x.get('category'), str) or not isinstance(x.get('items'), list) or any(not isinstance(i, str) for i in x['items']) for x in items):
            raise HTTPException(422, '检测项目需包含类别和项目列表')
    for pid in ids(value('leader_ids')):
        person = db.get(Personnel, int(pid))
        if person.role not in {'采样组长', 'field_leader'}:
            raise HTTPException(422, '负责人必须是采样组长')
    if status == 'progress' and (not current or {'date_start', 'date_end', 'leader_ids', 'member_ids', 'status'} & values.keys()):
        selected = ids(value('leader_ids')) | ids(value('member_ids'))
        candidates = db.query(Task).filter(Task.status == 'progress', Task.date_start <= end, Task.date_end >= start).all()
        for other in candidates:
            if current and other.id == current.id:
                continue
            if selected & (ids(other.leader_ids) | ids(other.member_ids)):
                raise HTTPException(409, f'人员安排与任务 {other.pid} 的采样日期冲突')

def validate_person(values, db, current=None):
    role = values.get('role', getattr(current, 'role', '采样组员'))
    if role not in {'采样组长', '采样组员', 'field_leader', 'field_member'}:
        raise HTTPException(422, '请选择有效的采样人员角色')
    leader_id = values.get('leader_id', getattr(current, 'leader_id', None))
    if leader_id:
        leader = db.get(Personnel, leader_id)
        if not leader or leader.status != 'active' or leader.role not in {'采样组长', 'field_leader'} or (current and leader_id == current.id):
            raise HTTPException(422, '所属组长无效，不能关联自己')
        if role in {'采样组长', 'field_leader'}:
            raise HTTPException(422, '组长不应归属另一位组长')
    if current and role not in {'采样组长', 'field_leader'} and db.query(Personnel).filter(Personnel.leader_id == current.id).first():
        raise HTTPException(409, '请先调整该组长的下属组员')
