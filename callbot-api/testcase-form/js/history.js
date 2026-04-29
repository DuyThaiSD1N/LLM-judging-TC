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

        listContainer.innerHTML = grouped.map(run => `
            <div class="history-item">
                <div class="history-header">
                    <div class="history-title">
                        ${run.testcase_name} <span style="color:#94a3b8;font-weight:400;">(${run.testcase_code})</span>
                    </div>
                    <div class="history-time">${formatDate(run.run_at)}</div>
                </div>
                <div class="history-meta">
                    <span>Nhóm: <strong>${run.group_type}</strong></span>
                    <span>Lượt: <strong>${run.turns}</strong></span>
                    <span>Thời gian TB: <strong>${run.avg_time}ms</strong></span>
                    <span class="history-result ${run.all_passed ? 'passed' : 'failed'}">
                        ${run.all_passed ? '✓ PASS' : '✕ FAIL'}
                    </span>
                </div>
            </div>
        `).join('');
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
                total_time: 0
            });
        }

        const run = runMap.get(key);
        run.turns++;
        if (item.verdict === 'PASS') run.passed++;
        if (item.response_time_ms) run.total_time += item.response_time_ms;
    });

    runMap.forEach(run => {
        runs.push({
            ...run,
            all_passed: run.passed === run.turns,
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
