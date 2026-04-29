# SQLite Database Setup

## Tổng quan

Ứng dụng sử dụng **SQLite** để lưu trữ:
- ✅ Testcases (mã, tên, nhóm, câu hỏi/đáp)
- ✅ Lịch sử chạy testcase (kết quả, thời gian, verdict)
- ✅ Thống kê (tỷ lệ pass, thời gian trung bình)

## Ưu điểm SQLite

- 📦 **Không cần server riêng** - database là 1 file duy nhất
- 🚀 **Nhanh và nhẹ** - phù hợp cho ứng dụng nhỏ/vừa
- 💾 **Dữ liệu persistent** - không mất khi restart server
- 🔧 **Dễ backup** - chỉ cần copy file `.db`
- ✅ **Hoạt động trên Render.com** - không cần config thêm

## Cấu trúc Database

### Bảng `testcases`
```sql
CREATE TABLE testcases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    group_type TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### Bảng `turns`
```sql
CREATE TABLE turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    testcase_id INTEGER NOT NULL,
    turn_number INTEGER NOT NULL,
    question TEXT NOT NULL,
    expected TEXT NOT NULL,
    FOREIGN KEY (testcase_id) REFERENCES testcases(id) ON DELETE CASCADE
)
```

### Bảng `history`
```sql
CREATE TABLE history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    testcase_id INTEGER NOT NULL,
    turn_number INTEGER NOT NULL,
    question TEXT NOT NULL,
    expected TEXT NOT NULL,
    actual TEXT,
    action TEXT,
    response_time_ms INTEGER,
    verdict TEXT,
    error_desc TEXT,
    suggestion TEXT,
    tone_note TEXT,
    brevity_note TEXT,
    time_verdict TEXT,
    time_note TEXT,
    error TEXT,
    run_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (testcase_id) REFERENCES testcases(id) ON DELETE CASCADE
)
```

## File Database

- **Location**: `callbot-api/data/testcases.db`
- **WAL files**: `testcases.db-shm`, `testcases.db-wal` (tự động tạo)
- **Gitignore**: Đã thêm vào `.gitignore` để không commit database

## API Endpoints

### Testcases
- `GET /api/testcases` - Lấy tất cả testcases
- `POST /api/testcases` - Tạo testcase mới
- `DELETE /api/testcases/:code` - Xóa testcase
- `DELETE /api/testcases` - Xóa tất cả

### History
- `GET /api/history` - Lấy lịch sử gần nhất (limit=50)
- `GET /api/history/stats` - Thống kê tổng quan
- `GET /api/history/:code` - Lịch sử theo testcase
- `DELETE /api/history/cleanup?days=30` - Xóa lịch sử cũ

## Backup & Restore

### Backup
```bash
# Copy database file
cp callbot-api/data/testcases.db backup-$(date +%Y%m%d).db
```

### Restore
```bash
# Restore from backup
cp backup-20260428.db callbot-api/data/testcases.db
```

### Export to SQL
```bash
# Install sqlite3 CLI
sqlite3 callbot-api/data/testcases.db .dump > backup.sql
```

### Import from SQL
```bash
sqlite3 callbot-api/data/testcases.db < backup.sql
```

## Xem Database

### Sử dụng SQLite CLI
```bash
# Mở database
sqlite3 callbot-api/data/testcases.db

# Xem tables
.tables

# Xem schema
.schema testcases

# Query
SELECT * FROM testcases LIMIT 10;

# Thoát
.quit
```

### Sử dụng GUI Tools
- **DB Browser for SQLite**: https://sqlitebrowser.org/
- **DBeaver**: https://dbeaver.io/
- **VS Code Extension**: SQLite Viewer

## Maintenance

### Cleanup old history (giữ 30 ngày)
```bash
curl -X DELETE "http://localhost:8099/api/history/cleanup?days=30"
```

### Vacuum database (tối ưu dung lượng)
```bash
sqlite3 callbot-api/data/testcases.db "VACUUM;"
```

## Troubleshooting

### Database locked
- Đóng tất cả connections
- Xóa file `.db-shm` và `.db-wal`
- Restart server

### Corrupt database
```bash
# Dump và rebuild
sqlite3 callbot-api/data/testcases.db .dump > dump.sql
rm callbot-api/data/testcases.db
sqlite3 callbot-api/data/testcases.db < dump.sql
```

## Deploy trên Render.com

✅ SQLite hoạt động tốt trên Render
⚠️ **Lưu ý**: Render free tier có thể xóa data khi sleep/restart

### Giải pháp cho production:
1. **Backup định kỳ** - Tự động backup database ra external storage
2. **Upgrade Render plan** - Persistent disk không bị xóa
3. **Chuyển sang PostgreSQL** - Nếu cần scale lớn hơn

## Performance Tips

- ✅ WAL mode đã enabled (tốc độ ghi nhanh hơn)
- ✅ Indexes đã tạo cho các query thường dùng
- ✅ Foreign keys với CASCADE delete
- ✅ Prepared statements để tránh SQL injection

## Migration từ In-Memory

Dữ liệu cũ (in-memory) sẽ **không tự động migrate**.
Nếu cần giữ data cũ, export ra Excel trước khi deploy.
