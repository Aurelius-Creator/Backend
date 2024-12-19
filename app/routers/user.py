from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from app.db.main import get_db
from app.schemas.pagination import PaginationParams
from app.schemas.user import UserSchema, CreateUserSchema, UserQueryParams, PaginateUserResponse, UserPermissionSchema, CreateUserPermissionSchema
from app.services import user

router = APIRouter()

@router.get("/users/all", response_model=PaginateUserResponse, status_code=status.HTTP_200_OK)
async def get_all_users(pagination: PaginationParams = Depends(), db: AsyncSession = Depends(get_db)):
    return await user.get_all_users(pagination, db)

@router.get("/user/{id}", response_model=UserSchema, status_code=status.HTTP_200_OK)
async def get_user_by_id(id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await user.get_user_by_id(db, id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Content not found")
    
@router.get("/users", tags=["Users"], response_model=PaginateUserResponse, status_code=status.HTTP_200_OK)
async def get_users(query_params: UserQueryParams = Depends(), db: AsyncSession = Depends(get_db)):
    return await user.fetch_users(query_params, db)

@router.post("/user", status_code=status.HTTP_201_CREATED)
async def create_user(user_data: CreateUserSchema, db: AsyncSession = Depends(get_db)):
    try:
        result = await user.create_user(db, user_data)
        if result["success"]:
            return {"msg": result["message"]}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/user/{id}/permissions", response_model=list[UserPermissionSchema], status_code=status.HTTP_200_OK)
async def get_user_permissions(id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await user.get_permissions_by_user_id(db, id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Content not found")

@router.post("/user/permissions", status_code=status.HTTP_201_CREATED)
async def create_permissions_by_user_id(permissions: CreateUserPermissionSchema, db: AsyncSession = Depends(get_db)):
    try:
        result = await user.create_permissions_by_user_id(db, permissions)
        if result["success"]:
            return {"msg": result["message"]}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))