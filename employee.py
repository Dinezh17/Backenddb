from datetime import date
from typing import List
from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Employee, EmployeeCompetency, RoleCompetency
from fastapi.responses import JSONResponse
import pandas as pd
import re
import json
from io import BytesIO
from typing import List
from sqlalchemy.orm import Session
from models import Employee, EmployeeCompetency, RoleCompetency
from database import get_db
from auth import get_current_user
from schemas import BulkEvaluationStatusUpdate, EmployeeCreateRequest, EmployeeEvaluationStatusUpdate, EmployeeResponse





router = APIRouter()
from fastapi import HTTPException, status

@router.post("/employees/", response_model=EmployeeResponse)
def create_employee(
    employee_data: EmployeeCreateRequest, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Check if employee already exists
    existing_employee = db.query(Employee).filter(
        Employee.employee_number == employee_data.employee_number
    ).first()
    
    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee with number {employee_data.employee_number} already exists"
        )
    
    try:
        # Create employee
        db_employee = Employee(**employee_data.dict())
        db.add(db_employee)
        db.flush()  # Ensure we get the employee_number
        
        # Get competencies for the role
        role_competencies = db.query(RoleCompetency).filter(
            RoleCompetency.role_code == employee_data.role_code
        ).all()
        
        # Create employee competencies
        for rc in role_competencies:
            db_competency = EmployeeCompetency(
                employee_number=db_employee.employee_number,
                competency_code=rc.competency_code,
                required_score=rc.required_score,
                actual_score=None  # Changed to None as per your original requirement
            )
            db.add(db_competency)
        
        db.commit()
        db.refresh(db_employee)
        return db_employee
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating employee: {str(e)}"
        )
    




@router.put("/employees/{employee_number}", response_model=EmployeeResponse)
def update_employee(
    employee_number: str,
    employee_data: EmployeeCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Check if employee exists
        db_employee = db.query(Employee).filter(
            Employee.employee_number == employee_number
        ).first()
        
        if not db_employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with number {employee_number} not found"
            )
        
        # Check if new employee_number already exists (if it's being changed)
        if employee_number != employee_data.employee_number:
            existing_employee = db.query(Employee).filter(
                Employee.employee_number == employee_data.employee_number
            ).first()
            
            if existing_employee:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Employee with number {employee_data.employee_number} already exists"
                )
        
        # First delete all existing employee competencies
        db.query(EmployeeCompetency).filter(
            EmployeeCompetency.employee_number == employee_number
        ).delete()
        
        # Update employee data
        for field, value in employee_data.dict().items():
            setattr(db_employee, field, value)
        
        # Get competencies for the new role
        role_competencies = db.query(RoleCompetency).filter(
            RoleCompetency.role_code == employee_data.role_code
        ).all()
        
        # Create new employee competencies
        for rc in role_competencies:
            db_competency = EmployeeCompetency(
                employee_number=employee_data.employee_number,
                competency_code=rc.competency_code,
                required_score=rc.required_score,
                actual_score=None
            )
            db.add(db_competency)
        
        db.commit()
        db.refresh(db_employee)
        return db_employee
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating employee: {str(e)}"
        )

@router.delete("/employees/{employee_number}")
def delete_employee(
    employee_number: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Check if employee exists
        db_employee = db.query(Employee).filter(
            Employee.employee_number == employee_number
        ).first()
        
        if not db_employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with number {employee_number} not found"
            )
        
        # First delete all employee competencies
        db.query(EmployeeCompetency).filter(
            EmployeeCompetency.employee_number == employee_number
        ).delete()
        
        # Then delete the employee
        db.delete(db_employee)
        db.commit()
        
        return {"message": f"Employee {employee_number} deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting employee: {str(e)}"
        )


