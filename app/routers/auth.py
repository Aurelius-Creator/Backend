import uuid
from datetime import datetime

import pytz
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.main import get_db
from app.schemas.user import UserLoginSchema
from app.services import auth

MY_TZ = pytz.timezone("Asia/Bangkok")
COOKIE_SETTINGS = {
    "httponly": True,
    "secure": False,  # Consider setting to True in production
    "samesite": "None",
}
router = APIRouter()


def set_auth_cookies(
    response: JSONResponse,
    access_token: str,
    refresh_token: str,
    csrf_token: str = None,
):
    """Helper function to set authentication cookies."""
    response.set_cookie(key="access_token", value=access_token, **COOKIE_SETTINGS)
    response.set_cookie(key="refresh_token", value=refresh_token, **COOKIE_SETTINGS)

    if csrf_token:
        response.set_cookie(
            key="csrf_token", value=csrf_token, **{**COOKIE_SETTINGS, "secure": True}
        )


def validate_tokens(request: Request) -> tuple[str, str, str]:
    """Validate and return all required tokens from cookies."""
    csrf_token = request.cookies.get("csrf_token")
    if not csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token missing"
        )

    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token missing"
        )

    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Refresh token missing"
        )

    return csrf_token, access_token, refresh_token


def format_token_payload(payload: dict) -> dict:
    """Format token payload with ISO formatted expiration datetime."""
    exp_datetime = datetime.fromtimestamp(payload.get("exp"))
    return {**payload, "exp_datetime": exp_datetime.isoformat()}


@router.post("/login")
async def login(
    user_login: UserLoginSchema, db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """Handle user login and set authentication cookies."""
    user = await auth.authenticate_user(db, user_login)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials"
        )

    # Update last login time
    user.last_login = datetime.now(MY_TZ)
    db.add(user)
    await db.commit()

    # Generate tokens
    access_token, refresh_token = auth.get_tokens(user)
    csrf_token = str(uuid.uuid4())

    # Create response with cookies
    response = JSONResponse(
        content={"msg": "Login successful", "csrf_token": csrf_token}
    )
    set_auth_cookies(response, access_token, refresh_token, csrf_token)

    return response


@router.post("/refresh")
async def refresh_token(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """Refresh access token using refresh token."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Refresh token missing"
        )

    try:
        # Validate refresh token and generate new access token
        auth.decode_token(refresh_token, is_refresh=True)
        access_token = await auth.refresh_access_token(refresh_token, db)

        response = JSONResponse(content={"msg": "Access token refreshed"})
        response.set_cookie(key="access_token", value=access_token, **COOKIE_SETTINGS)

        return response

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/logout")
async def logout(response: Response) -> dict:
    """Clear all authentication cookies."""
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    response.delete_cookie(key="csrf_token")

    return {"msg": "Logout successful"}


@router.get("/tokens/payload")
async def decode_access_token(request: Request) -> JSONResponse:
    """Decode and return payload from both access and refresh tokens."""
    csrf_token, access_token, refresh_token = validate_tokens(request)

    try:
        # Decode both tokens and format their payloads
        access_payload = auth.decode_token(access_token, is_refresh=False)
        refresh_payload = auth.decode_token(refresh_token, is_refresh=True)

        return JSONResponse(
            content={
                "access_token_payload": format_token_payload(access_payload),
                "refresh_token_payload": format_token_payload(refresh_payload),
            }
        )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
