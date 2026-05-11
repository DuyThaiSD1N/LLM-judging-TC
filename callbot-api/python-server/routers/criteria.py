"""
criteria.py — Router để lấy danh sách tiêu chí đánh giá
"""

from fastapi import APIRouter, Header
from typing import Optional

# Import criteria config
from config.criteria_weights import CRITERIA_LIST

router = APIRouter()


@router.get("/criteria")
async def get_criteria(x_api_key: Optional[str] = Header(None)):
    """
    Lấy danh sách tiêu chí đánh giá
    
    Returns:
        {
            "criteria": [
                {
                    "id": "standard",
                    "name": "Tiêu chí Chuẩn",
                    "description": "Cân bằng: ≥90% thông tin, giọng điệu lịch sự, thời gian ≤3s"
                },
                ...
            ]
        }
    """
    return {
        "criteria": CRITERIA_LIST
    }
