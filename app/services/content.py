from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.content import ContentPermissionModel, ContentTypeModel
from app.models.user import UserPermissionModel
from app.schemas.content import (
    ContentPermissionCreateSchema,
    ContentPermissionSchema,
    ContentTypeCreateSchema,
    ContentTypeSchema,
    ContentTypeUpdateSchema,
    FullContentSchema,
    PermissionResponse,
)


class ContentService:
    CRUD_ACTIONS = [
        {"action": "C", "name": "Add"},
        {"action": "R", "name": "View"},
        {"action": "U", "name": "Update"},
        {"action": "D", "name": "Delete"},
    ]

    @staticmethod
    async def get_contents(db: AsyncSession) -> List[ContentTypeSchema]:
        """Get all content types."""
        result = await db.execute(select(ContentTypeModel))
        return result.scalars().all()

    @staticmethod
    async def get_contents_by_user_id(db: AsyncSession, user_id: int) -> List[Dict]:
        """Get content types accessible by a specific user."""
        query = (
            select(
                ContentPermissionModel.content_type_id,
                ContentTypeModel.content_name,
                ContentTypeModel.icon,
            )
            .join(
                UserPermissionModel,
                ContentPermissionModel.id == UserPermissionModel.permission_id,
            )
            .join(
                ContentTypeModel,
                ContentTypeModel.id == ContentPermissionModel.content_type_id,
            )
            .where(UserPermissionModel.user_id == user_id)
            .group_by(ContentPermissionModel.content_type_id)
        )
        result = await db.execute(query)

        return [
            {
                "id": row.content_type_id,
                "content_name": row.content_name,
                "icon": row.icon,
            }
            for row in result
        ]

    @staticmethod
    async def get_content_by_id(db: AsyncSession, id: int) -> ContentTypeSchema:
        """Get a specific content type by ID."""
        result = await db.execute(
            select(ContentTypeModel).where(ContentTypeModel.id == id)
        )
        item = result.scalars().first()

        if item is None:
            raise NoResultFound("Content type not found")
        return item

    @classmethod
    async def create_content(
        cls, db: AsyncSession, content_data: ContentTypeCreateSchema
    ) -> Tuple[ContentTypeSchema, List[ContentPermissionSchema]]:
        """Create a new content type with default CRUD permissions."""
        # Create content type
        new_content = ContentTypeModel(
            content_name=content_data.content_name, icon=content_data.icon
        )
        db.add(new_content)
        await db.commit()
        await db.refresh(new_content)

        # Create default permissions
        new_permissions = []
        for action_item in cls.CRUD_ACTIONS:
            permission_data = ContentPermissionCreateSchema(
                name=f"{action_item['name']} {new_content.content_name}",
                content_type_id=new_content.id,
                action=action_item["action"],
            )
            new_permission = await cls.create_content_permission(db, permission_data)
            new_permissions.append(new_permission)

        return (
            ContentTypeSchema.model_validate(new_content),
            [ContentPermissionSchema.model_validate(perm) for perm in new_permissions],
        )

    @classmethod
    async def update_content(
        cls, db: AsyncSession, id: int, content_data: ContentTypeUpdateSchema
    ) -> Tuple[ContentTypeSchema, List[ContentPermissionSchema]]:
        """Update a content type and its associated permissions."""
        item = await cls.get_content_by_id(db, id)
        old_name = item.content_name

        # Update content fields
        if content_data.content_name is not None:
            item.content_name = content_data.content_name
        if content_data.icon is not None:
            item.icon = content_data.icon

        await db.commit()
        await db.refresh(item)

        # Update permission names if content name changed
        updated_permissions = []
        if (
            content_data.content_name is not None
            and old_name != content_data.content_name
        ):
            updated_permissions = await cls.update_content_permission(
                db, id, content_data.content_name
            )

        return (
            ContentTypeSchema.model_validate(item),
            [
                ContentPermissionSchema.model_validate(perm)
                for perm in updated_permissions
            ],
        )

    @staticmethod
    async def get_permissions_by_content_id(
        db: AsyncSession, content_id: int
    ) -> List[ContentPermissionSchema]:
        """Get all permissions for a specific content type."""
        result = await db.execute(
            select(ContentPermissionModel).where(
                ContentPermissionModel.content_type_id == content_id
            )
        )
        return result.scalars().all()

    @staticmethod
    async def create_content_permission(
        db: AsyncSession, permission_data: ContentPermissionCreateSchema
    ) -> ContentPermissionSchema:
        """Create a new content permission."""
        new_permission = ContentPermissionModel(
            name=permission_data.name,
            content_type_id=permission_data.content_type_id,
            action=permission_data.action,
        )
        db.add(new_permission)
        await db.commit()
        await db.refresh(new_permission)
        return new_permission

    @classmethod
    async def update_content_permission(
        cls, db: AsyncSession, content_id: int, content_name: str
    ) -> List[ContentPermissionSchema]:
        """Update permission names when content name changes."""
        permissions = await cls.get_permissions_by_content_id(db, content_id)

        for permission in permissions:
            action = permission.name.split(" ")[0]
            permission.name = f"{action} {content_name}"

        await db.commit()
        return permissions

    @staticmethod
    async def get_contents_with_permissions(
        db: AsyncSession,
    ) -> List[FullContentSchema]:
        """Get all content types with their associated permissions."""
        result = await db.execute(
            select(ContentTypeModel).options(selectinload(ContentTypeModel.permissions))
        )
        items = result.scalars().all()

        if not items:
            raise NoResultFound("Content not found")

        return [
            FullContentSchema(
                id=item.id,
                content_name=item.content_name,
                icon=item.icon,
                permissions=[
                    {
                        "id": permission.id,
                        "name": permission.name,
                        "action": permission.action,
                    }
                    for permission in item.permissions
                ],
            )
            for item in items
        ]

    @staticmethod
    async def get_user_content_permission(
        db: AsyncSession, id: int, token_payload: dict
    ) -> FullContentSchema:
        """Get content permissions for a specific user."""
        if token_payload.get("super"):
            query = select(ContentTypeModel).options(
                selectinload(ContentTypeModel.permissions)
            )
        else:
            query = select(ContentTypeModel).options(
                selectinload(
                    ContentTypeModel.permissions.and_(
                        ContentPermissionModel.id == UserPermissionModel.permission_id,
                        UserPermissionModel.user_id == token_payload.get("user_id"),
                        UserPermissionModel.active == True,
                    )
                )
            )

        query = query.where(ContentTypeModel.id == id)
        result = await db.execute(query)
        item = result.scalars().first()

        if not item:
            raise NoResultFound("Content not found")

        return FullContentSchema(
            id=item.id,
            content_name=item.content_name,
            icon=item.icon,
            permissions=[
                {
                    "id": permission.id,
                    "name": permission.name,
                    "action": permission.action,
                }
                for permission in item.permissions
            ],
        )

    @staticmethod
    async def get_all_permissions(db: AsyncSession) -> List[ContentPermissionSchema]:
        """Get all content permissions."""
        result = await db.execute(select(ContentPermissionModel))
        return result.scalars().all()

    @staticmethod
    async def check_user_permission(
        user_id: int, content_type: int, action: str, db: AsyncSession
    ) -> PermissionResponse:
        """Check user-content permission."""
        query_content = select(ContentPermissionModel.id).where(
            and_(
                ContentPermissionModel.content_type_id == content_type,
                ContentPermissionModel.action == action,
            )
        )
        result = await db.execute(query_content)
        permission_id = result.scalars().first()

        if not permission_id:
            raise NoResultFound("Permission not found")

        query = select(UserPermissionModel).where(
            and_(
                UserPermissionModel.user_id == user_id,
                UserPermissionModel.permission_id == permission_id,
                UserPermissionModel.active == 1,
            )
        )
        result = await db.execute(query)
        item = result.scalars().first()

        if not item:
            raise NoResultFound("This request required permission.")

        return PermissionResponse(
            authorized=True,
            permission_id=permission_id,
            user_id=user_id,
            content_type_id=content_type,
            action=action,
        )
