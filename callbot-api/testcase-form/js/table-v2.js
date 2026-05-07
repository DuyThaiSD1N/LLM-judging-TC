// table.js — quản lý state testcases (multi-turn) và render bảng đánh giá
// VERSION: 2024-05-06-v7 - FIXED reasoning object handling - CACHE BUSTED

import { filterTestcases } from './filter-v2.js';
import { getIsRunning } from './state.js';

console.log('✅ table.js loaded - VERSION 2024-05-06-v7 (FIXED reasoning object)');
console.log('🔍 Action buttons: ▶ Run, ✏️ Edit, 🗑 Delete ONLY');

let testcases = [];
let _runSingleFn = null;

export function setRunSingleFn(fn) { _runSingleFn = fn; }
export function getTestcases() { return testcases; }

export function addTestcase(tc) {
  console.log('🔍 addTestcase - Input tc:', tc);
  const newTc = initRow(tc);
  console.log('🔍 addTestcase - After initRow:', newTc);
  testcases.push(newTc);
  renderEval();
}

export function addBulkTestcases(list) {
  list.forEach(tc => testcases.push(initRow(tc)));
  renderEval();
}

export function deleteTestcase(idx) {
  testcases.splice(idx, 1);
  renderEval();
}

export function clearAllTestcases() {
  testcases = [];
  selectedIndices.clear(); // Clear selection
  renderEval();
  updateSelectionUI(); // Update compare button

  // Force enable upload zone (in case it was disabled during run)
  const fileInput = document.getElementById('file-input');
  const uploadZone = document.getElementById('upload-zone');

  if (fileInput) {
    fileInput.disabled = false;
    fileInput.value = ''; // Reset file input
    console.log('✅ File input enabled and reset');
  }

  if (uploadZone) {
    uploadZone.style.opacity = '1';
    uploadZone.style.cursor = 'pointer';
    uploadZone.style.pointerEvents = 'auto';
    console.log('✅ Upload zone enabled');
  }
}

export function updateTestcase(idx, updatedTc) {
  if (!testcases[idx]) return;
  testcases[idx] = initRow(updatedTc);
  renderEval();
}

function editTestcase(idx) {
  const tc = testcases[idx];
  if (!tc) return;

  // Dispatch custom event để form.js xử lý
  window.dispatchEvent(new CustomEvent('edit-testcase', {
    detail: { index: idx, testcase: tc }
  }));
}

export function setTurnResult(tcIdx, turnIdx, fields) {
  const tc = testcases[tcIdx];
  if (!tc || !tc.turns[turnIdx]) return;
  Object.assign(tc.turns[turnIdx], fields);
}

// Cập nhật trạng thái tổng của testcase
export function setTcStatus(tcIdx, status, error = '') {
  if (!testcases[tcIdx]) return;
  testcases[tcIdx].status = status;
  testcases[tcIdx].error = error;
}

// Reset turn data về trạng thái ban đầu (giữ question/expected/keywords, xóa kết quả cũ)
export function resetTurnData(tcIdx) {
  const tc = testcases[tcIdx];
  if (!tc) return;
  tc.turns = tc.turns.map(t => ({
    question: t.question,
    expected: t.expected,
    required_keywords: t.required_keywords || null,  // Preserve keywords
    forbidden_keywords: t.forbidden_keywords || null,  // Preserve keywords
    actual: null,
    action: '',
    response_time_ms: null,
    verdict: null,
    reasoning: '',
    error_desc: '',
    suggestion: '',
    suggested_response: '',
    tone_note: '',
    time_verdict: null,
    time_note: '',
  }));
}

function initRow(tc) {
  // Hỗ trợ cả format cũ (question/expected string) và mới (turns array)
  let turns = tc.turns;
  if (!turns) {
    turns = [{ question: tc.question ?? '', expected: tc.expected ?? '' }];
  }

  console.log('🔍 initRow - tc.bot_url:', tc.bot_url);
  console.log('🔍 initRow - saved bot_url:', tc.bot_url || null);

  return {
    code: tc.code,
    name: tc.name,
    group: tc.group,
    criteria: tc.criteria || 'standard',
    bot_url: tc.bot_url || null,
    status: 'pending',
    error: '',
    turns: turns.map(t => ({
      question: t.question,
      expected: t.expected,
      required_keywords: t.required_keywords || null,  // Preserve keywords
      forbidden_keywords: t.forbidden_keywords || null,  // Preserve keywords
      actual: null,
      action: '',
      response_time_ms: null,
      verdict: null,
      reasoning: '',
      error_desc: '',
      suggestion: '',
      suggested_response: '',
      tone_note: '',
      time_verdict: null,
      time_note: '',
    })),
  };
}

