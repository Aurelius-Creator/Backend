from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserLoginSchema
from app.services import auth
from app.db.main import get_db
from datetime import datetime
import uuid

router = APIRouter()

@router.post("/login")
async def login(user_login: UserLoginSchema, db: AsyncSession = Depends(get_db)):
    user = await auth.authenticate_user(db, user_login)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")
    
    access_token, refresh_token = auth.get_tokens(user)
    csrf_token = str(uuid.uuid4())
    
    response = JSONResponse(content={"msg": "Login successful", "csrf_token": csrf_token})
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="None")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="None")
    response.set_cookie(key="csrf_token", value=csrf_token, httponly=True, secure=True, samesite="None")
    
    return response

@router.post("/refresh")
async def refresh_token(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Refresh token missing")

    try:
        auth.decode_token(refresh_token, is_refresh=True)
        access_token = await auth.refresh_access_token(refresh_token, db)

        response = JSONResponse(content={"msg": "Access token refreshed"})
        response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="None")

        return response
    
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    response.delete_cookie(key="csrf_token")
    
    return {"msg": "Logout successful"}

@router.get("/tokens/payload")
async def decode_access_token(request: Request):
    print("Received cookies:", request.cookies)
    csrf_token = request.cookies.get("csrf_token")
    if not csrf_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token missing")
     
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token missing")
    
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Refresh token missing")
    
    try:
        access_payload = auth.decode_token(access_token, is_refresh=False)
        refresh_payload = auth.decode_token(refresh_token, is_refresh=True)
        
        access_exp_datetime = datetime.fromtimestamp(access_payload.get("exp"))
        refresh_exp_datetime = datetime.fromtimestamp(refresh_payload.get("exp"))

        return JSONResponse(content={
            "access_token_payload": {**access_payload, "exp_datetime": access_exp_datetime.isoformat()}, 
            "refresh_token_payload": {**refresh_payload, "exp_datetime": refresh_exp_datetime.isoformat()}
        })
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)