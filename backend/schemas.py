"""Pydantic schemas"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict
from datetime import datetime

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=72)

class RequestModel(BaseModel):
    model_config = {'extra': 'forbid'}

    @model_validator(mode='before')
    @classmethod
    def validate_values(cls, values):
        if not isinstance(values, dict):
            return values
        nullable = {'leader_id', 'date_start', 'date_end', 'actual_hrs', 'cancel_reason', 'permissions'}
        for key, value in values.items():
            if value is None and key not in nullable:
                raise ValueError(f'{key} 不能为空')
            if isinstance(value, str):
                if key in {'pid', 'name', 'username', 'display_name'} and (not value.strip()):
                    raise ValueError(f'{key} 不能为空')
                if key in {'pid', 'name', 'username', 'display_name'} and len(value) > 50:
                    raise ValueError(f'{key} 长度不能超过 50')
                if key in {'task_name', 'company'} and len(value) > 200:
                    raise ValueError(f'{key} 长度不能超过 200')
                if key == 'password' and cls.__name__ != 'LoginRequest' and (len(value) < 8):
                    raise ValueError('密码至少需要 8 位')
            if key == 'status' and (not cls.__name__.startswith('Task')) and (value not in {'active', 'inactive'}):
                raise ValueError('状态无效')
        return values

class LoginRequest(RequestModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user: dict

class RegisterRequest(RequestModel):
    reg_code: str = Field(..., min_length=6)
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=4)

class UserCreate(RequestModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=4)
    display_name: str = Field(..., min_length=1, max_length=50)
    role: str = Field(default='field_member')
    permissions: Optional[Dict[str, bool]] = None
    phone: str = ''

class UserUpdate(RequestModel):
    display_name: Optional[str] = None
    role: Optional[str] = None
    permissions: Optional[Dict[str, bool]] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    password: Optional[str] = None

class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    permissions: dict
    phone: str
    status: str
    created_at: Optional[datetime] = None
    model_config = {'from_attributes': True}

class PersonnelCreate(RequestModel):
    name: str = Field(..., min_length=1)
    role: str = '采样组员'
    phone: str = ''
    leader_id: Optional[int] = None

class PersonnelUpdate(RequestModel):
    name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    leader_id: Optional[int] = None

class PersonnelOut(BaseModel):
    id: int
    name: str
    role: str
    phone: str
    status: str
    reg_code: Optional[str] = None
    user_id: Optional[int] = None
    leader_id: Optional[int] = None
    leader_name: Optional[str] = None
    has_account: bool = False
    account_username: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {'from_attributes': True}

class TaskCreate(RequestModel):
    pid: str = Field(..., min_length=1)
    task_name: str = ''
    company: str = ''
    planned_hrs: float = 0
    testing_items: list = []
    project_type: str = ''
    valid_period: str = ''
    contact_person: str = ''
    contact_phone: str = ''
    project_region: str = ''
    market_manager: str = ''
    district: str = ''
    status: str = 'pending'
    note: str = ''

class TaskUpdate(RequestModel):
    pid: Optional[str] = None
    task_name: Optional[str] = None
    company: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    planned_hrs: Optional[float] = None
    actual_hrs: Optional[float] = None
    leader_ids: Optional[str] = None
    member_ids: Optional[str] = None
    testing_items: Optional[list] = None
    project_type: Optional[str] = None
    valid_period: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    project_region: Optional[str] = None
    market_manager: Optional[str] = None
    district: Optional[str] = None
    status: Optional[str] = None
    note: Optional[str] = None
    cancel_reason: Optional[str] = None

class TaskOut(BaseModel):
    id: int
    pid: str
    task_name: str
    company: str
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    planned_hrs: float
    actual_hrs: Optional[float] = None
    leader_ids: str
    member_ids: str
    leader_names: str = ''
    member_names: str = ''
    testing_items: list = []
    project_type: str = ''
    valid_period: str = ''
    contact_person: str = ''
    contact_phone: str = ''
    project_region: str = ''
    market_manager: str = ''
    district: str = ''
    status: str
    note: str
    cancel_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {'from_attributes': True}

class PortItem(BaseModel):
    name: str = ''
    note: str = ''
    photoCount: int = 0
    photoNames: List[str] = []

class SamplingCreate(RequestModel):
    task_id: int
    date: str = ''
    ports: List[PortItem] = []

class SamplingOut(BaseModel):
    id: int
    task_id: int
    sampler_id: int
    sampler_name: str = ''
    date: str
    ports: list = []
    created_at: Optional[datetime] = None
    model_config = {'from_attributes': True}
