// history.js — Quản lý lịch sử đánh giá (View mode) với tìm kiếm và export

import { API_ENDPOINTS, API_KEY } from './config.js';

// Selected history items for export
let selectedHistoryItems = new Set();

export function initHistory() {
    // History is now a view, not a modal
    console.log('✅ History initialized (view mode)');

    // Setup search and filters
    setupFilters();

    // Load history data when needed
    setTimeout(() => {
        loadHistoryData();
    }, 500);
}

function setupFilters() {
    const searchInput = document.getElementById('history-search');
    const searchExecutorInput = document.getElementById('history-search-executor');  // NEW
    const dateFromInput = document.getElementById('history-date-from');
    const timeFromInput = document.getElementById('history-time-from');
    const dateToInput = document.getElementById('history-date-to');
    const timeToInput = document.getElementById('history-time-to');
    const btnClearFilters = document.getElementById('btn-clear-filters');
    const btnExportSelected = document.getElementById('btn-export-selected');
    const btnRefreshHistory = document.getElementById('btn-refresh-history');

    if (searchInput) {
        searchInput.addEventListener('input', () => {
            applyFilters();
        });
    }

    if (searchExecutorInput) {  // NEW
        searchExecutorInput.addEventListener('input', () => {
            applyFilters();
        });
    }

    if (dateFromInput) {
        dateFromInput.addEventListener('change', () => {
            applyFilters();
        });
    }

    if (timeFromInput) {
        timeFromInput.addEventListener('change', () => {
            applyFilters();
        });
    }

    if (dateToInput) {
        dateToInput.addEventListener('change', () => {
            applyFilters();
        });
    }

    if (timeToInput) {
        timeToInput.addEventListener('change', () => {
            applyFilters();
        });
    }

    if (btnClearFilters) {
        btnClearFilters.addEventListener('click', () => {
            if (searchInput) searchInput.value = '';
            if (searchExecutorInput) searchExecutorInput.value = '';  // NEW
            if (dateFromInput) dateFromInput.value = '';
            if (timeFromInput) timeFromInput.value = '';
            if (dateToInput) dateToInput.value = '';
            if (timeToInput) timeToInput.value = '';
            applyFilters();
        });
    }

    if (btnExportSelected) {
        btnExportSelected.addEventListener('click', () => {
            exportSelectedHistory();
        });
    }

    if (btnRefreshHistory) {
        btnRefreshHistory.addEventListener('click', () => {
            console.log('🔄 Manual refresh triggered');
            loadHistoryData();
        });
    }
}

function applyFilters() {
    const searchInput = document.getElementById('history-search');
    const searchExecutorInput = document.getElementById('history-search-executor');  // NEW
    const dateFromInput = document.getElementById('history-date-from');
    const timeFromInput = document.getElementById('history-time-from');
    const dateToInput = document.getElementById('history-date-to');
    const timeToInput = document.getElementById('history-time-to');

    const searchTerm = searchInput?.value.toLowerCase() || '';
    const executorTerm = searchExecutorInput?.value.toLowerCase() || '';  // NEW

    // Build datetime from date + time
    let dateTimeFrom = null;
    if (dateFromInput?.value) {
        const timeFrom = timeFromInput?.value || '00:00';
        dateTimeFrom = new Date(`${dateFromInput.value}T${timeFrom}`);
    }

    let dateTimeTo = null;
    if (dateToInput?.value) {
        const timeTo = timeToInput?.value || '23:59';
        dateTimeTo = new Date(`${dateToInput.value}T${timeTo}`);
    }

    const historyItems = document.querySelectorAll('.history-item');

    historyItems.forEach(item => {
        const name = item.dataset.testcaseName?.toLowerCase() || '';
        const code = item.dataset.testcaseCode?.toLowerCase() || '';
        const executor = item.dataset.executor?.toLowerCase() || '';  // NEW
        const runAt = item.dataset.runAt ? new Date(item.dataset.runAt) : null;

        let show = true;

        // Search filter (by name or code)
        if (searchTerm && !name.includes(searchTerm) && !code.includes(searchTerm)) {
            show = false;
        }

        // Search filter by executor  // NEW
        if (executorTerm && !executor.includes(executorTerm)) {
            show = false;
        }

        // DateTime range filter
        if (dateTimeFrom && runAt && runAt < dateTimeFrom) {
            show = false;
        }
        if (dateTimeTo && runAt && runAt > dateTimeTo) {
            show = false;
        }

        item.style.display = show ? 'block' : 'none';
    });

    updateExportButtonState();
}

