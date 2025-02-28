from datetime import datetime, timedelta
from typing import Any, Dict

import bcrypt
from sqlalchemy import and_, insert, null, or_, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import UserModel, UserPermissionModel
from app.schemas.pagination import PaginationParams
from app.schemas.user import (
    CreateUserPermissionSchema,
    CreateUserSchema,
    PaginateUserResponse,
    UpdateUserPasswordSchema,
    UpdateUserPermissionSchema,
    UserCursorResponse,
    UserPermissionSchema,
    UserQueryParams,
    UserSchema,
)
from app.services.pagination import paginate_query


class UserService:
    @staticmethod
    async def _hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # For Login only!
    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> UserSchema:
        result = await db.execute(
            select(UserModel).where(
                UserModel.username == username, UserModel.deleted_at == null()
            )
        )
        item = result.scalars().first()

        if item is None:
            raise NoResultFound
        return item

    @staticmethod
    async def get_all_users(
        pagination: PaginationParams, db: AsyncSession
    ) -> PaginateUserResponse:
        """Get all users with pagination."""
        query = select(UserModel)
        users, total, total_pages = await paginate_query(
            db, query, UserModel, pagination.page, pagination.page_size
        )

        return PaginateUserResponse(
            data=[UserSchema.model_validate(user) for user in users],
            total_items=total,
            total_pages=total_pages,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    @staticmethod
    async def get_user_by_id(db: AsyncSession, id: int) -> UserSchema:
        """Get a single user by ID."""
        result = await db.execute(select(UserModel).where(UserModel.id == id))
        user = result.scalars().first()

        if user is None:
            raise NoResultFound
        return UserSchema.model_validate(user)

    @staticmethod
    async def fetch_users(
        query_params: UserQueryParams, db: AsyncSession
    ) -> PaginateUserResponse:
        """Fetch users based on query parameters."""
        query = select(UserModel)

        # Apply filters
        if query_params.active == "y":
            query = query.where(UserModel.deleted_at.is_(None))
        elif query_params.active == "n":
            query = query.where(UserModel.deleted_at.is_not(None))

        if query_params.superuser == "y":
            query = query.where(UserModel.is_superuser.is_(True))
        elif query_params.superuser == "n":
            query = query.where(UserModel.is_superuser.is_(False))

        if query_params.id:
            query = query.where(UserModel.id.startswith(query_params.id))

        if query_params.username:
            query = query.where(UserModel.username.startswith(query_params.username))

        if query_params.last_login_start:
            query = query.where(
                UserModel.last_login
                >= datetime.combine(query_params.last_login_start, datetime.min.time())
            )
        if query_params.last_login_end:
            query = query.where(
                UserModel.last_login
                < datetime.combine(
                    query_params.last_login_end + timedelta(days=1), datetime.min.time()
                )
            )

        if query_params.created_at_start:
            query = query.where(
                UserModel.created_at
                >= datetime.combine(query_params.created_at_start, datetime.min.time())
            )
        if query_params.created_at_end:
            query = query.where(
                UserModel.created_at
                < datetime.combine(
                    query_params.created_at_end + timedelta(days=1), datetime.min.time()
                )
            )

        # Sorting
        column_attr = getattr(UserModel, query_params.sort_by, None)
        if column_attr:
            if query_params.sort_order == "asc":
                query = query.order_by(column_attr.asc())
            elif query_params.sort_order == "desc":
                query = query.order_by(column_attr.desc())

        # Use pagination utility function
        users, total, total_pages = await paginate_query(
            db, query, UserModel, query_params.page, query_params.page_size
        )

        # Convert to schemas
        user_schemas = [UserSchema.model_validate(user) for user in users]

        return PaginateUserResponse(
            total_items=total,
            page=query_params.page,
            page_size=query_params.page_size,
            total_pages=total_pages,
            data=user_schemas,
        )

    @classmethod
    async def create_user(
        cls, db: AsyncSession, user_data: CreateUserSchema
    ) -> Dict[str, Any]:
        """Create a new user with optional permissions."""
        try:
            user = UserModel(
                username=user_data.username,
                password=await cls._hash_password(user_data.password),
                is_superuser=user_data.is_superuser,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            if user_data.permission_ids:
                permission_result = await cls.create_permissions_by_user_id(
                    db,
                    CreateUserPermissionSchema(
                        user_id=user.id, permission_ids=user_data.permission_ids
                    ),
                )
                if not permission_result["success"]:
                    return {
                        "success": False,
                        "error": f"User created but permissions failed: {permission_result['error']}",
                    }
            return {
                "success": True,
                "message": "User created successfully with permissions.",
            }
        except Exception as e:
            await db.rollback()
            return {"success": False, "error": str(e)}

    @staticmethod
    async def get_permissions_by_user_id(
        db: AsyncSession, user_id: int
    ) -> UserPermissionSchema:
        """Get active permissions for a user."""
        result = await db.execute(
            select(UserPermissionModel).where(
                and_(
                    UserPermissionModel.user_id == user_id,
                    UserPermissionModel.active == True,
                )
            )
        )
        items = result.scalars().all()

        if items is None:
            raise NoResultFound
        return items

    @staticmethod
    async def create_permissions_by_user_id(
        db: AsyncSession, permissions: CreateUserPermissionSchema
    ) -> dict:
        """Create permissions for a user."""
        try:
            for permission in permissions.permission_ids:
                new_permission = UserPermissionModel(
                    user_id=permissions.user_id, permission_id=permission, active=True
                )
                db.add(new_permission)
            await db.commit()
            return {"success": True, "message": "Permissions created successfully."}

        except Exception as e:
            await db.rollback()
            return {"success": False, "error": str(e)}

    @staticmethod
    async def update_permissions_by_user_id(
        db: AsyncSession, data: UpdateUserPermissionSchema
    ) -> Dict[str, Any]:
        """Update user permissions."""
        try:
            if data.active_ids:
                for permission_id in data.active_ids:
                    existing_row = await db.execute(
                        select(UserPermissionModel).where(
                            and_(
                                UserPermissionModel.user_id == data.user_id,
                                UserPermissionModel.permission_id == permission_id,
                            )
                        )
                    )
                    existing_row = existing_row.scalar_one_or_none()
                    if existing_row:
                        await db.execute(
                            update(UserPermissionModel)
                            .where(
                                and_(
                                    UserPermissionModel.user_id == data.user_id,
                                    UserPermissionModel.permission_id == permission_id,
                                )
                            )
                            .values(active=True)
                        )
                    else:
                        await db.execute(
                            insert(UserPermissionModel).values(
                                user_id=data.user_id,
                                permission_id=permission_id,
                                active=True,
                            )
                        )

                if data.inactive_ids:
                    await db.execute(
                        update(UserPermissionModel)
                        .where(
                            and_(
                                UserPermissionModel.user_id == data.user_id,
                                UserPermissionModel.permission_id.in_(
                                    data.inactive_ids
                                ),
                            )
                        )
                        .values(active=False)
                    )

                await db.commit()
                return {"success": True, "message": "Permissions updated successfully."}
        except Exception as e:
            await db.rollback()
            return {"success": False, "error": str(e)}

    @staticmethod
    async def get_users_with_cursor(
        db: AsyncSession, cursor: int, limit: int = 20
    ) -> UserCursorResponse:
        """Get users using cursor-based pagination."""
        query = select(UserModel).where(UserModel.id > cursor).limit(limit + 1)
        result = await db.execute(query)
        users = result.scalars().all()

        has_more = len(users) > limit
        users = users[:limit]
        next_cursor = users[-1].id if has_more else None

        return UserCursorResponse(
            users=[UserSchema.model_validate(user) for user in users],
            next_cursor=next_cursor,
        )

    @staticmethod
    async def get_users_list_from_search(
        db: AsyncSession, data: str, limit: int = 20
    ) -> UserCursorResponse:
        """Search users by username or ID."""
        query = (
            select(UserModel)
            .where(
                or_(
                    UserModel.username.ilike(f"{data}%"), UserModel.id.ilike(f"{data}%")
                )
            )
            .limit(limit)
        )

        result = await db.execute(query)
        users = result.scalars().all()

        return UserCursorResponse(
            users=[UserSchema.model_validate(user) for user in users], next_cursor=None
        )

    @classmethod
    async def update_user_password(
        cls, db: AsyncSession, token_payload: dict, data: UpdateUserPasswordSchema
    ) -> Dict[str, Any]:
        """Update user password."""
        try:
            if (
                data.user_id != token_payload.get("user_id")
                and token_payload.get("super") == False
            ):
                return {
                    "success": False,
                    "error": "Can not change other users password.",
                }

            if data.password != data.confirm_password:
                return {"success": False, "error": "Passwords do not match."}

            hashed_password = await cls._hash_password(data.password)
            await db.execute(
                update(UserModel)
                .where(UserModel.id == data.user_id)
                .values(password=hashed_password)
                .execution_options(synchronize_session="fetch")
            )
            await db.commit()
            return {"success": True, "message": "Password updated successfully."}
        except Exception as e:
            await db.rollback()
            return {"success": False, "error": str(e)}

    @classmethod
    async def reset_user_password(
        cls, db: AsyncSession, user_id: int
    ) -> Dict[str, Any]:
        """Reset user password to default."""
        try:
            if user_id is None:
                return {"success": False, "error": "User ID is required."}

            hashed_password = await cls._hash_password("start@123")
            await db.execute(
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(password=hashed_password)
                .execution_options(synchronize_session="fetch")
            )
            await db.commit()
            return {"success": True, "message": "Password reset successfully."}
        except Exception as e:
            await db.rollback()
            return {"success": False, "error": str(e)}

    @staticmethod
    async def deactivate_user(db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """Deactivate a user."""
        try:
            await db.execute(
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(deleted_at=datetime.now())
                .execution_options(synchronize_session="fetch")
            )
            await db.commit()
            return {"success": True, "message": "User deactivated successfully."}
        except Exception as e:
            await db.rollback()
            return {"success": False, "error": str(e)}

    @staticmethod
    async def activate_user(db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """re-Activate a user."""
        try:
            await db.execute(
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(deleted_at=None)
                .execution_options(synchronize_session="fetch")
            )
            await db.commit()
            return {"success": True, "message": "User activated successfully."}
        except Exception as e:
            await db.rollback()
            return {"success": False, "error": str(e)}
