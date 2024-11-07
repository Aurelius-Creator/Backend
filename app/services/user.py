from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.future import select
from app.models.user import UserModel
from app.schemas.user import UserSchema, UserCreateSchema
import bcrypt

async def get_users(db: AsyncSession) -> list[UserSchema]:
    result = await db.execute(select(UserModel))
    return result.scalars().all()

async def get_user_by_id(db: AsyncSession, id: int) -> UserSchema:
    result = await db.execute(select(UserModel).where(UserModel.id == id))
    item = result.scalars().first()
    
    if item is None:
        raise NoResultFound
    return item

async def create_user(db: AsyncSession, user_data: UserCreateSchema):
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
    
async def get_user_by_username(db: AsyncSession, username: str) -> UserSchema:
    result = await db.execute(select(UserModel).where(UserModel.username == username))
    item = result.scalars().first()
    
    if item is None:
        raise NoResultFound
    return item  