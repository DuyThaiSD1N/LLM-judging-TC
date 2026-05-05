// upload.js — upload Excel, tự động phân tích bằng AI ngay khi chọn file

import { addBulkTestcases } from './table.js';
import { showToast } from './toast.js';
import { API_ENDPOINTS, API_KEY } from './config.js';

let isInitialized = false;

export function initUpload() {
    // Prevent multiple initializations
    if (isInitialized) {
        console.warn('⚠️ Upload already initialized, skipping...');
        return;
    }
    isInitialized = true;

    const zone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');

    if (!zone || !fileInput) {
        console.error('❌ Upload elements not found');
        return;
    }

    zone.addEventListener('click', () => fileInput.click());

    zone.addEventListener('dragover', e => {
        e.preventDefault();
        zone.classList.add('drag-over');
    });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', e => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files[0]) handleFile(fileInput.files[0]);
    });

    console.log('✅ Upload initialized');
}

async function handleFile(file) {
    console.log('📁 handleFile called with:', file?.name);

    const status = document.getElementById('upload-status');
    const fileInput = document.getElementById('file-input');

    if (!file) {
        console.error('❌ No file provided to handleFile');
        return;
    }

    const ext = file.name.split('.').pop().toLowerCase();

    if (!['xlsx', 'xls'].includes(ext)) {
        setStatus(status, '❌ Chỉ chấp nhận .xlsx hoặc .xls', 'error');
        showToast('Chỉ chấp nhận file .xlsx hoặc .xls', 'error');
        // Reset file input
        if (fileInput) fileInput.value = '';
        return;
    }

    // Hiển thị toast đang xử lý
    showToast('Đang phân tích file Excel...', 'info');

    try {
        const formData = new FormData();
        formData.append('file', file);

        console.log('📤 Uploading to:', API_ENDPOINTS.UPLOAD);

        const res = await fetch(API_ENDPOINTS.UPLOAD, {
            method: 'POST',
            headers: { 'X-API-Key': API_KEY },
            body: formData
        });

        console.log('📥 Response status:', res.status);

        const data = await res.json();

        if (!res.ok) {
            // Hiển thị lỗi validation chi tiết
            const errorMsg = data.error || 'Lỗi server';
            console.error('❌ Upload error:', errorMsg);
            setStatus(status, '', '');
            showToast(errorMsg, 'error');
            // Reset file input
            if (fileInput) fileInput.value = '';
            return;
        }

        const list = data.testcases ?? [];
        console.log('✅ Received testcases:', list.length);

        if (list.length === 0) {
            setStatus(status, '', '');
            showToast('Không trích xuất được testcase nào từ file Excel', 'error');
            // Reset file input
            if (fileInput) fileInput.value = '';
            return;
        }

        // Thêm criteria mặc định nếu không có
        const listWithCriteria = list.map(tc => ({
            ...tc,
            criteria: tc.criteria || 'standard'
        }));

        console.log('➕ Adding testcases to table...');
        addBulkTestcases(listWithCriteria);
        setStatus(status, '', ''); // Xóa status text
        showToast(`Import thành công ${list.length} testcase`);

        // Reset file input để có thể upload lại cùng file
        if (fileInput) {
            console.log('🔄 Resetting file input');
            fileInput.value = '';
        }
    } catch (err) {
        console.error('❌ Upload exception:', err);
        setStatus(status, '', '');
        showToast('Import thất bại: ' + err.message, 'error');
        // Reset file input
        if (fileInput) fileInput.value = '';
    }
}

function setStatus(el, html, type) {
    el.innerHTML = html;
    el.className = 'upload-status' + (type ? ` ${type}` : '');
}
