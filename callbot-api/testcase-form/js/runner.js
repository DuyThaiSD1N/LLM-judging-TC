// runner.js — chạy multi-turn testcase + nhận kết quả LLM judge

import { getTestcases, setTurnResult, setTcStatus, resetTurnData, renderEval } from './table-v2.js';
import { showToast } from './toast.js';
import { API_ENDPOINTS, getAuthHeaders } from './config.js';
import { setRunning, getIsRunning } from './state.js';

export function initRunner() {
    const btnRunAll = document.getElementById('btn-run-all');

    if (!btnRunAll) {
        console.error('❌ Run button not found');
        return;
    }

    btnRunAll.addEventListener('click', runAll);

    // Listen for bulk run event
    window.addEventListener('bulk-run', (e) => {
        runBulk(e.detail.indices);
    });

    console.log('✅ Runner initialized');
}

// Export để các module khác có thể check trạng thái
export { getIsRunning } from './state.js';

// ── Disable/Enable UI khi đang chạy ──────────────────────────────────────
function setUIRunning(running) {
    console.log(`🔄 setUIRunning: ${running}`);
    setRunning(running);

    // Các nút chính
    const btnRunAll = document.getElementById('btn-run-all');
    const btnAdd = document.getElementById('btn-add');
    const btnReset = document.getElementById('btn-reset');
    const btnClearAll = document.getElementById('btn-clear-all');
    const btnTemplate = document.getElementById('btn-template');
    const btnImportExcel = document.getElementById('btn-import-excel');
    const btnExport = document.getElementById('btn-export');
    const btnCompare = document.getElementById('btn-compare');
    const fileInput = document.getElementById('file-input');

    // Form inputs
    const tcName = document.getElementById('tc-name');
    const tcCode = document.getElementById('tc-code');
    const tcExecutor = document.getElementById('tc-executor');  // NEW
    const tcScenario = document.getElementById('tc-scenario');
    const tcBotUrl = document.getElementById('tc-bot-url');
    const tcQuestion = document.getElementById('tc-question');
    const tcExpected = document.getElementById('tc-expected');
    const tcRequiredKeywords = document.getElementById('tc-required-keywords');
    const tcForbiddenKeywords = document.getElementById('tc-forbidden-keywords');
    const criteriaTrigger = document.getElementById('criteria-trigger');

    // Disable/enable tất cả buttons
    [btnRunAll, btnAdd, btnReset, btnClearAll, btnTemplate, btnImportExcel, btnExport, btnCompare].forEach(el => {
        if (el) {
            el.disabled = running;
            if (running) {
                el.style.opacity = '0.5';
                el.style.cursor = 'not-allowed';
            } else {
                el.style.opacity = '1';
                el.style.cursor = 'pointer';
            }
        }
    });

    // Disable/enable form inputs
    [tcName, tcCode, tcExecutor, tcScenario, tcBotUrl, tcQuestion, tcExpected, tcRequiredKeywords, tcForbiddenKeywords].forEach(el => {
        if (el) {
            el.disabled = running;
            if (running) {
                el.style.opacity = '0.5';
                el.style.cursor = 'not-allowed';
            } else {
                el.style.opacity = '1';
                el.style.cursor = 'text';
            }
        }
    });

    // Disable/enable file input
    if (fileInput) {
        fileInput.disabled = running;
    }

    // Disable/enable criteria dropdown
    if (criteriaTrigger) {
        criteriaTrigger.disabled = running;
        if (running) {
            criteriaTrigger.style.opacity = '0.5';
            criteriaTrigger.style.cursor = 'not-allowed';
            criteriaTrigger.style.pointerEvents = 'none';
        } else {
            criteriaTrigger.style.opacity = '1';
            criteriaTrigger.style.cursor = 'pointer';
            criteriaTrigger.style.pointerEvents = 'auto';
        }
    }

    // Update text nút Run All
    if (btnRunAll) {
        btnRunAll.textContent = running ? '⏳ Đang chạy...' : '▶ Chạy tất cả';
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
            reasoning: r.reasoning || '',
            error_desc: r.error_desc || '',
            suggestion: r.suggestion || '',
            suggested_response: r.suggested_response || '',
            tone_note: r.tone_note || '',
            time_verdict: r.time_verdict,
            time_note: r.time_note || '',
            error: r.error || '',
        });
    });
}

// ── Chạy tất cả với STREAMING ─────────────────────────────────────────────
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
    testcases.forEach((_, i) => {
        resetTurnData(i);      // xóa kết quả cũ → spinner hiện đúng
        setTcStatus(i, 'running');
    });
    renderEval(); // ← Render ngay để hiển thị spinner

    try {
        // Sử dụng EventSource để nhận streaming results
        const response = await fetch(API_ENDPOINTS.RUN_ALL_STREAM, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ testcases }),
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let completedCount = 0;

        while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            // Decode chunk
            buffer += decoder.decode(value, { stream: true });

            // Process complete messages (separated by \n\n)
            const messages = buffer.split('\n\n');
            buffer = messages.pop() || ''; // Keep incomplete message in buffer

            for (const message of messages) {
                if (!message.trim() || !message.startsWith('data: ')) continue;

                const data = message.replace('data: ', '').trim();

                try {
                    const result = JSON.parse(data);

                    // Check if done
                    if (result.done) {
                        console.log('✅ All testcases completed!');
                        continue;
                    }

                    // Update testcase result
                    const idx = result.index;
                    applyTurnResults(idx, result.turns);
                    setTcStatus(idx, result.status, result.error);
                    renderEval(); // ← Render ngay khi có kết quả

                    completedCount++;
                    console.log(`✅ Testcase ${idx + 1}/${testcases.length} completed`);

                } catch (e) {
                    console.error('Failed to parse SSE message:', e, data);
                }
            }
        }

        // Tổng kết
        const allTurns = testcases.flatMap((tc, i) => tc.turns);
        const passed = allTurns.filter(t => t.verdict === 'PASSED').length;
        const judged = allTurns.filter(t => t.verdict !== null).length;
        showToast(`✅ Xong! ${passed}/${judged} lượt đạt yêu cầu`);

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
    resetTurnData(idx);        // xóa kết quả cũ → spinner hiện đúng
    setTcStatus(idx, 'running');
    renderEval(); // ← Render ngay để hiển thị spinner

    try {
        const res = await fetch(API_ENDPOINTS.RUN_SINGLE, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                code: tc.code,
                group: tc.group,
                turns: tc.turns,
                criteria: tc.criteria || 'goal_achievement',
                bot_url: tc.bot_url || null,
                executor: tc.executor || null  // NEW
            }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Lỗi server');

        applyTurnResults(idx, data.turns);
        setTcStatus(idx, 'done');
        renderEval();

        const passed = data.turns.filter(t => t.verdict === 'PASSED').length;
        const judged = data.turns.filter(t => t.verdict !== null).length;
        showToast(`✅ TC ${tc.code}: ${passed}/${judged} lượt đạt yêu cầu`);
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
    indices.forEach(i => {
        resetTurnData(i);      // xóa kết quả cũ → spinner hiện đúng
        setTcStatus(i, 'running');
    });
    renderEval(); // ← Render ngay để hiển thị spinner

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
        showToast(`✅ Xong! ${passed}/${judged} lượt đạt yêu cầu (${selectedTcs.length} testcase)`);
    } catch (err) {
        indices.forEach(i => setTcStatus(i, 'error', err.message));
        renderEval();
        showToast('❌ ' + err.message, 'error');
    } finally {
        setUIRunning(false);
    }
}
