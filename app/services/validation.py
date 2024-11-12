from fastapi import Request, HTTPException, status
from app.services.auth import decode_token

async def validate_access_and_csrf(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access token missing from validation"
        )

    csrf_token_header = request.headers.get("X-CSRF-Token")
    csrf_token_cookie = request.cookies.get("csrf_token")
    if csrf_token_header != csrf_token_cookie:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token from validation"
        )

    try:
        payload = decode_token(access_token)
        return payload
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    
def check_superuser(token_payload: dict):
    if not token_payload.get("super"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This action requires superuser privileges"
        )