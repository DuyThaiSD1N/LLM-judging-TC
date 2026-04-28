# 🗄️ Database Setup Guide

## Tổng quan
Dự án sử dụng **MongoDB** để lưu trữ testcases và kết quả đánh giá.

---

## 🚀 Option 1: MongoDB Atlas (Cloud - Khuyến nghị cho Production)

### 1. Tạo tài khoản MongoDB Atlas

1. Vào [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Sign up miễn phí
3. Tạo cluster mới (chọn Free tier - M0)

### 2. Cấu hình Database

1. **Database Access:**
   - Tạo user mới
   - Username: `callbot_user`
   - Password: `your-secure-password`
   - Role: `Read and write to any database`

2. **Network Access:**
   - Add IP Address
   - Chọn `Allow access from anywhere` (0.0.0.0/0)
   - Hoặc chỉ định IP của Render.com

3. **Get Connection String:**
   - Click `Connect` → `Connect your application`
   - Copy connection string:
   ```
   mongodb+srv://callbot_user:<password>@cluster0.xxxxx.mongodb.net/callbot-testcase?retryWrites=true&w=majority
   ```

### 3. Cấu hình Environment Variables

**Local (.env):**
```env
MONGODB_URI=mongodb+srv://callbot_user:your-password@cluster0.xxxxx.mongodb.net/callbot-testcase?retryWrites=true&w=majority
```

**Render.com:**
1. Dashboard → Your Service → Environment
2. Add variable:
   - Key: `MONGODB_URI`
   - Value: `mongodb+srv://...`
3. Save Changes

---

## 🖥️ Option 2: Local MongoDB (Development)

### 1. Cài đặt MongoDB

**Windows:**
```bash
# Download từ mongodb.com/try/download/community
# Hoặc dùng Chocolatey
choco install mongodb
```

**Mac:**
```bash
brew tap mongodb/brew
brew install mongodb-community
```

**Linux:**
```bash
sudo apt-get install mongodb
```

### 2. Khởi động MongoDB

```bash
# Windows
mongod

# Mac/Linux
brew services start mongodb-community
# Hoặc
sudo systemctl start mongod
```

### 3. Cấu hình .env

```env
MONGODB_URI=mongodb://localhost:27017/callbot-testcase
```

---

## 🧪 Testing Connection

### Test với Node.js

```javascript
const mongoose = require('mongoose');

mongoose.connect('your-mongodb-uri')
  .then(() => console.log('✅ Connected'))
  .catch(err => console.error('❌ Error:', err));
```

### Test với MongoDB Compass

1. Download [MongoDB Compass](https://www.mongodb.com/products/compass)
2. Connect với URI
3. Browse collections

---

## 📊 Database Schema

### Collection: `testcases`

```javascript
{
  _id: ObjectId,
  code: String,           // Unique testcase code
  name: String,           // Testcase name
  group: String,          // A, B, C, D
  status: String,         // pending, running, done, error
  error: String,          // Error message if any
  turns: [
    {
      question: String,
      expected: String,
      actual: String,
      action: String,
      response_time_ms: Number,
      verdict: String,    // PASSED, FAILED, null
      error_desc: String,
      suggestion: String,
      tone_note: String,
      brevity_note: String,
      time_verdict: String, // good, ok, slow
      time_note: String
    }
  ],
  createdAt: Date,
  updatedAt: Date
}
```

---

## 🔧 API Endpoints

### GET /api/testcases
Lấy tất cả testcases

```bash
curl -H "X-API-Key: your-key" \
  https://your-app.onrender.com/api/testcases
```

### GET /api/testcases/:code
Lấy 1 testcase theo code

```bash
curl -H "X-API-Key: your-key" \
  https://your-app.onrender.com/api/testcases/TC-001
```

### POST /api/testcases
Tạo testcase mới

```bash
curl -X POST \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "TC-001",
    "name": "Test login",
    "group": "A",
    "turns": [
      {
        "question": "Làm sao để đăng nhập?",
        "expected": "Nhập username và password"
      }
    ]
  }' \
  https://your-app.onrender.com/api/testcases
```

### PUT /api/testcases/:code
Cập nhật testcase

```bash
curl -X PUT \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "done",
    "turns": [...]
  }' \
  https://your-app.onrender.com/api/testcases/TC-001
```

### DELETE /api/testcases/:code
Xóa 1 testcase

```bash
curl -X DELETE \
  -H "X-API-Key: your-key" \
  https://your-app.onrender.com/api/testcases/TC-001
```

### DELETE /api/testcases
Xóa tất cả testcases

```bash
curl -X DELETE \
  -H "X-API-Key: your-key" \
  https://your-app.onrender.com/api/testcases
```

---

## 🔍 Monitoring

### Check connection status

Server logs:
```
✅ MongoDB connected: callbot-testcase
```

### View data in MongoDB Compass

1. Connect to your database
2. Browse `testcases` collection
3. View/edit documents

---

## 🚨 Troubleshooting

### Lỗi: "MongoNetworkError"
- Check internet connection
- Check MongoDB Atlas IP whitelist
- Check connection string

### Lỗi: "Authentication failed"
- Check username/password
- Check user permissions in MongoDB Atlas

### Lỗi: "Connection timeout"
- Check firewall
- Check MongoDB service is running (local)
- Check network access (Atlas)

### App chạy mà không có database
Server sẽ log:
```
⚠️  Running without database - data will not persist
```
Data sẽ lưu trong memory, mất khi restart.

---

## 📈 Performance Tips

### 1. Indexes
```javascript
// Tự động tạo index cho code field (unique)
TestcaseSchema.index({ code: 1 }, { unique: true });

// Thêm index cho queries thường dùng
TestcaseSchema.index({ group: 1, status: 1 });
TestcaseSchema.index({ createdAt: -1 });
```

### 2. Pagination
```javascript
// GET /api/testcases?page=1&limit=20
const page = parseInt(req.query.page) || 1;
const limit = parseInt(req.query.limit) || 20;
const skip = (page - 1) * limit;

const testcases = await Testcase.find()
  .skip(skip)
  .limit(limit)
  .sort({ createdAt: -1 });
```

### 3. Projection
```javascript
// Chỉ lấy fields cần thiết
const testcases = await Testcase.find()
  .select('code name group status')
  .lean(); // Convert to plain JS object (faster)
```

---

## 🔄 Backup & Restore

### Backup
```bash
# MongoDB Atlas: Automatic backups
# Local:
mongodump --uri="mongodb://localhost:27017/callbot-testcase" --out=./backup
```

### Restore
```bash
mongorestore --uri="mongodb://localhost:27017/callbot-testcase" ./backup
```

---

## 📝 Checklist

- [ ] MongoDB Atlas account created (hoặc local MongoDB installed)
- [ ] Database user created
- [ ] IP whitelist configured
- [ ] Connection string copied
- [ ] `MONGODB_URI` set in .env
- [ ] `MONGODB_URI` set in Render environment variables
- [ ] Server restarted
- [ ] Connection successful (check logs)
- [ ] Test CRUD operations

---

## 🎯 Next Steps

1. **Backup strategy** - Schedule automatic backups
2. **Monitoring** - Setup alerts for connection issues
3. **Scaling** - Upgrade cluster when needed
4. **Security** - Rotate credentials regularly
