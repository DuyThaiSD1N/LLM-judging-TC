// export.js — xuất testcase ra Excel

import { getTestcases } from './table.js';
import { showToast } from './toast.js';
import { API_ENDPOINTS, getAuthHeaders } from './config.js';

export function initExport() {
    document.getElementById('btn-export').addEventListener('click', exportToExcel);
}

async function exportToExcel() {
    const testcases = getTestcases();

    if (testcases.length === 0) {
        showToast('⚠️ Không có testcase nào để xuất', 'error');
        return;
    }

    const btn = document.getElementById('btn-export');
    btn.disabled = true;
    btn.textContent = '⏳ Đang xuất...';

    try {
        const res = await fetch(API_ENDPOINTS.EXPORT, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ testcases }),
        });

        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.error || 'Lỗi server');
        }

        // Download file
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;

        // Lấy filename từ header hoặc dùng default
        const contentDisposition = res.headers.get('Content-Disposition');
        const filename = contentDisposition
            ? contentDisposition.split('filename=')[1].replace(/"/g, '')
            : `testcases_${new Date().toISOString().slice(0, 19).replace(/[:.]/g, '-')}.xlsx`;

        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        showToast(`✅ Đã xuất ${testcases.length} testcase ra Excel`);
    } catch (err) {
        showToast('❌ Xuất Excel thất bại: ' + err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '📥 Xuất Excel';
    }
}