export function getSelectedHistoryItems() {
    return Array.from(selectedHistoryItems);
}

function updateExportButtonState() {
    const btnExportSelected = document.getElementById('btn-export-selected');
    if (btnExportSelected) {
        const count = selectedHistoryItems.size;
        if (count > 0) {
            btnExportSelected.disabled = false;
            btnExportSelected.textContent = `📥 Export đã chọn (${count})`;
        } else {
            btnExportSelected.disabled = true;
            btnExportSelected.textContent = '📥 Export đã chọn';
        }
    }
}

async function loadHistoryData() {
    const historyStats = document.getElementById('history-stats');
    const historyList = document.getElementById('history-list');

    if (!historyStats || !historyList) {
        console.warn('⚠️ History elements not found in DOM yet');
        return;
    }

    // Load stats and history
    await Promise.all([
        loadStats(),
        loadHistory()
    ]);
}

async function loadStats() {
    const statsContainer = document.getElementById('history-stats');
    if (!statsContainer) return;

    statsContainer.innerHTML = '<p style="text-align:center;color:#94a3b8;">Đang tải thống kê...</p>';

    try {
        const res = await fetch(API_ENDPOINTS.HISTORY_STATS, {
            headers: { 'X-API-Key': API_KEY }
        });
        const stats = await res.json();

        statsContainer.innerHTML = `
            <div class="stat-card">
                <div class="stat-label">Tổng lượt chạy</div>
                <div class="stat-value">${stats.total_runs}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Đạt yêu cầu</div>
                <div class="stat-value">${stats.passed}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Không đạt</div>
                <div class="stat-value">${stats.failed}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Tỷ lệ Pass</div>
                <div class="stat-value">${stats.pass_rate}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Thời gian TB</div>
                <div class="stat-value">${stats.avg_response_time}ms</div>
            </div>
        `;
    } catch (err) {
        console.error('Failed to load stats:', err);
        statsContainer.innerHTML = '<p style="text-align:center;color:#dc2626;">Không tải được thống kê</p>';
    }
}

