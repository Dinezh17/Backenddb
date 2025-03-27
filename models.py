from sqlalchemy import Boolean, Column, Date, Integer, String, ForeignKey
from database import Base

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    role_code = Column(String , unique=True)
    name = Column(String, unique=True, index=True)

class Competency(Base):
    __tablename__ = "competencies"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    name = Column(String)
    description = Column(String)

class Employee(Base):
    __tablename__ = "employees"
    employee_number = Column(String, primary_key=True, index=True)
    employee_name = Column(String)
    job_code = Column(String)
    reporting_employee_name = Column(String)
    role_code = Column(String, ForeignKey("roles.role_code"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    evaluation_status = Column(Boolean, default=False)
    evaluation_by = Column(String)
    last_evaluated_date = Column(Date)

class RoleCompetency(Base):
    __tablename__ = "role_competencies"
    id = Column(Integer, primary_key=True, index=True)
    role_code = Column(Integer, ForeignKey("roles.code"))
    competency_code = Column(String, ForeignKey("competencies.code"))
    required_score = Column(Integer)

class EmployeeCompetency(Base):
    __tablename__ = "employee_competencies"
    id = Column(Integer, primary_key=True, index=True)
    employee_number = Column(String, ForeignKey("employees.number"), primary_key=True)
    competency_code = Column(Integer, ForeignKey("competencies.code"))
    required_score = Column(Integer)
    actual_score = Column(Integer)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)  # HR or HOD
    department_id = Column(Integer, ForeignKey("departments.id"))
