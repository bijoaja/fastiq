import math
from app.core.responses import PaginationInfo

def build_pagination_info(page: int, per_page: int, total: int) -> PaginationInfo:
    """
    Build PaginationInfo schema from page, per_page, and total count.
    """
    total_pages = math.ceil(total / per_page) if per_page > 0 else 0
    return PaginationInfo(
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages
    )
