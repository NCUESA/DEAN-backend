from datetime import datetime, timedelta

from fastapi.routing import APIRouter
from fastapi import Depends, Response

from sqlalchemy.orm import Session

from dependencies import get_db, get_password_hash, authenticate_user, create_token, get_current_user_by_refresh_token, get_current_user
from schemas import RegisterSchema, LoginSchema, TokenSchema, RefreshSchema, UserSchema
from models import User
from exceptions import UnauthenticatedException, DuplicateModelException

router = APIRouter(prefix="/auth")

@router.post("/register")
async def register(data: RegisterSchema, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise DuplicateModelException(attribute_name="username")
    db.add(User(username=data.username, password=get_password_hash(data.password)))
    db.flush()
    db.commit()
    return Response(content=None, status_code=204)

@router.post("/login", response_model=TokenSchema)
async def login(data: LoginSchema, db: Session = Depends(get_db)):
    user = await authenticate_user(db=db, username=data.username, password=data.password)
    if not user:
        raise UnauthenticatedException()
    access_token = await create_token({"sub": user.username, "exp": datetime.utcnow() + timedelta(hours=1), "for": "access"})
    refresh_token = await create_token({"sub": user.username, "exp": datetime.utcnow() + timedelta(days=3600), "for": "refresh"})
    return {"access_token": access_token, "refresh_token": refresh_token}

@router.post("/refresh", response_model=TokenSchema)
async def refresh(data: RefreshSchema, db: Session = Depends(get_db)):
    user = await get_current_user_by_refresh_token(token=data.refresh_token, db=db)
    if not user:
        raise UnauthenticatedException()
    access_token = await create_token({"sub": user.username, "exp": datetime.utcnow() + timedelta(hours=1), "for": "access"})
    return {"access_token": access_token, "refresh_token": data.refresh_token}

@router.get("/me", response_model=UserSchema)
async def me(user: User = Depends(get_current_user)):
    return user