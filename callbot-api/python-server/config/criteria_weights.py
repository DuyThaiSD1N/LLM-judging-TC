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
        description="Cân bằng: nội dung đúng đủ, giọng điệu tự nhiên, thời gian hợp lý"
    ),
    
    # Strict - Yêu cầu cao về tất cả khía cạnh
    "strict": CriteriaConfig(
        description="Nghiêm ngặt: yêu cầu cao về nội dung, giọng điệu, và thời gian"
    ),
    
    # Speed-Focused - Đánh giá theo tốc độ phản hồi
    "speed-focused": CriteriaConfig(
        description="Tốc độ: ưu tiên thời gian phản hồi nhanh, nội dung đủ tốt"
    ),
    
    # Content-Only - Chỉ tập trung vào nội dung
    "content-only": CriteriaConfig(
        description="Chỉ nội dung: đánh giá độ chính xác thông tin, bỏ qua giọng điệu"
    ),
    
    # UX-Focused - Ưu tiên trải nghiệm người dùng
    "ux-focused": CriteriaConfig(
        description="Trải nghiệm: ưu tiên giọng điệu thân thiện, tự nhiên"
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
        "description": CRITERIA_CONFIG["standard"].description
    },
    {
        "id": "strict",
        "name": "Tiêu chí Nghiêm ngặt",
        "description": CRITERIA_CONFIG["strict"].description
    },
    {
        "id": "speed-focused",
        "name": "Tiêu chí Tốc độ",
        "description": CRITERIA_CONFIG["speed-focused"].description
    },
    {
        "id": "content-only",
        "name": "Tiêu chí Nội dung",
        "description": CRITERIA_CONFIG["content-only"].description
    },
    {
        "id": "ux-focused",
        "name": "Tiêu chí Trải nghiệm",
        "description": CRITERIA_CONFIG["ux-focused"].description
    }
]
