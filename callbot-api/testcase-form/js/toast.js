// toast.js — hiển thị thông báo nhanh góc phải màn hình

export function showToast(msg, type = 'success') {
    const colors = {
        success: '#16a34a',
        error: '#dc2626',
        info: '#1d4ed8',
    };
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.style.background = colors[type] ?? colors.info;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2800);
}
