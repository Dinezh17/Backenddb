from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date

class DepartmentBase(BaseModel):
    name: str

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True




class RoleBase(BaseModel):
    role_code: str
    name: str

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    id: int

    class Config:
        from_attributes = True



class CompetencyBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None

class CompetencyCreate(CompetencyBase):
    pass

class CompetencyResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True




class RoleCompetencyBase(BaseModel):
    role_code: str
    code: str
    required_score: int

class RoleCompetencyCreate(RoleCompetencyBase):
    pass

class RoleCompetency(BaseModel):
    role_id: int
    competency_id: int
    required_score: int

    class Config:
        from_attributes = True








class EmployeeCreateRequest(BaseModel):
    employee_number: str
    employee_name: str
    job_code: str
    reporting_employee_name: str
    role_code: str
    department_id: int
class EmployeeResponse(BaseModel):
    employee_number: str
    employee_name: str
    job_code: str
    reporting_employee_name: str
    role_code: str
    department_id: int
    evaluation_status: bool
    evaluation_by: str | None
    last_evaluated_date: date | None
    
    class Config:
        from_attributes = True



class EmployeeEvaluationStatusUpdate(BaseModel):
    status: bool
    evaluated_by: Optional[str] = None

class BulkEvaluationStatusUpdate(BaseModel):
    employee_numbers: List[str]
    status: bool



    


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str
    department_id: int

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenData(BaseModel):
    username: str
    role: str
    department_id: int

 