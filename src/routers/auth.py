from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from src.schemas.token import Token
from src.schemas.user import UserCreate, UserLogin
from src.services import auth_service

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = auth_service.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    auth_service.create_user(db, user)
    return {"message": "User registered successfully"}


@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    authenticated_user = auth_service.authenticate_user(
        db, user.username, user.password
    )
    if not authenticated_user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": authenticated_user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