// ── Render ────────────────────────────────────────────────────────────────
export function renderEval() {
  document.getElementById('tc-count').textContent = testcases.length;
  const container = document.getElementById('table-container');

  // Áp dụng filter
  const filteredTestcases = filterTestcases(testcases);

  // Hiển thị số lượng đã filter
  const filterInfo = document.getElementById('filter-info');
  if (filteredTestcases.length < testcases.length) {
    filterInfo.textContent = `Hiển thị ${filteredTestcases.length}/${testcases.length} testcase`;
    filterInfo.style.display = 'block';
  } else {
    filterInfo.style.display = 'none';
  }

  if (filteredTestcases.length === 0) {
    if (testcases.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">📭</div>
          <p>Chưa có testcase nào.</p>
          <p class="empty-sub">Thêm testcase bên trên hoặc import từ Excel.</p>
        </div>`;
    } else {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">🔍</div>
          <p>Không tìm thấy testcase nào phù hợp với bộ lọc.</p>
          <p class="empty-sub">Thử thay đổi điều kiện lọc.</p>
        </div>`;
    }
    return;
  }

  const rows = filteredTestcases.map((tc, i) => {
    const turnCount = tc.turns.length;

    console.log(`🔍 Rendering TC ${i} - bot_url:`, tc.bot_url);

    // Map criteria ID to display name
    const criteriaNames = {
      'standard': 'Chuẩn',
      'strict': 'Nghiêm ngặt',
      'speed-focused': 'Tốc độ',
      'content-only': 'Nội dung',
      'ux-focused': 'Trải nghiệm'
    };
    const criteriaDisplay = criteriaNames[tc.criteria] || tc.criteria;

    return tc.turns.map((turn, j) => {
      const isFirst = j === 0;
      const rowClass = isFirst ? 'tc-first-row' : 'tc-sub-row';

      const checkboxCell = isFirst ? `
        <td class="col-checkbox" rowspan="${turnCount}">
          <input type="checkbox" class="tc-checkbox" data-idx="${i}" 
            ${tc.status !== 'done' ? 'disabled' : ''} />
        </td>` : '';

      const tcCells = isFirst ? `
        <td class="col-num"  rowspan="${turnCount}">${i + 1}</td>
        <td class="col-code" rowspan="${turnCount}">${tc.code}</td>
        <td class="col-name" rowspan="${turnCount}">${tc.name}</td>
        <td class="col-criteria" rowspan="${turnCount}"><span class="criteria-badge">${criteriaDisplay}</span></td>
        <td class="col-bot-url" rowspan="${turnCount}">${tc.bot_url
          ? `<span class="bot-url-text" title="${tc.bot_url}">${tc.bot_url}</span>`
          : '<span class="cell-empty">mặc định</span>'
        }</td>` : '';

      const actionCell = isFirst ? `
        <td class="col-actions" rowspan="${turnCount}">
          <button class="btn-run-one" data-idx="${i}" title="Chạy testcase này">▶</button>
          <button class="btn-edit"    data-idx="${i}" title="Sửa">✏️</button>
          <button class="btn-del"     data-idx="${i}" title="Xóa">🗑</button>
        </td>` : '';

      return `
        <tr class="${rowClass}">
          ${checkboxCell}
          ${tcCells}
          <td class="col-turn-num">Lượt ${j + 1}</td>
          <td class="col-q">${turn.question}</td>
          <td class="col-e">${turn.expected}</td>
          <td class="col-keywords">${turn.required_keywords || '<span class="cell-empty">—</span>'}</td>
          <td class="col-keywords">${turn.forbidden_keywords || '<span class="cell-empty">—</span>'}</td>
          <td class="col-actual">${renderActual(turn, tc.status)}</td>
          <td class="col-time">${renderTime(turn, tc.status)}</td>
          <td class="col-verdict">${renderVerdict(turn, tc.status)}</td>
          <td class="col-err">${renderErrorDesc(turn, tc.status)}</td>
          <td class="col-suggest">${renderSuggestion(turn, tc.status)}</td>
          ${actionCell}
        </tr>`;
    }).join('');
  }).join('');

  container.innerHTML = `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th class="col-checkbox">
              <input type="checkbox" id="select-all-checkbox" title="Chọn tất cả" />
            </th>
            <th>#</th>
            <th>Mã TC</th>
            <th>Tên Testcase</th>
            <th>LLM Judge</th>
            <th>Bot URL</th>
            <th>Lượt</th>
            <th>Câu hỏi từ User</th>
            <th>Câu trả lời kỳ vọng</th>
            <th>Từ khóa bắt buộc</th>
            <th>Từ khóa cấm</th>
            <th>Câu trả lời thực tế</th>
            <th>Thời gian</th>
            <th>Kết quả</th>
            <th>Lỗi</th>
            <th>Đề xuất sửa</th>
            <th></th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;

  // Event listeners
  container.querySelectorAll('.btn-del').forEach(btn =>
    btn.addEventListener('click', () => deleteTestcase(Number(btn.dataset.idx))));

  container.querySelectorAll('.btn-run-one').forEach(btn =>
    btn.addEventListener('click', () => _runSingleFn?.(Number(btn.dataset.idx))));

  container.querySelectorAll('.btn-edit').forEach(btn =>
    btn.addEventListener('click', () => editTestcase(Number(btn.dataset.idx))));

  // Disable buttons if running
  const running = getIsRunning();
  if (running) {
    container.querySelectorAll('.btn-edit, .btn-del, .btn-run-one').forEach(el => {
      el.disabled = true;
      el.style.opacity = '0.5';
      el.style.cursor = 'not-allowed';
    });
  }

  // Setup checkbox listeners
  setupCheckboxListeners();
}

// ── Checkbox Selection Logic ──────────────────────────────────────────────
let selectedIndices = new Set();

function setupCheckboxListeners() {
  const selectAllCheckbox = document.getElementById('select-all-checkbox');
  const checkboxes = document.querySelectorAll('.tc-checkbox:not([disabled])');

  // Select all
  if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener('change', (e) => {
      const isChecked = e.target.checked;
      checkboxes.forEach(cb => {
        cb.checked = isChecked;
        const idx = Number(cb.dataset.idx);
        if (isChecked) {
          selectedIndices.add(idx);
        } else {
          selectedIndices.delete(idx);
        }
      });
      updateSelectionUI();
    });
  }

  // Individual checkboxes
  checkboxes.forEach(cb => {
    cb.addEventListener('change', (e) => {
      const idx = Number(e.target.dataset.idx);
      if (e.target.checked) {
        selectedIndices.add(idx);
      } else {
        selectedIndices.delete(idx);
      }

      // Update select-all checkbox
      if (selectAllCheckbox) {
        selectAllCheckbox.checked = selectedIndices.size === checkboxes.length;
      }

      updateSelectionUI();
    });
  });
}

function updateSelectionUI() {
  const count = selectedIndices.size;

  // Update comparison button state
  const btnCompare = document.getElementById('btn-compare');
  if (btnCompare) {
    if (count >= 2 && count <= 10) {
      btnCompare.disabled = false;
      btnCompare.textContent = `⚖️ So sánh (${count})`;
    } else {
      btnCompare.disabled = true;
      if (count === 0) {
        btnCompare.textContent = '⚖️ So sánh';
      } else if (count === 1) {
        btnCompare.textContent = '⚖️ So sánh (chọn thêm ≥1)';
      } else {
        btnCompare.textContent = `⚖️ So sánh (tối đa 10)`;
      }
    }
  }
}

export function getSelectedTestcases() {
  return Array.from(selectedIndices).map(idx => testcases[idx]).filter(tc => tc);
}

export function clearSelection() {
  selectedIndices.clear();
  document.querySelectorAll('.tc-checkbox').forEach(cb => cb.checked = false);
  const selectAllCheckbox = document.getElementById('select-all-checkbox');
  if (selectAllCheckbox) selectAllCheckbox.checked = false;
  updateSelectionUI();
}

// ── Cell renderers ────────────────────────────────────────────────────────
function renderActual(turn, tcStatus) {
  if (tcStatus === 'pending') return '<span class="cell-empty">—</span>';
  if (tcStatus === 'running' && turn.actual === null) {
    return '<div class="cell-loading"><span class="spinner-cell"></span></div>';
  }
  if (tcStatus === 'error' && turn.actual === null) return `<span class="actual-error">❌ Lỗi</span>`;
  if (turn.actual === null) return '<span class="cell-empty">—</span>';

  const badge = turn.action
    ? `<span class="action-badge action-${turn.action}">${turn.action}</span>`
    : '';
  return `<div class="actual-text">${turn.actual}</div>${badge}`;
}

function renderTime(turn, tcStatus) {
  if (tcStatus === 'pending') return '<span class="cell-empty">—</span>';
  if (tcStatus === 'running' && turn.response_time_ms === null) {
    return '<div class="cell-loading"><span class="spinner-cell"></span></div>';
  }
  if (turn.response_time_ms == null) return '<span class="cell-empty">—</span>';

  const ms = turn.response_time_ms;
  const display = ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`;
  const level = turn.time_verdict ?? (ms <= 2000 ? 'good' : ms <= 3000 ? 'ok' : 'slow');
  const note = turn.time_note ? `title="${turn.time_note}"` : '';
  return `<span class="time-badge time-${level}" ${note}>${display}</span>`;
}

