from pwdlib import PasswordHash
from fastapi import Depends,HTTPException,status
from datetime import datetime,timedelta,timezone
from jose import jwt,JWTError
from db.database import get_redis
from redis import Redis
import os
from fastapi.security import OAuth2PasswordBearer

password_hash=PasswordHash.recommended()
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="login")
SECRET_KEY = os.getenv("SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))  # Default to 30 minutes
ALGORITHM = os.getenv("ALGORITHM", "HS256")  
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE", 60*24*30))  # 30 days

def hash_password(password):
    return password_hash.hash(password)

def verify_password(plain_password,hashed_password):
    return password_hash.verify(plain_password,hashed_password)

def create_access_token(data:dict,expires_delta:timedelta=None):
    to_encode=data.copy()
    if expires_delta:
        expire_dt=datetime.now(timezone.utc)+expires_delta
    else:
        expire_dt=datetime.now(timezone.utc)+timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire_ts=int(expire_dt.timestamp())
    to_encode.update({"exp":expire_ts})
    encode_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encode_jwt

def create_refresh_token(data:dict,expires_delta:timedelta=None):
    to_encode=data.copy()
    if expires_delta:
        expire_dt=datetime.now(timezone.utc)+expires_delta
    else:
        expire_dt=datetime.now(timezone.utc)+timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    expire_ts=int(expire_dt.timestamp())
    to_encode.update({"exp":expire_ts})
    encode_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encode_jwt

def get_current_user(
    token:str=Depends(oauth2_scheme),
    r:Redis=Depends(get_redis)
):
    try:
        if r.get(f"blacklist:{token}"):
            raise HTTPException(status_code=401,detail="Token is blacklisted")

        payload=jwt.decode(token,SECRET_KEY,algorithm=ALGORITHM)
        id=payload.get("user_id")
        if id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

def get_token_data(token:str=Depends(oauth2_scheme)):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithm=ALGORITHM)
        return {
            "token":token,
            "exp":payload.get("exp")
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
