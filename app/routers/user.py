from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from app.db.main import get_db
from app.schemas.user import UserSchema, UserCreateSchema
from app.services import user

router = APIRouter()

@router.get("/users", response_model=list[UserSchema], status_code=status.HTTP_200_OK)
async def get_users(db: AsyncSession = Depends(get_db)):
    return await user.get_users(db)

@router.get("/user/{id}", response_model=UserSchema, status_code=status.HTTP_200_OK)
async def get_user_by_id(id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await user.get_user_by_id(db, id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Content not found")

@router.post("/user", status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreateSchema, db: AsyncSession = Depends(get_db)):
    try:
        result = await user.create_user(db, user_data)
        if result["success"]:
            return {"msg": result["message"]}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
