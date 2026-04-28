// main.js — entry point, khởi tạo tất cả modules

import { initForm } from './form.js';
import { initUpload } from './upload.js';
import { initRunner, runSingle } from './runner.js';
import { renderEval, setRunSingleFn } from './table.js';

// Tự động detect API URL (localhost hoặc production)
const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:8099'
    : window.location.origin;

document.addEventListener('DOMContentLoaded', () => {
    setRunSingleFn(runSingle);
    initForm();
    initUpload();
    initRunner();
    renderEval();

    // Download Excel mẫu
    document.getElementById('btn-template').addEventListener('click', async () => {
        try {
            const res = await fetch(`${API_BASE}/api/template`);
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'testcase_mau.xlsx';
            a.click();
            URL.revokeObjectURL(url);
        } catch (e) {
            alert('Không tải được file mẫu. Kiểm tra server đang chạy chưa.');
        }
    });
});
