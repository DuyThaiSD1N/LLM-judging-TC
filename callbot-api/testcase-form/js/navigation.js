// navigation.js — Xử lý sidebar navigation

export function initNavigation() {
    const navItems = document.querySelectorAll('.sidebar-nav-item');
    const viewTitle = document.getElementById('view-title');

    // View titles mapping
    const viewTitles = {
        'testcases': 'Testcases',
        'history': 'History',
        'export': 'Export'
    };

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();

            const viewName = item.getAttribute('data-view');

            // Update active nav item
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            // Update view title
            if (viewTitle && viewTitles[viewName]) {
                viewTitle.textContent = viewTitles[viewName];
            }

            // Show corresponding view
            showView(viewName);
        });
    });

    // Show default view (testcases)
    showView('testcases');
}

function showView(viewName) {
    // Hide all views
    const allViews = document.querySelectorAll('.view-content');
    allViews.forEach(view => view.classList.remove('active'));

    // Show selected view
    const targetView = document.getElementById(`view-${viewName}`);
    if (targetView) {
        targetView.classList.add('active');
    }
}

// Export showView for external use
export { showView };
