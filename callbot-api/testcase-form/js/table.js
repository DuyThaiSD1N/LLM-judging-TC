// table.js — quản lý state testcases (multi-turn) và render bảng đánh giá

import { filterTestcases } from './filter.js';
import { getIsRunning } from './state.js';

let testcases = [];
let _runSingleFn = null;
let selectedIndices = new Set();

export function setRunSingleFn(fn) { _runSingleFn = fn; }
export function getTestcases() { return testcases; }
export function getSelectedIndices() { return Array.from(selectedIndices); }
export function clearSelection() {
  selectedIndices.clear();
  renderEval();
}

export function addTestcase(tc) {
  testcases.push(initRow(tc));
  renderEval();
}

export function addBulkTestcases(list) {
  list.forEach(tc => testcases.push(initRow(tc)));
  renderEval();
}

export function deleteTestcase(idx) {
  testcases.splice(idx, 1);
  selectedIndices.clear(); // Clear selection after delete
  renderEval();
}

export function deleteBulk(indices) {
  // Sort descending to delete from end to start
  indices.sort((a, b) => b - a);
  indices.forEach(idx => testcases.splice(idx, 1));
  selectedIndices.clear();
  renderEval();
}

export function clearAllTestcases() {
  testcases = [];
  renderEval();
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

function duplicateTestcase(idx) {
  const tc = testcases[idx];
  if (!tc) return;

  // Tạo bản sao với mã mới
  const newCode = generateDuplicateCode(tc.code);
  const duplicated = {
    code: newCode,
    name: tc.name + ' (copy)',
    group: tc.group,
    criteria: tc.criteria,
    turns: tc.turns.map(t => ({
      question: t.question,
      expected: t.expected
    }))
  };

  testcases.push(initRow(duplicated));
  renderEval();

  // Scroll to bottom
  setTimeout(() => {
    const table = document.querySelector('.table-wrap');
    if (table) table.scrollTop = table.scrollHeight;
  }, 100);
}

function generateDuplicateCode(originalCode) {
  // Tìm số lớn nhất trong các mã hiện có
  const codePattern = /^(.+?)(\d+)$/;
  const match = originalCode.match(codePattern);

  if (!match) {
    // Nếu không có số, thêm -1
    return originalCode + '-1';
  }

  const prefix = match[1];
  const num = parseInt(match[2]);

  // Tìm số lớn nhất với cùng prefix
  let maxNum = num;
  testcases.forEach(tc => {
    const tcMatch = tc.code.match(codePattern);
    if (tcMatch && tcMatch[1] === prefix) {
      const tcNum = parseInt(tcMatch[2]);
      if (tcNum > maxNum) maxNum = tcNum;
    }
  });

  return prefix + (maxNum + 1);
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

function initRow(tc) {
  // Hỗ trợ cả format cũ (question/expected string) và mới (turns array)
  let turns = tc.turns;
  if (!turns) {
    turns = [{ question: tc.question ?? '', expected: tc.expected ?? '' }];
  }
  return {
    code: tc.code,
    name: tc.name,
    group: tc.group,
    criteria: tc.criteria || 'standard',
    status: 'pending',
    error: '',
    turns: turns.map(t => ({
      question: t.question,
      expected: t.expected,
      actual: null,
      action: '',
      response_time_ms: null,
      verdict: null,
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

    // Map criteria ID to display name
    const criteriaNames = {
      'standard': 'Chuẩn',
      'strict': 'Nghiêm ngặt',
      'flexible': 'Linh hoạt',
      'content-only': 'Nội dung',
      'ux-focused': 'Trải nghiệm'
    };
    const criteriaDisplay = criteriaNames[tc.criteria] || tc.criteria;

    return tc.turns.map((turn, j) => {
      const isFirst = j === 0;
      const isSelected = selectedIndices.has(i);
      const rowClass = isFirst ? 'tc-first-row' : 'tc-sub-row';
      const selectedClass = isSelected ? 'row-selected' : '';

      const tcCells = isFirst ? `
        <td class="col-checkbox" rowspan="${turnCount}">
          <input type="checkbox" class="tc-checkbox" data-idx="${i}" ${isSelected ? 'checked' : ''} />
        </td>
        <td class="col-num"  rowspan="${turnCount}">${i + 1}</td>
        <td class="col-code" rowspan="${turnCount}">${tc.code}</td>
        <td class="col-name" rowspan="${turnCount}">${tc.name}</td>
        <td rowspan="${turnCount}"><span class="tag tag-${tc.group}">${tc.group}</span></td>
        <td class="col-criteria" rowspan="${turnCount}"><span class="criteria-badge">${criteriaDisplay}</span></td>` : '';

      const actionCell = isFirst ? `
        <td class="col-actions" rowspan="${turnCount}">
          <button class="btn-run-one" data-idx="${i}" title="Chạy testcase này">▶</button>
          <button class="btn-edit"    data-idx="${i}" title="Sửa">✏️</button>
          <button class="btn-duplicate" data-idx="${i}" title="Nhân bản">📋</button>
          <button class="btn-del"     data-idx="${i}" title="Xóa">🗑</button>
        </td>` : '';

      return `
        <tr class="${rowClass} ${selectedClass}">
          ${tcCells}
          <td class="col-turn-num">Lượt ${j + 1}</td>
          <td class="col-q">${turn.question}</td>
          <td class="col-e">${turn.expected}</td>
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
            <th style="width:40px;">
              <input type="checkbox" id="select-all-checkbox" title="Chọn tất cả" />
            </th>
            <th>#</th>
            <th>Mã TC</th>
            <th>Tên Testcase</th>
            <th>Nhóm</th>
            <th>LLM Judge</th>
            <th>Lượt</th>
            <th>Câu hỏi từ User</th>
            <th>Câu trả lời kỳ vọng</th>
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

  // Bulk action bar
  updateBulkActionBar();

  // Event listeners
  document.getElementById('select-all-checkbox')?.addEventListener('change', (e) => {
    if (e.target.checked) {
      filteredTestcases.forEach((_, i) => selectedIndices.add(i));
    } else {
      selectedIndices.clear();
    }
    renderEval();
  });

  container.querySelectorAll('.tc-checkbox').forEach(cb => {
    cb.addEventListener('change', (e) => {
      const idx = Number(e.target.dataset.idx);
      if (e.target.checked) {
        selectedIndices.add(idx);
      } else {
        selectedIndices.delete(idx);
      }
      renderEval();
    });
  });

  container.querySelectorAll('.btn-del').forEach(btn =>
    btn.addEventListener('click', () => deleteTestcase(Number(btn.dataset.idx))));

  container.querySelectorAll('.btn-run-one').forEach(btn =>
    btn.addEventListener('click', () => _runSingleFn?.(Number(btn.dataset.idx))));

  container.querySelectorAll('.btn-edit').forEach(btn =>
    btn.addEventListener('click', () => editTestcase(Number(btn.dataset.idx))));

  container.querySelectorAll('.btn-duplicate').forEach(btn =>
    btn.addEventListener('click', () => duplicateTestcase(Number(btn.dataset.idx))));

  // Disable buttons if running
  const running = getIsRunning();
  if (running) {
    container.querySelectorAll('.btn-edit, .btn-del, .btn-run-one, .btn-duplicate').forEach(el => {
      el.disabled = true;
      el.style.opacity = '0.5';
      el.style.cursor = 'not-allowed';
    });
  }
}

// ── Cell renderers ────────────────────────────────────────────────────────
function renderActual(turn, tcStatus) {
  if (tcStatus === 'pending') return '<span class="cell-empty">—</span>';
  if (tcStatus === 'running' && turn.actual === null) return '<span class="spinner-inline"></span>';
  if (tcStatus === 'error' && turn.actual === null) return `<span class="actual-error">❌ Lỗi</span>`;
  if (turn.actual === null) return '<span class="cell-empty">—</span>';

  const badge = turn.action
    ? `<span class="action-badge action-${turn.action}">${turn.action}</span>`
    : '';
  return `<div class="actual-text">${turn.actual}</div>${badge}`;
}

function renderTime(turn, tcStatus) {
  if (tcStatus === 'pending') return '<span class="cell-empty">—</span>';
  if (tcStatus === 'running' && turn.response_time_ms === null) return '<span class="spinner-inline"></span>';
  if (turn.response_time_ms == null) return '<span class="cell-empty">—</span>';

  const ms = turn.response_time_ms;
  const display = ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`;
  const level = turn.time_verdict ?? (ms <= 2000 ? 'good' : ms <= 3000 ? 'ok' : 'slow');
  const note = turn.time_note ? `title="${turn.time_note}"` : '';
  return `<span class="time-badge time-${level}" ${note}>${display}</span>`;
}

function renderVerdict(turn, tcStatus) {
  if (tcStatus === 'pending') return '<span class="cell-empty">—</span>';
  if (tcStatus === 'running' && turn.verdict === null) return '<span class="spinner-inline"></span>';
  if (tcStatus === 'error') return '<span class="verdict-fail">✕ Lỗi</span>';
  if (turn.actual === null) return '<span class="cell-empty">—</span>';
  if (!turn.verdict) return '<span class="verdict-fail">✕ Lỗi đánh giá</span>';

  return turn.verdict === 'PASSED'
    ? '<span class="verdict-pass">✓ PASSED</span>'
    : '<span class="verdict-fail">✕ FAILED</span>';
}

function renderErrorDesc(turn, tcStatus) {
  if (tcStatus !== 'done' || !turn.error_desc) return '<span class="cell-empty">—</span>';
  return `<div class="judge-text err-text">${turn.error_desc}</div>`;
}

function renderSuggestion(turn, tcStatus) {
  if (tcStatus !== 'done') return '<span class="cell-empty">—</span>';
  const parts = [];
  if (turn.suggestion) parts.push(`<div class="judge-text sug-text">💡 ${turn.suggestion}</div>`);
  if (turn.suggested_response) {
    parts.push(`<div class="judge-text suggested-response-text" style="margin-top:8px;padding:10px;background:#f0fdf4;border-left:3px solid #16a34a;border-radius:6px;color:#15803d;line-height:1.6;">📝 <strong>Mẫu đề xuất:</strong><br/>${turn.suggested_response}</div>`);
  }
  if (turn.tone_note) parts.push(`<div class="judge-text tone-text">🎙 ${turn.tone_note}</div>`);
  return parts.length ? parts.join('') : '<span class="cell-empty">—</span>';
}

// ── Bulk Actions ──────────────────────────────────────────────────────────
function updateBulkActionBar() {
  const count = selectedIndices.size;
  let bar = document.getElementById('bulk-action-bar');

  if (count === 0) {
    if (bar) bar.remove();
    return;
  }

  if (!bar) {
    bar = document.createElement('div');
    bar.id = 'bulk-action-bar';
    bar.className = 'bulk-action-bar';
    document.querySelector('.table-section').insertBefore(bar, document.getElementById('table-container'));
  }

  bar.innerHTML = `
    <div class="bulk-info">
      <span class="bulk-count">${count}</span> testcase được chọn
    </div>
    <div class="bulk-actions">
      <button id="bulk-run" class="btn-bulk btn-bulk-run">▶ Chạy đã chọn</button>
      <button id="bulk-delete" class="btn-bulk btn-bulk-delete">🗑 Xóa đã chọn</button>
      <button id="bulk-clear" class="btn-bulk btn-bulk-clear">✕ Bỏ chọn</button>
    </div>
  `;

  document.getElementById('bulk-run')?.addEventListener('click', handleBulkRun);
  document.getElementById('bulk-delete')?.addEventListener('click', handleBulkDelete);
  document.getElementById('bulk-clear')?.addEventListener('click', () => {
    selectedIndices.clear();
    renderEval();
  });
}

function handleBulkRun() {
  const indices = Array.from(selectedIndices);
  if (indices.length === 0) return;

  // Dispatch event for runner to handle
  window.dispatchEvent(new CustomEvent('bulk-run', { detail: { indices } }));
}

function handleBulkDelete() {
  const count = selectedIndices.size;
  if (count === 0) return;

  if (confirm(`Bạn có chắc muốn xóa ${count} testcase đã chọn?`)) {
    deleteBulk(Array.from(selectedIndices));
    import('./toast.js').then(({ showToast }) => {
      showToast(`🗑 Đã xóa ${count} testcase`, 'success');
    });
  }
}

