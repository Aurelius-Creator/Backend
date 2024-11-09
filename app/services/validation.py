from fastapi import Request, HTTPException, status
from app.services.auth import decode_token

async def validate_access_and_csrf(request: Request):
    access_token = request.cookies.get("access_token")
    csrf_token_cookie = request.cookies.get("csrf_token")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access token missing"
        )

    # Validate CSRF token in header matches the one in the cookie
    csrf_token_header = request.headers.get("X-CSRF-Token")
    if csrf_token_header != csrf_token_cookie:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token"
        )

    try:
        payload = decode_token(access_token)
        return payload
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=e.detail
        )