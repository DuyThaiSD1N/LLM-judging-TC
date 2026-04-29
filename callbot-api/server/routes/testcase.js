// routes/testcase.js — API endpoints cho quản lý testcases

const express = require('express');
const router = express.Router();
const Testcase = require('../models/testcase');

// GET /api/testcases - Lấy tất cả testcases
router.get('/testcases', (req, res) => {
    try {
        const testcases = Testcase.getAll();
        res.json({ testcases });
    } catch (err) {
        console.error('Error getting testcases:', err);
        res.status(500).json({ error: err.message });
    }
});

// POST /api/testcases - Tạo testcase mới
router.post('/testcases', (req, res) => {
    try {
        const { code, name, group, turns } = req.body;

        if (!code || !name || !group || !turns || turns.length === 0) {
            return res.status(400).json({ error: 'Missing required fields' });
        }

        const id = Testcase.create({ code, name, group, turns });
        res.json({ success: true, id });
    } catch (err) {
        console.error('Error creating testcase:', err);
        if (err.message.includes('UNIQUE constraint')) {
            return res.status(409).json({ error: 'Testcase code already exists' });
        }
        res.status(500).json({ error: err.message });
    }
});

// DELETE /api/testcases/:code - Xóa testcase
router.delete('/testcases/:code', (req, res) => {
    try {
        const { code } = req.params;
        const deleted = Testcase.delete(code);

        if (!deleted) {
            return res.status(404).json({ error: 'Testcase not found' });
        }

        res.json({ success: true });
    } catch (err) {
        console.error('Error deleting testcase:', err);
        res.status(500).json({ error: err.message });
    }
});

// DELETE /api/testcases - Xóa tất cả testcases
router.delete('/testcases', (req, res) => {
    try {
        Testcase.deleteAll();
        res.json({ success: true });
    } catch (err) {
        console.error('Error deleting all testcases:', err);
        res.status(500).json({ error: err.message });
    }
});

module.exports = router;
