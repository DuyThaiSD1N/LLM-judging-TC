# 📋 Hướng dẫn Hệ thống Prompt LLM Judge (Nâng cấp)

## 🎯 Tổng quan

Hệ thống prompt LLM Judge đã được nâng cấp để **mỗi tiêu chí đánh giá sẽ cho ra câu đánh giá khác nhau** tùy thuộc vào tiêu chí được chọn.

### 📁 Cấu trúc File

- **`simple_prompt.py`** - Prompt cơ bản (giữ lại để backward compatibility)
- **`advanced_prompt.py`** - Prompt nâng cấp (ĐƯỢC SỬ DỤNG)
- **`judge_agent.py`** - Agent sử dụng advanced_prompt

---

## 🔄 Cách hoạt động

### 1. **Người dùng chọn tiêu chí**
```
Tiêu chí: "strict" (Nghiêm ngặt)
```

### 2. **Hệ thống tạo prompt động**
```python
prompt = create_advanced_judge_prompt(
    question="...",
    expected="...",
    actual="...",
    criteria="strict"  # ← Tiêu chí được chọn
)
```

### 3. **Prompt chứa hướng dẫn riêng cho tiêu chí**
```
TIÊU CHÍ: NGHIÊM NGẶT (Yêu cầu cao)
- Nội dung: ≥95% thông tin
- Giọng điệu: PHẢI có xưng hô
- Thời gian: ≤2s là tốt, >3s là FAILED
```

### 4. **LLM đánh giá theo hướng dẫn**
- Kiểm tra ≥95% thông tin (không phải 90%)
- Bắt buộc có xưng hô (không phải tùy chọn)
- Thời gian >3s → FAILED (không phải chỉ ghi nhận)

### 5. **Output khác nhau tùy tiêu chí**
```json
{
  "verdict": "FAILED",
  "reasoning": "Kiểm tra 5 thông tin: (1) ✓, (2) ✓, (3) ✗, (4) ✓, (5) ✗. Đạt 60% < 95% → FAILED",
  "error_desc": "Response thiếu 2 thông tin quan trọng...",
  "suggestion": "Cần bổ sung..."
}
```

---

## 📊 5 Tiêu chí Đánh giá

### 1️⃣ **Tiêu chí Chuẩn (Standard)**
- **Focus**: Cân bằng tất cả yếu tố
- **Nội dung**: ≥90% thông tin
- **Giọng điệu**: Lịch sự (không bắt buộc xưng hô)
- **Thời gian**: ≤3s là tốt
- **Quyết định**: PASSED nếu ≥90% + không vi phạm keywords + lịch sự

**Ví dụ output:**
```
reasoning: "Kiểm tra 4 thông tin: (1) ✓, (2) ✓, (3) ✓, (4) ✓. Đạt 100% ≥ 90% → PASSED"
verdict: "PASSED"
```

---

### 2️⃣ **Tiêu chí Nghiêm ngặt (Strict)**
- **Focus**: Yêu cầu cao nhất
- **Nội dung**: ≥95% thông tin
- **Giọng điệu**: PHẢI có xưng hô + lịch sự
- **Thời gian**: ≤2s tốt, >3s FAILED
- **Quyết định**: PASSED nếu ≥95% + ≤3s + có xưng hô + không vi phạm keywords

**Ví dụ output:**
```
reasoning: "Kiểm tra 5 thông tin: (1) ✓, (2) ✓, (3) ✓, (4) ✓, (5) ✗. Đạt 80% < 95% → FAILED. Thêm vào: thiếu xưng hô"
verdict: "FAILED"
error_desc: "Response thiếu 1 thông tin và không có xưng hô"
```

---

### 3️⃣ **Tiêu chí Tốc độ (Speed-focused)**
- **Focus**: Ưu tiên nhanh
- **Thời gian**: ≤2s (bắt buộc)
- **Nội dung**: ≥80% thông tin
- **Giọng điệu**: KHÔNG đánh giá
- **Quyết định**: PASSED nếu ≤2s + ≥80% thông tin + không vi phạm keywords

