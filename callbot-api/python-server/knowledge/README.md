# Knowledge Base Module

## 📚 Tổng quan

Module này cung cấp knowledge base từ `main_data.json` để hỗ trợ LLM đánh giá response chính xác hơn.

## 🎯 Chức năng

### 1. Load Knowledge Base
```python
from knowledge import get_knowledge_base

kb = get_knowledge_base()
print(f"Loaded: {len(kb.procedures)} procedures, {len(kb.faqs)} FAQs")
```

### 2. Search Relevant Knowledge
```python
from knowledge import search_relevant_knowledge

question = "Đăng ký kết hôn cần giấy tờ gì?"
knowledge_text = search_relevant_knowledge(question, top_k=3)
print(knowledge_text)
```

### 3. Get Specific Procedure/FAQ
```python
kb = get_knowledge_base()

# Get by ID
procedure = kb.get_procedure_by_id(558)
faq = kb.get_faq_by_id(123)

# Format for prompt
formatted = kb.format_procedure_for_prompt(procedure)
```

## 🔧 Cách hoạt động

### Search Algorithm
1. **Keyword Extraction**: Trích xuất keywords từ câu hỏi
2. **Relevance Scoring**: Tính điểm liên quan dựa trên:
   - Keyword matching (70%)
   - Exact phrase matching (30%)
   - Pre-computed semantic similarity (nếu có)
3. **Ranking**: Sắp xếp theo điểm và trả về top-k

### Integration với LLM Judge

Khi `inject_knowledge=True` (default), prompt sẽ tự động thêm:

```
═══════════════════════════════════════════════════════════
KNOWLEDGE BASE - THÔNG TIN THAM KHẢO
═══════════════════════════════════════════════════════════

📋 **Thủ tục: Đăng ký kết hôn**

**Yêu cầu điều kiện:**
- Nam từ đủ 20 tuổi, nữ từ đủ 18 tuổi
- Tự nguyện kết hôn
- ...

**Thời hạn giải quyết:**
05 ngày làm việc

**Phí, lệ phí:**
Miễn phí với công dân Việt Nam thường trú trong nước
...
```

LLM sẽ dùng thông tin này để:
- ✅ Đối chiếu xem response có đầy đủ thông tin không
- ✅ Kiểm tra tính chính xác (thời hạn, phí, điều kiện...)
- ✅ Gợi ý bổ sung thông tin còn thiếu

## 📊 Data Structure

### main_data.json
```json
{
  "metadata": {
    "total_selected": 570,
    "sources": {
      "featured_procedures": "46/50",
      "national_procedures": "318/1993",
      "citizen_faq": "206/1133"
    }
  },
  "procedures": [
    {
      "id": 558,
      "name": "Thủ tục đăng ký khai sinh...",
      "content": {
        "Tên thủ tục": "...",
        "Yêu cầu điều kiện": "...",
        "Thời hạn giải quyết": "...",
        "Lệ phí": "..."
      },
      "semantic_score": {
        "max_similarity": 0.8299
      }
    }
  ],
  "citizen_faq": [
    {
      "id": 1,
      "question": "...",
      "answer": "...",
      "category": "..."
    }
  ]
}
```

## 🚀 Performance

- **Load time**: ~1-2 giây (chỉ load 1 lần khi khởi động)
- **Search time**: <50ms (keyword matching)
- **Memory**: ~50MB (570 procedures + 206 FAQs)

## 🔄 Update Knowledge Base

Để update knowledge base:

1. Thay thế file `data/main_data.json`
2. Restart server (hoặc reload module)
3. Knowledge base sẽ tự động load lại

## 📝 Example Usage

### Trong testcase runner:

```python
from prompts.simple_prompt import create_simple_judge_prompt

prompt = create_simple_judge_prompt(
    question="Đăng ký kết hôn cần giấy tờ gì?",
    expected="Cần CMND, giấy xác nhận độc thân",
    actual="Cần CMND",
    time_label="2000ms",
    inject_knowledge=True  # ← Enable knowledge injection
)
```

LLM sẽ nhận được:
- Câu hỏi, kỳ vọng, thực tế
- **+ Top 2-3 thủ tục liên quan từ knowledge base**
- → Đánh giá chính xác hơn!

## ⚙️ Configuration

### Disable Knowledge Injection

Nếu muốn tắt knowledge injection:

```python
prompt = create_simple_judge_prompt(
    ...,
    inject_knowledge=False
)
```

### Adjust Search Parameters

```python
from knowledge import get_knowledge_base

kb = get_knowledge_base()
results = kb.search_by_question(
    question="...",
    top_k=5,  # Số lượng kết quả
    min_similarity=0.3  # Ngưỡng tối thiểu
)
```

## 🐛 Troubleshooting

### Knowledge base không load được

```
❌ Failed to load knowledge base: [Errno 2] No such file or directory
```

**Giải pháp:**
- Kiểm tra file `python-server/data/main_data.json` có tồn tại không
- Kiểm tra quyền đọc file

### Search không trả về kết quả

```python
results = kb.search_by_question("test", top_k=3)
# results = []
```

**Nguyên nhân:**
- Câu hỏi quá ngắn hoặc không liên quan
- Threshold quá cao

**Giải pháp:**
- Giảm `min_similarity` xuống 0.3-0.4
- Tăng `top_k` lên 5-10

## 📈 Future Improvements

- [ ] Vector search với embeddings (thay vì keyword matching)
- [ ] Cache search results
- [ ] Support multiple languages
- [ ] Auto-update from API
- [ ] Fuzzy matching cho typos
