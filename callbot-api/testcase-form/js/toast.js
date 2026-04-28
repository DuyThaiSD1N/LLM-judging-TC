// toast.js — hiển thị thông báo popup góc phải trên màn hình

export function showToast(msg, type = 'success') {
    const colors = {
        success: '#16a34a',
        error: '#dc2626',
        info: '#1d4ed8',
    };

    const icons = {
        success: '✓',
        error: '✕',
        info: 'ℹ',
    };

    const t = document.getElementById('toast');
    t.textContent = msg;
    t.style.background = colors[type] ?? colors.info;

    // Update icon
    t.setAttribute('data-type', type);

    // Show toast
    t.classList.add('show');

    // Auto hide after 3 seconds
    setTimeout(() => {
        t.classList.remove('show');
    }, 3000);
}
