"""
Comparison router - So sánh testcases với LLM analysis và semantic similarity
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import asyncio
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langsmith import traceable
import numpy as np
import os
import re
from diff_match_patch import diff_match_patch

router = APIRouter()

# Embedding cache (LRU with max 1000 entries)
embedding_cache: Dict[str, List[float]] = {}
cache_access_order: List[str] = []
MAX_CACHE_SIZE = 1000

# Diff engine
dmp = diff_match_patch()


def _get_llm():
    """Get LLM instance (lazy initialization)"""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def _get_embeddings_model():
    """Get embeddings model instance (lazy initialization)"""
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY"),
    )


class TestcaseCompareData(BaseModel):
    """Dữ liệu testcase để so sánh"""
    code: str
    name: str
    bot_url: Optional[str]
    question: str
    expected: str
    actual: str
    response_time_ms: Optional[int]
    # Removed verdict field - LLM tự đánh giá dựa trên expected vs actual
    error_desc: str = ""
    # Keywords để hỗ trợ LLM đánh giá (optional)
    required_keywords: Optional[str] = None  # Từ khóa BẮT BUỘC phải có trong response
    forbidden_keywords: Optional[str] = None  # Từ khóa KHÔNG ĐƯỢC có trong response


class CompareRequest(BaseModel):
    """Request body cho comparison"""
    testcases: List[TestcaseCompareData]
    comparison_mode: str  # "bot_url", "time", "free"


class SimilarityPair(BaseModel):
    """Cặp similarity score"""
    index1: int
    index2: int
    score: float


class DiffOperation(BaseModel):
    """Một operation trong diff"""
    op: str  # "equal", "insert", "delete"
    text: str


class DiffPair(BaseModel):
    """Diff giữa 2 responses"""
    index1: int
    index2: int
    code1: str
    code2: str
    diff_ops: List[DiffOperation]
    diff_html: str
    similarity_percent: float


class CompareResponse(BaseModel):
    """Response body cho comparison"""
    llm_analysis: Dict[str, Any]
    similarity_matrix: List[List[float]]
    similarity_pairs: List[SimilarityPair]
    diff_pairs: List[DiffPair]
    metrics: Dict[str, Any]
    error: Optional[str] = None


def _get_embedding_cached(text: str) -> List[float]:
    """
    Lấy embedding với cache
    Cache key = hash của text
    """
    cache_key = str(hash(text))
    
    # Check cache
    if cache_key in embedding_cache:
        # Update access order (LRU)
        if cache_key in cache_access_order:
            cache_access_order.remove(cache_key)
        cache_access_order.append(cache_key)
        return embedding_cache[cache_key]
    
    # Generate new embedding
    embeddings_model = _get_embeddings_model()
    embedding = embeddings_model.embed_query(text)
    
    # Store in cache
    embedding_cache[cache_key] = embedding
    cache_access_order.append(cache_key)
    
    # Evict oldest if cache is full
    if len(embedding_cache) > MAX_CACHE_SIZE:
        oldest_key = cache_access_order.pop(0)
        del embedding_cache[oldest_key]
    
    return embedding


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Tính cosine similarity giữa 2 vectors"""
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    
    dot_product = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))


async def _compute_similarity_matrix(testcases: List[TestcaseCompareData]) -> List[List[float]]:
    """
    Tính similarity matrix cho tất cả testcases
    Sử dụng OpenAI embeddings
    """
    n = len(testcases)
    matrix = [[0.0] * n for _ in range(n)]
    
    # Generate embeddings for all actual responses
    embeddings = []
    for tc in testcases:
        if tc.actual:
            emb = _get_embedding_cached(tc.actual)
            embeddings.append(emb)
        else:
            embeddings.append([])
    
    # Compute pairwise similarities
    for i in range(n):
        for j in range(i, n):
            if i == j:
                matrix[i][j] = 1.0
            elif embeddings[i] and embeddings[j]:
                sim = _cosine_similarity(embeddings[i], embeddings[j])
                matrix[i][j] = sim
                matrix[j][i] = sim  # Symmetric
    
    return matrix


