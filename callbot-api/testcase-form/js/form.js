// form.js — xử lý form nhập tay testcase (SIMPLIFIED - No group logic)

import { addTestcase } from './table-v2.js';
import { showToast } from './toast.js';
import { getSelectedCriteria } from './criteria.js';

function parseLines(text) {
    return text.split('\n').map(l => l.trim()).filter(l => l.length > 0);
}

export function initForm() {
    const btnAdd = document.getElementById('btn-add');
    const btnReset = document.getElementById('btn-reset');

    if (!btnAdd || !btnReset) {
        console.error('❌ Form buttons not found:', { btnAdd: !!btnAdd, btnReset: !!btnReset });
        return;
    }

    btnAdd.addEventListener('click', handleAdd);
    btnReset.addEventListener('click', handleReset);

    // Listen for edit event from table
    window.addEventListener('edit-testcase', (e) => {
        loadTestcaseToForm(e.detail.index, e.detail.testcase);
    });

    console.log('✅ Form initialized');
}

let editingIndex = null;

function loadTestcaseToForm(index, tc) {
    editingIndex = index;

    // Populate form
    document.getElementById('tc-name').value = tc.name;
    document.getElementById('tc-code').value = tc.code;

    // Set questions and expected
    const questions = tc.turns.map(t => t.question).join('\n');
    const expecteds = tc.turns.map(t => t.expected).join('\n');
    document.getElementById('tc-question').value = questions;
    document.getElementById('tc-expected').value = expecteds;

    // Set bot URL
    document.getElementById('tc-bot-url').value = tc.bot_url || '';

    // Set keywords - mỗi turn 1 dòng
    const requiredKeywords = tc.turns.map(t => t.required_keywords || '').join('\n');
    const forbiddenKeywords = tc.turns.map(t => t.forbidden_keywords || '').join('\n');
    document.getElementById('tc-required-keywords').value = requiredKeywords;
    document.getElementById('tc-forbidden-keywords').value = forbiddenKeywords;

    // Set criteria
    const criteriaRadio = document.querySelector(`input[name="criteria"][value="${tc.criteria}"]`);
    if (criteriaRadio) {
        criteriaRadio.checked = true;
        criteriaRadio.dispatchEvent(new Event('change'));
    }

    // Change button text
    const btnAdd = document.getElementById('btn-add');
    btnAdd.textContent = '💾 Cập nhật Testcase';
    btnAdd.classList.add('btn-editing');

    // Scroll to form
    document.querySelector('.form-card').scrollIntoView({ behavior: 'smooth', block: 'start' });

    showToast(`Đang chỉnh sửa testcase "${tc.code}"`, 'info');
}

function handleAdd() {
    const name = document.getElementById('tc-name').value.trim();
    const code = document.getElementById('tc-code').value.trim();
    const questions = parseLines(document.getElementById('tc-question').value);
    const expecteds = parseLines(document.getElementById('tc-expected').value);

    // Get keywords (optional) - mỗi dòng cho 1 lượt hội thoại
    const requiredKeywordsLines = parseLines(document.getElementById('tc-required-keywords')?.value || '');
    const forbiddenKeywordsLines = parseLines(document.getElementById('tc-forbidden-keywords')?.value || '');

    if (!name || !code) {
        showToast('⚠️ Vui lòng điền đầy đủ Tên và Mã.', 'error');
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

    // Build turns với keywords tương ứng từng dòng
    const turns = questions.map((q, i) => ({
        question: q,
        expected: expecteds[i],
        required_keywords: requiredKeywordsLines[i] || null,  // Dòng i của required keywords
        forbidden_keywords: forbiddenKeywordsLines[i] || null  // Dòng i của forbidden keywords
    }));

    const criteria = getSelectedCriteria();
    const botUrl = document.getElementById('tc-bot-url').value.trim();

    console.log('🔍 Bot URL from input:', botUrl);
    console.log('🔍 Turns with keywords:', turns);

    if (editingIndex !== null) {
        // Update existing testcase
        import('./table.js').then(({ updateTestcase }) => {
            updateTestcase(editingIndex, { name, code, group: 'GENERAL', turns, criteria, bot_url: botUrl || null });
            resetForm();
            const turnText = turns.length === 1 ? '1 lượt hỏi' : `${turns.length} lượt hỏi`;
            showToast(`✅ Đã cập nhật testcase "${name}" với ${turnText}`, 'success');
        });
    } else {
        // Add new testcase
        addTestcase({ name, code, group: 'GENERAL', turns, criteria, bot_url: botUrl || null });
        resetForm();
        const turnText = turns.length === 1 ? '1 lượt hỏi' : `${turns.length} lượt hỏi`;
        showToast(`✅ Đã thêm testcase "${name}" với ${turnText}`, 'success');
    }
}

export function resetForm() {
    editingIndex = null;

    document.getElementById('tc-name').value = '';
    document.getElementById('tc-code').value = '';
    document.getElementById('tc-code').readOnly = false;
    document.getElementById('tc-question').value = '';
    document.getElementById('tc-expected').value = '';
    document.getElementById('tc-bot-url').value = '';
    document.getElementById('tc-required-keywords').value = '';
    document.getElementById('tc-forbidden-keywords').value = '';

    // Reset placeholders
    document.getElementById('tc-question').placeholder = 'Nhập câu hỏi (mỗi dòng 1 câu)';
    document.getElementById('tc-expected').placeholder = 'Nhập kỳ vọng (mỗi dòng 1 câu, tương ứng với câu hỏi)';

    // Reset button text and style
    const btnAdd = document.getElementById('btn-add');
    btnAdd.textContent = '+ Thêm Testcase';
    btnAdd.classList.remove('btn-editing');
    btnAdd.style.background = '';
}

function handleReset() {
    resetForm();
    showToast('Đã xóa nội dung form', 'info');
}
