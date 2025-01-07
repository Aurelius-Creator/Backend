from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.main import get_db
from app.schemas import content as contentSchemas
from app.services.content import ContentService
from app.services.validation import check_superuser, validate_access_and_csrf

router = APIRouter()


async def handle_service_error(service_call):
    try:
        return await service_call
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data not found"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/contents", response_model=List[contentSchemas.ContentTypeSchema])
async def get_contents(
    db: AsyncSession = Depends(get_db),
    token_payload: Dict = Depends(validate_access_and_csrf),
):
    service_call = (
        ContentService.get_contents_by_user_id(db, token_payload.get("user_id"))
        if not token_payload.get("super")
        else ContentService.get_contents(db)
    )
    return await handle_service_error(service_call)


@router.get("/content/{id}/permission", response_model=contentSchemas.FullContentSchema)
async def get_user_content_permission(
    id: int,
    db: AsyncSession = Depends(get_db),
    token_payload: dict = Depends(validate_access_and_csrf),
):
    return await handle_service_error(
        ContentService.get_user_content_permission(db, id, token_payload)
    )


@router.post("/content", response_model=Dict)
async def create_content(
    content_data: contentSchemas.ContentTypeCreateSchema,
    db: AsyncSession = Depends(get_db),
    token_payload: dict = Depends(validate_access_and_csrf),
):
    check_superuser(token_payload)
    new_content, new_permissions = await handle_service_error(
        ContentService.create_content(db, content_data)
    )
    return {"content_type": new_content, "content_permissions": new_permissions}


@router.patch("/content/{id}", response_model=Dict)
async def update_content(
    id: int,
    content_data: contentSchemas.ContentTypeUpdateSchema,
    db: AsyncSession = Depends(get_db),
    token_payload: Dict = Depends(validate_access_and_csrf),
):
    check_superuser(token_payload)
    new_content, new_permissions = await handle_service_error(
        ContentService.update_content(db, id, content_data)
    )
    return {"content_type": new_content, "content_permissions": new_permissions}


@router.get(
    "/contents/permissions", response_model=List[contentSchemas.FullContentSchema]
)
async def get_contents_with_permissions(db: AsyncSession = Depends(get_db)):
    return await handle_service_error(ContentService.get_contents_with_permissions(db))


@router.get("/permissions", response_model=List[contentSchemas.ContentPermissionSchema])
async def get_all_permissions(db: AsyncSession = Depends(get_db)):
    return await handle_service_error(ContentService.get_all_permissions(db))
