
from typing import List
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi import APIRouter
from auth import get_current_user
from database import get_db
from models import Competency, Role, RoleCompetency
from schemas import RoleCreate, RoleResponse


router = APIRouter()
@router.post("/roles", response_model=RoleResponse)
def create_role(role_data: RoleCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # Check if role already exists
    existing_role = db.query(Role).filter(Role.name == role_data.name).first()
    if existing_role:
        raise HTTPException(status_code=400, detail="Role already exists")

    # Create new role
    new_role = Role(role_code = role_data.role_code,name=role_data.name)
    db.add(new_role)
    db.commit()
    db.refresh(new_role)

    return new_role


@router.get("/roles", response_model=List[RoleResponse])
def get_all_roles(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    roles = db.query(Role).all()
    return roles



@router.get("/roles/{role_id}", response_model=RoleResponse)
def get_role_by_id(role_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role
@router.put("/roles/{role_id}", response_model=RoleResponse)
def update_role(role_id: int, role_data: RoleCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    role.role_code = role_data.role_code
    role.name = role_data.name
    db.commit()
    db.refresh(role)

    return role
@router.delete("/roles/{role_id}", response_model=dict)
def delete_role(role_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    db.delete(role)
    db.commit()

    return {"message": "Role deleted successfully"}









# Get all competencies assigned to a role
@router.get("/roles/{role_code}/competencies", response_model=List[str])
def get_role_competencies(
    role_code: str,
    db: Session = Depends(get_db)
):
    role = db.query(Role).filter(Role.role_code == role_code).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    assignments = db.query(RoleCompetency.competency_code).filter(
        RoleCompetency.role_code == role_code
    ).all()
    
    return [a[0] for a in assignments]


@router.post("/roles/{role_code}/competencies", response_model=List[str])
def assign_competencies_to_role(
    role_code: str,
    competency_codes: List[str],
    db: Session = Depends(get_db)
):
    # 1. Verify role exists
    role = db.query(Role).filter(
        Role.role_code == role_code
    ).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # 2. Get existing assignments for this role
    existing_assignments = db.query(RoleCompetency.competency_code).filter(
        RoleCompetency.role_code == role_code
    ).all()
    existing_codes = {a[0] for a in existing_assignments}

    # 3. Filter out already assigned competencies
    new_codes = set(competency_codes) - existing_codes
    if not new_codes:
        return []  # No new assignments needed

    # 4. Verify competencies exist and get their required scores
    competencies = db.query(Competency.code, Competency.required_score).filter(
        Competency.code.in_(new_codes)
    ).all()
    
    existing_competency_codes = {c[0] for c in competencies}
    missing = new_codes - existing_competency_codes
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Competencies not found: {', '.join(missing)}"
        )

    # Create a dictionary of code to required_score
    competency_scores = {c.code: c.required_score for c in competencies}

    # 5. Create new assignments with the correct required_score
    for code in new_codes:
        rc = RoleCompetency(
            role_code=role_code,
            competency_code=code,
            required_score=competency_scores[code]
        )
        db.add(rc)
    
    db.commit()
    return list(new_codes)



# Remove competencies from a role
@router.delete("/roles/{role_code}/competencies", response_model=List[str])
def remove_competencies_from_role(
    role_code: str,
    competency_codes: List[str],
    db: Session = Depends(get_db)
):
    # Verify role exists
    role = db.query(Role).filter(Role.role_code == role_code).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Delete specified assignments
    result = db.query(RoleCompetency).filter(
        RoleCompetency.role_code == role_code,
        RoleCompetency.competency_code.in_(competency_codes)
    ).delete(synchronize_session=False)
    
    db.commit()
    
    if result == 0:
        raise HTTPException(
            status_code=404,
            detail="No matching competency assignments found"
        )
    
    return competency_codes