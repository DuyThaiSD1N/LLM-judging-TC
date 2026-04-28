# routers/judge.py — LLM đánh giá nội dung + thời gian phản hồi chatbot

import re
import os
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TIME_GOOD = 2000  # ms
TIME_OK   = 3000  # ms

GROUP_DESC = {
    "A": "Hỏi đầy đủ thông tin — bot phải cung cấp đúng và đủ thông tin về thủ tục hành chính.",
    "B": (
        "Hỏi ngoại lệ / ngoài phạm vi — bot phải từ chối và chuyển hướng về hành chính công. "
        "Cách từ chối mặc định HỢP LỆ: KHÔNG trả lời nội dung ngoài phạm vi, sau đó hỏi lại "
        "người dùng có cần hỗ trợ thủ tục hành chính không. "
        'Ví dụ hợp lệ: "Dạ em rất sẵn lòng a, nhưng em xin phép hỗ trợ các nội dung hành chính '
        'công thôi, anh cần em tra cứu thủ tục nào không ạ?" '
        "Đây là hành vi ĐÚNG — phải chấm PASSED nếu bot từ chối và chuyển hướng như vậy."
    ),
    "C": "Hỏi chuyển topic đột ngột — bot phải xử lý chuyển chủ đề hợp lý, không bị lạc.",
    "D": "Hỏi tài liệu không có trong CSDL — bot phải thừa nhận không có thông tin và hướng dẫn đến văn phòng 1 cửa, tuyệt đối không bịa.",
}

GREETING_PATTERNS = [
    re.compile(r"em chào anh", re.IGNORECASE),
    re.compile(r"em chào chị", re.IGNORECASE),
    re.compile(r"xin chào", re.IGNORECASE),
    re.compile(r"tổng đài.*hành chính", re.IGNORECASE),
    re.compile(r"hành chính công.*tỉnh", re.IGNORECASE),
    re.compile(r"em có thể hỗ trợ gì", re.IGNORECASE),
    re.compile(r"em có thể giúp gì", re.IGNORECASE),
]


def is_greeting(text: str) -> bool:
    return any(p.search(text) for p in GREETING_PATTERNS)


def classify_time(ms: int) -> dict:
    if ms <= TIME_GOOD:
        return {"label": "Nhanh", "level": "good"}
    if ms <= TIME_OK:
        return {"label": "Chấp nhận được", "level": "ok"}
    return {"label": "Chậm", "level": "slow"}


async def judge_one(question: str, expected: str, actual: str, group: str, response_time_ms: int) -> dict | None:
    if is_greeting(actual):
        return None

    time_info  = classify_time(response_time_ms)
    time_label = f"{response_time_ms}ms ({time_info['label']})"
    group_desc = GROUP_DESC.get(group, "")

    prompt = f"""Bạn là chuyên gia kiểm thử chatbot hành chính công.
Nhiệm vụ: đánh giá toàn diện câu trả lời của chatbot theo 3 tiêu chí.

---
NHÓM KỊCH BẢN: {group}
MÔ TẢ NHÓM: {group_desc}

CÂU HỎI CỦA USER:
"{question}"

CÂU TRẢ LỜI KỲ VỌNG (nội dung cốt lõi cần có):
"{expected}"

CÂU TRẢ LỜI THỰC TẾ CỦA CHATBOT:
"{actual}"

THỜI GIAN PHẢN HỒI: {time_label}
---

## TIÊU CHÍ 1 — NỘI DUNG (PASSED/FAILED)

PASSED khi:
- Câu trả lời truyền đạt đúng và đủ thông tin cốt lõi so với kỳ vọng (không cần giống từng chữ)
- Với nhóm B: bot từ chối nội dung ngoài phạm vi VÀ chuyển hướng về hành chính công → PASSED

FAILED khi:
- Thiếu thông tin quan trọng mà kỳ vọng có
- Cung cấp thông tin sai lệch hoặc mâu thuẫn với kỳ vọng
- Bịa thông tin không có cơ sở — áp dụng cho TẤT CẢ nhóm
- Với nhóm B: bot trả lời nội dung ngoài phạm vi thay vì từ chối → FAILED
- Với nhóm D: bot bịa thông tin thay vì hướng dẫn đến văn phòng 1 cửa → FAILED

## TIÊU CHÍ 2 — ĐỘ TỰ NHIÊN & GIỌNG ĐIỆU (dành cho voicebot)
- Xưng hô lịch sự, đúng mực (anh/chị, dạ vâng...)
- Không cộc lốc, không quá máy móc
- Câu văn tự nhiên khi nghe, không vấp

## TIÊU CHÍ 3 — ĐỘ NGẮN GỌN & SÚC TÍCH (quan trọng với voicebot)
- Trả lời đúng trọng tâm, không lan man
- Không lặp lại thông tin không cần thiết
- Người dùng nghe xong không bị mất tập trung

## ĐÁNH GIÁ THỜI GIAN PHẢN HỒI:
- Nhận xét ngắn gọn về {time_label}
- Nếu chậm (> 3s): nêu ảnh hưởng đến trải nghiệm người dùng

Trả về JSON với đúng 7 trường:
{{
  "verdict": "PASSED" hoặc "FAILED",
  "error_desc": "Mô tả lỗi nội dung nếu FAILED. Để trống nếu PASSED.",
  "suggestion": "Đề xuất cải thiện nếu FAILED. Để trống nếu PASSED.",
  "tone_note": "Nhận xét 1 câu về độ tự nhiên và giọng điệu.",
  "brevity_note": "Nhận xét 1 câu về độ ngắn gọn.",
  "time_verdict": "good" hoặc "ok" hoặc "slow",
  "time_note": "Nhận xét ngắn về tốc độ phản hồi (1 câu)."
}}

Chỉ trả về JSON, không giải thích thêm."""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    import json
    parsed = json.loads(response.choices[0].message.content)

    return {
        "verdict":      parsed.get("verdict", "FAILED") if parsed.get("verdict") in ("PASSED", "FAILED") else "FAILED",
        "error_desc":   parsed.get("error_desc", ""),
        "suggestion":   parsed.get("suggestion", ""),
        "tone_note":    parsed.get("tone_note", ""),
        "brevity_note": parsed.get("brevity_note", ""),
        "time_verdict": parsed.get("time_verdict", time_info["level"]) if parsed.get("time_verdict") in ("good", "ok", "slow") else time_info["level"],
        "time_note":    parsed.get("time_note", time_label),
    }
