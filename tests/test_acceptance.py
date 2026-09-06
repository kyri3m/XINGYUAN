"""Regression coverage added during full UI and API acceptance testing."""
from test_api import env
from backend.models import User, Personnel, Task

def test_registration_code_reset_and_inactive(env):
    c,h,_=env
    result=c.post('/api/personnel/11/regenerate-code',headers=h())
    assert result.status_code==200
    assert result.json()['reg_code']!='CCCCCC33'
    assert c.post('/api/auth/register',json={'username':'newtest','password':'password123','reg_code':'CCCCCC33'}).status_code==400
    assert c.post('/api/personnel/2/regenerate-code',headers=h()).status_code==400
    assert c.put('/api/personnel/11',headers=h(),json={'status':'inactive'}).status_code==200
    assert c.post('/api/auth/register',json={'username':'newtest','password':'password123','reg_code':result.json()['reg_code']}).status_code==403

def test_user_disable_synced_to_personnel(env):
    c,h,_=env
    assert c.put('/api/users/2',headers=h(),json={'status':'inactive'}).status_code==200
    person=next(p for p in c.get('/api/personnel',headers=h()).json() if p['id']==1)
    assert person['status']=='inactive'
    assert c.get('/api/tasks',headers=h(2)).status_code==401

def test_person_edit_does_not_reactivate_disabled_account(env):
    c,h,factory=env
    with factory() as db:
        db.get(User,2).status='inactive'
        db.commit()
    assert c.put('/api/personnel/1',headers=h(),json={'phone':'13900000000'}).status_code==200
    assert c.get('/api/auth/me',headers=h(2)).status_code==401

def test_personnel_cannot_bypass_admin_protection(env):
    c,h,factory=env
    with factory() as db:
        db.get(User,3).role='admin'
        db.commit()
    assert c.put('/api/personnel/2',headers=h(4),json={'role':'采样组员'}).status_code==403
    assert c.put('/api/personnel/2',headers=h(4),json={'status':'inactive'}).status_code==403

def test_unscheduled_quarterly_statistics(env):
    c,h,_=env
    assert c.put('/api/tasks/2',headers=h(),json={'valid_period':'月度+季度'}).status_code==200
    result=c.get('/api/dashboard',headers=h()).json()['periods']
    assert result['monthly']['pending']==1
    assert result['quarterly']['pending']==1

def test_month_filter_rejects_invalid_month(env):
    c,h,_=env
    for month in ['invalid','2026-99','2026-1']:
        assert c.get('/api/tasks',headers=h(),params={'month':month}).status_code==422
    assert c.get('/api/tasks',headers=h(),params={'month':'2026-09'}).status_code==200

def test_missing_entities_and_permissions(env):
    c,h,_=env
    for kind in ['tasks','personnel','users']:
        assert c.delete('/api/'+kind+'/999',headers=h()).status_code==404
    assert c.get('/api/users',headers=h(2)).status_code==403
    assert c.post('/api/personnel',headers=h(2),json={'name':'test'}).status_code==403
    assert c.post('/api/sampling',headers=h(),json={'task_id':999}).status_code==404
    assert c.post('/api/sampling',headers=h(),json={'task_id':1,'date':'bad'}).status_code==422

def test_task_filters_and_members(env):
    c,h,_=env
    assert len(c.get('/api/tasks?status=progress&leader_id=2',headers=h()).json())==1
    assert len(c.get('/api/tasks?search=T-002',headers=h()).json())==1
    assert c.get('/api/tasks?leader_id=12',headers=h()).json()==[]
    assert c.put('/api/personnel/1',headers=h(),json={'leader_id':2}).status_code==200
    assert c.get('/api/personnel/members/2',headers=h()).json()[0]['id']==1
    assert c.delete('/api/personnel/2',headers=h()).status_code==409

def test_invalid_assignment_and_overlapping_member(env):
    c,h,_=env
    data={'date_start':'2026-09-07','date_end':'2026-09-08','status':'progress','leader_ids':'1'}
    assert c.put('/api/tasks/2',headers=h(),json=data).status_code==422
    data['leader_ids']='999'
    assert c.put('/api/tasks/2',headers=h(),json=data).status_code==422
    result=c.post('/api/personnel',headers=h(),json={'name':'another leader','role':'采样组长'})
    data['leader_ids']=str(result.json()['id']);data['member_ids']='11'
    assert c.put('/api/tasks/2',headers=h(),json=data).status_code==409

def test_short_password_and_extra_fields(env):
    c,h,_=env
    assert c.post('/api/users',headers=h(),json={'username':'short','display_name':'test','password':'1234'}).status_code==422
    assert c.put('/api/tasks/2',headers=h(),json={'unknown':'x'}).status_code==422
    assert c.put('/api/users/2',headers=h(),json={'permissions':{'invented':True}}).status_code==422

def test_safe_account_and_person_removal(env):
    c,h,_=env
    p=c.post('/api/personnel',headers=h(),json={'name':'temporary'}).json()
    assert c.delete('/api/personnel/'+str(p['id']),headers=h()).status_code==200
    user=c.post('/api/users',headers=h(),json={'username':'temporary','password':'password123','display_name':'temporary'}).json()
    assert c.delete('/api/users/'+str(user['id']),headers=h()).status_code==200

def test_invalid_date_canonical_form(env):
    c,h,_=env
    assert c.put('/api/tasks/2',headers=h(),json={'date_start':'20260906','date_end':'20260907'}).status_code==422

def test_recovery_clears_obsolete_failure_reason(env):
    c,h,_=env
    assert c.put('/api/tasks/1',headers=h(),json={'status':'abnormal','cancel_reason':'设备异常'}).status_code==200
    result=c.put('/api/tasks/1',headers=h(),json={'status':'done','actual_hrs':4})
    assert result.status_code==200 and result.json()['cancel_reason'] is None

def test_nonfinite_hours_rejected(env):
    c,h,_=env
    for hours in ['NaN','Infinity','-Infinity']:
        assert c.put('/api/tasks/2',headers=h(),json={'planned_hrs':hours}).status_code==422