@router.get("/employees", response_model=List[EmployeeResponse])
def get_all_employees(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a list of all employees with their details.
    """
    try:
        employees = db.query(Employee).all()
        return employees
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching employees: {str(e)}"
        )




#below this is not stable yet need to be tested soo remember that


def process_excel_content(excel_content: bytes) -> List[dict]:

    xls = pd.ExcelFile(BytesIO(excel_content))
    csv_content = []
    
    for sheet_name in xls.sheet_names:
        csv_content.append(f"--- Sheet: {sheet_name} ---,\n")
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        
        for row in df.values:
            clean_row = [str(cell).strip().replace(',', '/') if pd.notna(cell) else "" for cell in row]
            
            cleaned = []
            prev_empty = False
            for cell in clean_row:
                if cell == "":
                    if not prev_empty:
                        cleaned.append(cell)
                    prev_empty = True
                else:
                    cleaned.append(cell)
                    prev_empty = False
            
            csv_line = ",".join([cell for cell in cleaned if cell != ""]) + ","
            csv_line = re.sub(r',,+', ',', csv_line)
            
            if csv_line.strip(','):
                csv_content.append(csv_line + "\n")
        
        csv_content.append(",\n")
    
    employees = []
    current_employee = None
    current_sheet = ""
    words = []
    
    for line in csv_content:
        line = line.strip()
        if not line:
            continue
        line_words = [word.strip() for word in line.split(',') if word.strip()]
        words.extend(line_words)

    i = 0
    while i < len(words):
        word = words[i]
        
        if word.startswith('--- Sheet:'):
            if current_employee is not None:
                employees.append(current_employee)
            current_employee = {
                "EmployeeNumber": "",
                "EmployeeName": "",
                "JobCode": "",
                "ReportingEmployeeName": "",
                "RoleCode": "",
                "Department": ""
            }
            current_sheet = word.replace('--- Sheet:', '').replace('---', '').strip()
            i += 1
            continue
        
        if word == "Employee Number" and i+1 < len(words):
            current_employee["EmployeeNumber"] = words[i+1]
            i += 2
        elif word == "Employee Name" and i+1 < len(words):
            current_employee["EmployeeName"] = words[i+1]
            i += 2
        elif word == "Job Code" and i+1 < len(words):
            current_employee["JobCode"] = words[i+1]
            i += 2
        elif word == "Reporting Employee Name" and i+1 < len(words):
            current_employee["ReportingEmployeeName"] = words[i+1]
            i += 2
        elif word == "Role Code" and i+1 < len(words):
            current_employee["RoleCode"] = words[i+1]
            i += 2
        elif word == "Department & Cost Centre" and i+1 < len(words):
            current_employee["Department"] = words[i+1]
            i += 2
        else:
            i += 1
    
    if current_employee is not None:
        employees.append(current_employee)
    
    return employees

@router.post("/employees/upload-excel")
async def upload_excel_employees(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user)
):
    try:
        # Read and process Excel file using your exact method
        excel_content = await file.read()
        employee_data = process_excel_content(excel_content)
        
        results = []
        
        for emp in employee_data:
            try:
                # Check if employee exists
                if db.query(Employee).filter_by(employee_number=emp["EmployeeNumber"]).first():
                    results.append({
                        "employee_number": emp["EmployeeNumber"],
                        "status": "error",
                        # "Employee_name":emp["EmployeeName"],
                        "message": "Employee already exists"
                    })
                    continue
                
                # Create new employee
                new_employee = Employee(
                    employee_number=emp["EmployeeNumber"],
                    employee_name=emp["EmployeeName"],
                    job_code=emp["JobCode"],
                    reporting_employee_name=emp["ReportingEmployeeName"],
                    role_code=emp["RoleCode"],
                    department_id=1,  # You'll need to map department names to IDs
                    evaluation_status=False,
                    evaluation_by=None,
                    last_evaluated_date=None
                )
                db.add(new_employee)
                db.flush()
                
                # Add competencies
                competencies = db.query(RoleCompetency).filter_by(
                    role_code=emp["RoleCode"]
                ).all()
                
                for comp in competencies:
                    db.add(EmployeeCompetency(
                        employee_number=new_employee.employee_number,
                        competency_code=comp.competency_code,
                        required_score=comp.required_score,
                        actual_score=None
                    ))
                
                db.commit()
                
                results.append({
                    "employee_number": emp["EmployeeNumber"],
                    "status": "success",
                    "message": "Employee created successfully"
                })
                
            except Exception as e:
                db.rollback()
                results.append({
                    "employee_number": emp.get("EmployeeNumber", "UNKNOWN"),
                    "status": "error",
                    "message": str(e)
                })
        
        return JSONResponse(content={
            "results": results,
            "total_processed": len(employee_data),
            "success_count": len([r for r in results if r["status"] == "success"]),
            "error_count": len([r for r in results if r["status"] == "error"])
        })
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing file: {str(e)}"
        )
    












    
@router.patch("/employees/{employee_number}/evaluation-status", response_model=EmployeeResponse)
async def update_employee_evaluation_status(
    employee_number: str,
    update_data: EmployeeEvaluationStatusUpdate,
    db: Session = Depends(get_db)
):
    db_employee = db.query(Employee).filter(Employee.employee_number == employee_number).first()
    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    for key, value in update_data.dict().items():
        if value is not None:
            setattr(db_employee, key, value)
    
    if update_data.status:
        db_employee.last_evaluated_date = date.today()
    
    db.commit()
    db.refresh(db_employee)
    return db_employee



@router.patch("/employees/evaluation-status", response_model=List[EmployeeResponse])
async def bulk_update_evaluation_status(
    update_data: BulkEvaluationStatusUpdate,
    db: Session = Depends(get_db)
):
    employees = db.query(Employee).filter(
        Employee.employee_number.in_(update_data.employee_numbers)
    ).all()
    
    if not employees:
        raise HTTPException(status_code=404, detail="No employees found")
    
    for employee in employees:
        employee.evaluation_status = update_data.status
        if not update_data.status:
            employee.evaluation_by = None
            employee.last_evaluated_date = None
    
    db.commit()
    return employees