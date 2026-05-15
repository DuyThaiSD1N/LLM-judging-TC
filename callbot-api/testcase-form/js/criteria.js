// criteria.js — Quản lý dropdown và modal tiêu chí LLM Judge

import { API_ENDPOINTS, API_KEY } from './config.js';

let criteriaList = [];
let selectedCriteria = 'goal_achievement';

export function initCriteria() {
    loadCriteriaList();
    initDropdown();
    initModal();
}

export function getSelectedCriteria() {
    return selectedCriteria;
}

async function loadCriteriaList() {
    try {
        console.log('📡 Fetching criteria from:', API_ENDPOINTS.CRITERIA);
        const res = await fetch(API_ENDPOINTS.CRITERIA, {
            headers: { 'X-API-Key': API_KEY }
        });

        if (!res.ok) {
            throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }

        const data = await res.json();
        console.log('✅ Criteria loaded:', data);

        criteriaList = data.criteria || [];

        if (criteriaList.length === 0) {
            console.warn('⚠️ No criteria returned from API, using fallback');
            criteriaList = [
                { id: 'goal_achievement', name: 'Đạt mục tiêu', description: 'Đạt mục tiêu testcase' },
                { id: 'semantic_correctness', name: 'Đúng nghĩa & intent', description: 'Đúng nghĩa & đúng intent' },
                { id: 'conversation_quality', name: 'Chất lượng hội thoại', description: 'Tự nhiên & hữu ích' },
                { id: 'context_consistency', name: 'Tính nhất quán', description: 'Logic xuyên suốt' },
                { id: 'safety_compliance', name: 'An toàn & Tuân thủ', description: 'Không vi phạm' }
            ];
        }

        // Populate dropdown
        populateDropdown();
    } catch (err) {
        console.error('❌ Failed to load criteria:', err);
        // Fallback to default
        criteriaList = [
            { id: 'goal_achievement', name: 'Đạt mục tiêu', description: 'Đạt mục tiêu testcase' },
            { id: 'semantic_correctness', name: 'Đúng nghĩa & intent', description: 'Đúng nghĩa & đúng intent' },
            { id: 'conversation_quality', name: 'Chất lượng hội thoại', description: 'Tự nhiên & hữu ích' },
            { id: 'context_consistency', name: 'Tính nhất quán', description: 'Logic xuyên suốt' },
            { id: 'safety_compliance', name: 'An toàn & Tuân thủ', description: 'Không vi phạm' }
        ];
        populateDropdown();
    }
}

function populateDropdown() {
    const popup = document.getElementById('criteria-popup');

    popup.innerHTML = criteriaList.map(c => `
        <input type="radio" name="criteria" id="criteria-${c.id}" value="${c.id}" 
               class="criteria-radio" ${c.id === 'goal_achievement' ? 'checked' : ''} />
        <label for="criteria-${c.id}" class="criteria-option">
            <div class="criteria-name">${c.name}</div>
            <div class="criteria-desc">${c.description}</div>
        </label>
    `).join('');

    // Add change listeners
    popup.querySelectorAll('.criteria-radio').forEach(radio => {
        radio.addEventListener('change', (e) => {
            selectedCriteria = e.target.value;
            updateDisplay();
            closeDropdown();
        });
    });
}

function initDropdown() {
    const trigger = document.getElementById('criteria-trigger');
    const popup = document.getElementById('criteria-popup');

    if (!trigger || !popup) {
        console.error('❌ Criteria dropdown elements not found:', {
            trigger: !!trigger,
            popup: !!popup
        });
        return;
    }

    trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDropdown();
    });

    // Prevent closing when clicking inside popup
    popup.addEventListener('click', (e) => {
        e.stopPropagation();
    });

    // Close when clicking outside
    document.addEventListener('click', (e) => {
        if (!popup.contains(e.target) && !trigger.contains(e.target)) {
            closeDropdown();
        }
    });

    console.log('✅ Criteria dropdown initialized');
}

function toggleDropdown() {
    const trigger = document.getElementById('criteria-trigger');
    const popup = document.getElementById('criteria-popup');

    const isOpen = popup.classList.contains('show');
    if (isOpen) {
        closeDropdown();
    } else {
        trigger.classList.add('open');
        popup.classList.add('show');
    }
}

function closeDropdown() {
    const trigger = document.getElementById('criteria-trigger');
    const popup = document.getElementById('criteria-popup');
    trigger.classList.remove('open');
    popup.classList.remove('show');
}

function updateDisplay() {
    const display = document.getElementById('criteria-selected-display');
    const selected = criteriaList.find(c => c.id === selectedCriteria);

    if (selected) {
        display.innerHTML = `<span class="trigger-selected">${selected.name}</span>`;
    }
}

function initModal() {
    const btnInfo = document.getElementById('btn-criteria-info');
    const modal = document.getElementById('criteria-modal');
    const btnClose = document.getElementById('btn-close-criteria');

    if (!btnInfo || !modal || !btnClose) {
        console.error('❌ Criteria modal elements not found:', {
            btnInfo: !!btnInfo,
            modal: !!modal,
            btnClose: !!btnClose
        });
        return;
    }

    btnInfo.addEventListener('click', () => {
        openModal();
    });

    btnClose.addEventListener('click', () => {
        modal.classList.remove('show');
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('show');
        }
    });
}

function openModal() {
    const modal = document.getElementById('criteria-modal');
    const list = document.getElementById('criteria-info-list');

    // Populate modal with criteria info
    list.innerHTML = criteriaList.map(c => `
        <div class="criteria-info-card">
            <h3>${c.name}</h3>
            <p>${c.description}</p>
        </div>
    `).join('');

    modal.classList.add('show');
}
