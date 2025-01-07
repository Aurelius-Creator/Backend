from typing import List, Tuple, Type

from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


async def paginate_query(
    db: AsyncSession,
    query: select,
    model: Type[BaseModel],
    page: int,
    page_size: int,
) -> Tuple[List[BaseModel], int, int]:

    # Apply pagination
    paginated_query = query.limit(page_size).offset((page - 1) * page_size)

    # Get the total count of items
    total_query = query.with_only_columns(func.count(model.id))
    total_result = await db.execute(total_query)
    total = total_result.scalar()

    # Execute the paginated query
    result = await db.execute(paginated_query)
    items = result.scalars().all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return items, total, total_pages
