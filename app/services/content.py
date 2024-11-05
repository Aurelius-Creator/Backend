from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from sqlalchemy.future import select
from app.models.content import ContentTypeModel
from app.schemas.content import ContentTypeSchema, ContentTypeCreateSchema, ContentTypeUpdateSchema

async def get_contents(db: AsyncSession) -> list[ContentTypeSchema]:
    result = await db.execute(select(ContentTypeModel))
    items = result.scalars().all()
    return items

async def get_content_by_id(db: AsyncSession, id: int) -> ContentTypeSchema:
    result = await db.execute(select(ContentTypeModel).where(ContentTypeModel.id == id))
    item = result.scalars().first()
    
    if item is None:
        raise NoResultFound
    return item

async def create_content(db: AsyncSession, content_data: ContentTypeCreateSchema) -> ContentTypeSchema:
    new_item = ContentTypeModel(content_name=content_data.content_name, icon=content_data.icon)
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item

async def update_content(db: AsyncSession, id: int, content_data: ContentTypeUpdateSchema) -> ContentTypeSchema:
    item = await get_content_by_id(db, id)
    
    if item is None:
        raise NoResultFound
    
    if content_data.content_name is not None:
        item.content_name = content_data.content_name
    if content_data.icon is not None:
        item.icon = content_data.icon
    
    await db.commit()
    await db.refresh(item)
    return item