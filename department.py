from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import Department
from schemas import DepartmentCreate, DepartmentResponse
from database import get_db

router = APIRouter()

@router.post("/departments/", response_model=DepartmentResponse)
def create_department(department: DepartmentCreate, db: Session = Depends(get_db)):
    existing_department = db.query(Department).filter(Department.name == department.name).first()
    if existing_department:
        raise HTTPException(status_code=400, detail="Department already exists")

    new_department = Department(department_code = department.department_code,name=department.name)
    db.add(new_department)
    db.commit()
    db.refresh(new_department)

    return new_department

@router.get("/departments/", response_model=list[DepartmentResponse])
def get_departments(db: Session = Depends(get_db)):
    return db.query(Department).all()


@router.put("/departments/{department_code}", response_model=DepartmentResponse)
def update_department(department_code: str, department_data: DepartmentCreate, db: Session = Depends(get_db)):
    department = db.query(Department).filter(Department.department_code== department_code).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    department.department_code = department_data.department_code
    department.name = department_data.name
    db.commit()
    db.refresh(department)

    return department

@router.delete("/departments/{department_code}", response_model=dict)
def delete_department(department_code: str, db: Session = Depends(get_db)):
    department = db.query(Department).filter(Department.department_code== department_code).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    db.delete(department)
    db.commit()

    return {"message": "Department deleted successfully"}
