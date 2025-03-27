from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from models import Department, User
from schemas import UserCreate, UserLogin, TokenData
from database import get_db
from security import get_password_hash, verify_password, create_access_token
from datetime import timedelta
from jose import JWTError, jwt

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

@router.post("/register/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    db_user1 = db.query(User).filter(User.username == user.username).first()
    department = db.query(Department).filter(Department.id == user.department_id).first()
    if not department:
        raise HTTPException(status_code=400, detail="Invalid department_id: Department does not exist")
    if db_user1:
        raise HTTPException(status_code=400, detail="user already registered")

    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
        department_id=user.department_id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully", "user_id": new_user.id}

@router.post("/login/")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        data={"sub": db_user.username, "role": db_user.role, "department_id": db_user.department_id},
        expires_delta=timedelta(minutes=30)
    )

    return {"access_token": access_token, "token_type": "bearer" , "user":db_user.username , "role":db_user.role,"department_id":db_user.department_id}


    
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        department_id: int = payload.get("department_id")

        if username is None or role is None or department_id is None:
            raise HTTPException(status_code=401, detail="Invalid token data")

        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        print("called")
        return {"username": username, "role": role, "department_id": department_id}

    except JWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
