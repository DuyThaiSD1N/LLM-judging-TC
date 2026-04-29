// filter.js — filter và search testcase

import { renderEval } from './table.js';

let currentFilters = {
    search: '',
    group: 'all',
    criteria: 'all',
    status: 'all'
};

export function initFilter() {
    const searchInput = document.getElementById('search-input');
    const groupFilter = document.getElementById('filter-group');
    const criteriaFilter = document.getElementById('filter-criteria');
    const statusFilter = document.getElementById('filter-status');
    const clearBtn = document.getElementById('btn-clear-filter');

    // Search input với debounce
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentFilters.search = e.target.value.toLowerCase().trim();
            applyFilters();
        }, 300);
    });

    // Filter dropdowns
    groupFilter.addEventListener('change', (e) => {
        currentFilters.group = e.target.value;
        applyFilters();
    });

    criteriaFilter.addEventListener('change', (e) => {
        currentFilters.criteria = e.target.value;
        applyFilters();
    });

    statusFilter.addEventListener('change', (e) => {
        currentFilters.status = e.target.value;
        applyFilters();
    });

    // Clear filters
    clearBtn.addEventListener('click', () => {
        searchInput.value = '';
        groupFilter.value = 'all';
        criteriaFilter.value = 'all';
        statusFilter.value = 'all';
        currentFilters = { search: '', group: 'all', criteria: 'all', status: 'all' };
        applyFilters();
    });
}

export function getFilters() {
    return currentFilters;
}

export function filterTestcases(testcases) {
    return testcases.filter(tc => {
        // Search filter (tìm trong code, name)
        if (currentFilters.search) {
            const searchLower = currentFilters.search;
            const matchCode = tc.code.toLowerCase().includes(searchLower);
            const matchName = tc.name.toLowerCase().includes(searchLower);
            if (!matchCode && !matchName) return false;
        }

        // Group filter
        if (currentFilters.group !== 'all' && tc.group !== currentFilters.group) {
            return false;
        }

        // Criteria filter
        if (currentFilters.criteria !== 'all' && tc.criteria !== currentFilters.criteria) {
            return false;
        }

        // Status filter
        if (currentFilters.status !== 'all') {
            if (currentFilters.status === 'pending' && tc.status !== 'pending') return false;
            if (currentFilters.status === 'done' && tc.status !== 'done') return false;
            if (currentFilters.status === 'error' && tc.status !== 'error') return false;

            // Filter theo verdict
            if (currentFilters.status === 'passed') {
                const allPassed = tc.turns.every(t => t.verdict === 'PASSED');
                if (!allPassed) return false;
            }
            if (currentFilters.status === 'failed') {
                const anyFailed = tc.turns.some(t => t.verdict === 'FAILED');
                if (!anyFailed) return false;
            }
        }

        return true;
    });
}

function applyFilters() {
    renderEval();
    updateFilterBadge();
}

function updateFilterBadge() {
    const badge = document.getElementById('filter-badge');
    const activeCount = Object.values(currentFilters).filter(v => v && v !== 'all').length;

    if (activeCount > 0) {
        badge.textContent = activeCount;
        badge.style.display = 'inline-block';
    } else {
        badge.style.display = 'none';
    }
}
