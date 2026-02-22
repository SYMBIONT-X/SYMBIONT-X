"""Pagination utilities for SYMBIONT-X."""

from typing import TypeVar, Generic, List, Any, Optional
from dataclasses import dataclass
from math import ceil

from pydantic import BaseModel


T = TypeVar("T")


@dataclass
class PaginatedResponse(Generic[T]):
    """Paginated response container."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    def to_dict(self) -> dict:
        return {
            "items": self.items,
            "pagination": {
                "total": self.total,
                "page": self.page,
                "page_size": self.page_size,
                "total_pages": self.total_pages,
                "has_next": self.has_next,
                "has_prev": self.has_prev,
            }
        }


class Paginator:
    """Paginator for list data."""
    
    def __init__(
        self,
        default_page_size: int = 20,
        max_page_size: int = 100,
    ):
        self.default_page_size = default_page_size
        self.max_page_size = max_page_size
    
    def paginate(
        self,
        items: List[T],
        page: int = 1,
        page_size: Optional[int] = None,
    ) -> PaginatedResponse[T]:
        """Paginate a list of items."""
        
        # Validate inputs
        page = max(1, page)
        page_size = min(
            self.max_page_size,
            max(1, page_size or self.default_page_size)
        )
        
        total = len(items)
        total_pages = ceil(total / page_size) if total > 0 else 1
        
        # Ensure page is within bounds
        page = min(page, total_pages)
        
        # Calculate slice
        start = (page - 1) * page_size
        end = start + page_size
        
        return PaginatedResponse(
            items=items[start:end],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )
    
    def paginate_query(
        self,
        query_func,
        page: int = 1,
        page_size: Optional[int] = None,
        count_func=None,
    ) -> PaginatedResponse:
        """Paginate a database query with offset/limit."""
        
        page = max(1, page)
        page_size = min(
            self.max_page_size,
            max(1, page_size or self.default_page_size)
        )
        
        offset = (page - 1) * page_size
        
        # Get items with limit/offset
        items = query_func(limit=page_size, offset=offset)
        
        # Get total count
        total = count_func() if count_func else len(items)
        total_pages = ceil(total / page_size) if total > 0 else 1
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )


# Global paginator
paginator = Paginator()


def paginate(
    items: List[Any],
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse:
    """Helper function to paginate items."""
    return paginator.paginate(items, page, page_size)


class PaginationParams(BaseModel):
    """Pagination query parameters."""
    page: int = 1
    page_size: int = 20
    
    class Config:
        extra = "forbid"
