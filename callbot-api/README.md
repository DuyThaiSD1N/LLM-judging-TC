# Callbot Testcase Server

Server để chạy và đánh giá testcase cho callbot hành chính công.

## Deploy lên Railway

### Bước 1: Chuẩn bị
1. Tạo tài khoản tại [railway.app](https://railway.app)
2. Cài đặt Git và push code lên GitHub (nếu chưa có)

### Bước 2: Deploy
1. Đăng nhập Railway
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Chọn repository của bạn
4. Railway sẽ tự động detect và deploy

### Bước 3: Cấu hình biến môi trường
1. Vào project trên Railway
2. Click tab **"Variables"**
3. Thêm các biến sau:
   ```
   OPENAI_API_KEY=sk-your-openai-key-here
   PORT=8099
   ```

### Bước 4: Lấy URL
- Railway sẽ tự động tạo domain: `https://your-app.railway.app`
- Hoặc vào **Settings** → **Generate Domain** để tạo domain mới

### Bước 5: Cập nhật URL trong frontend
Sửa file `testcase-form/js/runner.js`:
```javascript
const RUN_ALL_URL = 'https://your-app.railway.app/api/run-testcases';
const RUN_SINGLE_URL = 'https://your-app.railway.app/api/run-single';
```

## Chạy local
```bash
cd server
npm install
npm start
```

Server chạy tại: http://localhost:8099