def _compute_metrics(testcases: List[TestcaseCompareData]) -> Dict[str, Any]:
    """Tính metrics cho comparison"""
    times = [tc.response_time_ms for tc in testcases if tc.response_time_ms is not None]
    
    fastest = min(times) if times else 0
    slowest = max(times) if times else 0
    average = int(sum(times) / len(times)) if times else 0
    
    fastest_tc = next((tc for tc in testcases if tc.response_time_ms == fastest), None)
    slowest_tc = next((tc for tc in testcases if tc.response_time_ms == slowest), None)
    
    return {
        "fastest_ms": fastest,
        "fastest_code": fastest_tc.code if fastest_tc else None,
        "slowest_ms": slowest,
        "slowest_code": slowest_tc.code if slowest_tc else None,
        "average_ms": average,
        "total_count": len(testcases),
    }


def _classify_time(ms: int) -> Dict[str, str]:
    """Phân loại thời gian phản hồi"""
    if ms <= 2000:
        return {"label": "Nhanh", "level": "good"}
    elif ms <= 3000:
        return {"label": "Chấp nhận được", "level": "ok"}
    else:
        return {"label": "Chậm", "level": "slow"}


def _clean_forbidden_words(data):
    """
    ULTRA AGGRESSIVE - Loại bỏ và THAY THẾ các từ cấm khỏi response của LLM
    Đặc biệt xử lý: "Failed: X" → "X" (bỏ "Failed:" ở đầu)
    """
    
    def clean_text(text):
        if not isinstance(text, str):
            return text
        
        original = text
        
        # STEP 1: Xử lý "Failed: X" / "FAILED: X" ở đầu câu → chỉ giữ lại X
        # Pattern: "Failed: Thiếu thông tin..." → "Thiếu thông tin..."
        text = re.sub(
            r'\b(?:Failed|FAILED|Fail|FAIL):\s*',
            '',
            text,
            flags=re.IGNORECASE
        )
        
        # STEP 2: Thay thế TOÀN BỘ câu chứa "Verdict: FAILED/PASSED vì X"
        # Pattern 1: "Verdict: FAILED vì X" → "Response còn thiếu X"
        text = re.sub(
            r'Verdict:\s*(?:FAILED|Fail|failed|FAIL)\s*(?:vì|do|bởi vì)?\s*(.+?)(?:\.|$|,)',
            lambda m: f"Response còn thiếu {m.group(1).strip()}" if m.group(1) else "Response chưa đầy đủ",
            text,
            flags=re.IGNORECASE | re.MULTILINE
        )
        
        # Pattern 2: "Verdict: PASSED vì X" → "Response đã có đầy đủ X"
        text = re.sub(
            r'Verdict:\s*(?:PASSED|Pass|passed|PASS)\s*(?:vì|do|bởi vì)?\s*(.+?)(?:\.|$|,)',
            lambda m: f"Response đã có đầy đủ {m.group(1).strip()}" if m.group(1) else "Response đã đầy đủ",
            text,
            flags=re.IGNORECASE | re.MULTILINE
        )
        
        # STEP 3: Xóa BẤT KỲ "Verdict:" nào còn sót lại (kể cả không có PASSED/FAILED)
        text = re.sub(r'Verdict:\s*[^\n]*', '', text, flags=re.IGNORECASE)
        
        # STEP 4: Thay thế standalone "FAILED" / "PASSED" / "FAIL" / "PASS"
        text = re.sub(r'\b(?:FAILED|Fail|failed|FAIL)\b', 'chưa đáp ứng', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(?:PASSED|Pass|passed|PASS)\b', 'đã đáp ứng', text, flags=re.IGNORECASE)
        
        # STEP 5: XÓA HOÀN TOÀN các dòng còn chứa "verdict" (bất kỳ biến thể nào)
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Check for "verdict" in any form
            if re.search(r'verdict', line, flags=re.IGNORECASE):
                print(f"🗑️ REMOVED LINE containing 'verdict': {line[:100]}")
                # Replace with neutral statement
                cleaned_lines.append("Response cần được đánh giá thêm.")
                continue
            cleaned_lines.append(line)
        text = '\n'.join(cleaned_lines)
        
        # STEP 6: Clean up multiple empty lines
        text = re.sub(r'\n\n+', '\n\n', text)
        
        result = text.strip()
        
        # Log nếu có thay đổi
        if result != original and len(original) > 0:
            print(f"🧹 Cleaned: '{original[:80]}...' → '{result[:80]}...'")
        
        return result
    
    def clean_recursive(obj):
        if isinstance(obj, dict):
            return {k: clean_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_recursive(item) for item in obj]
        elif isinstance(obj, str):
            return clean_text(obj)
        else:
            return obj
    
    cleaned = clean_recursive(data)
    print("✅ Ultra-aggressive cleaning completed")
    return cleaned


def _compute_diff(text1: str, text2: str) -> tuple[List[DiffOperation], str, float]:
    """
    Tính diff giữa 2 texts sử dụng Myers algorithm (diff-match-patch)
    
    Returns:
        - diff_ops: List of diff operations
        - diff_html: HTML representation of diff
        - similarity_percent: Similarity percentage based on Levenshtein distance
    """
    # Compute diff using Myers algorithm
    diffs = dmp.diff_main(text1, text2)
    dmp.diff_cleanupSemantic(diffs)  # Clean up for better readability
    
    # Convert to our format
    diff_ops = []
    for op, text in diffs:
        if op == 0:  # EQUAL
            diff_ops.append(DiffOperation(op="equal", text=text))
        elif op == 1:  # INSERT
            diff_ops.append(DiffOperation(op="insert", text=text))
        elif op == -1:  # DELETE
            diff_ops.append(DiffOperation(op="delete", text=text))
    
    # Generate HTML
    diff_html = dmp.diff_prettyHtml(diffs)
    
    # Calculate similarity using Levenshtein distance
    levenshtein = dmp.diff_levenshtein(diffs)
    max_len = max(len(text1), len(text2))
    similarity_percent = 0.0 if max_len == 0 else (1 - levenshtein / max_len) * 100
    
    return diff_ops, diff_html, similarity_percent


def _compute_all_diffs(testcases: List[TestcaseCompareData]) -> List[DiffPair]:
    """
    Tính diff cho tất cả các cặp testcases
    """
    n = len(testcases)
    diff_pairs = []
    
    for i in range(n):
        for j in range(i + 1, n):
            text1 = testcases[i].actual or ""
            text2 = testcases[j].actual or ""
            
            if text1 and text2:
                diff_ops, diff_html, similarity = _compute_diff(text1, text2)
                
                diff_pairs.append(DiffPair(
                    index1=i,
                    index2=j,
                    code1=testcases[i].code,
                    code2=testcases[j].code,
                    diff_ops=diff_ops,
                    diff_html=diff_html,
                    similarity_percent=round(similarity, 2)
                ))
    
    return diff_pairs


class PerformanceItem(BaseModel):
    """Performance analysis item"""
    testcase_code: str
    time_ms: int
    evaluation: str
    reason: str

class PerformanceAnalysis(BaseModel):
    """Performance analysis"""
    fastest: PerformanceItem
    slowest: PerformanceItem
    overall_speed: str

class BestResponse(BaseModel):
    """Best response analysis"""
    testcase_code: str
    reason: str
    strengths: List[str]

class WeakestResponse(BaseModel):
    """Weakest response analysis"""
    testcase_code: str
    reason: str
    weaknesses: List[str]
    missing_info: List[str]

class ContentAnalysis(BaseModel):
    """Content analysis"""
    best_response: BestResponse
    weakest_response: WeakestResponse
    similarity_note: str = ""

class Recommendation(BaseModel):
    """Recommendation item"""
    priority: str
    target: str
    category: str
    title: str
    description: str
    specific_actions: List[str]
    expected_improvement: str

class RankingItem(BaseModel):
    """Ranking item"""
    rank: int
    testcase_code: str
    score: float
    reason: str

class ComparisonAnalysisOutput(BaseModel):
    """Structured output for comparison analysis"""
    overview: str
    performance_analysis: PerformanceAnalysis
    content_analysis: ContentAnalysis
    recommendations: List[Recommendation] = Field(default_factory=list)
    ranking: List[RankingItem] = Field(default_factory=list)
    conclusion: str = ""


@traceable(name="llm_compare_analysis", run_type="chain")
async def _analyze_with_llm(
    testcases: List[TestcaseCompareData],
    comparison_mode: str,
    similarity_matrix: List[List[float]],
    metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Phân tích comparison với LLM - Đánh giá khách quan
    Trả về insights, performance analysis, và recommendations
    
    SỬ DỤNG STRUCTURED OUTPUT để ép LLM tuân thủ format
    """
    
    # Prepare context for LLM
    tc_summaries = []
    for i, tc in enumerate(testcases):
        time_class = _classify_time(tc.response_time_ms) if tc.response_time_ms else {"label": "N/A", "level": "unknown"}
        
        # Format multi-line text with proper indentation
        question_formatted = tc.question.replace('\n', '\n     ')
        expected_formatted = tc.expected.replace('\n', '\n     ')
        actual_formatted = (tc.actual or 'N/A').replace('\n', '\n     ')
        
        # Build summary with optional keywords
        summary = (
            f"[{i+1}] {tc.code} - {tc.name}\n"
            f"  Bot URL: {tc.bot_url or 'mặc định'}\n"
            f"  Câu hỏi:\n"
            f"     {question_formatted}\n"
            f"  Kỳ vọng:\n"
            f"     {expected_formatted}\n"
        )
        
        # Add keywords if provided
        if tc.required_keywords:
            summary += f"  Từ khóa BẮT BUỘC phải có: {tc.required_keywords}\n"
        if tc.forbidden_keywords:
            summary += f"  Từ khóa KHÔNG ĐƯỢC có: {tc.forbidden_keywords}\n"
        
        summary += (
            f"  Thực tế:\n"
            f"     {actual_formatted}\n"
            f"  Thời gian: {tc.response_time_ms}ms ({time_class['label']})\n"
        )
        
        tc_summaries.append(summary)
    
    # Prepare similarity insights
    similarity_insights = []
    n = len(testcases)
    for i in range(n):
        for j in range(i + 1, n):
            sim = similarity_matrix[i][j]
            similarity_insights.append(
                f"  - {testcases[i].code} vs {testcases[j].code}: {sim:.2%}"
            )
    
    # Prepare system message - SIMPLIFIED AND DIRECT
    system_message = """Bạn là chuyên gia phân tích chatbot. Nhiệm vụ: So sánh response thực tế với kỳ vọng.

🚫 CÁC TỪ TUYỆT ĐỐI CẤM (KHÔNG BAO GIỜ DÙNG):
- "Verdict" (bất kỳ dạng nào: Verdict:, verdict, VERDICT)
- "PASSED" / "FAILED" / "Pass" / "Fail" (bất kỳ dạng nào)
- "Failed:" / "FAILED:" (đặc biệt CẤM ở đầu câu)

✅ CHỈ ĐƯỢC DÙNG:
- "Response đã có X/Y thông tin"
- "Còn thiếu: [liệt kê]"
- "Đã đáp ứng: [liệt kê]"
- "Cần bổ sung: [liệt kê]"
- "Thiếu thông tin về..."
- "Chưa đầy đủ về..."

CÁCH VIẾT ĐÚNG:
❌ SAI: "Failed: Thiếu thông tin về thời hạn"
✅ ĐÚNG: "Thiếu thông tin về thời hạn"

❌ SAI: "FAILED vì không có giấy tờ"
✅ ĐÚNG: "Chưa đề cập đến giấy tờ cần thiết"

❌ SAI: "Verdict: Response còn thiếu..."
✅ ĐÚNG: "Response còn thiếu..."

CÁCH PHÂN TÍCH:
1. Liệt kê thông tin KỲ VỌNG yêu cầu (từng điểm)
2. Kiểm tra từ khóa BẮT BUỘC (nếu có)
3. Kiểm tra từ khóa CẤM (nếu có)
4. Liệt kê thông tin THỰC TẾ đã có (từng điểm)
5. So sánh: Thông tin nào ĐÃ CÓ ✓, thông tin nào CÒN THIẾU ✗
6. Kết luận: "Response đáp ứng X/Y thông tin"

VÍ DỤ HOÀN CHỈNH:
"Response đáp ứng 3/5 thông tin (60%). Đã có: nộp hồ sơ, chấm điểm, thông báo. Còn thiếu: khảo sát thực tế, thời hạn xử lý."

Trả về JSON theo format yêu cầu. Mỗi trường phải DÀI, CHI TIẾT, CỤ THỂ (150+ từ)."""

    # Prepare user prompt - SIMPLIFIED for structured output
    prompt_text = f"""Phân tích {len(testcases)} testcase sau:

## Testcases:
{chr(10).join(tc_summaries)}

## Metrics:
- Nhanh nhất: {metrics['fastest_ms']}ms ({metrics['fastest_code']})
- Chậm nhất: {metrics['slowest_ms']}ms ({metrics['slowest_code']})
- Trung bình: {metrics['average_ms']}ms

## Semantic Similarity:
{chr(10).join(similarity_insights)}

Hãy phân tích và trả về:

1. **overview**: Tóm tắt tổng quan (TC nào tốt, TC nào cần cải thiện, với số liệu cụ thể)

2. **performance_analysis**:
   - fastest: TC nhanh nhất với đánh giá chi tiết (100+ từ)
   - slowest: TC chậm nhất với phân tích nguyên nhân (100+ từ)
   - overall_speed: Đánh giá chung về tốc độ

3. **content_analysis**:
   - best_response: TC có nội dung tốt nhất
     * So sánh KỲ VỌNG vs THỰC TẾ (TỪNG ĐIỂM CỤ THỂ)
     * Liệt kê điểm mạnh với trích dẫn
   - weakest_response: TC có nội dung yếu nhất
     * So sánh KỲ VỌNG vs THỰC TẾ (TỪNG ĐIỂM CỤ THỂ)
     * Phân tích CHI TIẾT từng lỗi:
       + Lỗi gì? (thiếu thông tin / sai thông tin / không rõ ràng)
       + Thiếu ở đâu? (đầu / giữa / cuối response)
       + Tác động gì? (user không hiểu / không làm được / hiểu sai)
       + Mức độ nghiêm trọng? (Critical / Major / Minor)
     * Liệt kê TỪNG thông tin còn thiếu với vị trí cụ thể
     * Đề xuất vị trí cần bổ sung (sau câu nào, trước đoạn nào)
   - similarity_note: Phân tích độ tương đồng

4. **recommendations**: Danh sách đề xuất cải thiện (CHI TIẾT)
   - Mỗi đề xuất có: priority, target, category, title, description, specific_actions, expected_improvement
   - **description** phải CHI TIẾT (150+ từ):
     + Hiện trạng: Response hiện tại như thế nào? Thiếu gì cụ thể?
     + Tác động: Ảnh hưởng đến user ra sao? (không hiểu / không làm được / mất thời gian)
     + Yêu cầu: Cần bổ sung thông tin gì? Ở vị trí nào? Với format như thế nào?
     + Ví dụ cụ thể: Nên viết như thế nào?
   - **specific_actions** phải là các bước CỤ THỂ (không chung chung):
     + ❌ KHÔNG viết: "Bổ sung thông tin"
     + ✅ PHẢI viết: "Thêm câu 'Thời hạn xử lý: 15 ngày làm việc' sau đoạn giới thiệu thủ tục"
   - **TUYỆT ĐỐI KHÔNG dùng "Failed:" trong description hay specific_actions**

5. **ranking**: Xếp hạng các TC từ tốt nhất đến yếu nhất
   - Mỗi TC có: rank, testcase_code, score (0-10), reason
   - **reason** phải phân tích CHI TIẾT:
     + (1) Tốc độ: Nhanh/chậm bao nhiêu so với trung bình? Tại sao?
     + (2) Nội dung: Đáp ứng bao nhiêu % thông tin? Thiếu gì cụ thể?
     + (3) Độ chính xác: Có thông tin sai không? Có rõ ràng không?
     + (4) Keywords: Có đầy đủ từ khóa bắt buộc không? Có vi phạm từ khóa cấm không?

6. **conclusion**: Kết luận với ưu tiên hành động (Critical → High → Medium)
   - Liệt kê TỪNG hành động cụ thể cần làm ngay
   - Không viết chung chung, phải có TC code + vị trí + nội dung cần sửa

**QUY TẮC QUAN TRỌNG:**
- Dùng: "Thiếu...", "Còn thiếu...", "Cần bổ sung...", "Chưa đề cập..."
- TUYỆT ĐỐI KHÔNG dùng: "Verdict", "PASSED", "FAILED", "Pass", "Fail", "Failed:"
- Mỗi phân tích phải DÀI, CHI TIẾT, CỤ THỂ (150+ từ)
- Phải có cấu trúc: Hiện trạng → So sánh → Phân tích → Kết luận
- Phải chỉ rõ VỊ TRÍ cần sửa (sau câu nào, trước đoạn nào, ở đầu/giữa/cuối)
- Phải có VÍ DỤ CỤ THỂ về cách sửa (nên viết như thế nào)
"""
    
    try:
        # Invoke LLM với STRUCTURED OUTPUT (không dùng JSON mode)
        from langchain_core.messages import SystemMessage, HumanMessage
        
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.0,  # Giảm xuống 0 để deterministic
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        
        # Use structured output - ép LLM phải trả về đúng schema
        structured_llm = llm.with_structured_output(ComparisonAnalysisOutput)
        
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=prompt_text)
        ]
        
        # Invoke với retry logic
        max_retries = 2
        result_obj = None
        
        for attempt in range(max_retries):
            try:
                # Invoke và nhận Pydantic object
                result_obj = await structured_llm.ainvoke(messages)
                
                # Validation passed, break retry loop
                print(f"✅ LLM response received successfully on attempt {attempt + 1}")
                break
                
            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt == max_retries - 1:
                    # Last attempt failed, use fallback
                    print("❌ All retries failed, using fallback response")
                    result_obj = None
                    break
                # Retry with more explicit prompt
                messages.append(HumanMessage(content="\n\n**CRITICAL: You MUST include ALL required fields: similarity_note (string), recommendations (non-empty list), ranking (non-empty list), and conclusion (string). Do not skip any field!**"))
        
        # If all retries failed, use fallback
        if result_obj is None:
            raise ValueError("Failed to get valid response from LLM after retries")
        
        # Convert Pydantic to dict
        result = result_obj.model_dump()
        
        # POST-PROCESSING: Fill missing fields with defaults
        if not result.get("content_analysis", {}).get("similarity_note"):
            result["content_analysis"]["similarity_note"] = "Độ tương đồng giữa các response khá cao, cần xem xét chi tiết để phân biệt."
        
        if not result.get("recommendations") or len(result.get("recommendations", [])) == 0:
            result["recommendations"] = [{
                "priority": "High",
                "target": "All",
                "category": "Content",
                "title": "Cải thiện nội dung response",
                "description": "Cần bổ sung thêm thông tin chi tiết để đáp ứng đầy đủ yêu cầu của user.",
                "specific_actions": ["Xem xét từng response và bổ sung thông tin còn thiếu"],
                "expected_improvement": "Tăng độ đầy đủ thông tin lên 90%+"
            }]
        
        if not result.get("ranking") or len(result.get("ranking", [])) == 0:
            # Auto-generate ranking based on verdict (use flat structure, not turns)
            testcases_sorted = sorted(
                enumerate(testcases),
                key=lambda x: (
                    0 if x[1].actual else 1,  # Has actual response
                    x[1].response_time_ms or 9999
                )
            )
            result["ranking"] = [
                {
                    "rank": i + 1,
                    "testcase_code": tc.code,
                    "score": 7,  # Default score
                    "reason": f"Response với thời gian {tc.response_time_ms or 0}ms"
                }
                for i, (idx, tc) in enumerate(testcases_sorted[:10])
            ]
        
        if not result.get("conclusion"):
            result["conclusion"] = "Cần xem xét và cải thiện các response để đảm bảo chất lượng đồng đều."
        
        # POST-PROCESSING: Loại bỏ các từ cấm nếu LLM vẫn vi phạm
        print("🔍 Before cleaning:", str(result)[:500])
        result = _clean_forbidden_words(result)
        print("✅ After cleaning:", str(result)[:500])
        
        return result
        
    except Exception as e:
        print(f"❌ LLM analysis error: {str(e)}")
        return {
            "overview": "Không thể phân tích do lỗi LLM",
            "performance_analysis": {
                "fastest": {"testcase_code": "", "time_ms": 0, "evaluation": "N/A", "reason": ""},
                "slowest": {"testcase_code": "", "time_ms": 0, "evaluation": "N/A", "reason": ""},
                "overall_speed": "N/A"
            },
            "content_analysis": {
                "best_response": {"testcase_code": "", "reason": "", "strengths": []},
                "weakest_response": {"testcase_code": "", "reason": "", "weaknesses": [], "missing_info": []},
                "similarity_note": "Không thể phân tích do lỗi LLM"
            },
            "recommendations": [{
                "priority": "Critical",
                "target": "All",
                "category": "System",
                "title": "LLM Analysis Failed",
                "description": f"Lỗi: {str(e)}. Vui lòng thử lại sau.",
                "specific_actions": ["Kiểm tra kết nối API", "Thử lại sau vài phút"],
                "expected_improvement": "N/A"
            }],
            "ranking": [{"rank": 1, "testcase_code": "N/A", "score": 0, "reason": "Không thể xếp hạng do lỗi LLM"}],
            "conclusion": "Không thể hoàn thành phân tích. Vui lòng thử lại sau."
        }


@router.post("/compare", response_model=CompareResponse)
@traceable(name="compare_testcases_endpoint", run_type="chain")
async def compare_testcases(request: CompareRequest):
    """
    So sánh multiple testcases với LLM analysis và semantic similarity
    
    POST /api/compare
    Body: { testcases: [...], comparison_mode: "bot_url"|"time"|"free" }
    """
    
    # Validation
    if not request.testcases:
        raise HTTPException(status_code=400, detail="Không có testcase nào để so sánh")
    
    if len(request.testcases) < 2:
        raise HTTPException(status_code=400, detail="Cần ít nhất 2 testcases để so sánh")
    
    if len(request.testcases) > 10:
        raise HTTPException(status_code=400, detail="Chỉ có thể so sánh tối đa 10 testcases")
    
    try:
        # Compute metrics
        metrics = _compute_metrics(request.testcases)
        
        # Compute similarity matrix (async)
        similarity_matrix = await _compute_similarity_matrix(request.testcases)
        
        # Extract similarity pairs for frontend
        similarity_pairs = []
        n = len(request.testcases)
        for i in range(n):
            for j in range(i + 1, n):
                similarity_pairs.append(
                    SimilarityPair(
                        index1=i,
                        index2=j,
                        score=similarity_matrix[i][j]
                    )
                )
        
        # Compute visual diffs (Myers algorithm)
        diff_pairs = _compute_all_diffs(request.testcases)
        
        # LLM analysis (async)
        llm_analysis = await _analyze_with_llm(
            request.testcases,
            request.comparison_mode,
            similarity_matrix,
            metrics
        )
        
        return CompareResponse(
            llm_analysis=llm_analysis,
            similarity_matrix=similarity_matrix,
            similarity_pairs=similarity_pairs,
            diff_pairs=diff_pairs,
            metrics=metrics,
            error=None
        )
        
    except Exception as e:
        print(f"❌ Comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi so sánh: {str(e)}")


@router.get("/cache-stats")
async def get_cache_stats():
    """
    Lấy thống kê embedding cache
    
    GET /api/cache-stats
    """
    return {
        "cache_size": len(embedding_cache),
        "max_size": MAX_CACHE_SIZE,
        "usage_percent": round((len(embedding_cache) / MAX_CACHE_SIZE) * 100, 2)
    }


class SuggestionGroup(BaseModel):
    """Nhóm testcases được đề xuất để so sánh"""
    title: str
    reason: str
    testcase_codes: List[str]
    testcase_indices: List[int]
    priority: str  # "high", "medium", "low"


@router.post("/suggest-comparisons")
@traceable(name="suggest_comparisons_endpoint", run_type="chain")
async def suggest_comparisons(testcases: List[TestcaseCompareData]):
    """
    Đề xuất các nhóm testcases nên so sánh
    
    POST /api/suggest-comparisons
    Body: { testcases: [...] }
    """
    if not testcases or len(testcases) < 2:
        return {"suggestions": []}
    
    suggestions: List[SuggestionGroup] = []
    
    # 1. Suggest: Same question, different bot URLs
    question_groups: Dict[str, List[int]] = {}
    for i, tc in enumerate(testcases):
        q = tc.question
        if q not in question_groups:
            question_groups[q] = []
        question_groups[q].append(i)
    
    for question, indices in question_groups.items():
        if len(indices) >= 2:
            # Check if they have different bot URLs
            bot_urls = set(testcases[i].bot_url for i in indices)
            if len(bot_urls) > 1:
                suggestions.append(SuggestionGroup(
                    title=f"So sánh {len(indices)} bot với cùng câu hỏi",
                    reason=f"Cùng câu hỏi '{question[:50]}...' nhưng khác bot URL",
                    testcase_codes=[testcases[i].code for i in indices],
                    testcase_indices=indices,
                    priority="high"
                ))
    
    # 2. Suggest: Same bot URL, significantly different response times
    bot_url_groups: Dict[str, List[int]] = {}
    for i, tc in enumerate(testcases):
        url = tc.bot_url or "default"
        if url not in bot_url_groups:
            bot_url_groups[url] = []
        bot_url_groups[url].append(i)
    
    for bot_url, indices in bot_url_groups.items():
        if len(indices) >= 2:
            times = [(i, testcases[i].response_time_ms) for i in indices if testcases[i].response_time_ms]
            if len(times) >= 2:
                times.sort(key=lambda x: x[1])
                fastest_idx, fastest_time = times[0]
                slowest_idx, slowest_time = times[-1]
                
                # If difference > 500ms, suggest comparison
                if slowest_time - fastest_time > 500:
                    suggestions.append(SuggestionGroup(
                        title=f"So sánh performance: {fastest_time}ms vs {slowest_time}ms",
                        reason=f"Cùng bot nhưng chênh lệch thời gian >500ms",
                        testcase_codes=[testcases[fastest_idx].code, testcases[slowest_idx].code],
                        testcase_indices=[fastest_idx, slowest_idx],
                        priority="medium"
                    ))
    
    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda s: priority_order.get(s.priority, 3))
    
    return {"suggestions": suggestions[:10]}  # Limit to top 10
