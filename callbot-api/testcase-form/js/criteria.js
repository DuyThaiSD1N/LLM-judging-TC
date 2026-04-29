// criteria.js — Quản lý dropdown và modal tiêu chí LLM Judge

import { API_ENDPOINTS, API_KEY } from './config.js';

let criteriaList = [];
let selectedCriteria = 'standard';

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
        const res = await fetch(API_ENDPOINTS.CRITERIA, {
            headers: { 'X-API-Key': API_KEY }
        });
        const data = await res.json();
        criteriaList = data.criteria || [];

        // Populate dropdown
        populateDropdown();
    } catch (err) {
        console.error('Failed to load criteria:', err);
        // Fallback to default
        criteriaList = [
            { id: 'standard', name: 'Tiêu chí Chuẩn', description: 'Đánh giá cân bằng' }
        ];
        populateDropdown();
    }
}

function populateDropdown() {
    const popup = document.getElementById('criteria-popup');

    popup.innerHTML = criteriaList.map(c => `
        <input type="radio" name="criteria" id="criteria-${c.id}" value="${c.id}" 
               class="criteria-radio" ${c.id === 'standard' ? 'checked' : ''} />
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
}

function toggleDropdown() {
    const trigger = document.getElementById('criteria-trigger');
    const popup = document.getElementById('criteria-popup');

    const isOpen = popup.classList.contains('open');
    if (isOpen) {
        closeDropdown();
    } else {
        trigger.classList.add('open');
        popup.classList.add('open');
    }
}

function closeDropdown() {
    const trigger = document.getElementById('criteria-trigger');
    const popup = document.getElementById('criteria-popup');
    trigger.classList.remove('open');
    popup.classList.remove('open');
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