async function loadHistory() {
    const listContainer = document.getElementById('history-list');
    if (!listContainer) return;

    listContainer.innerHTML = '<p style="text-align:center;color:#94a3b8;">Đang tải lịch sử...</p>';

    try {
        const res = await fetch(API_ENDPOINTS.HISTORY + '?limit=50', {
            headers: { 'X-API-Key': API_KEY }
        });
        const data = await res.json();
        const history = data.history || [];

        if (history.length === 0) {
            listContainer.innerHTML = '<p style="text-align:center;color:#94a3b8;">Chưa có lịch sử nào</p>';
            return;
        }

        // Group by testcase and run time
        const grouped = groupHistoryByRun(history);

        listContainer.innerHTML = grouped.map((run, index) => `
            <div class="history-item" 
                 data-run-index="${index}"
                 data-testcase-name="${run.testcase_name}"
                 data-testcase-code="${run.testcase_code}"
                 data-executor="${run.executor || ''}"
                 data-run-at="${run.run_at}">
                <div class="history-header">
                    <input type="checkbox" 
                           class="history-checkbox" 
                           data-run-index="${index}"
                           title="Chọn để export">
                    <button class="history-expand-btn" data-run-index="${index}">
                        <span class="expand-icon">▶</span>
                    </button>
                    <div class="history-title">
                        ${run.testcase_name} <span style="color:#94a3b8;font-weight:400;">(${run.testcase_code})</span>
                    </div>
                    <div class="history-time">${formatDate(run.run_at)}</div>
                </div>
                <div class="history-meta">
                    <span>Lượt: <strong>${run.turns}</strong></span>
                    <span style="color:#16a34a;">✓ Đạt: <strong>${run.passed}</strong></span>
                    <span style="color:#dc2626;">✕ Không đạt: <strong>${run.failed}</strong></span>
                    <span>Thời gian TB: <strong>${run.avg_time}ms</strong></span>
                    ${run.executor ? `<span style="color:#94a3b8;">👤 Người thực hiện: <strong style="color:#e2e8f0;">${run.executor}</strong></span>` : ''}
                </div>
                <div class="history-details">
                    ${run.details.map((turn, i) => `
                        <div class="turn-detail ${turn.verdict === 'PASSED' ? 'pass' : 'fail'}">
                            <div class="turn-header">Lượt ${i + 1} - ${turn.verdict || 'N/A'}</div>
                            ${turn.scenario ? `
                                <div class="turn-row">
                                    <div class="turn-label">Setup lịch sử:</div>
                                    <div class="turn-value scenario-value">${turn.scenario}</div>
                                </div>
                            ` : ''}
                            <div class="turn-row">
                                <div class="turn-label">Câu hỏi:</div>
                                <div class="turn-value">${turn.question}</div>
                            </div>
                            <div class="turn-row">
                                <div class="turn-label">Kỳ vọng:</div>
                                <div class="turn-value">${turn.expected}</div>
                            </div>
                            <div class="turn-row">
                                <div class="turn-label">Thực tế:</div>
                                <div class="turn-value">${turn.actual || 'N/A'}</div>
                            </div>
                            <div class="turn-row">
                                <div class="turn-label">Thời gian:</div>
                                <div class="turn-value">${turn.response_time_ms || 0}ms</div>
                            </div>
                            ${turn.error_desc ? `
                                <div class="turn-row">
                                    <div class="turn-label">Lỗi:</div>
                                    <div class="turn-value" style="color:#dc2626;">${turn.error_desc}</div>
                                </div>
                            ` : ''}
                            ${turn.suggestion ? `
                                <div class="turn-row">
                                    <div class="turn-label">Gợi ý:</div>
                                    <div class="turn-value" style="color:#1d4ed8;">${turn.suggestion}</div>
                                </div>
                            ` : ''}
                            ${turn.suggested_response ? `
                                <div class="turn-row" style="margin-top:12px;padding-top:12px;border-top:1px dashed #334155;">
                                    <div class="turn-label" style="color:#10b981;font-weight:700;">📝 Mẫu đề xuất:</div>
                                    <div class="turn-value" style="color:#10b981;background:#0f172a;padding:12px;border-radius:6px;border-left:3px solid #10b981;line-height:1.6;">${turn.suggested_response}</div>
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');

        // Store grouped data for export
        window.historyGroupedData = grouped;

        // Add click handlers for checkboxes
        document.querySelectorAll('.history-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const index = parseInt(e.target.dataset.runIndex);
                if (e.target.checked) {
                    selectedHistoryItems.add(index);
                } else {
                    selectedHistoryItems.delete(index);
                }
                updateExportButtonState();
            });
        });

        // Add click handlers for expand buttons only
        document.querySelectorAll('.history-expand-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const index = btn.dataset.runIndex;
                const item = document.querySelector(`.history-item[data-run-index="${index}"]`);
                const icon = btn.querySelector('.expand-icon');

                item.classList.toggle('expanded');

                // Rotate icon
                if (item.classList.contains('expanded')) {
                    icon.style.transform = 'rotate(90deg)';
                } else {
                    icon.style.transform = 'rotate(0deg)';
                }
            });
        });
    } catch (err) {
        console.error('Failed to load history:', err);
        listContainer.innerHTML = '<p style="text-align:center;color:#dc2626;">Không tải được lịch sử</p>';
    }
}

function groupHistoryByRun(history) {
    const runs = [];
    const runMap = new Map();

    history.forEach(item => {
        const key = `${item.testcase_id}_${item.run_at}`;

        if (!runMap.has(key)) {
            runMap.set(key, {
                testcase_id: item.testcase_id,
                testcase_code: item.testcase_code,
                testcase_name: item.testcase_name,
                executor: item.executor || null,  // NEW
                run_at: item.run_at,
                turns: 0,
                passed: 0,
                total_time: 0,
                details: []
            });
        }

        const run = runMap.get(key);
        run.turns++;
        if (item.verdict === 'PASSED') run.passed++;
        if (item.response_time_ms) run.total_time += item.response_time_ms;
        run.details.push(item);
    });

    runMap.forEach(run => {
        runs.push({
            ...run,
            all_passed: run.passed === run.turns,
            failed: run.turns - run.passed,
            avg_time: run.turns > 0 ? Math.round(run.total_time / run.turns) : 0
        });
    });

    return runs;
}

function formatDate(dateStr) {
    if (!dateStr) return 'N/A';

    try {
        // Parse date - Database returns local time in format 'YYYY-MM-DDTHH:MM:SS'
        // We need to treat it as local time, not UTC
        let date;

        if (dateStr.includes('T')) {
            // ISO format: 'YYYY-MM-DDTHH:MM:SS'
            // Parse as local time by removing 'T' and using space
            const localStr = dateStr.replace('T', ' ');
            date = new Date(localStr);
        } else {
            // Already has space: 'YYYY-MM-DD HH:MM:SS'
            date = new Date(dateStr);
        }

        // Check if date is valid
        if (isNaN(date.getTime())) {
            console.error('Invalid date:', dateStr);
            return dateStr; // Return original string if invalid
        }

        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'Vừa xong';
        if (minutes < 60) return `${minutes} phút trước`;
        if (hours < 24) return `${hours} giờ trước`;
        if (days < 7) return `${days} ngày trước`;

        // For older dates, show full date/time
        return date.toLocaleString('vi-VN', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        console.error('Error formatting date:', e, dateStr);
        return dateStr;
    }
}


async function exportSelectedHistory() {
    if (selectedHistoryItems.size === 0) {
        alert('⚠️ Vui lòng chọn ít nhất 1 lịch sử để export');
        return;
    }

    const grouped = window.historyGroupedData;
    if (!grouped) {
        alert('❌ Không tìm thấy dữ liệu history');
        return;
    }

    // Get selected history runs
    const selectedRuns = Array.from(selectedHistoryItems).map(index => grouped[index]);

    // Convert to testcase format for export
    const testcases = selectedRuns.map(run => ({
        code: run.testcase_code,
        name: run.testcase_name,
        executor: run.executor || null,  // NEW
        group: run.group_type || 'GENERAL',
        criteria: run.details[0]?.criteria || 'standard',
        bot_url: null,
        run_at: run.run_at, // Include run time
        turns: run.details.map(turn => ({
            scenario: turn.scenario || null,
            question: turn.question,
            expected: turn.expected,
            required_keywords: turn.required_keywords || null,
            forbidden_keywords: turn.forbidden_keywords || null,
            actual: turn.actual || '',
            action: turn.action || '',
            response_time_ms: turn.response_time_ms || null,
            verdict: turn.verdict || '',
            error_desc: turn.error_desc || '',
            suggestion: turn.suggestion || '',
            suggested_response: turn.suggested_response || '',
            tone_note: turn.tone_note || ''
        }))
    }));

    const btnExport = document.getElementById('btn-export-selected');
    btnExport.disabled = true;
    btnExport.textContent = '⏳ Đang xuất...';

    try {
        const res = await fetch(API_ENDPOINTS.EXPORT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
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
            : `history_export_${new Date().toISOString().slice(0, 19).replace(/[:.]/g, '-')}.xlsx`;

        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        alert(`✅ Đã xuất ${selectedRuns.length} lịch sử ra Excel`);
    } catch (err) {
        alert('❌ Xuất Excel thất bại: ' + err.message);
    } finally {
        btnExport.disabled = false;
        updateExportButtonState();
    }
}