**Ví dụ output:**
```
reasoning: "Kiểm tra thời gian: 2500ms > 2s → FAILED ngay (quá chậm)"
verdict: "FAILED"
error_desc: "Response quá chậm (2.5s > 2s)"
tone_note: "" (để trống - không đánh giá)
```

---

### 4️⃣ **Tiêu chí Nội dung (Content-only)**
- **Focus**: Chỉ độ chính xác
- **Nội dung**: ≥95% thông tin
- **Thời gian**: KHÔNG đánh giá
- **Giọng điệu**: KHÔNG đánh giá
- **Quyết định**: PASSED nếu ≥95% thông tin + không vi phạm keywords

**Ví dụ output:**
```
reasoning: "Kiểm tra 5 thông tin: (1) ✓, (2) ✓, (3) ✓, (4) ✓, (5) ✓. Đạt 100% ≥ 95% → PASSED"
verdict: "PASSED"
time_note: "" (để trống - không đánh giá)
tone_note: "" (để trống - không đánh giá)
```

---

### 5️⃣ **Tiêu chí Trải nghiệm (UX-focused)**
- **Focus**: Ưu tiên thân thiện
- **Giọng điệu**: PHẢI có xưng hô + lịch sự (bắt buộc)
- **Nội dung**: ≥85% thông tin
- **Thời gian**: ≤3s là tốt
- **Quyết định**: PASSED nếu có xưng hô + ≥85% thông tin + không vi phạm keywords

**Ví dụ output:**
```
reasoning: "Kiểm tra giọng điệu: có xưng hô 'anh' ✓. Kiểm tra 5 thông tin: (1) ✓, (2) ✓, (3) ✓, (4) ✓, (5) ✗. Đạt 80% ≥ 85%? Không → FAILED"
verdict: "FAILED"
error_desc: "Response thiếu 1 thông tin quan trọng"
tone_note: "Giọng điệu tốt, có xưng hô" (hoặc để trống nếu không có vấn đề)
```

---

## 🔍 So sánh Output giữa các Tiêu chí

### Cùng một Response, 5 Tiêu chí khác nhau:

**Response:** "Cần CMND, sổ hộ khẩu, giấy xác nhận độc thân. Nộp tại UBND phường."
**Kỳ vọng:** "Cần CMND, sổ hộ khẩu, giấy xác nhận độc thân, lệ phí. Nộp tại UBND phường."
**Thời gian:** 2500ms

| Tiêu chí | Verdict | Lý do |
|----------|---------|-------|
| **Chuẩn** | PASSED | 4/5 = 80% ≥ 90%? Không... Sửa: 4/5 = 80% < 90% → FAILED |
| **Nghiêm ngặt** | FAILED | 4/5 = 80% < 95% + 2.5s > 2s + không xưng hô |
| **Tốc độ** | FAILED | 2.5s > 2s (quá chậm) |
| **Nội dung** | FAILED | 4/5 = 80% < 95% |
| **Trải nghiệm** | FAILED | Không xưng hô + 4/5 = 80% < 85% |

---

## 💡 Cách sử dụng

### 1. **Trong Code Python**

```python
from prompts.advanced_prompt import create_advanced_judge_prompt

# Tạo prompt cho tiêu chí "strict"
prompt = create_advanced_judge_prompt(
    question="Thủ tục đăng ký kết hôn cần gì?",
    expected="Cần CMND, sổ hộ khẩu, giấy xác nhận độc thân",
    actual="Cần CCCD, giấy đăng ký hộ khẩu, xác nhận chưa kết hôn",
    time_label="2000ms (Nhanh)",
    criteria="strict",  # ← Tiêu chí
    required_keywords="CMND,hộ khẩu",
    forbidden_keywords="bảo hiểm"
)

# Gửi prompt cho LLM
response = llm.invoke(prompt)
```

