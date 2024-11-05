from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from app.db.main import get_db
from app.schemas.content import ContentTypeSchema, ContentTypeCreateSchema, ContentTypeUpdateSchema
from app.schemas.content import ContentTypeUpdateSchema, FullContentSchemas
from app.services import content

router = APIRouter()

@router.get("/contents", response_model=list[ContentTypeSchema])
async def get_contents(db: AsyncSession = Depends(get_db)):
    return await content.get_contents(db)

@router.get("/content/{id}", response_model=ContentTypeSchema)
async def get_content_by_id(id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await content.get_content_by_id(db, id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Content not found")
    
@router.post("/content", response_model=dict)
async def create_content(content_data: ContentTypeCreateSchema, db: AsyncSession = Depends(get_db)):
    try:
        new_content, new_permissions = await content.create_content(db, content_data)
        return {"content_type": new_content, "content_permissions": new_permissions}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/content/{id}", response_model=dict)
async def update_content(id: int, content_data: ContentTypeUpdateSchema, db: AsyncSession = Depends(get_db)):
    try:
        new_content, new_permissions = await content.update_content(db, id, content_data)
        return {"content_type": new_content, "content_permissions": new_permissions}
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Content not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/contents/permissions", response_model=list[FullContentSchemas])
async def get_contents_with_permissions(db: AsyncSession = Depends(get_db)):
    try:
        return await content.get_contents_with_permissions(db)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Content not found")
    
@router.get("/content/permissions/{id}", response_model=FullContentSchemas)
async def get_content_with_permissions_by_id(id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await content.get_content_with_permissions_by_id(db, id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Content not found")