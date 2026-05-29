"""Pydantic schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class LoginRequest(BaseModel): username: str; password: str
class TokenResponse(BaseModel): access_token: str; token_type: str = "bearer"; user: dict
class RegisterRequest(BaseModel): reg_code: str = Field(..., min_length=6); username: str = Field(..., min_length=2, max_length=50); password: str = Field(..., min_length=4)

class UserCreate(BaseModel): username: str = Field(..., min_length=2, max_length=50); password: str = Field(..., min_length=4); display_name: str = Field(..., min_length=1, max_length=50); role: str = Field(default="field_member"); permissions: Optional[Dict[str, bool]] = None; phone: str = ""
class UserUpdate(BaseModel): display_name: Optional[str] = None; role: Optional[str] = None; permissions: Optional[Dict[str, bool]] = None; phone: Optional[str] = None; status: Optional[str] = None; password: Optional[str] = None
class UserOut(BaseModel): id: int; username: str; display_name: str; role: str; permissions: dict; phone: str; status: str; created_at: Optional[datetime] = None; model_config = {"from_attributes": True}

class PersonnelCreate(BaseModel): name: str = Field(..., min_length=1); role: str = "采样组员"; phone: str = ""; leader_id: Optional[int] = None
class PersonnelUpdate(BaseModel): name: Optional[str] = None; role: Optional[str] = None; phone: Optional[str] = None; status: Optional[str] = None; leader_id: Optional[int] = None
class PersonnelOut(BaseModel): id: int; name: str; role: str; phone: str; status: str; reg_code: Optional[str] = None; user_id: Optional[int] = None; leader_id: Optional[int] = None; leader_name: Optional[str] = None; has_account: bool = False; account_username: Optional[str] = None; created_at: Optional[datetime] = None; model_config = {"from_attributes": True}

class TaskCreate(BaseModel): pid: str = Field(..., min_length=1); task_name: str = ""; company: str = ""; planned_hrs: float = 0; testing_items: list = []; project_type: str = ""; valid_period: str = ""; contact_person: str = ""; contact_phone: str = ""; project_region: str = ""; market_manager: str = ""; district: str = ""; status: str = "pending"; note: str = ""
class TaskUpdate(BaseModel): pid: Optional[str] = None; task_name: Optional[str] = None; company: Optional[str] = None; date_start: Optional[str] = None; date_end: Optional[str] = None; planned_hrs: Optional[float] = None; actual_hrs: Optional[float] = None; leader_ids: Optional[str] = None; member_ids: Optional[str] = None; testing_items: Optional[list] = None; project_type: Optional[str] = None; valid_period: Optional[str] = None; contact_person: Optional[str] = None; contact_phone: Optional[str] = None; project_region: Optional[str] = None; market_manager: Optional[str] = None; district: Optional[str] = None; status: Optional[str] = None; note: Optional[str] = None; cancel_reason: Optional[str] = None
class TaskOut(BaseModel): id: int; pid: str; task_name: str; company: str; date_start: Optional[str] = None; date_end: Optional[str] = None; planned_hrs: float; actual_hrs: Optional[float] = None; leader_ids: str; member_ids: str; leader_names: str = ""; member_names: str = ""; testing_items: list = []; project_type: str = ""; valid_period: str = ""; contact_person: str = ""; contact_phone: str = ""; project_region: str = ""; market_manager: str = ""; district: str = ""; status: str; note: str; cancel_reason: Optional[str] = None; created_at: Optional[datetime] = None; model_config = {"from_attributes": True}

class PortItem(BaseModel): name: str = ""; note: str = ""; photoCount: int = 0; photoNames: List[str] = []
class SamplingCreate(BaseModel): task_id: int; date: str = ""; ports: List[PortItem] = []
class SamplingOut(BaseModel): id: int; task_id: int; sampler_id: int; sampler_name: str = ""; date: str; ports: list = []; created_at: Optional[datetime] = None; model_config = {"from_attributes": True}
