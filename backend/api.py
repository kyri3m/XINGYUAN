"""API - 无企业管理，企业为文本字段"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import secrets
from .models import get_db, User, Personnel, Task, SamplingRecord, ALL_PERMISSIONS, ROLE_TEMPLATES, ROLE_LABELS
from .schemas import *
from .auth import hash_password, verify_password, create_access_token, get_current_user, require_perm

router = APIRouter()

@router.post("/api/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash): raise HTTPException(401, "用户名或密码错误")
    if user.status != "active": raise HTTPException(403, "账号已被停用")
    return TokenResponse(access_token=create_access_token({"sub": str(user.id)}), user={"id": user.id, "username": user.username, "display_name": user.display_name, "role": user.role, "role_label": ROLE_LABELS.get(user.role, user.role), "permissions": user.permissions})

@router.get("/api/auth/me")
def me(user: User = Depends(get_current_user)): return {"id": user.id, "username": user.username, "display_name": user.display_name, "role": user.role, "role_label": ROLE_LABELS.get(user.role, user.role), "permissions": user.permissions, "phone": user.phone, "status": user.status}

@router.post("/api/auth/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    p = db.query(Personnel).filter(Personnel.reg_code == req.reg_code).first()
    if not p: raise HTTPException(400, "注册码无效")
    if p.user_id: raise HTTPException(400, "已注册")
    if db.query(User).filter(User.username == req.username).first(): raise HTTPException(400, "用户名已存在")
    u = User(username=req.username, password_hash=hash_password(req.password), display_name=p.name, role=p.role, permissions=ROLE_TEMPLATES.get(p.role, {}), phone=p.phone or "", status="active")
    db.add(u); db.flush(); p.user_id = u.id; db.commit()
    return {"ok": True, "message": f"注册成功，欢迎 {u.display_name}"}

@router.get("/api/meta/permissions")
def meta(_: User = Depends(get_current_user)): return {"permissions": [{"key": k, "label": v} for k, v in ALL_PERMISSIONS.items()], "roles": [{"key": k, "label": v} for k, v in ROLE_LABELS.items()], "templates": ROLE_TEMPLATES}

# --- USERS ---
@router.get("/api/users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_perm("manage_users"))): return db.query(User).order_by(User.id).all()
@router.post("/api/users", response_model=UserOut)
def create_user(data: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_perm("manage_users"))):
    if db.query(User).filter(User.username == data.username).first(): raise HTTPException(400, "用户名已存在")
    u = User(username=data.username, password_hash=hash_password(data.password), display_name=data.display_name, role=data.role, phone=data.phone, status="active")
    u.permissions = data.permissions or ROLE_TEMPLATES.get(data.role, {}); db.add(u); db.commit(); db.refresh(u); return u
@router.put("/api/users/{uid}", response_model=UserOut)
def update_user(uid: int, data: UserUpdate, db: Session = Depends(get_db), _: User = Depends(require_perm("manage_users"))):
    u = db.query(User).filter(User.id == uid).first()
    if not u: raise HTTPException(404, "不存在")
    d = data.model_dump(exclude_unset=True)
    if d.get("password"): d["password_hash"] = hash_password(d.pop("password"))
    else: d.pop("password", None)
    for k, v in d.items():
        if v is not None: setattr(u, k, v)
    db.commit(); db.refresh(u); return u
@router.delete("/api/users/{uid}")
def delete_user(uid: int, db: Session = Depends(get_db), cur: User = Depends(require_perm("manage_users"))):
    if cur.id == uid: raise HTTPException(400, "不能删除自己")
    u = db.query(User).filter(User.id == uid).first()
    if not u: raise HTTPException(404, "不存在")
    p = db.query(Personnel).filter(Personnel.user_id == uid).first()
    if p: p.user_id = None
    db.delete(u); db.commit(); return {"ok": True}

# --- PERSONNEL ---
def _ep(p, db):
    p.has_account = p.user_id is not None
    p.account_username = (db.query(User).filter(User.id == p.user_id).first().username) if p.user_id else None
    if p.leader_id:
        leader = db.query(Personnel).filter(Personnel.id == p.leader_id).first()
        p.leader_name = leader.name if leader else None
    else:
        p.leader_name = None
    return p
@router.get("/api/personnel", response_model=List[PersonnelOut])
def list_personnel(search: Optional[str] = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = db.query(Personnel)
    if search: q = q.filter(or_(Personnel.name.contains(search), Personnel.phone.contains(search)))
    return [_ep(p, db) for p in q.order_by(Personnel.id).all()]
@router.post("/api/personnel", response_model=PersonnelOut)
def create_personnel(data: PersonnelCreate, db: Session = Depends(get_db), _: User = Depends(require_perm("manage_personnel"))):
    while True:
        c = secrets.token_hex(4).upper()[:8]
        if not db.query(Personnel).filter(Personnel.reg_code == c).first(): break
    p = Personnel(name=data.name, role=data.role, phone=data.phone, leader_id=data.leader_id, reg_code=c); db.add(p); db.commit(); db.refresh(p); return _ep(p, db)
@router.put("/api/personnel/{pid}", response_model=PersonnelOut)
def update_personnel(pid: int, data: PersonnelUpdate, db: Session = Depends(get_db), _: User = Depends(require_perm("manage_personnel"))):
    p = db.query(Personnel).filter(Personnel.id == pid).first()
    if not p: raise HTTPException(404, "不存在")
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(p, k, v)
    db.commit(); db.refresh(p); return _ep(p, db)
@router.delete("/api/personnel/{pid}")
def delete_personnel(pid: int, db: Session = Depends(get_db), _: User = Depends(require_perm("manage_personnel"))):
    p = db.query(Personnel).filter(Personnel.id == pid).first()
    if not p: raise HTTPException(404, "不存在")
    db.delete(p); db.commit(); return {"ok": True}
@router.post("/api/personnel/{pid}/regenerate-code")
def regen_code(pid: int, db: Session = Depends(get_db), _: User = Depends(require_perm("manage_personnel"))):
    p = db.query(Personnel).filter(Personnel.id == pid).first()
    if not p: raise HTTPException(404, "不存在")
    if p.user_id: raise HTTPException(400, "已注册")
    while True:
        c = secrets.token_hex(4).upper()[:8]
        if not db.query(Personnel).filter(Personnel.reg_code == c).first(): break
    p.reg_code = c; db.commit(); return {"reg_code": c}

@router.get("/api/personnel/members/{leader_id}")
def get_members(leader_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """获取某组长的所有下属组员"""
    members = db.query(Personnel).filter(Personnel.leader_id == leader_id, Personnel.status == "active").all()
    return [{"id": m.id, "name": m.name, "role": m.role} for m in members]

# --- TASKS ---
def _et(task, db):
    def _names(s):
        if not s: return ""
        ids = [x.strip() for x in s.split(",") if x.strip()]
        ns = []
        for i in ids:
            try: p = db.query(Personnel).filter(Personnel.id == int(i)).first(); ns.append(p.name if p else i)
            except: ns.append(i)
        return "、".join(ns)
    task.leader_names = _names(task.leader_ids); task.member_names = _names(task.member_ids)
    return task

@router.get("/api/tasks", response_model=List[TaskOut])
def list_tasks(status: Optional[str] = None, search: Optional[str] = None, month: Optional[str] = None,
               leader_id: Optional[int] = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(Task)
    if status: q = q.filter(Task.status == status)
    if month: q = q.filter(or_(Task.date_start == None, Task.date_start <= month + "-31")).filter(or_(Task.date_end == None, Task.date_end >= month + "-01"))
    if leader_id: q = q.filter(or_(Task.leader_ids == str(leader_id), Task.leader_ids.like(f"{leader_id},%"), Task.leader_ids.like(f"%,{leader_id},%"), Task.leader_ids.like(f"%,{leader_id}")))
    if search: q = q.filter(or_(Task.pid.contains(search), Task.task_name.contains(search), Task.company.contains(search)))
    tasks = q.order_by(Task.id.desc()).all()
    if not user.has_perm("view_all_tasks"):
        lp = db.query(Personnel).filter(Personnel.user_id == user.id).first()
        ps = str(lp.id) if lp else str(user.id)
        tasks = [t for t in tasks if ps in (t.leader_ids or "") or ps in (t.member_ids or "")]
    return [_et(t, db) for t in tasks]

@router.post("/api/tasks", response_model=TaskOut)
def create_task(data: TaskCreate, db: Session = Depends(get_db), _: User = Depends(require_perm("manage_tasks"))):
    t = Task(**data.model_dump()); db.add(t); db.commit(); db.refresh(t); return _et(t, db)

@router.put("/api/tasks/{tid}", response_model=TaskOut)
def update_task(tid: int, data: TaskUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = db.query(Task).filter(Task.id == tid).first()
    if not t: raise HTTPException(404, "不存在")
    if data.status in ("done", "cancelled"):
        if not user.has_perm("manage_tasks"):
            lp = db.query(Personnel).filter(Personnel.user_id == user.id).first()
            if not lp or str(lp.id) not in (t.leader_ids or ""): raise HTTPException(403, "只有组长或管理员可操作")
        if data.status == "cancelled" and not data.cancel_reason: raise HTTPException(400, "取消需填写原因")
        if data.status == "abnormal" and not data.cancel_reason: raise HTTPException(400, "异常需填写原因")
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(t, k, v)
    db.commit(); db.refresh(t); return _et(t, db)

@router.delete("/api/tasks/{tid}")
def delete_task(tid: int, db: Session = Depends(get_db), _: User = Depends(require_perm("manage_tasks"))):
    t = db.query(Task).filter(Task.id == tid).first()
    if not t: raise HTTPException(404, "不存在")
    db.delete(t); db.commit(); return {"ok": True}

# --- SAMPLING ---
@router.get("/api/sampling", response_model=List[SamplingOut])
def list_sampling(task_id: Optional[int] = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(SamplingRecord)
    if task_id: q = q.filter(SamplingRecord.task_id == task_id)
    recs = q.order_by(SamplingRecord.id.desc()).all()
    if not user.has_perm("view_all_tasks"): recs = [r for r in recs if r.sampler_id == user.id]
    for r in recs: r.sampler_name = r.sampler_user.display_name if r.sampler_user else ""
    return recs

@router.post("/api/sampling", response_model=SamplingOut)
def create_sampling(data: SamplingCreate, db: Session = Depends(get_db), user: User = Depends(require_perm("do_sampling"))):
    r = SamplingRecord(task_id=data.task_id, sampler_id=user.id, date=data.date or datetime.now(timezone.utc).strftime("%Y-%m-%d"), ports=[p.model_dump() for p in data.ports])
    db.add(r); db.commit(); db.refresh(r); r.sampler_name = user.display_name; return r

@router.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    all_t = db.query(Task).all()
    if not user.has_perm("view_all_tasks"):
        lp = db.query(Personnel).filter(Personnel.user_id == user.id).first()
        ps = str(lp.id) if lp else str(user.id)
        all_t = [t for t in all_t if ps in (t.leader_ids or "") or ps in (t.member_ids or "")]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Current week (Mon-Sun)
    now = datetime.now(timezone.utc)
    wd = now.weekday()
    ws = (now - timedelta(days=wd)).strftime("%Y-%m-%d")
    we = (now + timedelta(days=6 - wd)).strftime("%Y-%m-%d")
    # Today tasks grouped by leader
    tt = [t for t in all_t if t.date_start and t.date_end and t.date_start <= today <= t.date_end][:20]
    tg = {}
    for t in tt:
        lids = [x.strip() for x in (t.leader_ids or "").split(",") if x.strip()]
        for lid in lids:
            ld = db.query(Personnel).filter(Personnel.id == int(lid)).first()
            ln = ld.name if ld else lid
            if ln not in tg: tg[ln] = []
            tg[ln].append(_et(t, db))
    # Week tasks per leader
    wt = [t for t in all_t if t.date_start and t.date_end and t.date_start <= we and t.date_end >= ws]
    wg = {}
    for t in wt:
        lids = [x.strip() for x in (t.leader_ids or "").split(",") if x.strip()]
        for lid in lids:
            ld = db.query(Personnel).filter(Personnel.id == int(lid)).first()
            ln = ld.name if ld else lid
            if ln not in wg: wg[ln] = {"pending": 0, "progress": 0, "done": 0, "abnormal": 0, "total": 0}
            wg[ln][t.status if t.status in ["pending","progress","done","abnormal"] else "pending"] += 1
            wg[ln]["total"] += 1
    # Period stats
    ym = now.strftime("%Y-%m")
    yq = str(now.year) + "-Q" + str((now.month - 1) // 3 + 1)
    yy = str(now.year)
    def _pm(t):
        ds = t.date_start or ""
        return {
            "monthly": ds.startswith(ym),
            "quarterly": ds[:7] >= yy + "-" + str(((int(yq[-1]) - 1) * 3 + 1)).zfill(2) and ds[:7] <= yy + "-" + str(int(yq[-1]) * 3).zfill(2),
            "yearly": ds.startswith(yy)
        }
    ms = {"pending": 0, "progress": 0, "done": 0, "total": 0}
    qs = {"pending": 0, "progress": 0, "done": 0, "total": 0}
    ys = {"pending": 0, "progress": 0, "done": 0, "total": 0}
    for t in all_t:
        p = _pm(t)
        for k, v in [("monthly", ms), ("quarterly", qs), ("yearly", ys)]:
            if p[k]:
                v["total"] += 1
                v["pending"] += 1 if t.status == "pending" else 0
                v["progress"] += 1 if t.status == "progress" else 0
                v["done"] += 1 if t.status == "done" else 0
    return {
        "total": len(all_t), "pending": sum(1 for t in all_t if t.status == "pending"),
        "progress": sum(1 for t in all_t if t.status == "progress"),
        "done": sum(1 for t in all_t if t.status == "done"),
        "today_tasks": tg,
        "week_tasks": wg,
        "week_dates": {"start": ws, "end": we},
        "periods": {"monthly": ms, "quarterly": qs, "yearly": ys}
    }
