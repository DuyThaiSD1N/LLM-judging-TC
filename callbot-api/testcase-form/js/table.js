// table.js — quản lý state testcases (multi-turn) và render bảng đánh giá

let testcases = [];
let _runSingleFn = null;

export function setRunSingleFn(fn) { _runSingleFn = fn; }
export function getTestcases() { return testcases; }

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
  renderEval();
}

export function clearAllTestcases() {
  testcases = [];
  renderEval();
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
      brevity_note: '',
      time_verdict: null,
      time_note: '',
    })),
  };
}

// ── Render ────────────────────────────────────────────────────────────────
export function renderEval() {
  document.getElementById('tc-count').textContent = testcases.length;
  const container = document.getElementById('table-container');

  if (testcases.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📭</div>
        <p>Chưa có testcase nào.</p>
        <p class="empty-sub">Thêm testcase bên trên hoặc import từ Excel.</p>
      </div>`;
    return;
  }

  const rows = testcases.map((tc, i) => {
    const turnCount = tc.turns.length;

    return tc.turns.map((turn, j) => {
      const isFirst = j === 0;
      const tcCells = isFirst ? `
        <td class="col-num"  rowspan="${turnCount}">${i + 1}</td>
        <td class="col-code" rowspan="${turnCount}">${tc.code}</td>
        <td class="col-name" rowspan="${turnCount}">${tc.name}</td>
        <td rowspan="${turnCount}"><span class="tag tag-${tc.group}">${tc.group}</span></td>` : '';

      const actionCell = isFirst ? `
        <td class="col-actions" rowspan="${turnCount}">
          <button class="btn-run-one" data-idx="${i}" title="Chạy testcase này">▶</button>
          <button class="btn-del"     data-idx="${i}" title="Xóa">🗑</button>
        </td>` : '';

      return `
        <tr class="${isFirst ? 'tc-first-row' : 'tc-sub-row'}">
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
            <th>#</th>
            <th>Mã TC</th>
            <th>Tên Testcase</th>
            <th>Nhóm</th>
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

  container.querySelectorAll('.btn-del').forEach(btn =>
    btn.addEventListener('click', () => deleteTestcase(Number(btn.dataset.idx))));

  container.querySelectorAll('.btn-run-one').forEach(btn =>
    btn.addEventListener('click', () => _runSingleFn?.(Number(btn.dataset.idx))));
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
  if (turn.actual === null) return '<span class="cell-empty">—</span>';
  if (!turn.verdict) return '<span class="verdict-skip">⏭ Bỏ qua</span>';

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
  if (turn.brevity_note) parts.push(`<div class="judge-text brevity-text">✂️ ${turn.brevity_note}</div>`);
  return parts.length ? parts.join('') : '<span class="cell-empty">—</span>';
}
