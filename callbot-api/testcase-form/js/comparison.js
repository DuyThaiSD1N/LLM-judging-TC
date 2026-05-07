// comparison.js — Xử lý so sánh testcase

import { getSelectedTestcases, clearSelection } from './table-v2.js';
import { showToast } from './toast.js';

export function initComparison() {
    const btnCompare = document.getElementById('btn-compare');
    if (btnCompare) {
        btnCompare.addEventListener('click', handleCompare);
    }
}

async function handleCompare() {
    const selected = getSelectedTestcases();

    if (selected.length < 2) {
        showToast('⚠️ Vui lòng chọn ít nhất 2 testcase để so sánh', 'error');
        return;
    }

    if (selected.length > 10) {
        showToast('⚠️ Chỉ có thể so sánh tối đa 10 testcase', 'error');
        return;
    }

    // Validate: Kiểm tra điều kiện chung
    const validation = validateComparison(selected);
    if (!validation.valid) {
        showToast(`⚠️ ${validation.error}`, 'error');
        return;
    }

    console.log('🔍 Comparing testcases:', selected);
    console.log('📊 Comparison mode:', validation.mode);

    // Hiển thị modal so sánh
    showComparisonModal(selected, validation.mode);
}

function validateComparison(testcases) {
    // Kiểm tra: Cùng câu hỏi
    const firstQuestion = testcases[0].turns[0]?.question;
    const sameQuestion = testcases.every(tc =>
        tc.turns.some(turn => turn.question === firstQuestion)
    );

    // Kiểm tra: Cùng bot URL
    const firstBotUrl = testcases[0].bot_url;
    const sameBotUrl = testcases.every(tc => tc.bot_url === firstBotUrl);

    if (sameQuestion && !sameBotUrl) {
        return { valid: true, mode: 'bot_url' };
    }

    if (sameBotUrl && sameQuestion) {
        return { valid: true, mode: 'time' };
    }

    if (!sameQuestion && !sameBotUrl) {
        return { valid: true, mode: 'free' };
    }

    return {
        valid: false,
        error: 'Các testcase không có điểm chung để so sánh. Vui lòng chọn testcase có cùng câu hỏi hoặc cùng bot URL.'
    };
}

