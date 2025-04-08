from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from auth import get_current_user
from database import get_db
from models import Competency, Department, Employee, EmployeeCompetency
from schemas import CompetencyCreate, CompetencyResponse, EmployeeCompetencyResponse
import schemas

router = APIRouter()

@router.post("/competency", response_model=CompetencyResponse)
def create_competency(
    competency: CompetencyCreate, 
    db: Session = Depends(get_db), 
    # current_user: dict = Depends(get_current_user)
):
    # Checking if competency already exists
    db_competency = db.query(Competency).filter(Competency.code == competency.code).first()
    if db_competency:
        raise HTTPException(status_code=400, detail="Competency code already exists")
    
    new_competency = Competency(
        code=competency.code,
        name=competency.name,
        description=competency.description,
        required_score = competency.required_score
    )
    
    db.add(new_competency)
    db.commit()
    db.refresh(new_competency)
    
    return new_competency


@router.get("/competency", response_model=List[CompetencyResponse])
def get_all_competencies(db: Session = Depends(get_db),current_user: dict = Depends(get_current_user)):
    return db.query(Competency).all()


@router.put("/competency/{competency_id}", response_model=CompetencyResponse)
def update_competency(
    competency_id: int, 
    competency: CompetencyCreate, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    db_competency = db.query(Competency).filter(Competency.id == competency_id).first()
    if not db_competency:
        raise HTTPException(status_code=404, detail="Competency not found")
     
    if competency.code != db_competency.code:
        existing_code = db.query(Competency).filter(Competency.code == competency.code).first()
        if existing_code:
            raise HTTPException(status_code=400, detail="Competency code already exists")
    
    db_competency.code = competency.code
    db_competency.name = competency.name
    db_competency.description = competency.description
    db_competency.required_score = competency.required_score

    db.commit()
    db.refresh(db_competency)
    
    return db_competency


@router.delete("/competency/{competency_id}")
def delete_competency(competency_id: int, db: Session = Depends(get_db),current_user: dict = Depends(get_current_user)):
    competency = db.query(Competency).filter(Competency.id == competency_id).first()
    if not competency:
        raise HTTPException(status_code=404, detail="Competency not found")
    
    db.delete(competency)
    db.commit()
    return {"message": "Competency deleted successfully"}



@router.get("/employee-competencies/{employee_number}")
def get_employee_competencies(
    employee_number: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not db.query(Employee).filter(Employee.employee_number == employee_number).first():
        raise HTTPException(status_code=404, detail="Employee not found")
    
    competencies = db.query(
        EmployeeCompetency.competency_code,
        EmployeeCompetency.required_score,
        EmployeeCompetency.actual_score
    ).filter(
        EmployeeCompetency.employee_number == employee_number
    ).all()
    
    return [{
        "code": comp.competency_code,
        "required_score": comp.required_score,
        "actual_score": comp.actual_score
    } for comp in competencies]



@router.post("/evaluations")
def submit_evaluation(
    evaluation_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Validate input
    if not all(key in evaluation_data for key in ["employee_number", "evaluator_id", "scores"]):
        raise HTTPException(status_code=400, detail="Invalid evaluation data format")
    
    employee_number = evaluation_data["employee_number"]
    evaluator_id = current_user["username"]
    
    # Check if employee exists
    employee = db.query(Employee).filter(Employee.employee_number == employee_number).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Process each competency score
    for score in evaluation_data["scores"]:
        if not all(key in score for key in ["competency_code", "actual_score"]):
            continue
            
        # Update or create competency record
        competency = db.query(EmployeeCompetency).filter(
            EmployeeCompetency.employee_number == employee_number,
            EmployeeCompetency.competency_code == score["competency_code"]
        ).first()
        
        if competency:
            # Update existing record
            competency.actual_score = score["actual_score"]
            competency.last_updated = datetime.utcnow()
            competency.updated_by = evaluator_id
        # else:
        #     # Create new record
        #     new_competency = EmployeeCompetency(
        #         employee_number=employee_number,
        #         competency_code=score["competency_code"],
        #         required_score=0,  # You might want to get this from somewhere
        #         actual_score=score["actual_score"],
        #         created_by=evaluator_id,
        #         updated_by=evaluator_id
        #     )
        #     db.add(new_competency)
    
    # Update employee evaluation status
    employee.evaluation_status = True
    employee.evaluation_by = evaluator_id
    employee.last_evaluated_date = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Evaluation submitted successfully"}







@router.get("/employee-competencies", response_model=List[EmployeeCompetencyResponse])
def get_all_employee_competencies(
    db: Session = Depends(get_db)
    # current_user: dict = Depends(get_current_user)
):
    return db.query(EmployeeCompetency).all()

