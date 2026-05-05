// config.js — Cấu hình API URL tập trung

// Tự động detect API base URL
export const API_BASE_URL = window.location.origin;

// API Key - Hardcoded (đổi key này khi deploy production)
export const API_KEY = 'your-secret-api-key-here-change-in-production';

// Log để debug
console.log('🔧 Config loaded!');
console.log('🌐 Window location:', window.location.href);
console.log('🔗 API Base URL:', API_BASE_URL);

// Export các endpoint
export const API_ENDPOINTS = {
    RUN_ALL: `${API_BASE_URL}/api/run-testcases`,
    RUN_ALL_STREAM: `${API_BASE_URL}/api/run-testcases-stream`,  // ← NEW: Streaming
    RUN_SINGLE: `${API_BASE_URL}/api/run-single`,
    UPLOAD: `${API_BASE_URL}/api/upload-excel`,
    TEMPLATE: `${API_BASE_URL}/api/template`,
    TESTCASES: `${API_BASE_URL}/api/testcases`,
    HISTORY: `${API_BASE_URL}/api/history`,
    HISTORY_STATS: `${API_BASE_URL}/api/history/stats`,
    CRITERIA: `${API_BASE_URL}/api/criteria`,
    EXPORT: `${API_BASE_URL}/api/export`,
};

console.log('📋 API Endpoints:', API_ENDPOINTS);

// Helper function để tạo headers với API key
export function getAuthHeaders() {
    return {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
    };
}

// Lấy bot URL từ input (rỗng = dùng default ở server)
export function getBotUrl() {
    const input = document.getElementById('bot-url-input');
    return input ? input.value.trim() : '';
}
