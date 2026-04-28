# Callbot Testcase Server

Server để chạy và đánh giá testcase cho callbot hành chính công.

## 🚀 Deploy lên Render.com

### Bước 1: Push code lên GitHub
```bash
cd callbot-api
git init
git add .
git commit -m "Ready for Render"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### Bước 2: Deploy trên Render
1. Vào [render.com](https://render.com) → Sign up (dùng GitHub)
2. Click **"New +"** → **"Web Service"**
3. Connect GitHub repository của bạn
4. Cấu hình:
   - **Name:** `callbot-api`
   - **Region:** Singapore (gần VN nhất)
   - **Branch:** `main`
   - **Root Directory:** `callbot-api` (nếu repo có nhiều folder)
   - **Runtime:** Node
   - **Build Command:** `npm install`
   - **Start Command:** `npm start`
   - **Instance Type:** Free

### Bước 3: Thêm Environment Variables
Trong trang setup, scroll xuống **Environment Variables**:
- Click **"Add Environment Variable"**
- Key: `OPENAI_API_KEY`
- Value: `sk-proj-your-actual-key`

### Bước 4: Deploy
- Click **"Create Web Service"**
- Đợi 3-5 phút để Render build và deploy
- URL sẽ có dạng: `https://callbot-api.onrender.com`

### Bước 5: Test
```bash
curl https://callbot-api.onrender.com/health
```

### Bước 6: Cập nhật Frontend
Sửa `testcase-form/js/runner.js`:
```javascript
const RUN_ALL_URL = 'https://callbot-api.onrender.com/api/run-testcases';
const RUN_SINGLE_URL = 'https://callbot-api.onrender.com/api/run-single';
```

## ⚠️ Lưu ý Render Free Tier
- Free tier sẽ **sleep sau 15 phút không dùng**
- Request đầu tiên sau khi sleep sẽ mất ~30s để wake up
- Giải pháp: Dùng cron job ping mỗi 10 phút (hoặc upgrade $7/tháng)

## 🔄 Auto Deploy
Render tự động deploy khi bạn push code mới lên GitHub:
```bash
git add .
git commit -m "Update feature"
git push
# Render sẽ tự động deploy!
```

## 📊 Xem Logs
Render Dashboard → Your Service → **Logs** tab

## 💰 Chi phí
- **Free tier:** Miễn phí mãi mãi
- **Paid tier:** $7/tháng (không sleep, tốc độ nhanh hơn)

## 🐛 Troubleshooting

### Service sleep quá lâu
→ Upgrade lên paid tier hoặc dùng cron job ping

### Build failed
→ Xem logs trong Render dashboard

### CORS error
→ Server đã config `cors({ origin: '*' })`

## 🌐 Custom Domain (Optional)
Render Dashboard → Settings → Custom Domain → Add your domain

