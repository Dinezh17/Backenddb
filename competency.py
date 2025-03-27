# competencies.py (backend)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from auth import get_current_user
from database import get_db
from models import Competency
from schemas import CompetencyCreate, CompetencyResponse

router = APIRouter()

@router.post("/competency", response_model=CompetencyResponse)
def create_competency(competency: CompetencyCreate, db: Session = Depends(get_db),current_user: dict = Depends(get_current_user)):
    # Check if competency code already exists
    db_competency = db.query(Competency).filter(Competency.code == competency.code).first()
    if db_competency:
        raise HTTPException(status_code=400, detail="Competency code already exists")
    
    new_competency = Competency(**competency.model_dump())
    db.add(new_competency)
    db.commit()
    db.refresh(new_competency)
    return new_competency

@router.get("/competency", response_model=List[CompetencyResponse])
def get_all_competencies(db: Session = Depends(get_db),current_user: dict = Depends(get_current_user)):
    return db.query(Competency).all()

@router.put("/competency/{competency_id}", response_model=CompetencyResponse)
def update_competency(competency_id: int, competency: CompetencyCreate, db: Session = Depends(get_db),current_user: dict = Depends(get_current_user)):
    db_competency = db.query(Competency).filter(Competency.id == competency_id).first()
    if not db_competency:
        raise HTTPException(status_code=404, detail="Competency not found")
     
    # Check if new code conflicts with existing competencies
    if competency.code != db_competency.code:
        existing_code = db.query(Competency).filter(Competency.code == competency.code).first()
        if existing_code:
            raise HTTPException(status_code=400, detail="Competency code already exists")
    
    for key, value in competency.model_dump().items():
        setattr(db_competency, key, value)
    
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