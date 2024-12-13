from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.future import select
from sqlalchemy import null
from datetime import datetime, timedelta
from app.models.user import UserModel
from app.schemas.pagination import PaginationParams
from app.schemas.user import UserSchema, CreateUserSchema, UserQueryParams, PaginateUserResponse
from app.services.pagination import paginate_query
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

async def create_user(db: AsyncSession, user_data: CreateUserSchema):
    try:
        hashed_pass = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_user = UserModel(
            username=user_data.username, 
            password=hashed_pass,
            is_superuser=user_data.is_superuser
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return {"success": True, "message": "User created successfully."}
    
    except IntegrityError as e:
        db.rollback()
        return {"success": False, "error": "Username already exists."}
    
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

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