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

from prompts.prompt_factory import create_judge_prompt


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
            temperature=0.1,
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
        group: str,
        response_time_ms: int,
        criteria: str = "standard"
    ) -> Dict[str, Any]:
        """
        Đánh giá một câu trả lời
        
        Args:
            question: Câu hỏi
            expected: Câu trả lời kỳ vọng
            actual: Câu trả lời thực tế
            group: Nhóm testcase (A/B/C/D)
            response_time_ms: Thời gian phản hồi (ms)
            criteria: Tiêu chí đánh giá
            
        Returns:
            Dict với kết quả đánh giá
        """
        # Classify time
        time_info = classify_time(response_time_ms)
        time_label = f"{response_time_ms}ms ({time_info['label']})"
        
        # Create prompt
        prompt = create_judge_prompt(
            criteria=criteria,
            question=question,
            expected=expected,
            actual=actual,
            group=group,
            time_label=time_label
        )
        
        # Retry logic với exponential backoff
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                # Invoke LLM — nhận raw string, tự parse để kiểm soát lỗi
                chain = prompt | self.llm
                ai_message = await chain.ainvoke({})
                raw_content = ai_message.content

                # Parse JSON an toàn, tự sửa lỗi nhỏ
                result = _safe_parse_json(raw_content)
                
                # Get verdict from LLM
                verdict = result.get("verdict", "FAILED")
                
                # Đảm bảo consistency: PASSED không có error_desc
                error_desc = result.get("error_desc", "")
                suggestion = result.get("suggestion", "")
                suggested_response = result.get("suggested_response", "")
                
                if verdict == "PASSED":
                    # PASSED phải rỗng error fields
                    error_desc = ""
                    suggestion = ""
                    suggested_response = ""
                elif verdict == "FAILED":
                    # FAILED phải có error_desc và suggestion chi tiết
                    # Nếu LLM không điền, lấy từ reasoning hoặc errors
                    if not error_desc:
                        reasoning = result.get("reasoning", "")
                        errors = result.get("errors", [])
                        if errors:
                            # Ghép từ errors array
                            error_desc = " | ".join(
                                f"[{e.get('severity','?')}] {e.get('description','')}"
                                for e in errors if e.get("description")
                            )
                        elif reasoning:
                            # Lấy phần kết luận từ reasoning
                            error_desc = reasoning.split("[CoT-6]")[-1].strip() if "[CoT-6]" in reasoning else reasoning[-300:]
                        else:
                            error_desc = "LLM không cung cấp lý do — cần human review"

                    if not suggestion:
                        suggestion = "Xem lại nội dung câu trả lời và bổ sung thông tin còn thiếu."
                
                # Extract confidence fields
                confidence_level = result.get("confidence_level")
                needs_human_review = result.get("needs_human_review", False)
                if confidence_level is not None and confidence_level < 0.7:
                    needs_human_review = True
                
                # Logging for monitoring
                print(
                    f"📊 Judge Result [{criteria}]: verdict={verdict}, "
                    f"confidence={confidence_level}, "
                    f"needs_review={needs_human_review}"
                )
                
                return {
                    # Main verdict
                    "verdict": verdict,

                    # Chain-of-Thought reasoning
                    "reasoning": result.get("reasoning", ""),

                    # Confidence fields
                    "confidence_level": confidence_level,
                    "needs_human_review": needs_human_review,
                    "confidence_reason": result.get("confidence_reason", ""),
                    "errors": result.get("errors", []),

                    # Error details
                    "error_desc": error_desc,
                    "suggestion": suggestion,
                    "suggested_response": suggested_response,

                    # Notes
                    "tone_note": result.get("tone_note", ""),
                    "time_verdict": result.get("time_verdict", time_info["level"]),
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