function showComparisonModal(testcases, mode) {
    // Remove any existing comparison modal first
    const existingModal = document.getElementById('comparison-modal');
    if (existingModal) {
        existingModal.remove();
    }

    // Tạo modal HTML
    const modal = document.createElement('div');
    modal.id = 'comparison-modal';
    modal.className = 'modal show';

    modal.innerHTML = `
        <div class="modal-content" style="max-width: 95%; max-height: 95vh;">
            <div class="modal-header">
                <h2>⚖️ So sánh ${testcases.length} Testcase</h2>
                <button id="btn-close-comparison" class="btn-close">✕</button>
            </div>
            <div class="modal-body">
                <div class="comparison-tabs">
                    <button class="comparison-tab active" data-tab="table">📊 Bảng so sánh</button>
                    <button class="comparison-tab" data-tab="analysis">🤖 Phân tích LLM</button>
                </div>
                
                <div class="comparison-content">
                    <div class="comparison-tab-content active" data-content="table">
                        ${renderComparisonTable(testcases)}
                    </div>
                    <div class="comparison-tab-content" data-content="analysis">
                        <div class="llm-analysis-loading">
                            <div class="spinner-cell"></div>
                            <p>Đang phân tích với LLM...</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Setup event listeners
    setupModalListeners(modal, testcases, mode);

    // Start LLM analysis
    analyzWithLLM(testcases, mode);
}

function getModeBadge(mode) {
    const badges = {
        'bot_url': '<span class="mode-badge mode-bot-url">📊 So sánh theo Bot URL</span>',
        'time': '<span class="mode-badge mode-time">⏱️ So sánh theo Thời gian</span>',
        'free': '<span class="mode-badge mode-free">🔄 So sánh tự do</span>'
    };
    return badges[mode] || '';
}

function renderComparisonTable(testcases) {
    const rows = testcases.map(tc => {
        const turn = tc.turns[0]; // Lấy turn đầu tiên
        const timeDisplay = turn.response_time_ms
            ? (turn.response_time_ms >= 1000
                ? `${(turn.response_time_ms / 1000).toFixed(1)}s`
                : `${turn.response_time_ms}ms`)
            : '—';

        return `
            <tr>
                <td class="col-code">${tc.code}</td>
                <td class="col-name">${tc.name}</td>
                <td class="col-bot-url">${tc.bot_url || '<span class="cell-empty">mặc định</span>'}</td>
                <td class="col-q">${turn.question}</td>
                <td class="col-actual">${turn.actual || '—'}</td>
                <td class="col-time">${timeDisplay}</td>
                <td class="col-verdict">
                    ${turn.verdict === 'PASSED'
                ? '<span class="verdict-pass">✓ Đạt yêu cầu</span>'
                : turn.verdict === 'FAILED'
                    ? '<span class="verdict-fail">⚠ Cần cải thiện</span>'
                    : '—'}
                </td>
            </tr>
        `;
    }).join('');

    return `
        <div class="comparison-table-wrap">
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>Mã TC</th>
                        <th>Tên</th>
                        <th>Bot URL</th>
                        <th>Câu hỏi</th>
                        <th>Câu trả lời thực tế</th>
                        <th>Thời gian</th>
                        <th>Kết quả</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows}
                </tbody>
            </table>
        </div>
    `;
}

function renderMetrics(testcases) {
    // Tính toán metrics
    const times = testcases
        .map(tc => tc.turns[0]?.response_time_ms)
        .filter(t => t != null);

    const fastest = times.length > 0 ? Math.min(...times) : 0;
    const slowest = times.length > 0 ? Math.max(...times) : 0;
    const average = times.length > 0
        ? Math.round(times.reduce((a, b) => a + b, 0) / times.length)
        : 0;

    const passCount = testcases.filter(tc => tc.turns[0]?.verdict === 'PASSED').length;
    const passRate = testcases.length > 0
        ? Math.round((passCount / testcases.length) * 100)
        : 0;

    const fastestTc = testcases.find(tc => tc.turns[0]?.response_time_ms === fastest);
    const slowestTc = testcases.find(tc => tc.turns[0]?.response_time_ms === slowest);

    return `
        <div class="metrics-dashboard">
            <div class="metric-card">
                <div class="metric-icon">⚡</div>
                <div class="metric-label">Nhanh nhất</div>
                <div class="metric-value">${fastest}ms</div>
                <div class="metric-sub">${fastestTc?.code || '—'}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-icon">🐌</div>
                <div class="metric-label">Chậm nhất</div>
                <div class="metric-value">${slowest}ms</div>
                <div class="metric-sub">${slowestTc?.code || '—'}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-icon">📈</div>
                <div class="metric-label">Trung bình</div>
                <div class="metric-value">${average}ms</div>
                <div class="metric-sub">Avg time</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-icon">✅</div>
                <div class="metric-label">Pass Rate</div>
                <div class="metric-value">${passRate}%</div>
                <div class="metric-sub">${passCount}/${testcases.length} passed</div>
            </div>
        </div>
        
        <div class="metrics-chart">
            <h3>Biểu đồ thời gian phản hồi</h3>
            <div class="bar-chart">
                ${testcases.map(tc => {
        const time = tc.turns[0]?.response_time_ms || 0;
        const maxTime = slowest || 1;
        const width = (time / maxTime) * 100;
        const isFastest = time === fastest;
        const isSlowest = time === slowest;
        const barClass = isFastest ? 'bar-fastest' : isSlowest ? 'bar-slowest' : 'bar-normal';

        return `
                        <div class="bar-row">
                            <div class="bar-label">${tc.code}</div>
                            <div class="bar-container">
                                <div class="bar ${barClass}" style="width: ${width}%">
                                    <span class="bar-value">${time}ms</span>
                                </div>
                            </div>
                        </div>
                    `;
    }).join('')}
            </div>
        </div>
    `;
}

async function analyzWithLLM(testcases, mode) {
    const analysisContent = document.querySelector('[data-content="analysis"]');

    try {
        // Prepare request data
        const requestData = {
            testcases: testcases.map(tc => ({
                code: tc.code,
                name: tc.name,
                bot_url: tc.bot_url || null,
                question: tc.turns[0]?.question || '',
                expected: tc.turns[0]?.expected || '',
                actual: tc.turns[0]?.actual || '',
                response_time_ms: tc.turns[0]?.response_time_ms || null,
                // Removed verdict - LLM tự đánh giá dựa trên expected vs actual
                error_desc: tc.turns[0]?.error_desc || '',
                // Keywords để hỗ trợ LLM (optional)
                required_keywords: tc.turns[0]?.required_keywords || null,
                forbidden_keywords: tc.turns[0]?.forbidden_keywords || null
            })),
            comparison_mode: mode
        };

        // Call API
        const response = await fetch('/api/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const result = await response.json();

        // Render LLM analysis
        if (analysisContent) {
            analysisContent.innerHTML = renderLLMAnalysis(result, testcases);
        }

    } catch (error) {
        console.error('❌ LLM analysis error:', error);
        if (analysisContent) {
            analysisContent.innerHTML = `
                <div class="llm-analysis error">
                    <div class="analysis-section">
                        <h3>❌ Lỗi phân tích</h3>
                        <p>Không thể phân tích với LLM: ${error.message}</p>
                        <button class="btn-retry" onclick="location.reload()">🔄 Thử lại</button>
                    </div>
                </div>
            `;
        }
    }
}

function renderLLMAnalysis(result, testcases) {
    const analysis = result.llm_analysis;

    // Render Performance Analysis
    const perfAnalysis = analysis.performance_analysis || {};
    const fastest = perfAnalysis.fastest || {};
    const slowest = perfAnalysis.slowest || {};

    const performanceHtml = `
        <div class="perf-grid">
            <div class="perf-card perf-fastest">
                <div class="perf-icon">⚡</div>
                <div class="perf-header">
                    <h4>Nhanh nhất</h4>
                    <span class="perf-code">${fastest.testcase_code || 'N/A'}</span>
                </div>
                <div class="perf-time">${fastest.time_ms || 0}ms</div>
                <div class="perf-eval">${fastest.evaluation || 'N/A'}</div>
                <div class="perf-reason">${fastest.reason || ''}</div>
            </div>
            
            <div class="perf-card perf-slowest">
                <div class="perf-icon">🐌</div>
                <div class="perf-header">
                    <h4>Chậm nhất</h4>
                    <span class="perf-code">${slowest.testcase_code || 'N/A'}</span>
                </div>
                <div class="perf-time">${slowest.time_ms || 0}ms</div>
                <div class="perf-eval">${slowest.evaluation || 'N/A'}</div>
                <div class="perf-reason">${slowest.reason || ''}</div>
            </div>
        </div>
        <div class="perf-overall">
            <strong>Đánh giá chung:</strong> ${perfAnalysis.overall_speed || 'N/A'}
        </div>
    `;

    // Render Content Analysis
    const contentAnalysis = analysis.content_analysis || {};
    const bestResponse = contentAnalysis.best_response || {};
    const weakestResponse = contentAnalysis.weakest_response || {};

    const contentHtml = `
        <div class="content-comparison">
            <div class="content-card content-best">
                <div class="content-header">
                    <span class="content-icon">🏆</span>
                    <h4>Câu trả lời tốt nhất</h4>
                    <span class="content-code">${bestResponse.testcase_code || 'N/A'}</span>
                </div>
                <div class="content-reason">${bestResponse.reason || ''}</div>
                ${bestResponse.strengths && bestResponse.strengths.length > 0 ? `
                    <div class="content-strengths">
                        <strong>Điểm mạnh:</strong>
                        <ul>
                            ${bestResponse.strengths.map(s => `<li>${s}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
            
            <div class="content-card content-weakest">
                <div class="content-header">
                    <span class="content-icon">⚠️</span>
                    <h4>Câu trả lời yếu nhất</h4>
                    <span class="content-code">${weakestResponse.testcase_code || 'N/A'}</span>
                </div>
                <div class="content-reason">${weakestResponse.reason || ''}</div>
                ${weakestResponse.weaknesses && weakestResponse.weaknesses.length > 0 ? `
                    <div class="content-weaknesses">
                        <strong>Điểm yếu:</strong>
                        <ul>
                            ${weakestResponse.weaknesses.map(w => `<li>${w}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                ${weakestResponse.missing_info && weakestResponse.missing_info.length > 0 ? `
                    <div class="content-missing">
                        <strong>Thông tin còn thiếu cần bổ sung:</strong>
                        <ul>
                            ${weakestResponse.missing_info.map(m => `<li>${m}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        </div>
        ${contentAnalysis.similarity_note ? `
            <div class="content-similarity-note">
                <strong>Độ tương đồng:</strong> ${contentAnalysis.similarity_note}
            </div>
        ` : ''}
    `;

    // Render Recommendations
    const recommendations = analysis.recommendations || [];
    const recommendationsHtml = recommendations.length > 0
        ? `
            <div class="recommendations-list">
                ${recommendations.map(rec => `
                    <div class="recommendation-card priority-${rec.priority.toLowerCase()}">
                        <div class="rec-header">
                            <span class="rec-priority">${rec.priority}</span>
                            <span class="rec-category">${rec.category}</span>
                            <span class="rec-target">${rec.target}</span>
                        </div>
                        <h4 class="rec-title">${rec.title}</h4>
                        <p class="rec-description">${rec.description}</p>
                        ${rec.specific_actions && rec.specific_actions.length > 0 ? `
                            <div class="rec-actions">
                                <strong>Hành động cụ thể:</strong>
                                <ul>
                                    ${rec.specific_actions.map(a => `<li>${a}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                        <div class="rec-improvement">
                            <strong>Kết quả mong đợi:</strong> ${rec.expected_improvement}
                        </div>
                    </div>
                `).join('')}
            </div>
        `
        : '<p class="empty-state">Không có đề xuất</p>';

    return `
        <div class="llm-analysis">
            <div class="analysis-section">
                <h3>🎯 Tổng quan</h3>
                <p class="analysis-overview">${analysis.overview || 'Không có tổng quan'}</p>
            </div>

            <div class="analysis-section">
                <h3>⚡ So sánh Performance</h3>
                ${performanceHtml}
            </div>

            <div class="analysis-section">
                <h3>📝 So sánh Nội dung</h3>
                ${contentHtml}
            </div>

            <div class="analysis-section">
                <h3>💡 Đề xuất cải thiện cho cả 2 testcase</h3>
                ${recommendationsHtml}
            </div>

            <div class="analysis-section conclusion">
                <h3>🎬 Kết luận</h3>
                <p class="analysis-conclusion">${analysis.conclusion || 'Không có kết luận'}</p>
            </div>
        </div>
    `;
}



function updateMetricsWithSimilarity(similarityMatrix, testcases) {
    const metricsContent = document.querySelector('[data-content="metrics"]');
    if (!metricsContent) return;

    // Find existing metrics dashboard
    const dashboard = metricsContent.querySelector('.metrics-dashboard');
    if (!dashboard) return;

    // Add similarity section after metrics dashboard
    const existingSimilarity = metricsContent.querySelector('.similarity-section');
    if (existingSimilarity) {
        existingSimilarity.remove();
    }

    const similarityHtml = renderSimilarityMatrix(similarityMatrix, testcases);
    dashboard.insertAdjacentHTML('afterend', similarityHtml);
}

function renderSimilarityMatrix(matrix, testcases) {
    const n = testcases.length;

    // Build matrix HTML
    let matrixHtml = '<table class="similarity-matrix"><thead><tr><th></th>';
    for (let i = 0; i < n; i++) {
        matrixHtml += `<th>${testcases[i].code}</th>`;
    }
    matrixHtml += '</tr></thead><tbody>';

    for (let i = 0; i < n; i++) {
        matrixHtml += `<tr><th>${testcases[i].code}</th>`;
        for (let j = 0; j < n; j++) {
            const score = matrix[i][j];
            const percent = Math.round(score * 100);
            const colorClass = score >= 0.9 ? 'sim-high' : score >= 0.7 ? 'sim-medium' : 'sim-low';
            matrixHtml += `<td class="${colorClass}">${percent}%</td>`;
        }
        matrixHtml += '</tr>';
    }
    matrixHtml += '</tbody></table>';

    return `
        <div class="similarity-section">
            <h3>🔗 Semantic Similarity Matrix</h3>
            <p class="similarity-desc">Độ tương đồng ngữ nghĩa giữa các câu trả lời (sử dụng OpenAI embeddings)</p>
            ${matrixHtml}
            <div class="similarity-legend">
                <span class="legend-item"><span class="legend-color sim-high"></span> ≥90% (Rất cao)</span>
                <span class="legend-item"><span class="legend-color sim-medium"></span> 70-89% (Cao)</span>
                <span class="legend-item"><span class="legend-color sim-low"></span> <70% (Thấp)</span>
            </div>
        </div>
    `;
}

function setupModalListeners(modal, testcases, mode) {
    // Close button
    const btnClose = modal.querySelector('#btn-close-comparison');
    if (btnClose) {
        btnClose.addEventListener('click', () => {
            modal.remove();
        });
    }

    // Click outside to close
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });

    // Tab switching
    const tabs = modal.querySelectorAll('.comparison-tab');
    const contents = modal.querySelectorAll('.comparison-tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;

            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Update active content
            contents.forEach(c => c.classList.remove('active'));
            const targetContent = modal.querySelector(`[data-content="${targetTab}"]`);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });
}


function renderVisualDiff(diffPairs, testcases) {
    if (!diffPairs || diffPairs.length === 0) {
        return `
            <div class="diff-empty">
                <p>Không có diff để hiển thị</p>
            </div>
        `;
    }

    const pairsHtml = diffPairs.map(pair => {
        const tc1 = testcases[pair.index1];
        const tc2 = testcases[pair.index2];

        // Render diff operations
        const diffHtml = pair.diff_ops.map(op => {
            if (op.op === 'equal') {
                return `<span class="diff-equal">${escapeHtml(op.text)}</span>`;
            } else if (op.op === 'insert') {
                return `<span class="diff-insert">${escapeHtml(op.text)}</span>`;
            } else if (op.op === 'delete') {
                return `<span class="diff-delete">${escapeHtml(op.text)}</span>`;
            }
            return '';
        }).join('');

        const similarityClass = pair.similarity_percent >= 90 ? 'sim-high'
            : pair.similarity_percent >= 70 ? 'sim-medium'
                : 'sim-low';

        return `
            <div class="diff-pair-card">
                <div class="diff-pair-header">
                    <div class="diff-pair-title">
                        <span class="diff-code">${pair.code1}</span>
                        <span class="diff-arrow">→</span>
                        <span class="diff-code">${pair.code2}</span>
                    </div>
                    <div class="diff-similarity ${similarityClass}">
                        ${pair.similarity_percent.toFixed(1)}% similar
                    </div>
                </div>
                <div class="diff-content">
                    <div class="diff-view">
                        ${diffHtml}
                    </div>
                </div>
                <div class="diff-legend-inline">
                    <span class="legend-item"><span class="diff-equal">Không đổi</span></span>
                    <span class="legend-item"><span class="diff-insert">Thêm vào</span></span>
                    <span class="legend-item"><span class="diff-delete">Xóa đi</span></span>
                </div>
            </div>
        `;
    }).join('');

    return `
        <div class="visual-diff-container">
            <div class="diff-header">
                <h3>🔍 Visual Diff (Myers Algorithm)</h3>
                <p class="diff-desc">So sánh từng cặp câu trả lời với thuật toán Myers để tìm sự khác biệt</p>
            </div>
            <div class="diff-pairs-list">
                ${pairsHtml}
            </div>
        </div>
    `;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
