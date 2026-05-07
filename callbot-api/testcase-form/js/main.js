// main.js — entry point, khởi tạo tất cả modules

import { initForm } from './form.js';
import { initUpload } from './upload.js';
import { initRunner, runSingle } from './runner.js';
import { renderEval, setRunSingleFn, clearAllTestcases, getTestcases } from './table-v2.js';
import { initHistory } from './history.js';
import { initCriteria } from './criteria.js';
import { initExport } from './export.js';
import { initFilter } from './filter-v2.js';
import { initComparison } from './comparison.js';
import { showToast } from './toast.js';
import { API_ENDPOINTS, API_KEY } from './config.js';
import { initNavigation } from './navigation.js';

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 App initialized');

    // Initialize navigation first
    initNavigation();

    setRunSingleFn(runSingle);
    initForm();
    initUpload();
    initRunner();
    initHistory();
    initCriteria();
    initExport();
    initFilter();
    initComparison();

    renderEval();

    // Xóa tất cả testcase
    const btnClearAll = document.getElementById('btn-clear-all');
    if (btnClearAll) {
        btnClearAll.addEventListener('click', () => {
            if (confirm('⚠️ Bạn có chắc muốn xóa TẤT CẢ testcase?\n\nHành động này không thể hoàn tác!')) {
                clearAllTestcases();

                // Remove any existing comparison modal
                const existingModal = document.getElementById('comparison-modal');
                if (existingModal) {
                    existingModal.remove();
                }

                showToast('🗑 Đã xóa tất cả testcase', 'success');

                // Force reload page to clean up all state
                console.log('🔄 Reloading page to clean up state...');
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        });
    }

    // Download Excel mẫu
    const btnTemplate = document.getElementById('btn-template');
    if (btnTemplate) {
        btnTemplate.addEventListener('click', async () => {
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
    }
});
