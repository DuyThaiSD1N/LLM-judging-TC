"""
Pydantic schemas cho API requests/responses và LLM structured output
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# ============================================================================
# Testcase Schemas
# ============================================================================

class Turn(BaseModel):
    """Một lượt hội thoại trong testcase"""
    question: str
    expected: str


class TestcaseBase(BaseModel):
    """Base schema cho testcase"""
    code: str
    name: str
    group: Literal["A", "B", "C", "D"]
    turns: List[Turn]
    criteria: str = "standard"


class TestcaseCreate(TestcaseBase):
    """Schema cho tạo testcase mới"""
    pass


class TestcaseResponse(TestcaseBase):
    """Schema cho response testcase"""
    id: int
    created_at: str
    
    class Config:
        from_attributes = True


# ============================================================================
# Judge Result Schemas (LLM Structured Output)
# ============================================================================

class ErrorDetail(BaseModel):
    """Chi tiết một lỗi"""
    description: str = Field(description="Mô tả lỗi cụ thể (1 câu)")
    severity: Literal["Critical", "Major", "Minor"] = Field(
        description="Mức độ nghiêm trọng"
    )
    quote: str = Field(
        default="",
        description="Trích dẫn từ câu trả lời thực tế (nếu có)"
    )


class JudgeResult(BaseModel):
    """
    Kết quả đánh giá từ LLM Judge - LLM tự đánh giá không dùng scoring
    Sử dụng cho structured output với LangChain
    """
    # Main verdict
    verdict: Literal["PASSED", "FAILED"] = Field(
        description="Kết quả đánh giá"
    )
    
    # Confidence fields
    confidence_level: float = Field(
        ge=0.0, le=1.0,
        description="Độ tự tin về kết quả (0.0-1.0)"
    )
    needs_human_review: bool = Field(
        description="Có cần human review không"
    )
    confidence_reason: str = Field(
        description="Giải thích ngắn gọn tại sao confidence ở mức này (1 câu)"
    )
    
    # Error details
    errors: List[ErrorDetail] = Field(
        default_factory=list,
        description="Danh sách lỗi (chỉ khi FAILED)"
    )
    error_desc: str = Field(
        default="",
        description="Mô tả lỗi chi tiết (nếu FAILED)"
    )
    suggestion: str = Field(
        default="",
        description="Đề xuất cải thiện (nếu FAILED)"
    )
    suggested_response: str = Field(
        default="",
        description="Mẫu câu trả lời đề xuất (nếu FAILED)"
    )
    
    # Notes
    tone_note: str = Field(
        default="",
        description="Nhận xét về giọng điệu"
    )
    time_verdict: Literal["good", "ok", "slow"] = Field(
        description="Đánh giá thời gian phản hồi"
    )
    time_note: str = Field(
        default="",
        description="Nhận xét về thời gian"
    )


# ============================================================================
# Turn Result Schemas
# ============================================================================

class TurnResult(BaseModel):
    """Kết quả chạy một lượt hội thoại"""
    question: str
    expected: str
    actual: str = ""
    action: str = ""
    response_time_ms: Optional[int] = None
    verdict: Optional[str] = None
    error_desc: str = ""
    suggestion: str = ""
    suggested_response: str = ""
    tone_note: str = ""
    time_verdict: Optional[str] = None
    time_note: str = ""
    error: str = ""
    
    # Phase 2 fields
    confidence_level: Optional[float] = None
    needs_human_review: Optional[bool] = None
    confidence_reason: str = ""
    errors: List[ErrorDetail] = Field(default_factory=list)


# ============================================================================
# Run Testcase Schemas
# ============================================================================

class RunSingleRequest(BaseModel):
    """Request cho chạy single testcase"""
    code: str
    group: Literal["A", "B", "C", "D"] = "A"
    turns: Optional[List[Turn]] = None
    question: Optional[str] = None
    expected: Optional[str] = None
    criteria: str = "standard"


class RunTestcasesRequest(BaseModel):
    """Request cho chạy multiple testcases"""
    testcases: List[TestcaseBase]


class TestcaseRunResult(TestcaseBase):
    """Kết quả chạy một testcase"""
    turns: List[TurnResult]  # type: ignore
    status: Literal["done", "error"]
    error: Optional[str] = None


class RunTestcasesResponse(BaseModel):
    """Response cho chạy testcases"""
    results: List[TestcaseRunResult]


# ============================================================================
# History Schemas
# ============================================================================

class HistoryRecord(BaseModel):
    """Một record trong lịch sử"""
    id: int
    testcase_id: int
    turn_number: int
    question: str
    expected: str
    actual: Optional[str]
    action: Optional[str]
    response_time_ms: Optional[int]
    verdict: Optional[str]
    error_desc: Optional[str]
    suggestion: Optional[str]
    suggested_response: Optional[str]
    tone_note: Optional[str]
    time_verdict: Optional[str]
    time_note: Optional[str]
    criteria: str
    error: Optional[str]
    run_at: str
    testcase_code: Optional[str] = None
    testcase_name: Optional[str] = None
    group_type: Optional[str] = None


class HistoryStats(BaseModel):
    """Thống kê lịch sử"""
    total_runs: int
    passed: int
    failed: int
    pass_rate: float
    avg_response_time: int


# ============================================================================
# Upload/Export Schemas
# ============================================================================

class UploadExcelResponse(BaseModel):
    """Response cho upload Excel"""
    testcases: List[TestcaseBase]


class ExportRequest(BaseModel):
    """Request cho export Excel"""
    testcases: List[TestcaseRunResult]
