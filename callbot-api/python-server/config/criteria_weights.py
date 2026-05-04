"""
Configuration cho trọng số và ngưỡng của từng tiêu chí đánh giá.
Phase 3: Criteria-Specific Weights and Thresholds
"""

from typing import Dict, Optional
from pydantic import BaseModel


class CriteriaWeights(BaseModel):
    """Trọng số cho từng thành phần điểm"""
    content: float
    tone: float
    time: float


class MinScores(BaseModel):
    """Điểm tối thiểu cho từng thành phần (optional)"""
    content: Optional[float] = None
    tone: Optional[float] = None


class CriteriaConfig(BaseModel):
    """Cấu hình cho một tiêu chí đánh giá"""
    weights: CriteriaWeights
    threshold: float
    description: str
    min_scores: Optional[MinScores] = None


# Req 11-15: Cấu hình cho từng tiêu chí
CRITERIA_CONFIG: Dict[str, CriteriaConfig] = {
    # Req 11: Standard - Cân bằng giữa nội dung và trải nghiệm
    "standard": CriteriaConfig(
        weights=CriteriaWeights(content=0.5, tone=0.3, time=0.2),
        threshold=70,
        description="Cân bằng: nội dung đúng đủ, giọng điệu tự nhiên, thời gian hợp lý"
    ),
    
    # Req 12: Strict - Yêu cầu cao về tất cả khía cạnh
    "strict": CriteriaConfig(
        weights=CriteriaWeights(content=0.4, tone=0.4, time=0.2),
        threshold=85,
        description="Nghiêm ngặt: yêu cầu cao về nội dung, giọng điệu, và thời gian",
        min_scores=MinScores(content=90, tone=90)
    ),
    
    # Req 13: Flexible - Khoan dung hơn, chấp nhận đủ tốt
    "flexible": CriteriaConfig(
        weights=CriteriaWeights(content=0.6, tone=0.2, time=0.2),
        threshold=60,
        description="Linh hoạt: ưu tiên nội dung, khoan dung về giọng điệu",
        min_scores=MinScores(content=70)
    ),
    
    # Req 14: Content-Only - Chỉ tập trung vào nội dung
    "content-only": CriteriaConfig(
        weights=CriteriaWeights(content=0.8, tone=0.0, time=0.2),
        threshold=70,
        description="Chỉ nội dung: đánh giá độ chính xác thông tin, bỏ qua giọng điệu"
    ),
    
    # Req 15: UX-Focused - Ưu tiên trải nghiệm người dùng
    "ux-focused": CriteriaConfig(
        weights=CriteriaWeights(content=0.3, tone=0.5, time=0.2),
        threshold=70,
        description="Trải nghiệm: ưu tiên giọng điệu thân thiện, tự nhiên",
        min_scores=MinScores(tone=80)
    )
}


def get_criteria_config(criteria: str) -> CriteriaConfig:
    """
    Lấy config cho một tiêu chí
    
    Args:
        criteria: Tên tiêu chí (standard, strict, flexible, content-only, ux-focused)
        
    Returns:
        CriteriaConfig object với weights, threshold, description
    """
    config = CRITERIA_CONFIG.get(criteria)
    if not config:
        print(f"⚠️ Unknown criteria: {criteria}, using standard config")
        return CRITERIA_CONFIG["standard"]
    return config


def calculate_total_score(
    criteria: str,
    content_score: float,
    tone_score: float,
    time_score: float
) -> float:
    """
    Tính total_score dựa trên trọng số của tiêu chí
    
    Args:
        criteria: Tên tiêu chí
        content_score: Điểm nội dung (0-100)
        tone_score: Điểm giọng điệu (0-100)
        time_score: Điểm thời gian (0-100)
        
    Returns:
        Total score (0-100)
    """
    config = get_criteria_config(criteria)
    weights = config.weights
    
    total_score = (
        content_score * weights.content +
        tone_score * weights.tone +
        time_score * weights.time
    )
    
    return round(total_score, 1)


def determine_verdict(criteria: str, total_score: float) -> str:
    """
    Xác định verdict dựa trên total_score và threshold
    
    Args:
        criteria: Tên tiêu chí
        total_score: Tổng điểm (0-100)
        
    Returns:
        'PASSED' hoặc 'FAILED'
    """
    config = get_criteria_config(criteria)
    return "PASSED" if total_score >= config.threshold else "FAILED"


def validate_config():
    """Validate config: tổng trọng số phải = 1.0"""
    for criteria, config in CRITERIA_CONFIG.items():
        weights = config.weights
        total = weights.content + weights.tone + weights.time
        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f"❌ Invalid weights for {criteria}: sum = {total}, expected 1.0"
            )
    print("✅ Criteria weights config validated")


# Validate khi load module
validate_config()


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
        "id": "flexible",
        "name": "Tiêu chí Linh hoạt",
        "description": CRITERIA_CONFIG["flexible"].description
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
