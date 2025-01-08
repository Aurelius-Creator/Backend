from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.main import get_db
from app.schemas import user as userSchemas
from app.schemas.pagination import PaginationParams
from app.services.user import UserService
from app.services.validation import (
    check_superuser,
    validate_access_and_csrf,
    validate_permission,
)

router = APIRouter(prefix="/users", tags=["Users"])


async def handle_service_result(result: dict[str, Any]) -> dict[str, str]:
    """Handle common service result pattern."""
    if result["success"]:
        return {"msg": result["message"]}
    raise HTTPException(status_code=400, detail=result["error"])


async def handle_service_execution(operation: callable, *args) -> Any:
    """Generic exception handler for service operations."""
    try:
        return await operation(*args)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Content not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/all", response_model=userSchemas.PaginateUserResponse)
async def get_all_users(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    validation: Dict = Depends(validate_permission),
) -> userSchemas.PaginateUserResponse:
    """Get all users with pagination."""
    return await UserService.get_all_users(pagination, db)


@router.get("/{id}", response_model=userSchemas.UserSchema)
async def get_user_by_id(
    id: int,
    db: AsyncSession = Depends(get_db),
    validation: Dict = Depends(validate_permission),
) -> userSchemas.UserSchema:
    """Get a single user by ID."""
    return await handle_service_execution(UserService.get_user_by_id, db, id)


@router.get("/", response_model=userSchemas.PaginateUserResponse)
async def get_users(
    query_params: userSchemas.UserQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    validation: Dict = Depends(validate_permission),
) -> userSchemas.PaginateUserResponse:
    """Get users based on query parameters."""
    return await UserService.fetch_users(query_params, db)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: userSchemas.CreateUserSchema,
    db: AsyncSession = Depends(get_db),
    token_payload: Dict = Depends(validate_access_and_csrf),
) -> dict[str, str]:
    """Create a new user."""
    check_superuser(token_payload)
    return await handle_service_execution(
        handle_service_result, await UserService.create_user(db, user_data)
    )


@router.get("/{id}/permissions", response_model=list[userSchemas.UserPermissionSchema])
async def get_user_permissions(
    id: int,
    db: AsyncSession = Depends(get_db),
    validation: Dict = Depends(validate_permission),
) -> list[userSchemas.UserPermissionSchema]:
    """Get permissions for a specific user."""
    return await handle_service_execution(
        UserService.get_permissions_by_user_id, db, id
    )


@router.post("/permissions", status_code=status.HTTP_201_CREATED)
async def create_user_permissions(
    permissions: userSchemas.CreateUserPermissionSchema,
    db: AsyncSession = Depends(get_db),
    token_payload: Dict = Depends(validate_access_and_csrf),
) -> dict[str, str]:
    """Create permissions for a user."""
    check_superuser(token_payload)
    result = await handle_service_execution(
        UserService.create_permissions_by_user_id, db, permissions
    )
    return await handle_service_result(result)


@router.put("/permissions")
async def update_user_permissions(
    data: userSchemas.UpdateUserPermissionSchema,
    db: AsyncSession = Depends(get_db),
    token_payload: Dict = Depends(validate_access_and_csrf),
) -> dict[str, str]:
    """Update user permissions."""
    check_superuser(token_payload)
    result = await handle_service_execution(
        UserService.update_permissions_by_user_id, db, data
    )
    return await handle_service_result(result)


@router.get("/cursor/list", response_model=userSchemas.UserCursorResponse)
async def get_users_cursor(
    cursor: int = Query(..., description="Cursor position for pagination"),
    limit: int = Query(..., description="Number of items to return"),
    db: AsyncSession = Depends(get_db),
    validation: Dict = Depends(validate_permission),
) -> userSchemas.UserCursorResponse:
    """Get users using cursor-based pagination."""

    return await handle_service_execution(
        UserService.get_users_with_cursor, db, cursor, limit
    )


@router.get("/search/list", response_model=userSchemas.UserCursorResponse)
async def get_users_list_from_search(
    data: str = Query(..., description="Search key for pagination"),
    limit: int = Query(..., description="Number of items to return"),
    db: AsyncSession = Depends(get_db),
    validation: Dict = Depends(validate_permission),
) -> userSchemas.UserCursorResponse:
    """Get users list based on search criteria."""
    return await UserService.get_users_list_from_search(db, data, limit)


@router.patch("/password")
async def update_user_password(
    data: userSchemas.UpdateUserPasswordSchema,
    db: AsyncSession = Depends(get_db),
    token_payload: Dict = Depends(validate_access_and_csrf),
) -> dict[str, str]:
    """Update user password."""
    result = await handle_service_execution(
        UserService.update_user_password, db, token_payload, data
    )
    return await handle_service_result(result)


@router.patch("/{id}/password/reset")
async def reset_user_password(
    id: int,
    db: AsyncSession = Depends(get_db),
    token_payload: Dict = Depends(validate_access_and_csrf),
) -> dict[str, str]:
    """Reset user password."""
    check_superuser(token_payload)
    result = await handle_service_execution(UserService.reset_user_password, db, id)
    return await handle_service_result(result)


@router.patch("/{id}/deactivate")
async def deactivate_user(
    id: int,
    db: AsyncSession = Depends(get_db),
    token_payload: Dict = Depends(validate_access_and_csrf),
) -> dict[str, str]:
    """Deactivate a user."""
    check_superuser(token_payload)
    result = await handle_service_execution(UserService.deactivate_user, db, id)
    return await handle_service_result(result)


@router.patch("/{id}/activate")
async def activate_user(
    id: int,
    db: AsyncSession = Depends(get_db),
    token_payload: Dict = Depends(validate_access_and_csrf),
) -> dict[str, str]:
    """Activate a user."""
    check_superuser(token_payload)
    result = await handle_service_execution(UserService.activate_user, db, id)
    return await handle_service_result(result)
