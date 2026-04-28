// runner.js — chạy multi-turn testcase + nhận kết quả LLM judge

import { getTestcases, setTurnResult, setTcStatus, renderEval } from './table.js';
import { showToast } from './toast.js';
import { API_ENDPOINTS } from './config.js';

export function initRunner() {
    document.getElementById('btn-run-all').addEventListener('click', runAll);
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

    const btn = document.getElementById('btn-run-all');
    btn.disabled = true;
    btn.textContent = '⏳ Đang chạy...';

    testcases.forEach((_, i) => setTcStatus(i, 'running'));
    renderEval();

    try {
        const res = await fetch(API_ENDPOINTS.RUN_ALL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
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
        btn.disabled = false;
        btn.textContent = '▶ Chạy tất cả testcase';
    }
}

// ── Chạy 1 testcase ───────────────────────────────────────────────────────
export async function runSingle(idx) {
    const tc = getTestcases()[idx];
    if (!tc) return;

    setTcStatus(idx, 'running');
    renderEval();

    try {
        const res = await fetch(API_ENDPOINTS.RUN_SINGLE, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: tc.code, group: tc.group, turns: tc.turns }),
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
    }
}
