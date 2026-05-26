"""
LLM Judge Agent sử dụng LangChain + LangGraph
Đánh giá câu trả lời của chatbot theo tiêu chí
"""

import os
import json
import re
import asyncio
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langsmith import traceable

from prompts.advanced_prompt import create_advanced_judge_prompt


# Time thresholds
TIME_THRESHOLD = {
    "GOOD": 2000,   # <= 2s: tốt
    "OK": 3000,     # <= 3s: chấp nhận được
}


def classify_time(ms: int) -> Dict[str, str]:
    """Phân loại thời gian phản hồi"""
    if ms <= TIME_THRESHOLD["GOOD"]:
        return {"label": "Nhanh", "level": "good"}
    if ms <= TIME_THRESHOLD["OK"]:
        return {"label": "Chấp nhận được", "level": "ok"}
    return {"label": "Chậm", "level": "slow"}


def _clean_forbidden_words(text: str) -> str:
    """
    Xóa các từ cấm khỏi LLM output (error_desc, suggestion, etc.)
    Đặc biệt xử lý: "Failed: X" → "X"
    """
    if not isinstance(text, str) or not text:
        return text
    
    original = text
    
    # STEP 1: Xử lý "Failed: X" / "FAILED: X" ở đầu câu → chỉ giữ lại X
    text = re.sub(r'\b(?:Failed|FAILED|Fail|FAIL):\s*', '', text, flags=re.IGNORECASE)
    
    # STEP 2: Xóa "Verdict:" patterns
    text = re.sub(r'Verdict:\s*[^\n]*', '', text, flags=re.IGNORECASE)
    
    # STEP 3: Thay thế standalone "FAILED" / "PASSED"
    text = re.sub(r'\b(?:FAILED|Fail|failed|FAIL)\b', 'chưa đáp ứng', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(?:PASSED|Pass|passed|PASS)\b', 'đã đáp ứng', text, flags=re.IGNORECASE)
    
    # Clean up
    text = text.strip()
    
    if text != original:
        print(f"🧹 Cleaned judge output: '{original[:60]}...' → '{text[:60]}...'")
    
    return text


def _clean_tone_note(text: str) -> str:
    """
    Xóa các nhận xét TÍCH CỰC khỏi tone_note
    CHỈ giữ lại những gì CẦN CẢI THIỆN
    """
    if not isinstance(text, str) or not text:
        return text
    
    original = text
    
    # Danh sách các cụm từ tích cực cần xóa
    positive_patterns = [
        r'giọng điệu\s+(?:rất\s+)?lịch sự',
        r'(?:rất\s+)?lịch sự',
        r'có\s+xưng\s+hô',
        r'xưng\s+hô\s+(?:đầy\s+đủ|phù\s+hợp|tốt)',
        r'có\s+(?:dạ|ạ)',
        r'(?:dạ|ạ)\s+đầy\s+đủ',
        r'thân\s+thiện',
        r'tôn\s+trọng',
        r'chuyên\s+nghiệp',
        r'giọng\s+điệu\s+tốt',
        r'phù\s+hợp',
        r'hợp\s+lý',
    ]
    
    # Xóa các pattern tích cực
    for pattern in positive_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Xóa các câu chỉ chứa khen ngợi
    # VD: "Giọng điệu lịch sự và có xưng hô." → ""
    if re.match(r'^[\s,\.;và]+$', text):
        text = ""
    
    # Clean up: xóa dấu phẩy, chấm, "và" thừa
    text = re.sub(r'^[\s,\.;và]+', '', text)
    text = re.sub(r'[\s,\.;và]+$', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Nếu sau khi xóa chỉ còn dấu câu hoặc rỗng → trả về rỗng
    if not text or re.match(r'^[\s,\.;]+$', text):
        text = ""
    
    if text != original and original:
        print(f"🧹 Cleaned tone_note: '{original[:60]}...' → '{text[:60] if text else '(empty)'}...'")
    
    return text


def _safe_parse_json(raw: str) -> Dict[str, Any]:
    """
    Parse JSON từ LLM output một cách an toàn.
    Xử lý các lỗi phổ biến: thiếu dấu phẩy, ký tự đặc biệt trong reasoning.
    """
    # Thử parse trực tiếp trước
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Trích xuất JSON block nếu có text thừa bao quanh
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Thử sửa lỗi thiếu dấu phẩy giữa các field (lỗi phổ biến nhất)
    # Pattern: "..." "key": → "...", "key":
    fixed = re.sub(r'"\s*\n\s*"', '",\n"', raw)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # Không parse được → raise để caller xử lý
    raise ValueError(f"Cannot parse LLM JSON output: {raw[:200]}...")


class JudgeAgent:
    """LLM Judge Agent với LangChain"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY"),
            # Bắt buộc trả về JSON object — tránh LLM thêm text thừa
            model_kwargs={"response_format": {"type": "json_object"}}
        )
    
    @traceable(name="judge_one", run_type="chain")
    async def judge_one(
        self,
        question: str,
        expected: str,
        actual: str,
        response_time_ms: int,
        criteria: str = "goal_achievement",
        required_keywords: str = None,
        forbidden_keywords: str = None
    ) -> Dict[str, Any]:
        """
        Đánh giá một câu trả lời (SIMPLIFIED - No group logic)
        
        Args:
            question: Câu hỏi
            expected: YÊU CẦU KỲ VỌNG (không phải câu trả lời cụ thể)
            actual: Câu trả lời thực tế
            response_time_ms: Thời gian phản hồi (ms)
            criteria: Tiêu chí đánh giá
            required_keywords: Từ khóa bắt buộc (optional)
            forbidden_keywords: Từ khóa cấm (optional)
            
        Returns:
            Dict với kết quả đánh giá
        """
        # Classify time
        time_info = classify_time(response_time_ms)
        time_label = f"{response_time_ms}ms ({time_info['label']})"
        
        # Create advanced prompt with criteria-specific instructions
        prompt_text = create_advanced_judge_prompt(
            question=question,
            expected=expected,
            actual=actual,
            time_label=time_label,
            criteria=criteria,  # Pass criteria to get dynamic prompt
            required_keywords=required_keywords,
            forbidden_keywords=forbidden_keywords,
            inject_knowledge=True  # ← Enable knowledge base injection
        )
        
        # Retry logic với exponential backoff
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                # Invoke LLM
                from langchain_core.messages import HumanMessage
                
                ai_message = await self.llm.ainvoke([HumanMessage(content=prompt_text)])
                raw_content = ai_message.content

                # Parse JSON an toàn
                result = _safe_parse_json(raw_content)
                
                # Normalize errors from both the current top-level schema and older nested schema.
                errors = result.get("errors") or result.get("accuracy_analysis", {}).get("errors", [])
                if not isinstance(errors, list):
                    errors = []
                severe_errors = [
                    e for e in errors
                    if isinstance(e, dict) and e.get("severity") in ("Critical", "Major")
                ]

                # Get and validate verdict from LLM
                verdict = result.get("verdict", "FAILED")
                if verdict not in ("PASSED", "FAILED"):
                    verdict = "FAILED"
                if verdict == "FAILED" and not severe_errors:
                    verdict = "PASSED"
                    result["needs_human_review"] = True
                    result["confidence_reason"] = (
                        "LLM returned FAILED without Critical/Major evidence; normalized to PASSED for consistency."
                    )
                
                # Đảm bảo consistency: PASSED không có error_desc
                error_desc = result.get("error_desc", "")
                suggestion = result.get("suggestion", "")
                suggested_response = result.get("suggested_response", "")
                
                # CLEAN forbidden words from all text fields
                error_desc = _clean_forbidden_words(error_desc)
                suggestion = _clean_forbidden_words(suggestion)
                suggested_response = _clean_forbidden_words(suggested_response)
                
                if verdict == "PASSED":
                    # PASSED phải rỗng error fields
                    error_desc = ""
                    suggestion = ""
                    suggested_response = ""
                elif verdict == "FAILED":
                    # FAILED phải có error_desc và suggestion chi tiết.
                    # Nếu LLM không điền, lấy từ rationale hoặc errors.
                    if not error_desc:
                        reasoning = result.get("reasoning", "")
                        if errors:
                            # Ghép từ errors array
                            error_desc = " | ".join(
                                f"[{e.get('severity','?')}] {e.get('description','')}"
                                for e in errors if e.get("description")
                            )
                            error_desc = _clean_forbidden_words(error_desc)
                        elif reasoning:
                            error_desc = reasoning[-300:].strip()
                            error_desc = _clean_forbidden_words(error_desc)
                        else:
                            error_desc = "LLM không cung cấp lý do — cần human review"

                    if not suggestion:
                        suggestion = "Xem lại nội dung câu trả lời và bổ sung thông tin còn thiếu."
                
                # Extract confidence fields
                confidence_level = result.get("confidence_level")
                needs_human_review = result.get("needs_human_review", False)
                if confidence_level is not None and confidence_level < 0.7:
                    needs_human_review = True
                
                # Clean tone_note - chỉ giữ lại vấn đề, xóa khen ngợi
                tone_note = result.get("tone_note", "")
                tone_note = _clean_tone_note(tone_note)
                
                time_verdict = result.get("time_verdict", time_info["level"])
                if time_verdict not in ("good", "ok", "slow"):
                    time_verdict = time_info["level"]

                # Logging for monitoring
                print(
                    f"📊 Judge Result [{criteria}]: result={verdict}, "
                    f"confidence={confidence_level}, "
                    f"needs_review={needs_human_review}"
                )
                
                return {
                    # Main verdict
                    "verdict": verdict,

                    # Short evidence-based rationale
                    "reasoning": result.get("reasoning", ""),

                    # Confidence fields
                    "confidence_level": confidence_level,
                    "needs_human_review": needs_human_review,
                    "confidence_reason": result.get("confidence_reason", ""),
                    "errors": errors,

                    # Error details
                    "error_desc": error_desc,
                    "suggestion": suggestion,
                    "suggested_response": suggested_response,

                    # Notes
                    "tone_note": tone_note,
                    "time_verdict": time_verdict,
                    "time_note": result.get("time_note", time_label),
                }
                
            except Exception as e:
                error_msg = str(e)
                
                # JSON parse error — retry ngay (không cần delay)
                if "Cannot parse" in error_msg and attempt < max_retries - 1:
                    print(
                        f"⚠️ JSON parse error, retrying immediately "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    continue

                # Rate limit error - wait and retry
                if "429" in error_msg and attempt < max_retries - 1:
                    print(
                        f"⚠️ OpenAI rate limit hit, retrying in {retry_delay}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(retry_delay)
                    continue
                
                # Timeout error - retry immediately
                if "timeout" in error_msg.lower() and attempt < 2:
                    print(
                        f"⚠️ OpenAI timeout, retrying immediately "
                        f"(attempt {attempt + 1}/2)"
                    )
                    continue
                
                # Max retries reached or other error
                print(f"❌ OpenAI API error after {attempt + 1} attempts: {error_msg}")
                
                # Return fallback response
                return {
                    "verdict": "FAILED",
                    "reasoning": "",
                    "confidence_level": 0.0,
                    "needs_human_review": True,
                    "confidence_reason": "LLM Judge unavailable - API error",
                    "errors": [{
                        "description": f"LLM Judge unavailable: {error_msg}",
                        "severity": "Critical",
                        "quote": ""
                    }],
                    "error_desc": f"LLM Judge unavailable: {error_msg}",
                    "suggestion": "Please retry later or contact support",
                    "suggested_response": "",
                    "tone_note": "",
                    "time_verdict": time_info["level"],
                    "time_note": time_label,
                }
        
        # Should not reach here, but just in case
        return {
            "verdict": "FAILED",
            "reasoning": "",
            "confidence_level": 0.0,
            "needs_human_review": True,
            "confidence_reason": "Max retries exceeded",
            "errors": [],
            "error_desc": "Max retries exceeded",
            "suggestion": "",
            "suggested_response": "",
            "tone_note": "",
            "time_verdict": time_info["level"],
            "time_note": time_label,
        }


# Global instance
judge_agent = JudgeAgent()
