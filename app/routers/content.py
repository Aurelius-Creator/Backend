from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from app.db.main import get_db
from app.schemas.content import ContentTypeSchema, ContentTypeCreateSchema, ContentTypeUpdateSchema
from app.schemas.content import ContentTypeUpdateSchema, FullContentSchemas
from app.services import content
from app.services.validation import validate_access_and_csrf, check_superuser

router = APIRouter()

@router.get("/contents", response_model=list[ContentTypeSchema])
async def get_contents(
    db: AsyncSession = Depends(get_db),
    token_payload: dict = Depends(validate_access_and_csrf)
):
    try:
        if not token_payload.get("super"):
            return await content.get_contents_by_user_id(db, token_payload.get("user_id"))
        else:
            return await content.get_contents(db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/content/{id}/permission", response_model=FullContentSchemas)
async def get_user_content_permission(
    id: int, 
    db: AsyncSession = Depends(get_db),
    token_payload: dict = Depends(validate_access_and_csrf)
):
    try:
        return await content.get_user_content_permission(db, id, token_payload)
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    
@router.post("/content", response_model=dict)
async def create_content(
    content_data: ContentTypeCreateSchema,
    db: AsyncSession = Depends(get_db),
    token_payload: dict = Depends(validate_access_and_csrf)
):
    check_superuser(token_payload)
    try:
        new_content, new_permissions = await content.create_content(db, content_data)
        return {"content_type": new_content, "content_permissions": new_permissions}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.patch("/content/{id}", response_model=dict)
async def update_content(
    id: int, content_data: ContentTypeUpdateSchema,
    db: AsyncSession = Depends(get_db),
    token_payload: dict = Depends(validate_access_and_csrf)
):
    check_superuser(token_payload)   
    try:
        new_content, new_permissions = await content.update_content(db, id, content_data)
        return {"content_type": new_content, "content_permissions": new_permissions}
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
@router.get("/contents/permissions", response_model=list[FullContentSchemas])
async def get_contents_with_permissions(
    db: AsyncSession = Depends(get_db),
    token_payload: dict = Depends(validate_access_and_csrf)
):
    try:
        return await content.get_contents_with_permissions(db)
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")