// filter.js — filter và search testcase (SIMPLIFIED - No group filter)
// VERSION: 2024-05-07-v16 - FIXED clearBtn check removed - NO CACHE

import { renderEval } from './table-v2.js';

let currentFilters = {
    search: '',
    criteria: 'all',
    status: 'all'
};

export function initFilter() {
    const searchInput = document.getElementById('search-input');
    const criteriaFilter = document.getElementById('filter-criteria');
    const statusFilter = document.getElementById('filter-status');

    // Null check - CRITICAL: Prevent error if elements not found
    if (!searchInput || !criteriaFilter || !statusFilter) {
        console.error('❌ Filter elements not found:', {
            searchInput: !!searchInput,
            criteriaFilter: !!criteriaFilter,
            statusFilter: !!statusFilter
        });
        return;
    }

    console.log('✅ Filter initialized successfully');

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
    criteriaFilter.addEventListener('change', (e) => {
        currentFilters.criteria = e.target.value;
        applyFilters();
    });

    statusFilter.addEventListener('change', (e) => {
        currentFilters.status = e.target.value;
        applyFilters();
    });
}

export function getFilters() {
    return currentFilters;
}

export function filterTestcases(testcases) {
    return testcases.filter(tc => {
        // Search filter (tìm trong code, name, executor)
        if (currentFilters.search) {
            const searchLower = currentFilters.search;
            const matchCode = tc.code.toLowerCase().includes(searchLower);
            const matchName = tc.name.toLowerCase().includes(searchLower);
            const matchExecutor = tc.executor ? tc.executor.toLowerCase().includes(searchLower) : false;
            if (!matchCode && !matchName && !matchExecutor) return false;
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
}
