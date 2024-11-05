from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from app.db.main import get_db
from app.schemas.content import ContentTypeSchema, ContentTypeCreateSchema, ContentTypeUpdateSchema
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
    
@router.post("/content", response_model=ContentTypeSchema)
async def create_content(content_data: ContentTypeCreateSchema, db: AsyncSession = Depends(get_db)):
    return await content.create_content(db, content_data)

@router.patch("/content/{id}", response_model=ContentTypeSchema)
async def update_content(id: int, content_data: ContentTypeUpdateSchema, db: AsyncSession = Depends(get_db)):
    try:
        return await content.update_content(db, id, content_data)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Content not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))