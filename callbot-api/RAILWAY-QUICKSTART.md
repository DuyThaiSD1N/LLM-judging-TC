# 🚂 Railway Deploy - Quick Start

## ✅ Checklist trước khi deploy

- [ ] File `package.json` có ở root folder `callbot-api/`
- [ ] File `.env` có `OPENAI_API_KEY`
- [ ] Code đã commit và push lên GitHub

## 🎯 Deploy trong 5 phút

### Bước 1: Push code lên GitHub
```bash
cd callbot-api
git init
git add .
git commit -m "Ready for Railway"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### Bước 2: Deploy trên Railway
1. Vào https://railway.app
2. Login bằng GitHub
3. Click **"New Project"** → **"Deploy from GitHub repo"**
4. Chọn repo của bạn
5. Đợi Railway build (2-3 phút)

### Bước 3: Set Environment Variables
1. Click vào project
2. Tab **"Variables"**
3. Add:
   ```
   OPENAI_API_KEY=sk-proj-your-key-here
   ```
4. Railway sẽ tự động redeploy

### Bước 4: Lấy URL
1. Tab **"Settings"** → **"Networking"**
2. Click **"Generate Domain"**
3. Copy URL (vd: `https://callbot-api-production.up.railway.app`)

### Bước 5: Test
```bash
curl https://your-app.railway.app/health
# Kết quả: {"status":"ok","timestamp":"..."}
```

### Bước 6: Cập nhật Frontend
Sửa `testcase-form/js/runner.js`:
```javascript
const RUN_ALL_URL = 'https://your-app.railway.app/api/run-testcases';
const RUN_SINGLE_URL = 'https://your-app.railway.app/api/run-single';
```

## 🐛 Troubleshooting

### Lỗi: "Could not determine how to build"
**Nguyên nhân:** Railway không tìm thấy `package.json`

**Giải pháp:**
1. Đảm bảo `package.json` ở root của repo
2. Hoặc set Root Directory trong Railway Settings:
   - Settings → Root Directory → `callbot-api`

### Lỗi: "Application failed to respond"
**Nguyên nhân:** Server không listen đúng port

**Giải pháp:**
- Railway tự động set biến `PORT`
- Code đã có: `const PORT = process.env.PORT || 8099`
- Xem logs: Deployments → View Logs

### Lỗi: "Module not found"
**Nguyên nhân:** Dependencies chưa cài đúng

**Giải pháp:**
```bash
# Test local trước
cd callbot-api
npm install
npm start
```

## 📊 Xem Logs
Railway Dashboard → Deployments → Click deployment mới nhất → **View Logs**

## 💡 Tips
- Railway auto-deploy khi push code mới
- Free tier: $5 credit/tháng
- Nếu hết credit, thêm payment method
