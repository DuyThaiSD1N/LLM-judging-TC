# Thay đổi hệ thống đánh giá Chatbot

## Tóm tắt thay đổi

### 1. **Xóa hệ thống chấm điểm (Scoring System)**
- ❌ Xóa: `content_score`, `tone_score`, `time_score`, `total_score`
- ❌ Xóa: Trọng số (weights) và ngưỡng (threshold)
- ✅ Thay bằng: **LLM tự đánh giá** trực tiếp PASSED/FAILED

### 2. **Thay "Flexible" thành "Speed-Focused"**
- ❌ Xóa: Tiêu chí "flexible" (Linh hoạt)
- ✅ Thêm: Tiêu chí "speed-focused" (Tốc độ)
- 🎯 Mục đích: Đánh giá ưu tiên thời gian phản hồi nhanh

---

## Chi tiết thay đổi

### Backend (Python)

#### 1. **models/schemas.py**
```python
# TRƯỚC (13 trường):
class JudgeResult(BaseModel):
    total_score: float
    content_score: float
    tone_score: float
    time_score: float
    confidence_level: float
    needs_human_review: bool
    confidence_reason: str
    errors: List[ErrorDetail]
    verdict: Literal["PASSED", "FAILED"]
    error_desc: str
    suggestion: str
    suggested_response: str
    tone_note: str
    time_verdict: Literal["good", "ok", "slow"]
    time_note: str

# SAU (10 trường - xóa 4 trường scoring):
class JudgeResult(BaseModel):
    verdict: Literal["PASSED", "FAILED"]
    confidence_level: float
    needs_human_review: bool
    confidence_reason: str
    errors: List[ErrorDetail]
    error_desc: str
    suggestion: str
    suggested_response: str
    tone_note: str
    time_verdict: Literal["good", "ok", "slow"]
    time_note: str
```

#### 2. **config/criteria_weights.py**
```python
# TRƯỚC: Có trọng số và ngưỡng
CRITERIA_CONFIG = {
    "standard": CriteriaConfig(
        weights=CriteriaWeights(content=0.5, tone=0.3, time=0.2),
        threshold=70,
        description="..."
    ),
    "flexible": CriteriaConfig(...)
}

# SAU: Chỉ có description
CRITERIA_CONFIG = {
    "standard": CriteriaConfig(
        description="Cân bằng: nội dung đúng đủ, giọng điệu tự nhiên, thời gian hợp lý"
    ),
    "speed-focused": CriteriaConfig(
        description="Tốc độ: ưu tiên thời gian phản hồi nhanh, nội dung đủ tốt"
    )
}
```

#### 3. **graphs/judge_agent.py**
```python
# TRƯỚC: Tính toán điểm số
content_score = result.get("content_score", 0)
tone_score = result.get("tone_score", 0)
time_score = result.get("time_score", 0)
total_score = calculate_total_score(criteria, content_score, tone_score, time_score)
verdict = determine_verdict(criteria, total_score)

# SAU: LLM tự quyết định verdict
verdict = result.get("verdict", "FAILED")
```

#### 4. **prompts/prompt_factory.py**
```python
# TRƯỚC: Prompt có scoring rubric
"""
**Content Score (0-100):**
• 100: 100% thông tin kỳ vọng + 100% chính xác
• 80-99: 100% thông tin nhưng có chi tiết nhỏ không chính xác
...

**Total Score = content_score × 0.5 + tone_score × 0.3 + time_score × 0.2**
**PASSED nếu total_score ≥ 70, FAILED nếu < 70**
"""

# SAU: Prompt không có scoring, LLM tự đánh giá
"""
## ĐÁNH GIÁ (LLM tự quyết định PASSED/FAILED)

Phân tích các khía cạnh sau và tự quyết định PASSED hoặc FAILED:

**1. Nội dung (Content):**
- Có đầy đủ thông tin kỳ vọng không?
- Thông tin có chính xác không?

**2. Giọng điệu (Tone):**
- Có xưng hô phù hợp không?
- Có dùng dạ/ạ không?

**Quyết định PASSED/FAILED:**
- PASSED: Nội dung đúng đủ (≥80%), giọng điệu tự nhiên
- FAILED: Thiếu thông tin quan trọng, giọng điệu kém
"""
```

### Frontend (HTML/JS)

