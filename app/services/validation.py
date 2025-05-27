from typing import Dict

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import NoResultFound

from app.db.main import get_db
from app.schemas.content import PermissionResponse
from app.services.auth import decode_token
from app.services.content import ContentService

HTTP_METHOD_TO_CRUD_ACTION: Dict[str, str] = {
    "POST": "C",
    "GET": "R",
    "PUT": "U",
    "PATCH": "U",
    "DELETE": "D",
}


async def validate_access_and_csrf(request: Request) -> dict:
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access token missing from validation",
        )

    csrf_token_header = request.headers.get("X-CSRF-Token")
    csrf_token_cookie = request.cookies.get("csrf_token")
    if csrf_token_header != csrf_token_cookie:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token from validation",
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
            detail="This action requires superuser privileges",
        )


async def validate_permission(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> PermissionResponse:
    token_payload = await validate_access_and_csrf(request)

    content_type = request.headers.get("X-Content")
    if not content_type:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Content type missing from validation",
        )

    action = HTTP_METHOD_TO_CRUD_ACTION.get(request.method)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid HTTP method"
        )

    if token_payload.get("super"):
        return PermissionResponse(
            authorized=True,
            user_id=token_payload.get("user_id"),
            content_type_id=content_type,
            action=action,
        )

    try:
        content_type_id = int(content_type)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid content type ID")

    try:
        return await ContentService.check_user_permission(
            user_id=token_payload.get("user_id"),
            content_type=content_type_id,
            action=action,
            db=db,
        )
    except NoResultFound as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
