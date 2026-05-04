# Callbot Testcase Runner v2.0

Hệ thống tự động chạy và đánh giá testcase cho chatbot hành chính công sử dụng LLM Judge (GPT-4o-mini).

## 🚀 Quick Start

### 1. Cài đặt
```bash
cd callbot-api
pip install -r requirements.txt
```

### 2. Cấu hình .env
```env
OPENAI_API_KEY=your-openai-key
LANGCHAIN_API_KEY=your-langsmith-key  # Optional
PORT=8099
```

### 3. Chạy server
```bash
python main.py
```

### 4. Truy cập
- **Frontend**: http://localhost:8099
- **API Docs**: http://localhost:8099/docs
- **LangSmith**: https://smith.langchain.com/

---

## 📊 Stack công nghệ

| Layer | Technology |
|-------|-----------|
| Frontend | HTML + CSS + JavaScript |
| Backend | Python + FastAPI |
| LLM | LangChain + LangGraph + OpenAI GPT-4o-mini |
| Monitor | LangSmith |
| Database | SQLite |

---

## 🎯 Tính năng

- ✅ **5 tiêu chí đánh giá LLM**: Standard, Strict, Flexible, Content-Only, UX-Focused
- ✅ **Multi-turn conversation**: Hỗ trợ nhiều lượt hội thoại
- ✅ **LangGraph workflow**: State machine tự động (warmup → run → judge → save)
- ✅ **LangSmith tracing**: Monitor & debug LLM calls
- ✅ **Excel import/export**: Import testcases và export kết quả với styling
- ✅ **Real-time tracking**: Spinner animation khi đang chạy
- ✅ **History & Stats**: Lịch sử và thống kê chi tiết

---

## 📁 Cấu trúc dự án

```
callbot-api/
├── main.py                 # FastAPI entry point (chạy từ đây!)
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── .env.example            # Template cho .env
├── .gitignore              # Git ignore (đã cập nhật)
├── README.md               # Documentation
├── render.yaml             # Render.com deployment config
│
├── data/                   # Database
│   └── testcases.db        # SQLite database
│
├── python-server/          # Backend modules
│   ├── config/             # Cấu hình (criteria, database)
│   ├── models/             # Pydantic schemas + CRUD
│   ├── prompts/            # LangChain prompts (5 criteria)
│   ├── graphs/             # LangGraph workflows
│   └── routers/            # FastAPI routes
│
└── testcase-form/          # Frontend
    ├── index.html
    ├── css/style.css
    └── js/*.js             # ES6 modules
```

---

## 🎓 LLM Judge - 5 Tiêu chí

| Tiêu chí | Content | Tone | Time | Ngưỡng PASSED | Đặc điểm |
|----------|---------|------|------|---------------|----------|
| **Standard** | 50% | 30% | 20% | ≥70 | Cân bằng, phù hợp chung |
| **Strict** | 40% | 40% | 20% | ≥85 | Nghiêm ngặt, yêu cầu cao |
| **Flexible** | 60% | 20% | 20% | ≥60 | Khoan dung, dễ pass |
| **Content-Only** | 80% | 0% | 20% | ≥70 | Chỉ đánh giá nội dung |
| **UX-Focused** | 30% | 50% | 20% | ≥70 | Ưu tiên trải nghiệm |

---

## 📊 API Endpoints

### Run Testcases
- `POST /api/run-testcases` - Chạy nhiều testcases
- `POST /api/run-single` - Chạy 1 testcase
- `GET /api/criteria` - Lấy danh sách tiêu chí

### Testcase CRUD
- `GET /api/testcases` - Lấy tất cả testcases
- `POST /api/testcases` - Tạo testcase mới
- `DELETE /api/testcases/:code` - Xóa testcase
- `DELETE /api/testcases` - Xóa tất cả

### History
- `GET /api/history` - Lịch sử gần nhất
- `GET /api/history/stats` - Thống kê
- `GET /api/history/:code` - Lịch sử theo testcase
- `DELETE /api/history/cleanup` - Xóa lịch sử cũ

### Upload/Export
- `POST /api/upload-excel` - Import từ Excel
- `GET /api/template` - Download template Excel
- `POST /api/export` - Export kết quả ra Excel

---

## 🔧 Troubleshooting

### Server không chạy
```bash
cd callbot-api
python main.py
```

### Thiếu dependencies
```bash
pip install -r requirements.txt
```

### Database error
Database tự động tạo tại `callbot-api/data/testcases.db`

### LangSmith không có traces
1. Kiểm tra `LANGCHAIN_API_KEY` trong `.env`
2. Chạy một testcase để tạo traces
3. Refresh trang LangSmith

---

## 🚀 Deploy lên Render.com

### 1. Chuẩn bị
File `render.yaml` đã có sẵn trong project.

### 2. Deploy
1. Push code lên GitHub
2. Vào [render.com](https://render.com) → New → Web Service
3. Connect GitHub repository
4. Render tự động detect `render.yaml`
5. Thêm Environment Variables:
   - `OPENAI_API_KEY`
   - `LANGCHAIN_API_KEY` (optional)

### 3. Lưu ý Free Tier
- Sleep sau 15 phút không dùng
- Request đầu tiên sau sleep mất ~30s wake up
- Upgrade $7/tháng để không sleep

---

## 🎉 Highlights

- 🚀 **Modern Stack**: Python + LangChain + LangGraph + LangSmith
- 🤖 **LLM Judge**: GPT-4o-mini với structured output (Pydantic)
- 📊 **Tracing**: LangSmith monitoring cho mỗi LLM call
- 🔄 **State Machine**: LangGraph workflow tự động
- 📈 **Type Safe**: Pydantic models validation
- ⚡ **Async**: Native async/await support
- 🎨 **Modern UI**: Responsive design với spinner animation

---

**Made with ❤️ using LangChain + LangGraph + LangSmith**