### 2. **Trong Judge Agent**

```python
from graphs.judge_agent import judge_agent

result = await judge_agent.judge_one(
    question="...",
    expected="...",
    actual="...",
    response_time_ms=2000,
    criteria="strict"  # ← Tiêu chí được chọn
)

print(result["verdict"])  # "PASSED" hoặc "FAILED"
print(result["reasoning"])  # Chi tiết suy luận
```

---

## 🎓 Ví dụ Chi tiết

### Scenario: Đánh giá Response về Thủ tục Đăng ký Kết Hôn

**Input:**
```
Câu hỏi: "Thủ tục đăng ký kết hôn cần gì?"
Kỳ vọng: "Cần CMND, sổ hộ khẩu, giấy xác nhận độc thân. Nộp tại UBND phường."
Thực tế: "Dạ, anh cần chuẩn bị CCCD, giấy đăng ký hộ khẩu, xác nhận chưa kết hôn. Nộp hồ sơ tại Ủy ban nhân dân cấp xã ạ."
Thời gian: 1500ms
Tiêu chí: "strict"
```

**Output (Tiêu chí Strict):**
```json
{
  "reasoning": "Kiểm tra 4 thông tin: (1) CMND=CCCD ✓, (2) Sổ hộ khẩu=Giấy đăng ký hộ khẩu ✓, (3) Xác nhận độc thân=Xác nhận chưa kết hôn ✓, (4) UBND phường=UBND cấp xã ✓. Đạt 4/4 (100%) ≥ 95% ✓. Thời gian 1500ms ≤ 2s ✓. Có xưng hô 'anh' ✓. Không vi phạm keywords ✓. → PASSED",
  "verdict": "PASSED",
  "confidence_level": 0.95,
  "needs_human_review": false,
  "error_desc": "",
  "suggestion": "",
  "tone_note": "",
  "time_verdict": "good"
}
```

**Output (Tiêu chí Chuẩn):**
```json
{
  "reasoning": "Kiểm tra 4 thông tin: (1) CMND=CCCD ✓, (2) Sổ hộ khẩu=Giấy đăng ký hộ khẩu ✓, (3) Xác nhận độc thân=Xác nhận chưa kết hôn ✓, (4) UBND phường=UBND cấp xã ✓. Đạt 4/4 (100%) ≥ 90% ✓. Giọng điệu lịch sự ✓. Không vi phạm keywords ✓. → PASSED",
  "verdict": "PASSED",
  "confidence_level": 0.95,
  "needs_human_review": false,
  "error_desc": "",
  "suggestion": "",
  "tone_note": "Có xưng hô 'anh' và lịch sự",
  "time_verdict": "good"
}
```

---

## 🚀 Lợi ích của Hệ thống Mới

✅ **Đánh giá linh hoạt** - Mỗi tiêu chí có quy tắc riêng
✅ **Output nhất quán** - LLM tuân theo hướng dẫn cụ thể
✅ **Dễ bảo trì** - Thay đổi tiêu chí chỉ cần sửa prompt
✅ **Rõ ràng cho user** - Biết chính xác tại sao PASSED/FAILED
✅ **Hỗ trợ nhiều use case** - Từ nội dung đến trải nghiệm

---

## 📝 Ghi chú

- Prompt được tối ưu hóa cho **GPT-4o-mini**
- Sử dụng **JSON response format** để đảm bảo output nhất quán
- Có **retry logic** với exponential backoff
- **Grounding requirement** để tránh hallucination
- **Few-shot examples** để hướng dẫn LLM

---

## 🔗 Liên kết

- `advanced_prompt.py` - Hệ thống prompt nâng cấp
- `judge_agent.py` - Agent sử dụng prompt
- `criteria_weights.py` - Cấu hình tiêu chí
