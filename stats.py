# analytics.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from auth import get_current_user
from database import get_db
from models import Department, Employee, EmployeeCompetency, Competency, RoleCompetency

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
)

@router.get("/dashboard")
def get_analytics_dashboard(db: Session = Depends(get_db)):
    """
    Get overall analytics data for the dashboard including:
    - Total employees
    - Total evaluated employees
    - Total not evaluated employees
    - Department-wise employee counts
    - Department-wise competency gaps
    - Competency-wise gap distribution
    """
    # Get total employees count
    total_employees = db.query(Employee).count()
    
    # Get evaluation status counts
    evaluated_count = db.query(Employee).filter(Employee.evaluation_status == True).count()
    not_evaluated_count = total_employees - evaluated_count
    
    # Get department data
    departments = db.query(Department).all()
    department_data = []
    
    for dept in departments:
        # Get employees in this department
        dept_employees = db.query(Employee).filter(Employee.department_code == dept.department_code).all()
        dept_employee_count = len(dept_employees)
        
        # Get employee numbers for competency gap calculation
        employee_numbers = [emp.employee_number for emp in dept_employees]
        
        # Initialize gap counters
        gap1_count = 0
        gap2_count = 0
        gap3_count = 0
        
        # Get competency gaps for employees in this department
        if employee_numbers:
            employee_competencies = db.query(EmployeeCompetency).filter(
                EmployeeCompetency.employee_number.in_(employee_numbers)
            ).all()
            
            for ec in employee_competencies:
                    if ec.required_score is not None and ec.actual_score is not None:
                        gap = ec.required_score - ec.actual_score
                        if gap == 1:
                            gap1_count += 1
                        elif gap == 2:
                            gap2_count += 1
                        elif gap == 3:
                            gap3_count += 1

        
        # Get evaluation status counts for this department
        dept_evaluated = db.query(Employee).filter(
            Employee.department_code == dept.department_code,
            Employee.evaluation_status == True
        ).count()
        
        dept_not_evaluated = dept_employee_count - dept_evaluated
        
        department_data.append({
            "departmentCode": dept.department_code,
            "departmentName": dept.name,
            "employeeCount": dept_employee_count,
            "gapData": {
                "gap1": gap1_count,
                "gap2": gap2_count,
                "gap3": gap3_count
            },
            "evaluatedCount": dept_evaluated,
            "notEvaluatedCount": dept_not_evaluated
        })
    
    # Get competency data
    competencies = db.query(Competency).all()
    competency_data = []
    
    for comp in competencies:
        # Get competency gaps by competency
        employee_comp_records = db.query(EmployeeCompetency).filter(
            EmployeeCompetency.competency_code == comp.code
        ).all()
        
        gap1_count = 0
        gap2_count = 0
        gap3_count = 0
        
        for ec in employee_comp_records:
            if ec.required_score is not None and ec.actual_score is not None:
                gap = ec.required_score - ec.actual_score
                if gap == 1:
                    gap1_count += 1
                elif gap == 2:
                    gap2_count += 1
                elif gap == 3:
                    gap3_count += 1

        
        competency_data.append({
            "competencyCode": comp.code,
            "competencyName": comp.name,
            "gapData": {
                "gap1": gap1_count,
                "gap2": gap2_count,
                "gap3": gap3_count
            }
        })
    
    # Compile all data
    return {
        "totalEmployees": total_employees,
        "totalEvaluated": evaluated_count,
        "totalNotEvaluated": not_evaluated_count,
        "departmentData": department_data,
        "competencyData": competency_data
    }

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Competency, EmployeeCompetency


@router.get("/by-competency")
def get_competency_gap_data(db: Session = Depends(get_db)):
    competencies = db.query(Competency).all()
    result = []

    for comp in competencies:
        gap1 = 0
        gap2 = 0
        gap3 = 0

        # Get all employee competencies for this competency
        records = db.query(EmployeeCompetency).filter(
            EmployeeCompetency.competency_code == comp.code
        ).all()

        for record in records:
            if record.required_score is not None and record.actual_score is not None:
                gap = record.required_score - record.actual_score
                if gap == 1:
                    gap1 += 1
                elif gap == 2:
                    gap2 += 1
                elif gap == 3:
                    gap3 += 1

        result.append({
            "competencyCode": comp.code,
            "competencyName": comp.name,
            "gap1": gap1,
            "gap2": gap2,
            "gap3": gap3,
            "totalGapEmployees": gap1 + gap2 + gap3
        })

    return result




@router.get("/details/by-competency/{compcode}")
def get_employee_gaps_by_competency(
    compcode: str,
    db: Session = Depends(get_db)
    # ,current_user: dict = Depends(get_current_user)
):
    records = db.query(EmployeeCompetency).filter(
        EmployeeCompetency.competency_code == compcode
    ).all()

    result = []

    for rec in records:
        if rec.required_score is not None and rec.actual_score is not None:
            gap = rec.required_score - rec.actual_score
            if gap > 0:
                result.append({
                    "employeeNumber": rec.employee_number,
                    "requiredScore": rec.required_score,
                    "actualScore": rec.actual_score,
                    "gap": gap
                })

    # Sort by descending gap
    result.sort(key=lambda x: x["gap"], reverse=True)

    return result
