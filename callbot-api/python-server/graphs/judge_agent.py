"""
LLM Judge Agent sử dụng LangChain + LangGraph
Đánh giá câu trả lời của chatbot theo tiêu chí
"""

import os
import asyncio
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langsmith import traceable

from models.schemas import JudgeResult
from prompts.prompt_factory import create_judge_prompt


# Time thresholds
TIME_THRESHOLD = {
    "GOOD": 2000,   # <= 2s: tốt
    "OK": 3000,     # <= 3s: chấp nhận được
    # > 3s: chậm
}


def classify_time(ms: int) -> Dict[str, str]:
    """Phân loại thời gian phản hồi"""
    if ms <= TIME_THRESHOLD["GOOD"]:
        return {"label": "Nhanh", "level": "good"}
    if ms <= TIME_THRESHOLD["OK"]:
        return {"label": "Chấp nhận được", "level": "ok"}
    return {"label": "Chậm", "level": "slow"}


class JudgeAgent:
    """LLM Judge Agent với LangChain"""
    
    def __init__(self):
        """Initialize judge agent"""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.parser = JsonOutputParser(pydantic_object=JudgeResult)
    
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
                # Invoke LLM với structured output
                chain = prompt | self.llm | self.parser
                result = await chain.ainvoke({})
                
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
                    # FAILED phải có ít nhất error_desc
                    if not error_desc:
                        error_desc = "Không đạt yêu cầu"
                
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
