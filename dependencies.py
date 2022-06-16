from datetime import datetime, timedelta
from typing import Union

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi import Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import sqlalchemy
import databases
import motor.motor_asyncio
from pymongo import MongoClient
from models import User, UserInDB, Token, TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
ALGORITHM = "HS256"
SECRET_KEY = "#"


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user


def verify_password(plain_password, password):
    return plain_password == password


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str):
    MONGO_DETAILS = "mongodb://localhost:27017"

    client = MongoClient(MONGO_DETAILS)
    database = client.mydb
    doctors = database.doctors
    patients = database.patients
    admins = database.admins

    cursor = doctors.find()
    print(cursor)
    for doc in cursor:
        if doc["username"] == username:
            user_dict = doc
            return UserInDB(**user_dict)
    cursor = patients.find()
    for patient in cursor:
        if patient["username"] == username:
            user_dict = patient
            return UserInDB(**user_dict)
    cursor = admins.find()
    for admin in cursor:
        if admin["username"] == username:
            user_dict = admin
            return UserInDB(**user_dict)


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
