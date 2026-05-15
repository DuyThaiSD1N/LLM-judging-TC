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
    # 1. Goal Achievement
    "goal_achievement": CriteriaConfig(
        description="Goal Achievement: Đạt mục tiêu testcase"
    ),
    
    # 2. Semantic Correctness
    "semantic_correctness": CriteriaConfig(
        description="Semantic Correctness: Đúng nghĩa & đúng intent"
    ),
    
    # 3. Conversation Quality
    "conversation_quality": CriteriaConfig(
        description="Conversation Quality: Tự nhiên & hữu ích"
    ),
    
    # 4. Context Consistency
    "context_consistency": CriteriaConfig(
        description="Context Consistency: Logic xuyên suốt"
    ),
    
    # 5. Safety & Compliance
    "safety_compliance": CriteriaConfig(
        description="Safety & Compliance: Không vi phạm"
    )
}


def get_criteria_config(criteria: str) -> CriteriaConfig:
    """
    Lấy config cho một tiêu chí
    
    Args:
        criteria: Tên tiêu chí (goal_achievement, semantic_correctness, conversation_quality, context_consistency, safety_compliance)
        
    Returns:
        CriteriaConfig object với description
    """
    config = CRITERIA_CONFIG.get(criteria)
    if not config:
        print(f"⚠️ Unknown criteria: {criteria}, using goal_achievement config")
        return CRITERIA_CONFIG["goal_achievement"]
    return config


# Export danh sách tiêu chí cho frontend
CRITERIA_LIST = [
    {
        "id": "goal_achievement",
        "name": "Đạt mục tiêu",
        "description": "Đạt mục tiêu testcase"
    },
    {
        "id": "semantic_correctness",
        "name": "Đúng nghĩa & intent",
        "description": "Đúng nghĩa & đúng intent"
    },
    {
        "id": "conversation_quality",
        "name": "Chất lượng hội thoại",
        "description": "Tự nhiên & hữu ích"
    },
    {
        "id": "context_consistency",
        "name": "Tính nhất quán",
        "description": "Logic xuyên suốt"
    },
    {
        "id": "safety_compliance",
        "name": "An toàn & Tuân thủ",
        "description": "Không vi phạm"
    }
]