#### 1. **index.html**
```html
<!-- TRƯỚC -->
<option value="flexible">Linh hoạt</option>

<!-- SAU -->
<option value="speed-focused">Tốc độ</option>
```

#### 2. **js/table.js**
```javascript
// TRƯỚC
'flexible': 'Linh hoạt'

// SAU
'speed-focused': 'Tốc độ'
```

---

## 5 Tiêu chí đánh giá mới

| Tiêu chí | Mô tả | Ưu tiên |
|----------|-------|---------|
| **standard** | Cân bằng: nội dung đúng đủ, giọng điệu tự nhiên, thời gian hợp lý | Nội dung + Tone + Time |
| **strict** | Nghiêm ngặt: yêu cầu cao về nội dung, giọng điệu, và thời gian | Tất cả phải hoàn hảo |
| **speed-focused** | Tốc độ: ưu tiên thời gian phản hồi nhanh, nội dung đủ tốt | **Time > Content > Tone** |
| **content-only** | Chỉ nội dung: đánh giá độ chính xác thông tin, bỏ qua giọng điệu | **Content only** |
| **ux-focused** | Trải nghiệm: ưu tiên giọng điệu thân thiện, tự nhiên | **Tone > Content** |

---

## Tiêu chí "Speed-Focused" chi tiết

### Quy tắc đánh giá:
```
1. Thời gian phản hồi (QUAN TRỌNG NHẤT):
   - ≤1.5s: Xuất sắc → PASSED (nếu nội dung ≥70%)
   - ≤2s: Rất tốt → PASSED (nếu nội dung ≥70%)
   - ≤3s: Chấp nhận được → PASSED (nếu nội dung ≥80%)
   - >3s: Chậm → Khó PASSED (cần nội dung ≥90%)

2. Nội dung (Chỉ cần đủ tốt):
   - ≥70% thông tin quan trọng là chấp nhận được
   - Không cần 100% hoàn hảo
   - Ưu tiên trả lời nhanh hơn là chi tiết

3. Giọng điệu (Không quan trọng):
   - Có xưng hô hoặc dạ/ạ là được
   - Chấp nhận hơi máy móc
```

### Quyết định PASSED/FAILED:
- ✅ **PASSED**: Thời gian nhanh (≤2s) + nội dung đủ tốt (≥70%)
- ❌ **FAILED**: Thời gian chậm (>3s) hoặc nội dung quá thiếu (<70%)

---

## Lợi ích của thay đổi

### 1. **Đơn giản hóa**
- Không cần tính toán điểm số phức tạp
- LLM tự đánh giá dựa trên phân tích định tính
- Dễ hiểu và dễ bảo trì

### 2. **Linh hoạt hơn**
- LLM có thể xem xét nhiều yếu tố phức tạp
- Không bị giới hạn bởi công thức cứng nhắc
- Phù hợp với các trường hợp edge case

### 3. **Tập trung vào tốc độ**
- Tiêu chí "speed-focused" giúp đánh giá chatbot nhanh
- Phù hợp với yêu cầu thực tế: người dùng muốn phản hồi nhanh

---

## Cách sử dụng

### 1. Chạy server
```bash
cd callbot-api
python main.py
```

### 2. Truy cập
- Frontend: http://localhost:8099
- API Docs: http://localhost:8099/docs

### 3. Chọn tiêu chí đánh giá
- **Standard**: Đánh giá cân bằng (mặc định)
- **Strict**: Yêu cầu cao
- **Speed-Focused**: Ưu tiên tốc độ ⚡ (MỚI)
- **Content-Only**: Chỉ nội dung
- **UX-Focused**: Ưu tiên trải nghiệm

---

## Migration Guide

### Nếu bạn có testcase cũ với "flexible":
1. Mở file Excel testcase
2. Tìm cột "LLM Judge"
3. Thay "flexible" → "speed-focused"
4. Import lại vào hệ thống

### Nếu bạn có code tích hợp API:
```python
# TRƯỚC
response = {
    "verdict": "PASSED",
    "total_score": 75,
    "content_score": 80,
    "tone_score": 70,
    "time_score": 100
}

# SAU
response = {
    "verdict": "PASSED",
    "confidence_level": 0.85,
    "needs_human_review": False
}
```

---

**Ngày thay đổi**: 2026-05-04
**Phiên bản**: 3.0.0
