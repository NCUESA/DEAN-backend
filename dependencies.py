from typing import Annotated

from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse

from jose import JWTError, jwt
from passlib.context import CryptContext

from models import User
from exceptions import UnauthenticatedException


engine = create_engine("mysql+pymysql://root@localhost:3306/dean")
SessionLocal = sessionmaker(engine, autoflush=False)

async def get_db():
    db = SessionLocal()
    try:
        yield db
    except:
        raise
    finally:
        db.close()


SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

async def authenticate_user(db: Session, username: str, password: str):
    user = await get_user(db=db, username=username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

async def create_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        used_for: str = payload.get("for")
        if not used_for:
            raise UnauthenticatedException()
        if used_for != "access":
            raise UnauthenticatedException()
        username: str = payload.get("sub")
        if not username:
            raise UnauthenticatedException()
    except JWTError:
        raise UnauthenticatedException()
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise UnauthenticatedException()
    return user

async def get_current_user_by_refresh_token(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        used_for: str = payload.get("for")
        if not used_for:
            raise UnauthenticatedException()
        if used_for != "refresh":
            raise UnauthenticatedException()
        username: str = payload.get("sub")
        if not username:
            raise UnauthenticatedException()
    except JWTError:
        raise UnauthenticatedException()
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise UnauthenticatedException()
    return user