import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.main import app
from backend.models import Base, get_db, User, Personnel, Task, ROLE_TEMPLATES
from backend.auth import hash_password, create_access_token

@pytest.fixture
def env():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    def database():
        with factory() as session:
            yield session
    app.dependency_overrides[get_db] = database
    with factory() as db:
        for uid, role in [(1, 'admin'), (2, 'field_member'), (3, 'field_leader'), (4, 'field_director')]:
            db.add(User(id=uid, username=f'user{uid}', display_name=f'用户{uid}', password_hash=hash_password('password123'), role=role, permissions=ROLE_TEMPLATES[role], status='active'))
        db.add_all([Personnel(id=1,name='组员',role='采样组员',user_id=2,status='active',reg_code='AAAAAA11'), Personnel(id=2,name='组长',role='采样组长',user_id=3,status='active',reg_code='BBBBBB22'), Personnel(id=11,name='另一组员',role='采样组员',status='active',reg_code='CCCCCC33')])
        db.add_all([Task(id=1,pid='T-001',task_name='河道监测',leader_ids='2',member_ids='11',date_start='2026-09-07',date_end='2026-09-08',status='progress'), Task(id=2,pid='T-002',task_name='待派单',status='pending')])
        db.commit()
    client = TestClient(app)
    def headers(uid=1):
        return {'Authorization': 'Bearer '+create_access_token({'sub': str(uid)})}
    yield client, headers, factory
    app.dependency_overrides.clear()
    engine.dispose()

def test_login_and_health(env):
    c,h,_=env
    assert c.get('/api/health').json()['status']=='ok'
    assert c.post('/api/auth/login',json={'username':'user1','password':'password123'}).status_code==200
    assert c.post('/api/auth/login',json={'username':'user1','password':'wrong'}).status_code==401
    assert c.get('/api/tasks').status_code in (401,403)

def test_exact_membership_not_substring(env):
    c,h,_=env
    assert c.get('/api/tasks',headers=h(2)).json()==[]
    assert c.get('/api/dashboard',headers=h(2)).json()['total']==0
    assert c.get('/api/personnel',headers=h(2)).json()[0]['reg_code'] is None

def test_member_cannot_modify_arbitrary_task(env):
    c,h,_=env
    assert c.put('/api/tasks/1',headers=h(2),json={'company':'tampered'}).status_code==403
    assert c.put('/api/tasks/1',headers=h(2),json={'status':'abnormal','cancel_reason':'x'}).status_code==403

def test_leader_limited_result_update(env):
    c,h,_=env
    assert c.put('/api/tasks/1',headers=h(3),json={'company':'tampered'}).status_code==403
    assert c.put('/api/tasks/1',headers=h(3),json={'status':'abnormal'}).status_code==422
    assert c.put('/api/tasks/1',headers=h(3),json={'status':'done','actual_hrs':4}).status_code==200

def test_duplicate_and_date_validation(env):
    c,h,_=env
    assert c.post('/api/tasks',headers=h(),json={'pid':'T-001'}).status_code==409
    for data in [{'date_start':'2026-09-09','date_end':'2026-09-08'}, {'date_start':'2026-02-30','date_end':'2026-03-01'}, {'planned_hrs':-2}, {'status':'anything'}, {'pid':None}, {'testing_items':[{}]}]:
        assert c.put('/api/tasks/2',headers=h(),json=data).status_code==422

def test_dispatch_and_conflict(env):
    c,h,_=env
    data={'status':'progress','date_start':'2026-09-07','date_end':'2026-09-09','leader_ids':'2','member_ids':''}
    assert c.put('/api/tasks/2',headers=h(),json=data).status_code==409
    data.update(date_start='2026-09-10',date_end='2026-09-11')
    assert c.put('/api/tasks/2',headers=h(),json=data).status_code==200
    assert c.get('/api/tasks',headers=h()).json()[0]['leader_names']=='组长'

def test_sampling_scope_and_delete_protection(env):
    c,h,_=env
    data={'task_id':1,'date':'2026-09-07','ports':[{'name':'排水口','note':'正常'}]}
    assert c.post('/api/sampling',headers=h(2),json=data).status_code==403
    assert c.post('/api/sampling',headers=h(3),json=data).status_code==200
    assert c.delete('/api/tasks/1',headers=h()).status_code==409
    assert c.delete('/api/users/3',headers=h()).status_code==409

def test_personnel_relationship_guards(env):
    c,h,_=env
    assert c.put('/api/personnel/2',headers=h(),json={'leader_id':2}).status_code==422
    assert c.delete('/api/personnel/11',headers=h()).status_code==409
    assert c.post('/api/personnel',headers=h(),json={'name':'新增','role':'admin'}).status_code==422

def test_no_privilege_escalation(env):
    c,h,_=env
    assert c.post('/api/users',headers=h(4),json={'username':'hack','password':'password123','display_name':'x','role':'admin'}).status_code==403
    assert c.put('/api/users/1',headers=h(4),json={'password':'password456'}).status_code==403
    assert c.put('/api/users/1',headers=h(),json={'status':'inactive'}).status_code==409
    assert c.delete('/api/users/1',headers=h()).status_code==400

def test_registration_maps_role_and_single_use(env):
    c,h,_=env
    data={'username':'newperson','password':'password123','reg_code':'CCCCCC33'}
    assert c.post('/api/auth/register',json=data).status_code==200
    assert c.post('/api/auth/register',json=data).status_code==400
    result=c.post('/api/auth/login',json={'username':'newperson','password':'password123'}).json()
    assert result['user']['role']=='field_member'

def test_change_password(env):
    c,h,_=env
    assert c.post('/api/auth/password',headers=h(),json={'current_password':'bad','new_password':'newpassword'}).status_code==400
    assert c.post('/api/auth/password',headers=h(),json={'current_password':'password123','new_password':'newpassword'}).status_code==200
    assert c.post('/api/auth/login',json={'username':'user1','password':'newpassword'}).status_code==200

def test_crud_roundtrip_and_empty_permissions(env):
    c,h,_=env
    result=c.post('/api/tasks',headers=h(),json={'pid':'T-003','task_name':'土壤监测','testing_items':[{'category':'土壤','items':['pH']}]} )
    assert result.status_code==200
    tid=result.json()['id']
    assert c.put(f'/api/tasks/{tid}',headers=h(),json={'task_name':'更新任务'}).json()['task_name']=='更新任务'
    assert c.delete(f'/api/tasks/{tid}',headers=h()).status_code==200
    result=c.post('/api/users',headers=h(),json={'username':'empty','password':'password123','display_name':'无权限','permissions':{}})
    assert result.status_code==200 and result.json()['permissions']=={}
