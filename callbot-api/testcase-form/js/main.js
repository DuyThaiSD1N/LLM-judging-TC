// main.js — entry point, khởi tạo tất cả modules

import { initForm } from './form.js';
import { initUpload } from './upload.js';
import { initRunner, runSingle } from './runner.js';
import { renderEval, setRunSingleFn, clearAllTestcases } from './table.js';
import { initHistory } from './history.js';
import { initCriteria } from './criteria.js';
import { initExport } from './export.js';
import { initFilter } from './filter.js';
import { showToast } from './toast.js';
import { API_ENDPOINTS, API_KEY } from './config.js';

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 App initialized');

    setRunSingleFn(runSingle);
    initForm();
    initUpload();
    initRunner();
    initHistory();
    initCriteria();
    initExport();
    initFilter();

    renderEval();

    // Xóa tất cả testcase
    document.getElementById('btn-clear-all').addEventListener('click', () => {
        if (confirm('⚠️ Bạn có chắc muốn xóa TẤT CẢ testcase?\n\nHành động này không thể hoàn tác!')) {
            clearAllTestcases();
            showToast('🗑 Đã xóa tất cả testcase', 'success');
        }
    });

    // Download Excel mẫu
    document.getElementById('btn-template').addEventListener('click', async () => {
        try {
            console.log('📥 Downloading template from:', API_ENDPOINTS.TEMPLATE);
            const res = await fetch(API_ENDPOINTS.TEMPLATE, {
                headers: { 'X-API-Key': API_KEY }
            });
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'testcase_mau.xlsx';
            a.click();
            URL.revokeObjectURL(url);
        } catch (e) {
            console.error('❌ Template download error:', e);
            alert('Không tải được file mẫu: ' + e.message);
        }
    });
});