function renderVerdict(turn, tcStatus) {
  if (tcStatus === 'pending') return '<span class="cell-empty">—</span>';
  if (tcStatus === 'running' && turn.verdict === null) {
    return '<div class="cell-loading"><span class="spinner-cell"></span></div>';
  }
  if (tcStatus === 'error') return '<span class="verdict-fail">✕ Lỗi</span>';
  if (turn.actual === null) return '<span class="cell-empty">—</span>';
  if (!turn.verdict) return '<span class="verdict-fail">✕ Lỗi đánh giá</span>';

  return turn.verdict === 'PASSED'
    ? '<span class="verdict-pass">✓ Đạt yêu cầu</span>'
    : '<span class="verdict-fail">⚠ Cần cải thiện</span>';
}

function renderErrorDesc(turn, tcStatus) {
  // Chỉ hiển thị lỗi khi FAILED
  if (tcStatus !== 'done') return '<span class="cell-empty">—</span>';
  if (turn.verdict === 'PASSED') return '<span class="cell-empty">—</span>';

  // Ưu tiên error_desc, fallback về reasoning nếu error_desc rỗng
  const desc = turn.error_desc || (turn.reasoning ? '⚠️ Xem reasoning' : '');
  if (!desc) return '<span class="cell-empty">—</span>';

  // Thêm reasoning tooltip nếu có
  let reasoningAttr = '';
  if (turn.reasoning) {
    // Reasoning có thể là string hoặc object
    const reasoningText = typeof turn.reasoning === 'string'
      ? turn.reasoning
      : JSON.stringify(turn.reasoning, null, 2);
    reasoningAttr = `title="${reasoningText.replace(/"/g, '&quot;').replace(/\n/g, ' ')}"`;
  }

  return `<div class="judge-text err-text" ${reasoningAttr}>${desc}</div>`;
}

function renderSuggestion(turn, tcStatus) {
  if (tcStatus !== 'done') return '<span class="cell-empty">—</span>';

  // Chỉ hiển thị suggestion khi FAILED
  if (turn.verdict === 'PASSED') {
    // Với PASSED, chỉ hiển thị tone_note nếu có
    if (turn.tone_note) {
      return `<div class="judge-text tone-text">🎙 ${turn.tone_note}</div>`;
    }
    return '<span class="cell-empty">—</span>';
  }

  // Với FAILED, hiển thị đầy đủ
  const parts = [];
  if (turn.suggestion) parts.push(`<div class="judge-text sug-text">💡 ${turn.suggestion}</div>`);
  if (turn.suggested_response) {
    parts.push(`<div class="judge-text suggested-response-text" style="margin-top:8px;padding:10px;background:#f0fdf4;border-left:3px solid #16a34a;border-radius:6px;color:#15803d;line-height:1.6;">📝 <strong>Mẫu đề xuất:</strong><br/>${turn.suggested_response}</div>`);
  }
  if (turn.tone_note) parts.push(`<div class="judge-text tone-text">🎙 ${turn.tone_note}</div>`);
  return parts.length ? parts.join('') : '<span class="cell-empty">—</span>';
}
