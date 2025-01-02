from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.future import select
from sqlalchemy import null, or_
from datetime import datetime, timedelta
from app.models.user import UserModel, UserPermissionModel
from app.schemas.pagination import PaginationParams
from app.schemas.user import UserSchema, CreateUserSchema, UserQueryParams, PaginateUserResponse, UserPermissionSchema, CreateUserPermissionSchema, UserCursorResponse
from app.services.pagination import paginate_query
from typing import Dict, Any
import bcrypt

async def get_all_users(pagination: PaginationParams, db: AsyncSession) -> PaginateUserResponse:
    query = select(UserModel)
    users, total, total_pages = await paginate_query(db, query, UserModel, pagination.page, pagination.page_size)

    return PaginateUserResponse(
        data= [UserSchema.model_validate(user) for user in users],
        total_items= total,
        total_pages= total_pages,
        page= pagination.page,
        page_size= pagination.page_size
    )

async def get_user_by_id(db: AsyncSession, id: int) -> UserSchema:
    result = await db.execute(select(UserModel).where(UserModel.id == id))
    item = result.scalars().first()
    
    if item is None:
        raise NoResultFound

    return UserSchema.model_validate(item)

async def fetch_users(query_params: UserQueryParams, db: AsyncSession) -> PaginateUserResponse:
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
        query = query.where(UserModel.last_login >= datetime.combine(query_params.last_login_start, datetime.min.time()))
    if query_params.last_login_end:
        query = query.where(UserModel.last_login < datetime.combine(query_params.last_login_end + timedelta(days=1), datetime.min.time()))

    if query_params.created_at_start:
        query = query.where(UserModel.created_at >= datetime.combine(query_params.created_at_start, datetime.min.time()))
    if query_params.created_at_end:
        query = query.where(UserModel.created_at < datetime.combine(query_params.created_at_end + timedelta(days=1), datetime.min.time()))

    # Sorting
    column_attr = getattr(UserModel, query_params.sort_by, None)
    if column_attr:
        if query_params.sort_order == "asc":
            query = query.order_by(column_attr.asc())
        elif query_params.sort_order == "desc":
            query = query.order_by(column_attr.desc())

    # Use pagination utility function
    users, total, total_pages = await paginate_query(db, query, UserModel, query_params.page, query_params.page_size)

    # Convert to schemas
    user_schemas = [UserSchema.model_validate(user) for user in users]
    
    return PaginateUserResponse(
        total_items=total,
        page=query_params.page,
        page_size=query_params.page_size,
        total_pages=total_pages,
        data=user_schemas
    )

async def create_user(db: AsyncSession, user_data: CreateUserSchema)-> Dict[str, Any]:
    async def create_user_record() -> UserModel:
        hashed_password = bcrypt.hashpw(
            user_data.password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        user = UserModel(
            username = user_data.username,
            password = hashed_password,
            is_superuser = user_data.is_superuser
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    try:
        new_user = await create_user_record()
        if user_data.permission_ids:
            permission_result = await create_permissions_by_user_id(
                db,
                CreateUserPermissionSchema(
                    user_id = new_user.id,
                    permission_ids = user_data.permission_ids
                )
            )
        
            if not permission_result["success"]:
                await db.rollback()
                return {
                    "success": False,
                    "error": f"User created but permissions failed: {permission_result['error']}"
                }
        return {
            "success": True,
            "message": "User created successfully with permissions."
        }
    except IntegrityError:
        await db.rollback()
        return {"success": False, "error": "User already exists."}
    except Exception as e:
        await db.rollback()
        return {"success": False, "error": f"Error creating user: {str(e)}"}

# For Login only!
async def get_user_by_username(db: AsyncSession, username: str) -> UserSchema:
    result = await db.execute(select(UserModel).where(
            UserModel.username == username,
            UserModel.deleted_at == null()
    ))
    item = result.scalars().first()
    
    if item is None:
        raise NoResultFound
    return item

async def get_permissions_by_user_id(db: AsyncSession, user_id: int) -> UserPermissionSchema:
    result = await db.execute(select(UserPermissionModel).where(
        UserPermissionModel.user_id == user_id,
        UserPermissionModel.active == True
    ))
    items = result.scalars().all()
    
    if items is None:
        raise NoResultFound
    return items

async def create_permissions_by_user_id(db: AsyncSession, permissions: CreateUserPermissionSchema) -> dict:
    try:
        for permission in permissions.permission_ids:
            new_permission = UserPermissionModel(
                user_id=permissions.user_id,
                permission_id=permission,
                active=True
            )
            db.add(new_permission)
        await db.commit()
        return {"success": True, "message": "Permissions created successfully."}
    
    except IntegrityError as e:
        db.rollback()
        return {"success": False, "error": "Permission already exists."}
    
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

async def get_users_with_cursor(db: AsyncSession, cursor: int, limit: int = 20) -> UserCursorResponse:
    query = select(UserModel).where(UserModel.id > cursor).limit(limit)
    users = await db.execute(query)
    users = users.scalars().all()
    next_cursor = users[-1].id if users else None
    
    return UserCursorResponse(
        users=[UserSchema.model_validate(user) for user in users],
        next_cursor=next_cursor
    ) 
    
async def get_users_list_from_search(db: AsyncSession, data: str, limit: int = 20) -> UserCursorResponse:
    query = (
        select(UserModel)
        .where(
            or_(UserModel.username.ilike(f"{data}%"),
                UserModel.id.ilike(f"{data}%")
            )
        ).limit(limit)
    )
    users = await db.execute(query)
    users = users.scalars().all()
    
    return UserCursorResponse(
        users=[UserSchema.model_validate(user) for user in users],
        next_cursor=None
    )