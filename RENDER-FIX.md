# 🔧 Sửa lỗi Render Deploy

## Vấn đề
Render không tìm thấy `package.json` vì cấu trúc thư mục.

## Đã sửa
✅ Tạo `package.json` ở root với đường dẫn đúng
✅ Tạo `render.yaml` ở root
✅ Sửa đường dẫn `.env` trong `server/index.js`

## Các bước tiếp theo

### 1. Push code mới lên GitHub
```bash
git add .
git commit -m "Fix Render deploy paths"
git push origin main
```

### 2. Redeploy trên Render
Render sẽ tự động detect và redeploy.

Hoặc manual:
1. Vào Render Dashboard
2. Click service của bạn
3. Click **"Manual Deploy"** → **"Deploy latest commit"**

### 3. Kiểm tra logs
Trong Render Dashboard → **Logs** tab

Bạn sẽ thấy:
```
==> Building...
==> Installing dependencies
==> Starting server
✅ Server running on port 10000
```

### 4. Test
```bash
curl https://your-app.onrender.com/health
```

## Nếu vẫn lỗi

### Option: Xóa service và tạo lại
1. Render Dashboard → Settings → Delete Service
2. Tạo service mới:
   - **Root Directory:** Để trống (vì package.json đã ở root)
   - **Build Command:** `npm install`
   - **Start Command:** `npm start`
   - **Environment Variables:** Add `OPENAI_API_KEY`

Xong!
