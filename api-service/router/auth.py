from fastapi import APIRouter , HTTPException , Depends,status
from sqlalchemy.orm import Session
from redis import Redis
from gateway.auth.utils import hash_password, verify_password, create_access_token, create_refresh_token, get_token_data, get_current_user
from db.database import get_db,get_redis
from schemas.client import UserLogin, UserRegister
from db.models.client import User
import os
from datetime import datetime, timedelta

router=APIRouter()


@router.post("/register")
def register(user_data:UserRegister,db:Session=Depends(get_db)):
    existing_user=db.query(User).filter(User.email==user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    new_user=User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User registration failed"
        )

@router.post("/login")
def login(user_data:UserLogin,db:Session=Depends(get_db),r:Redis=Depends(get_redis)):
    user=db.query(User).filter(User.email==user_data.email).first()
    if not user or not verify_password(user_data.password,user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )  
    access_token_expires=timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))) 
    access_token=create_access_token(
        data={
            "sub":user.email,
            "user_id":user.id
            },
        expires_delta=access_token_expires
    )   
    refresh_token_expires=timedelta(minutes=int(os.getenv("REFRESH_TOKEN_EXPIRE", 60*24*30)))
    refresh_token=create_refresh_token(
        data={"sub":user.email},
        expires_delta=refresh_token_expires
    )
    r.setex(f"refresh_token:{user.id}",refresh_token_expires,refresh_token)
    return {
        "access_token":access_token,
        "token_type":"bearer",
        "refresh_token":refresh_token
        } 

@router.post("/logout")
def logout(
    r:Redis=Depends(get_redis),
    user_id:int=Depends(get_current_user),
    token_data:dict=Depends(get_token_data)
):
    try:
        access_token=token_data.get("token")
        access_token_exp=token_data.get("exp")
        now=datetime.now().timestamp()
        remaining_seconds=int(access_token_exp-now)
        if remaining_seconds>0:
            r.setex(
                f"blacklist:{access_token}",
                remaining_seconds,
                "blacklisted"
            )
        refresh_token_key=f"refresh_token:{user_id}"
        r.delete(refresh_token_key)
        return 
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )
