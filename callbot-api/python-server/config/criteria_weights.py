"""
Configuration cho các tiêu chí đánh giá - LLM tự đánh giá không dùng scoring
"""

from typing import Dict
from pydantic import BaseModel


class CriteriaConfig(BaseModel):
    """Cấu hình cho một tiêu chí đánh giá"""
    description: str


# Cấu hình cho từng tiêu chí - LLM tự đánh giá
CRITERIA_CONFIG: Dict[str, CriteriaConfig] = {
    # Standard - Cân bằng giữa nội dung và trải nghiệm
    "standard": CriteriaConfig(
        description="Cân bằng: ≥90% thông tin, giọng điệu lịch sự, thời gian ≤3s"
    ),
    
    # Strict - Yêu cầu cao về tất cả khía cạnh
    "strict": CriteriaConfig(
        description="Nghiêm ngặt: ≥95% thông tin, giọng điệu tự nhiên, thời gian ≤2s"
    ),
    
    # Speed-Focused - Đánh giá theo tốc độ phản hồi
    "speed-focused": CriteriaConfig(
        description="Tốc độ: thời gian ≤2s (bắt buộc), ≥80% thông tin"
    ),
    
    # Content-Only - Chỉ tập trung vào nội dung
    "content-only": CriteriaConfig(
        description="Nội dung: ≥95% thông tin chính xác, bỏ qua thời gian & giọng điệu"
    ),
    
    # UX-Focused - Ưu tiên trải nghiệm người dùng
    "ux-focused": CriteriaConfig(
        description="Trải nghiệm: giọng điệu thân thiện + xưng hô (bắt buộc), ≥85% thông tin"
    )
}


def get_criteria_config(criteria: str) -> CriteriaConfig:
    """
    Lấy config cho một tiêu chí
    
    Args:
        criteria: Tên tiêu chí (standard, strict, speed-focused, content-only, ux-focused)
        
    Returns:
        CriteriaConfig object với description
    """
    config = CRITERIA_CONFIG.get(criteria)
    if not config:
        print(f"⚠️ Unknown criteria: {criteria}, using standard config")
        return CRITERIA_CONFIG["standard"]
    return config


# Export danh sách tiêu chí cho frontend
CRITERIA_LIST = [
    {
        "id": "standard",
        "name": "Tiêu chí Chuẩn",
        "description": "Cân bằng: ≥90% thông tin, giọng điệu lịch sự, thời gian ≤3s"
    },
    {
        "id": "strict",
        "name": "Tiêu chí Nghiêm ngặt",
        "description": "Nghiêm ngặt: ≥95% thông tin, giọng điệu tự nhiên, thời gian ≤2s"
    },
    {
        "id": "speed-focused",
        "name": "Tiêu chí Tốc độ",
        "description": "Tốc độ: thời gian ≤2s (bắt buộc), ≥80% thông tin"
    },
    {
        "id": "content-only",
        "name": "Tiêu chí Nội dung",
        "description": "Nội dung: ≥95% thông tin chính xác, bỏ qua thời gian & giọng điệu"
    },
    {
        "id": "ux-focused",
        "name": "Tiêu chí Trải nghiệm",
        "description": "Trải nghiệm: giọng điệu thân thiện + xưng hô (bắt buộc), ≥85% thông tin"
    }
]
