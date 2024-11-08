from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserLoginSchema
from app.services import auth
from app.db.main import get_db

router = APIRouter()

@router.post("/login")
async def login(user_login: UserLoginSchema, db: AsyncSession = Depends(get_db)):
    user = await auth.authenticate_user(db, user_login)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token, refresh_token = auth.create_tokens(user)
    
    response = JSONResponse(content={
        "message": "Login successful",
        "content": ["bobo_1", "bobo_2"],
        "access_token": access_token,
        "refresh_token": refresh_token
    })
    
    response.set_cookie(key="2_access_token", value=access_token, httponly=True, secure=True, samesite="strict")
    response.set_cookie(key="2_refresh_token", value=refresh_token, httponly=True, secure=True, samesite="strict")
    
    return response

@router.post("/refresh")
async def refresh_token(response: Response, db: AsyncSession = Depends(get_db)):
    refresh_token = response.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    access_token = await auth.refresh_access_token(refresh_token, db)

    response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=15*60)

    return {"msg": "Access token refreshed"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    
    return {"msg": "Logout successful"}

@router.post("/access-token/payload")
async def decode_access_token(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Access token missing")
    
    try:
        payload = auth.decode_token(access_token, is_refresh=False)
        return JSONResponse(content=payload)
    except HTTPException as e:
        raise e
    
@router.post("/refresh-token/payload")
async def decode_refresh_token(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token missing")
    
    try:
        payload = auth.decode_token(refresh_token, is_refresh=True)
        return JSONResponse(content=payload)
    except HTTPException as e:
        raise e