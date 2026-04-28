// upload.js — upload Excel, tự động phân tích bằng AI ngay khi chọn file

import { addBulkTestcases } from './table.js';
import { showToast } from './toast.js';
import { API_ENDPOINTS } from './config.js';

export function initUpload() {
    const zone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');

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
}

async function handleFile(file) {
    const status = document.getElementById('upload-status');
    const ext = file.name.split('.').pop().toLowerCase();

    if (!['xlsx', 'xls'].includes(ext)) {
        setStatus(status, '❌ Chỉ chấp nhận .xlsx hoặc .xls', 'error');
        return;
    }

    setStatus(status, '<span class="spinner-inline"></span> Đang phân tích...', '');

    try {
        const formData = new FormData();
        formData.append('file', file);

        const res = await fetch(API_ENDPOINTS.UPLOAD, { method: 'POST', body: formData });
        const data = await res.json();

        if (!res.ok) throw new Error(data.error || 'Lỗi server');

        const list = data.testcases ?? [];
        if (list.length === 0) {
            setStatus(status, '⚠️ Không trích xuất được testcase nào.', 'error');
            return;
        }

        addBulkTestcases(list);
        setStatus(status, '', ''); // Xóa status text
        showToast(`Import thành công ${list.length} testcase`);
    } catch (err) {
        setStatus(status, `❌ ${err.message}`, 'error');
        showToast('Import thất bại: ' + err.message, 'error');
    }
}

function setStatus(el, html, type) {
    el.innerHTML = html;
    el.className = 'upload-status' + (type ? ` ${type}` : '');
}
