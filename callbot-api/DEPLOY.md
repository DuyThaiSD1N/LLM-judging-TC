# Hướng dẫn Deploy lên Railway

## 🚀 Các bước thực hiện

### 1. Chuẩn bị Git Repository

```bash
# Nếu chưa có git
cd callbot-api
git init
git add .
git commit -m "Initial commit"

# Push lên GitHub
git remote add origin https://github.com/your-username/your-repo.git
git branch -M main
git push -u origin main
```

### 2. Deploy trên Railway

#### Cách 1: Deploy từ GitHub (Khuyến nghị)

1. Truy cập [railway.app](https://railway.app)
2. Đăng nhập bằng GitHub
3. Click **"New Project"**
4. Chọn **"Deploy from GitHub repo"**
5. Chọn repository của bạn
6. Railway sẽ tự động:
   - Detect Node.js project
   - Cài đặt dependencies
   - Deploy server

#### Cách 2: Deploy bằng Railway CLI

```bash
# Cài Railway CLI
npm i -g @railway/cli

# Đăng nhập
railway login

# Khởi tạo project
railway init

# Deploy
railway up
```

### 3. Cấu hình Environment Variables

1. Vào project trên Railway Dashboard
2. Click tab **"Variables"**
3. Thêm các biến sau:

```
OPENAI_API_KEY=sk-proj-your-actual-openai-key
PORT=8099
NODE_ENV=production
```

**Lưu ý:** Railway tự động set `PORT`, nhưng bạn có thể override nếu cần.

### 4. Lấy Public URL

Railway tự động tạo domain:
- Vào **Settings** → **Networking**
- Click **"Generate Domain"**
- Bạn sẽ có URL dạng: `https://callbot-api-production.up.railway.app`

### 5. Cập nhật Frontend

Sửa file `testcase-form/js/runner.js`:

```javascript
// Thay localhost bằng Railway URL
const RUN_ALL_URL = 'https://your-app.railway.app/api/run-testcases';
const RUN_SINGLE_URL = 'https://your-app.railway.app/api/run-single';
```

### 6. Test Deployment

```bash
# Test health check
curl https://your-app.railway.app/health

# Kết quả mong đợi:
# {"status":"ok","timestamp":"2024-..."}
```

## 🔧 Troubleshooting

### Lỗi: "Application failed to respond"
- Kiểm tra server có listen trên `0.0.0.0` không
- Kiểm tra PORT environment variable
- Xem logs: Railway Dashboard → **Deployments** → Click vào deployment → **View Logs**

### Lỗi: "Module not found"
- Đảm bảo `package.json` có đầy đủ dependencies
- Railway sẽ tự động chạy `npm install`

### Lỗi CORS
- Server đã config `cors({ origin: '*' })`
- Nếu cần restrict, sửa trong `server/index.js`

## 📊 Monitoring

- **Logs**: Railway Dashboard → Deployments → View Logs
- **Metrics**: Railway Dashboard → Metrics tab
- **Health Check**: `GET /health`

## 💰 Chi phí

- Railway free tier: $5 credit/tháng
- Nếu vượt quá, cần thêm payment method
- Ước tính: ~$5-10/tháng cho app nhỏ

## 🔄 Auto Deploy

Railway tự động deploy khi bạn push code lên GitHub:

```bash
git add .
git commit -m "Update feature"
git push origin main
# Railway sẽ tự động deploy!
```

## 🌐 Custom Domain (Optional)

1. Railway Dashboard → Settings → Domains
2. Click **"Custom Domain"**
3. Thêm domain của bạn (vd: `api.yourdomain.com`)
4. Cấu hình DNS theo hướng dẫn Railway

## 📝 Checklist

- [ ] Code đã push lên GitHub
- [ ] Project đã tạo trên Railway
- [ ] Environment variables đã set
- [ ] Domain đã generate
- [ ] Health check endpoint hoạt động
- [ ] Frontend đã update URL
- [ ] Test API endpoints thành công
