// history.js — Xem lịch sử đánh giá testcase

import { API_ENDPOINTS, getAuthHeaders } from './config.js';
import { showToast } from './toast.js';

export function initHistory() {
    const modal = document.getElementById('history-modal');
    const btnView = document.getElementById('btn-view-history');
    const btnClose = document.getElementById('btn-close-history');

    btnView.addEventListener('click', async () => {
        modal.classList.add('show');
        await loadHistory();
    });

    btnClose.addEventListener('click', () => {
        modal.classList.remove('show');
    });

    // Close khi click outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('show');
        }
    });
}

async function loadHistory() {
    try {
        // Load stats
        const statsRes = await fetch(`${API_ENDPOINTS.TESTCASES.replace('/testcases', '/history/stats')}?days=7`, {
            headers: getAuthHeaders()
        });
        const statsData = await statsRes.json();

        // Load history list
        const historyRes = await fetch(`${API_ENDPOINTS.TESTCASES.replace('/testcases', '/history')}?limit=20`, {
            headers: getAuthHeaders()
        });
        const historyData = await historyRes.json();

        renderStats(statsData);
        renderHistoryList(historyData.histories || []);
    } catch (error) {
        console.error('Error loading history:', error);
        showToast('Không thể tải lịch sử', 'error');
    }
}

function renderStats(stats) {
    const container = document.getElementById('history-stats');
    container.innerHTML = `
        <div class="stat-card">
            <div class="stat-label">Tổng lần chạy</div>
            <div class="stat-value">${stats.total_runs || 0}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Testcases</div>
            <div class="stat-value">${stats.unique_testcases || 0}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Pass Rate</div>
            <div class="stat-value" style="color: ${stats.pass_rate >= 80 ? '#15803d' : stats.pass_rate >= 60 ? '#d97706' : '#dc2626'}">
                ${stats.pass_rate || 0}%
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Avg Response Time</div>
            <div class="stat-value" style="font-size: 1.5rem;">
                ${stats.avg_response_time || 0}ms
            </div>
        </div>
    `;
}

function renderHistoryList(histories) {
    const container = document.getElementById('history-list');

    if (histories.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #94a3b8; padding: 40px;">Chưa có lịch sử nào</p>';
        return;
    }

    container.innerHTML = histories.map(h => {
        const passRate = h.total_turns > 0
            ? ((h.passed_turns / h.total_turns) * 100).toFixed(0)
            : 0;
        const resultClass = passRate >= 80 ? 'passed' : 'failed';
        const runDate = new Date(h.run_at).toLocaleString('vi-VN');

        return `
            <div class="history-item">
                <div class="history-header">
                    <div>
                        <span class="history-title">${h.testcase_name}</span>
                        <span class="tag tag-${h.group}" style="margin-left: 8px;">${h.group}</span>
                    </div>
                    <span class="history-time">${runDate}</span>
                </div>
                <div class="history-meta">
                    <span>Code: <strong>${h.testcase_code}</strong></span>
                    <span>•</span>
                    <span>Lượt: <strong>${h.total_turns}</strong></span>
                    <span>•</span>
                    <span class="history-result ${resultClass}">
                        ${h.passed_turns}/${h.total_turns} PASSED (${passRate}%)
                    </span>
                    <span>•</span>
                    <span>Avg: <strong>${h.avg_response_time}ms</strong></span>
                </div>
            </div>
        `;
    }).join('');
}
