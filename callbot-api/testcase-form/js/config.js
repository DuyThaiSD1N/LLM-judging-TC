// config.js — Cấu hình API URL tập trung

// Tự động detect API base URL
export const API_BASE_URL = window.location.origin;

// Log để debug
console.log('🔧 Config loaded!');
console.log('🌐 Window location:', window.location.href);
console.log('🔗 API Base URL:', API_BASE_URL);

// Export các endpoint
export const API_ENDPOINTS = {
    RUN_ALL: `${API_BASE_URL}/api/run-testcases`,
    RUN_SINGLE: `${API_BASE_URL}/api/run-single`,
    UPLOAD: `${API_BASE_URL}/api/upload-excel`,
    TEMPLATE: `${API_BASE_URL}/api/template`,
};

console.log('📋 API Endpoints:', API_ENDPOINTS);
