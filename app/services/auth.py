from fastapi import HTTPException, status
from sqlalchemy.exc import NoResultFound
from jose import JWTError, jwt, ExpiredSignatureError
from datetime import datetime, timedelta
from app.models.user import UserModel
from app.schemas.user import UserLoginSchema
from app.services.user import get_user_by_username, get_user_by_id
import bcrypt
import pytz

MY_TZ = pytz.timezone("Asia/Bangkok")
SECRET_KEY = "urielAccessKey"
REFRESH_SECRET_KEY = "urielRefreshKey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10
REFRESH_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 3

async def authenticate_user(db, user_login: UserLoginSchema):
    try:
        user = await get_user_by_username(db, user_login.username)
        if not await verify_password(user_login.password, user.password):
            return None
        
        return user
    except NoResultFound:
        return None

async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_tokens(user: UserModel):
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_token(
        data={"user_id": user.id, "super": user.is_superuser}, expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    refresh_token = create_token(
        data={"user_id": user.id, "super": user.is_superuser}, expires_delta=refresh_token_expires, is_refresh=True
    )

    return access_token, refresh_token

def create_token(data: dict, expires_delta: timedelta, is_refresh: bool = False):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.now(MY_TZ) + expires_delta})
    
    return jwt.encode(to_encode, REFRESH_SECRET_KEY if is_refresh else SECRET_KEY, algorithm=ALGORITHM)
    
async def refresh_access_token(refresh_token: str, db):
    try:
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid refresh token")
        
        user = await get_user_by_id(db, user_id)
        access_token, _ = get_tokens(user)
        
        return access_token
    except JWTError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Refresh token expired or invalid. Please log in again.")
    
def decode_token(token: str, is_refresh: bool = False):
    try:
        if is_refresh:
            payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        else:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if "user_id" not in payload:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=  "Token is invalid. Please login again"
            )
        
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if is_refresh else status.HTTP_401_UNAUTHORIZED,
            detail=  "Refresh token expired. Please login again" if is_refresh else "Access token expired. Please refresh your token."
        )
    except JWTError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired token")