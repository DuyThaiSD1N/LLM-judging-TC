// runner.js — chạy multi-turn testcase + nhận kết quả LLM judge

import { getTestcases, setTurnResult, setTcStatus, renderEval } from './table.js';
import { showToast } from './toast.js';
import { API_ENDPOINTS, getAuthHeaders } from './config.js';
import { setRunning, getIsRunning } from './state.js';

export function initRunner() {
    document.getElementById('btn-run-all').addEventListener('click', runAll);

    // Listen for bulk run event
    window.addEventListener('bulk-run', (e) => {
        runBulk(e.detail.indices);
    });
}

// Export để các module khác có thể check trạng thái
export { getIsRunning } from './state.js';

// ── Disable/Enable UI khi đang chạy ──────────────────────────────────────
function setUIRunning(running) {
    setRunning(running);

    // Các nút chính
    const btnRunAll = document.getElementById('btn-run-all');
    const btnAdd = document.getElementById('btn-add');
    const btnReset = document.getElementById('btn-reset');
    const btnClearAll = document.getElementById('btn-clear-all');
    const btnTemplate = document.getElementById('btn-template');
    const btnHistory = document.getElementById('btn-history');
    const btnExport = document.getElementById('btn-export');
    const fileInput = document.getElementById('file-input');
    const uploadZone = document.getElementById('upload-zone');

    // Form inputs
    const tcName = document.getElementById('tc-name');
    const tcCode = document.getElementById('tc-code');
    const tcQuestion = document.getElementById('tc-question');
    const tcExpected = document.getElementById('tc-expected');
    const groupTrigger = document.getElementById('group-trigger');
    const criteriaTrigger = document.getElementById('criteria-trigger');

    // Disable/enable tất cả
    [btnRunAll, btnAdd, btnReset, btnClearAll, btnTemplate, btnHistory, btnExport,
        fileInput, tcName, tcCode, tcQuestion, tcExpected, groupTrigger, criteriaTrigger].forEach(el => {
            if (el) el.disabled = running;
        });

    // Upload zone styling
    if (uploadZone) {
        if (running) {
            uploadZone.style.opacity = '0.5';
            uploadZone.style.cursor = 'not-allowed';
            uploadZone.style.pointerEvents = 'none';
        } else {
            uploadZone.style.opacity = '1';
            uploadZone.style.cursor = 'pointer';
            uploadZone.style.pointerEvents = 'auto';
        }
    }

    // Update text nút Run All
    if (btnRunAll) {
        btnRunAll.textContent = running ? '⏳ Đang chạy...' : '▶ Chạy tất cả testcase';
    }

    // Render lại bảng để disable các nút trong bảng
    renderEval();
}

// ── Áp kết quả turns từ server vào state ─────────────────────────────────
function applyTurnResults(tcIdx, turnResults) {
    turnResults.forEach((r, j) => {
        setTurnResult(tcIdx, j, {
            actual: r.actual,
            action: r.action,
            response_time_ms: r.response_time_ms,
            verdict: r.verdict,
            error_desc: r.error_desc,
            suggestion: r.suggestion,
            time_verdict: r.time_verdict,
            time_note: r.time_note,
            error: r.error,
        });
    });
}

// ── Chạy tất cả ───────────────────────────────────────────────────────────
async function runAll() {
    const testcases = getTestcases();
    if (testcases.length === 0) {
        showToast('⚠️ Chưa có testcase nào để chạy.', 'error');
        return;
    }

    if (getIsRunning()) {
        showToast('⚠️ Đang có testcase đang chạy, vui lòng đợi!', 'error');
        return;
    }

    setUIRunning(true);
    testcases.forEach((_, i) => setTcStatus(i, 'running'));

    try {
        const res = await fetch(API_ENDPOINTS.RUN_ALL, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ testcases }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Lỗi server');

        data.results.forEach((r, i) => {
            applyTurnResults(i, r.turns);
            setTcStatus(i, r.status, r.error);
        });
        renderEval();

        // Tổng kết: đếm số turn PASSED
        const allTurns = data.results.flatMap(r => r.turns ?? []);
        const passed = allTurns.filter(t => t.verdict === 'PASSED').length;
        const judged = allTurns.filter(t => t.verdict !== null).length;
        showToast(`✅ Xong! ${passed}/${judged} lượt PASSED`);
    } catch (err) {
        testcases.forEach((_, i) => setTcStatus(i, 'error', err.message));
        renderEval();
        showToast('❌ ' + err.message, 'error');
    } finally {
        setUIRunning(false);
    }
}

// ── Chạy 1 testcase ───────────────────────────────────────────────────────
export async function runSingle(idx) {
    const tc = getTestcases()[idx];
    if (!tc) return;

    if (getIsRunning()) {
        showToast('⚠️ Đang có testcase đang chạy, vui lòng đợi!', 'error');
        return;
    }

    setUIRunning(true);
    setTcStatus(idx, 'running');

    try {
        const res = await fetch(API_ENDPOINTS.RUN_SINGLE, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                code: tc.code,
                group: tc.group,
                turns: tc.turns,
                criteria: tc.criteria || 'standard'
            }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Lỗi server');

        applyTurnResults(idx, data.turns);
        setTcStatus(idx, 'done');
        renderEval();

        const passed = data.turns.filter(t => t.verdict === 'PASSED').length;
        const judged = data.turns.filter(t => t.verdict !== null).length;
        showToast(`✅ TC ${tc.code}: ${passed}/${judged} lượt PASSED`);
    } catch (err) {
        setTcStatus(idx, 'error', err.message);
        renderEval();
        showToast('❌ ' + err.message, 'error');
    } finally {
        setUIRunning(false);
    }
}

// ── Chạy nhiều testcase đã chọn ───────────────────────────────────────────
async function runBulk(indices) {
    if (indices.length === 0) return;

    if (getIsRunning()) {
        showToast('⚠️ Đang có testcase đang chạy, vui lòng đợi!', 'error');
        return;
    }

    const testcases = getTestcases();
    const selectedTcs = indices.map(i => testcases[i]).filter(tc => tc);

    if (selectedTcs.length === 0) {
        showToast('⚠️ Không có testcase nào được chọn.', 'error');
        return;
    }

    setUIRunning(true);
    indices.forEach(i => setTcStatus(i, 'running'));

    try {
        const res = await fetch(API_ENDPOINTS.RUN_ALL, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ testcases: selectedTcs }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Lỗi server');

        data.results.forEach((r, resultIdx) => {
            const originalIdx = indices[resultIdx];
            applyTurnResults(originalIdx, r.turns);
            setTcStatus(originalIdx, r.status, r.error);
        });
        renderEval();

        const allTurns = data.results.flatMap(r => r.turns ?? []);
        const passed = allTurns.filter(t => t.verdict === 'PASSED').length;
        const judged = allTurns.filter(t => t.verdict !== null).length;
        showToast(`✅ Xong! ${passed}/${judged} lượt PASSED (${selectedTcs.length} testcase)`);
    } catch (err) {
        indices.forEach(i => setTcStatus(i, 'error', err.message));
        renderEval();
        showToast('❌ ' + err.message, 'error');
    } finally {
        setUIRunning(false);
    }
}
