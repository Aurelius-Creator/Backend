from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.main import get_db
from app.models import content
from app.models.content import ContentType
from pydantic import BaseModel
from typing import Optional

from app.schemas.content import ContentTypeSchema

router = APIRouter()

@router.get("/contents")
async def get_contents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(content.ContentType))
    items = result.scalars().all()
    return items

@router.get("/content/{id}")
async def get_content_by_id(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(content.ContentType).where(content.ContentType.id==id))
    item = result.scalars().first()
    
    if item is None:
        raise HTTPException(status_code=404, detail="Content not found")
    
    return item

class ContentTypeBase(BaseModel):
    id: int
    content_name: str
    icon: Optional[str] = None
    class Config:
        from_attributes = True

class ContentCreate(BaseModel):
    content_name: str
    icon: Optional[str] = None
    
@router.post("/content")
async def create_content(content_data: ContentCreate, db: AsyncSession = Depends(get_db)):
    new_item = ContentType(content_name=content_data.content_name, icon=content_data.icon)
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item


class ContentUpdate(BaseModel):
    content_name: Optional[str] = None
    icon: Optional[str] = None

@router.patch("/content/{id}")
async def update_content(id: int, content_data: ContentUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ContentType).where(ContentType.id == id))
    item = result.scalars().first()
    
    if item is None:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if content_data.content_name is not None:
        item.content_name = content_data.content_name
    if content_data.icon is not None:
        item.icon = content_data.icon
    
    await db.commit()
    await db.refresh(item)
    return item