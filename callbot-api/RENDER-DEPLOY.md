# 🎨 Deploy lên Render.com - Hướng dẫn chi tiết

## ✅ Ưu điểm Render.com
- ✅ Free tier mãi mãi (không giới hạn thời gian)
- ✅ Không cần credit card
- ✅ Auto deploy từ GitHub
- ✅ SSL certificate miễn phí
- ✅ Dễ dùng hơn Railway

## 📋 Các bước deploy

### Bước 1: Chuẩn bị GitHub Repository

```bash
# Di chuyển vào thư mục
cd callbot-api

# Khởi tạo git (nếu chưa có)
git init

# Add tất cả files
git add .

# Commit
git commit -m "Deploy to Render"

# Tạo repo trên GitHub, sau đó:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### Bước 2: Đăng ký Render.com

1. Vào [render.com](https://render.com)
2. Click **"Get Started for Free"**
3. Sign up bằng **GitHub** (khuyến nghị)
4. Authorize Render truy cập GitHub repos

### Bước 3: Tạo Web Service

1. Sau khi đăng nhập, click **"New +"** (góc trên phải)
2. Chọn **"Web Service"**
3. Click **"Connect a repository"**
4. Chọn repository của bạn (nếu không thấy, click "Configure account" để grant access)

### Bước 4: Cấu hình Service

Điền thông tin sau:

**Basic Settings:**
- **Name:** `callbot-api` (hoặc tên bạn muốn)
- **Region:** `Singapore` (gần VN nhất, tốc độ nhanh)
- **Branch:** `main`
- **Root Directory:** `callbot-api` (nếu repo có nhiều folder, bỏ trống nếu callbot-api là root)

**Build & Deploy:**
- **Runtime:** `Node`
- **Build Command:** `npm install`
- **Start Command:** `npm start`

**Instance Type:**
- Chọn **"Free"** ($0/month)

### Bước 5: Thêm Environment Variables

Scroll xuống phần **Environment Variables**:

1. Click **"Add Environment Variable"**
2. Thêm:
   ```
   Key: OPENAI_API_KEY
   Value: sk-proj-your-actual-openai-key-here
   ```

3. (Optional) Thêm thêm:
   ```
   Key: NODE_ENV
   Value: production
   ```

### Bước 6: Deploy

1. Click **"Create Web Service"** (nút xanh ở cuối trang)
2. Render sẽ bắt đầu build:
   - Clone repo từ GitHub
   - Chạy `npm install`
   - Chạy `npm start`
3. Đợi 3-5 phút
4. Khi thấy **"Live"** màu xanh → Deploy thành công! 🎉

### Bước 7: Lấy URL

- URL sẽ hiển thị ở đầu trang, dạng: `https://callbot-api.onrender.com`
- Copy URL này

### Bước 8: Test API

```bash
# Thay YOUR_URL bằng URL Render vừa tạo
curl https://callbot-api.onrender.com/health
```

Kết quả mong đợi:
```json
{"status":"ok","timestamp":"2024-..."}
```

### Bước 9: Cập nhật Frontend

Sửa file `testcase-form/js/runner.js`:

```javascript
// Thay localhost bằng Render URL
const RUN_ALL_URL = 'https://callbot-api.onrender.com/api/run-testcases';
const RUN_SINGLE_URL = 'https://callbot-api.onrender.com/api/run-single';
```

Commit và push:
```bash
git add testcase-form/js/runner.js
git commit -m "Update API URL to Render"
git push
```

Render sẽ tự động deploy lại!

## 📊 Quản lý Service

### Xem Logs
1. Vào Render Dashboard
2. Click vào service `callbot-api`
3. Tab **"Logs"** → Xem logs real-time

### Xem Metrics
- Tab **"Metrics"** → CPU, Memory, Request count

### Manual Deploy
- Tab **"Manual Deploy"** → Click **"Deploy latest commit"**

### Restart Service
- Settings → **"Restart Service"**

## ⚠️ Lưu ý quan trọng về Free Tier

### Service sẽ sleep sau 15 phút không hoạt động
- Request đầu tiên sau khi sleep mất ~30-50 giây để wake up
- Các request sau đó sẽ nhanh bình thường

### Giải pháp để service không sleep:

#### Option 1: Dùng Cron Job (Free)
Tạo cron job ping service mỗi 10 phút:

1. Vào [cron-job.org](https://cron-job.org) (free)
2. Tạo job:
   - URL: `https://callbot-api.onrender.com/health`
   - Interval: Every 10 minutes
   - Method: GET

#### Option 2: Upgrade lên Paid ($7/tháng)
- Không sleep
- Tốc độ nhanh hơn
- Nhiều resources hơn

## 🔄 Auto Deploy từ GitHub

Render tự động deploy khi bạn push code:

```bash
# Sửa code
# ...

# Commit và push
git add .
git commit -m "Update feature"
git push origin main

# Render tự động detect và deploy!
```

Xem tiến trình deploy trong Dashboard → Logs

## 🐛 Troubleshooting

### Build failed: "Cannot find module"
**Nguyên nhân:** Dependencies chưa đúng

**Giải pháp:**
```bash
# Test local trước
cd callbot-api
npm install
npm start
```

### Service không start: "Application failed to respond"
**Nguyên nhân:** Server không listen đúng port

**Giải pháp:** Code đã có `const PORT = process.env.PORT || 8099`
Render tự động set PORT, không cần config thêm.

### CORS error từ frontend
**Giải pháp:** Server đã config:
```javascript
app.use(cors({ origin: '*' }));
```

### Service sleep quá lâu
**Giải pháp:** Dùng cron job ping hoặc upgrade paid tier

### Environment variable không load
**Giải pháp:**
1. Dashboard → Environment
2. Kiểm tra key/value đúng chưa
3. Click **"Save Changes"**
4. Service sẽ tự động restart

## 💰 So sánh Free vs Paid

| Feature | Free | Paid ($7/mo) |
|---------|------|--------------|
| Sleep | Có (15 phút) | Không |
| RAM | 512 MB | 2 GB |
| CPU | Shared | Dedicated |
| Build time | Chậm hơn | Nhanh hơn |
| SSL | ✅ | ✅ |
| Custom domain | ✅ | ✅ |

## 🌐 Custom Domain (Optional)

1. Dashboard → Settings → Custom Domain
2. Add domain: `api.yourdomain.com`
3. Cấu hình DNS:
   - Type: `CNAME`
   - Name: `api`
   - Value: `callbot-api.onrender.com`
4. Đợi DNS propagate (5-30 phút)

## 📈 Monitoring

### Health Check Endpoint
Render tự động ping `/` mỗi vài phút.
Nếu muốn custom:
1. Settings → Health Check Path
2. Set: `/health`

### Alerts
Settings → Notifications → Add email để nhận alert khi service down

## ✅ Checklist hoàn tất

- [ ] Code đã push lên GitHub
- [ ] Service đã tạo trên Render
- [ ] Environment variables đã set
- [ ] Service status = "Live" (màu xanh)
- [ ] Test `/health` endpoint thành công
- [ ] Frontend đã update URL
- [ ] Test API endpoints từ frontend
- [ ] (Optional) Setup cron job để không sleep
- [ ] (Optional) Add custom domain

## 🎉 Xong!

Service của bạn đã live tại: `https://callbot-api.onrender.com`

Mỗi lần push code lên GitHub, Render sẽ tự động deploy!
