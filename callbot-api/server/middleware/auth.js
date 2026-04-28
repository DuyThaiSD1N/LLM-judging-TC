// middleware/auth.js — API Key authentication middleware

const API_SECRET_KEY = process.env.API_SECRET_KEY;

function authMiddleware(req, res, next) {
    // TẠM THỜI TẮT AUTH - cho phép tất cả requests
    // TODO: Bật lại khi cần bảo mật
    console.log(`[${req.method}] ${req.path} - Auth bypassed`);
    return next();

    /* ORIGINAL AUTH CODE - uncomment để bật lại
    // Bỏ qua auth cho health check và static files
    if (req.path === '/health' || !req.path.startsWith('/api')) {
        return next();
    }

    // Lấy API key từ header
    const apiKey = req.headers['x-api-key'] || req.headers['authorization']?.replace('Bearer ', '');

    // Nếu không có API_SECRET_KEY trong env, bỏ qua auth (dev mode)
    if (!API_SECRET_KEY) {
        console.warn('⚠️  API_SECRET_KEY not set - running without authentication');
        return next();
    }

    // Kiểm tra API key
    if (!apiKey) {
        return res.status(401).json({
            error: 'Unauthorized',
            message: 'API key is required. Please provide X-API-Key header.'
        });
    }

    if (apiKey !== API_SECRET_KEY) {
        return res.status(403).json({
            error: 'Forbidden',
            message: 'Invalid API key.'
        });
    }

    // API key hợp lệ
    next();
    */
}

module.exports = authMiddleware;
