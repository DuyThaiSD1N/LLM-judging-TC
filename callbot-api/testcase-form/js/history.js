// history.js — Quản lý modal lịch sử đánh giá

import { API_ENDPOINTS, API_KEY } from './config.js';

export function initHistory() {
    const modal = document.getElementById('history-modal');
    const btnOpen = document.getElementById('btn-history');
    const btnClose = document.getElementById('btn-close-history');

    btnOpen.addEventListener('click', () => {
        openHistoryModal();
    });

    btnClose.addEventListener('click', () => {
        modal.classList.remove('show');
    });

    // Click outside to close
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('show');
        }
    });
}

async function openHistoryModal() {
    const modal = document.getElementById('history-modal');
    modal.classList.add('show');

    // Load stats and history
    await Promise.all([
        loadStats(),
        loadHistory()
    ]);
}

async function loadStats() {
    const statsContainer = document.getElementById('history-stats');
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
            <div class="history-item" data-run-index="${index}">
                <div class="history-header">
                    <div class="history-title">
                        ${run.testcase_name} <span style="color:#94a3b8;font-weight:400;">(${run.testcase_code})</span>
                    </div>
                    <div class="history-time">${formatDate(run.run_at)}</div>
                </div>
                <div class="history-meta">
                    <span>Nhóm: <strong>${run.group_type}</strong></span>
                    <span>Lượt: <strong>${run.turns}</strong></span>
                    <span style="color:#16a34a;">✓ Đạt: <strong>${run.passed}</strong></span>
                    <span style="color:#dc2626;">✕ Không đạt: <strong>${run.failed}</strong></span>
                    <span>Thời gian TB: <strong>${run.avg_time}ms</strong></span>
                </div>
                <div class="history-details">
                    ${run.details.map((turn, i) => `
                        <div class="turn-detail ${turn.verdict === 'PASSED' ? 'pass' : 'fail'}">
                            <div class="turn-header">Lượt ${i + 1} - ${turn.verdict || 'N/A'}</div>
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
                                <div class="turn-row" style="margin-top:12px;padding-top:12px;border-top:1px dashed #e2e8f0;">
                                    <div class="turn-label" style="color:#16a34a;font-weight:700;">📝 Mẫu đề xuất:</div>
                                    <div class="turn-value" style="color:#15803d;background:#f0fdf4;padding:12px;border-radius:6px;border-left:3px solid #16a34a;line-height:1.6;">${turn.suggested_response}</div>
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');

        // Add click handlers
        document.querySelectorAll('.history-item').forEach(item => {
            item.addEventListener('click', () => {
                item.classList.toggle('expanded');
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
                group_type: item.group_type,
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
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Vừa xong';
    if (minutes < 60) return `${minutes} phút trước`;
    if (hours < 24) return `${hours} giờ trước`;
    if (days < 7) return `${days} ngày trước`;

    return date.toLocaleDateString('vi-VN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}
