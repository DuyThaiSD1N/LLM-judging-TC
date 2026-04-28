// form.js — xử lý form nhập tay testcase

import { addTestcase } from './table.js';
import { showToast } from './toast.js';

const GROUP_META = {
    A: { label: 'Hỏi đầy đủ thông tin', color: '#2563eb' },
    B: { label: 'Hỏi ngoại lệ / ngoài phạm vi', color: '#16a34a' },
    C: { label: 'Hỏi chuyển topic đột ngột', color: '#d97706' },
    D: { label: 'Tài liệu không có trong CSDL', color: '#dc2626' },
};

function parseLines(text) {
    return text.split('\n').map(l => l.trim()).filter(l => l.length > 0);
}

// ── Dropdown logic ────────────────────────────────────────────────────────
function initGroupDropdown() {
    const trigger = document.getElementById('group-trigger');
    const popup = document.getElementById('group-popup');

    trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = popup.classList.toggle('open');
        trigger.classList.toggle('open', isOpen);
    });

    // Đóng khi click ngoài
    document.addEventListener('click', () => {
        popup.classList.remove('open');
        trigger.classList.remove('open');
    });
    popup.addEventListener('click', e => e.stopPropagation());

    // Khi chọn option → cập nhật trigger display
    document.querySelectorAll('input[name="group"]').forEach(el => {
        el.addEventListener('change', () => {
            const meta = GROUP_META[el.value];
            document.getElementById('group-selected-display').innerHTML = `
        <span class="trigger-selected">
          <span class="group-badge badge-${el.value}" style="width:20px;height:20px;font-size:0.7rem;border-radius:5px;">${el.value}</span>
          <span style="font-size:0.85rem;">${meta.label}</span>
        </span>`;
            popup.classList.remove('open');
            trigger.classList.remove('open');
        });
    });
}

export function initForm() {
    initGroupDropdown();
    document.getElementById('btn-add').addEventListener('click', handleAdd);
    document.getElementById('btn-reset').addEventListener('click', resetForm);
}

function handleAdd() {
    const name = document.getElementById('tc-name').value.trim();
    const code = document.getElementById('tc-code').value.trim();
    const group = document.querySelector('input[name="group"]:checked')?.value;
    const questions = parseLines(document.getElementById('tc-question').value);
    const expecteds = parseLines(document.getElementById('tc-expected').value);

    if (!name || !code || !group) {
        showToast('⚠️ Vui lòng điền đầy đủ Tên, Mã và Nhóm.', 'error');
        return;
    }
    if (questions.length === 0) {
        showToast('⚠️ Vui lòng nhập ít nhất 1 câu hỏi.', 'error');
        return;
    }
    if (expecteds.length !== questions.length) {
        showToast(`⚠️ Số câu hỏi (${questions.length}) và kỳ vọng (${expecteds.length}) phải bằng nhau.`, 'error');
        return;
    }

    const turns = questions.map((q, i) => ({ question: q, expected: expecteds[i] }));
    addTestcase({ name, code, group, turns });
    resetForm();

    // Thông báo đẹp hơn
    const turnText = turns.length === 1 ? '1 lượt hỏi' : `${turns.length} lượt hỏi`;
    showToast(`Đã thêm testcase "${name}" với ${turnText}`, 'success');
}

export function resetForm() {
    document.getElementById('tc-name').value = '';
    document.getElementById('tc-code').value = '';
    document.getElementById('tc-question').value = '';
    document.getElementById('tc-expected').value = '';
    document.querySelectorAll('input[name="group"]').forEach(el => el.checked = false);
    document.getElementById('group-selected-display').innerHTML =
        '<span class="trigger-placeholder">Chọn nhóm...</span>';
}
