from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.content import ContentTypeModel, ContentPermissionModel
from app.schemas.content import ContentTypeSchema, ContentTypeCreateSchema, ContentTypeUpdateSchema
from app.schemas.content import ContentPermissionSchema, ContentPermissionCreateSchema, FullContentSchemas

async def get_contents(db: AsyncSession) -> list[ContentTypeSchema]:
    result = await db.execute(select(ContentTypeModel))
    return result.scalars().all()

async def get_content_by_id(db: AsyncSession, id: int) -> ContentTypeSchema:
    result = await db.execute(select(ContentTypeModel).where(ContentTypeModel.id == id))
    item = result.scalars().first()
    
    if item is None:
        raise NoResultFound
    return item

async def create_content(db: AsyncSession, content_data: ContentTypeCreateSchema):
    new_content = ContentTypeModel(content_name=content_data.content_name, icon=content_data.icon)
    db.add(new_content)
    await db.commit()
    await db.refresh(new_content)
    
    new_permissions = []
    actions = [
        {"action": "C", "name": "Add"},
        {"action": "R", "name": "View"},
        {"action": "U", "name": "Update"},
        {"action": "D", "name": "Delete"}
    ]
    for action_item in actions:
        permission_data = ContentPermissionCreateSchema(
            name=f"{action_item['name']} {new_content.content_name}",
            content_type_id=new_content.id,
            action=action_item['action']
        )
        new_permission = await create_content_permission(db, permission_data)
        new_permissions.append(new_permission)
    
    content_schema = ContentTypeSchema.model_validate(new_content)
    permissions_schema = [ContentPermissionSchema.model_validate(perm) for perm in new_permissions]
    return content_schema, permissions_schema

async def update_content(db: AsyncSession, id: int, content_data: ContentTypeUpdateSchema):
    item = await get_content_by_id(db, id)
    
    if item is None:
        raise NoResultFound
    
    if content_data.content_name is not None:
        old_name = item.content_name
        item.content_name = content_data.content_name
    if content_data.icon is not None:
        item.icon = content_data.icon
        
    await db.commit()
    await db.refresh(item)
    
    updated_permissions = []
    if content_data.content_name is not None and old_name != content_data.content_name:
        updated_permissions = await update_content_permission(db, id, content_data.content_name)
    
    content_schema = ContentTypeSchema.model_validate(item)
    permission_schema = [ContentPermissionSchema.model_validate(perm) for perm in updated_permissions]
    return content_schema, permission_schema

async def get_permissions_by_content_id(db: AsyncSession, content_id: int) -> list[ContentPermissionSchema]:
    result = await db.execute(select(ContentPermissionModel).where(ContentPermissionModel.content_type_id == content_id))
    return result.scalars().all()

async def create_content_permission(db: AsyncSession, permission_data: ContentPermissionCreateSchema) -> ContentPermissionSchema:
    new_permission = ContentPermissionModel(
        name= permission_data.name,
        content_type_id= permission_data.content_type_id,
        action= permission_data.action
    )
    db.add(new_permission)
    await db.commit()
    await db.refresh(new_permission)
    return new_permission

async def update_content_permission(db: AsyncSession, content_id: int, content_name: str):
    permissions = await get_permissions_by_content_id(db, content_id)
    
    for permission in permissions:
        action = permission.name.split(" ")[0]
        permission.name = f"{action} {content_name}"
    
    await db.commit()
    return permissions

async def get_contents_with_permissions(db: AsyncSession) -> list[FullContentSchemas]:
    result = await db.execute(select(ContentTypeModel).options(selectinload(ContentTypeModel.permissions)))
    items = result.scalars().all()
    
    if not items:
        raise NoResultFound("Content not found")
    
    content_permissions = [
        FullContentSchemas(
            content_name=item.content_name,
            icon=item.icon,
            permissions=[
                {"name": permission.name, "action": permission.action}
                for permission in item.permissions
            ]
        )
        for item in items
    ]
    
    return content_permissions

async def get_content_with_permissions_by_id(db: AsyncSession, id: int) -> FullContentSchemas:
    result = await db.execute(
        select(ContentTypeModel)
        .options(selectinload(ContentTypeModel.permissions))
        .where(ContentTypeModel.id == id)
    )
    item = result.scalars().first()
    
    if not item:
        raise NoResultFound("Content not found")
    
    content_permission = FullContentSchemas(
        content_name=item.content_name,
        icon=item.icon,
        permissions=[
            {"name": permission.name, "action": permission.action}
            for permission in item.permissions
        ]
    )
    
    return content_permission