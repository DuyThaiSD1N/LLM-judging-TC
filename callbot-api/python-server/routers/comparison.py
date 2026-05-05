"""
Comparison router - So sánh testcases với LLM analysis và semantic similarity
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import asyncio
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langsmith import traceable
import numpy as np
import os
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
    group: str
    bot_url: Optional[str]
    question: str
    expected: str
    actual: str
    response_time_ms: Optional[int]
    verdict: Optional[str]
    error_desc: str = ""


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
    
    passed = sum(1 for tc in testcases if tc.verdict == "PASSED")
    pass_rate = round((passed / len(testcases)) * 100) if testcases else 0
    
    fastest_tc = next((tc for tc in testcases if tc.response_time_ms == fastest), None)
    slowest_tc = next((tc for tc in testcases if tc.response_time_ms == slowest), None)
    
    return {
        "fastest_ms": fastest,
        "fastest_code": fastest_tc.code if fastest_tc else None,
        "slowest_ms": slowest,
        "slowest_code": slowest_tc.code if slowest_tc else None,
        "average_ms": average,
        "pass_rate": pass_rate,
        "passed_count": passed,
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


@traceable(name="llm_compare_analysis", run_type="chain")
async def _analyze_with_llm(
    testcases: List[TestcaseCompareData],
    comparison_mode: str,
    similarity_matrix: List[List[float]],
    metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Phân tích comparison với LLM
    Trả về insights, patterns, outliers, và suggestions
    """
    
    # Prepare context for LLM
    tc_summaries = []
    for i, tc in enumerate(testcases):
        time_class = _classify_time(tc.response_time_ms) if tc.response_time_ms else {"label": "N/A", "level": "unknown"}
        tc_summaries.append(
            f"[{i+1}] {tc.code} - {tc.name}\n"
            f"  Bot URL: {tc.bot_url or 'mặc định'}\n"
            f"  Câu hỏi: {tc.question}\n"
            f"  Kỳ vọng: {tc.expected[:100]}...\n"
            f"  Thực tế: {tc.actual[:100] if tc.actual else 'N/A'}...\n"
            f"  Thời gian: {tc.response_time_ms}ms ({time_class['label']})\n"
            f"  Kết quả: {tc.verdict or 'N/A'}\n"
            f"  Lỗi: {tc.error_desc[:100] if tc.error_desc else 'Không có'}...\n"
        )
    
    # Prepare similarity insights
    similarity_insights = []
    n = len(testcases)
    for i in range(n):
        for j in range(i + 1, n):
            sim = similarity_matrix[i][j]
            if sim >= 0.9:
                level = "rất cao"
            elif sim >= 0.7:
                level = "cao"
            elif sim >= 0.5:
                level = "trung bình"
            else:
                level = "thấp"
            similarity_insights.append(
                f"  - {testcases[i].code} vs {testcases[j].code}: {sim:.2%} ({level})"
            )
    
    prompt_text = f"""Bạn là chuyên gia phân tích chất lượng chatbot. Hãy phân tích kết quả so sánh {len(testcases)} testcases sau:

## Chế độ so sánh: {comparison_mode}
- bot_url: So sánh cùng câu hỏi, khác bot URL
- time: So sánh cùng câu hỏi và bot URL (focus vào thời gian)
- free: So sánh tự do

## Testcases:
{chr(10).join(tc_summaries)}

## Metrics tổng quan:
- Nhanh nhất: {metrics['fastest_ms']}ms ({metrics['fastest_code']})
- Chậm nhất: {metrics['slowest_ms']}ms ({metrics['slowest_code']})
- Trung bình: {metrics['average_ms']}ms
- Pass rate: {metrics['pass_rate']}% ({metrics['passed_count']}/{metrics['total_count']})

## Semantic Similarity:
{chr(10).join(similarity_insights)}

Hãy phân tích và trả về JSON với cấu trúc sau:
{{
  "overview": "Tóm tắt tổng quan về kết quả so sánh (2-3 câu)",
  "patterns": [
    {{"description": "Mô tả pattern", "severity": "Info|Warning|Critical"}}
  ],
  "outliers": [
    {{"testcase_code": "TC001", "reason": "Lý do là outlier", "severity": "Minor|Major|Critical"}}
  ],
  "suggestions": [
    {{
      "priority": "Critical|Major|Minor",
      "title": "Tiêu đề ngắn gọn",
      "description": "Mô tả chi tiết đề xuất",
      "affected_testcases": ["TC001", "TC002"]
    }}
  ],
  "time_analysis": "Phân tích về thời gian phản hồi",
  "quality_analysis": "Phân tích về chất lượng câu trả lời",
  "conclusion": "Kết luận và hành động tiếp theo"
}}

Lưu ý:
- Tập trung vào insights thực tế, không chung chung
- Đề xuất phải cụ thể và có thể thực hiện được
- Ưu tiên các vấn đề Critical và Major
- Nếu comparison_mode là "bot_url", focus vào so sánh giữa các bot
- Nếu comparison_mode là "time", focus vào performance
"""
    
    try:
        # Invoke LLM với JSON mode
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY"),
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        
        response = await llm.ainvoke(prompt_text)
        
        # Parse JSON response
        import json
        result = json.loads(response.content)
        
        return result
        
    except Exception as e:
        print(f"❌ LLM analysis error: {str(e)}")
        return {
            "overview": "Không thể phân tích do lỗi LLM",
            "patterns": [],
            "outliers": [],
            "suggestions": [{
                "priority": "Critical",
                "title": "LLM Analysis Failed",
                "description": f"Error: {str(e)}",
                "affected_testcases": []
            }],
            "time_analysis": "N/A",
            "quality_analysis": "N/A",
            "conclusion": "Vui lòng thử lại sau"
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
    
    # 3. Suggest: Same question, one passed one failed
    for question, indices in question_groups.items():
        if len(indices) >= 2:
            passed = [i for i in indices if testcases[i].verdict == "PASSED"]
            failed = [i for i in indices if testcases[i].verdict == "FAILED"]
            
            if passed and failed:
                # Pick one from each
                suggestions.append(SuggestionGroup(
                    title=f"So sánh PASSED vs FAILED",
                    reason=f"Cùng câu hỏi '{question[:50]}...' nhưng kết quả khác nhau",
                    testcase_codes=[testcases[passed[0]].code, testcases[failed[0]].code],
                    testcase_indices=[passed[0], failed[0]],
                    priority="high"
                ))
    
    # 4. Suggest: All failed testcases (if 2-10)
    failed_indices = [i for i, tc in enumerate(testcases) if tc.verdict == "FAILED"]
    if 2 <= len(failed_indices) <= 10:
        suggestions.append(SuggestionGroup(
            title=f"So sánh tất cả {len(failed_indices)} testcases FAILED",
            reason="Tìm pattern chung trong các testcases thất bại",
            testcase_codes=[testcases[i].code for i in failed_indices],
            testcase_indices=failed_indices,
            priority="high"
        ))
    
    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda s: priority_order.get(s.priority, 3))
    
    return {"suggestions": suggestions[:10]}  # Limit to top 10
