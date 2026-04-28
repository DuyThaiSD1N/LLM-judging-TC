// routes/testcase.js — CRUD operations for testcases

const express = require('express');
const router = express.Router();
const Testcase = require('../models/Testcase');

// ── GET /api/testcases - Lấy tất cả testcases ────────────────────────────
router.get('/testcases', async (req, res) => {
    try {
        const testcases = await Testcase.find().sort({ createdAt: -1 });
        res.json({ testcases });
    } catch (error) {
        console.error('Error fetching testcases:', error);
        res.status(500).json({ error: 'Failed to fetch testcases' });
    }
});

// ── GET /api/testcases/:code - Lấy 1 testcase theo code ──────────────────
router.get('/testcases/:code', async (req, res) => {
    try {
        const testcase = await Testcase.findOne({ code: req.params.code });
        if (!testcase) {
            return res.status(404).json({ error: 'Testcase not found' });
        }
        res.json({ testcase });
    } catch (error) {
        console.error('Error fetching testcase:', error);
        res.status(500).json({ error: 'Failed to fetch testcase' });
    }
});

// ── POST /api/testcases - Tạo testcase mới ───────────────────────────────
router.post('/testcases', async (req, res) => {
    try {
        const { code, name, group, turns } = req.body;

        // Validate
        if (!code || !name || !group || !turns || turns.length === 0) {
            return res.status(400).json({ error: 'Missing required fields' });
        }

        // Check duplicate code
        const existing = await Testcase.findOne({ code });
        if (existing) {
            return res.status(409).json({ error: 'Testcase code already exists' });
        }

        // Create
        const testcase = new Testcase({ code, name, group, turns });
        await testcase.save();

        res.status(201).json({ testcase, message: 'Testcase created successfully' });
    } catch (error) {
        console.error('Error creating testcase:', error);
        res.status(500).json({ error: 'Failed to create testcase' });
    }
});

// ── PUT /api/testcases/:code - Cập nhật testcase ─────────────────────────
router.put('/testcases/:code', async (req, res) => {
    try {
        const { name, group, turns, status, error } = req.body;

        const testcase = await Testcase.findOne({ code: req.params.code });
        if (!testcase) {
            return res.status(404).json({ error: 'Testcase not found' });
        }

        // Update fields
        if (name) testcase.name = name;
        if (group) testcase.group = group;
        if (turns) testcase.turns = turns;
        if (status) testcase.status = status;
        if (error !== undefined) testcase.error = error;

        await testcase.save();

        res.json({ testcase, message: 'Testcase updated successfully' });
    } catch (error) {
        console.error('Error updating testcase:', error);
        res.status(500).json({ error: 'Failed to update testcase' });
    }
});

// ── DELETE /api/testcases/:code - Xóa testcase ───────────────────────────
router.delete('/testcases/:code', async (req, res) => {
    try {
        const testcase = await Testcase.findOneAndDelete({ code: req.params.code });
        if (!testcase) {
            return res.status(404).json({ error: 'Testcase not found' });
        }

        res.json({ message: 'Testcase deleted successfully' });
    } catch (error) {
        console.error('Error deleting testcase:', error);
        res.status(500).json({ error: 'Failed to delete testcase' });
    }
});

// ── DELETE /api/testcases - Xóa tất cả testcases ─────────────────────────
router.delete('/testcases', async (req, res) => {
    try {
        const result = await Testcase.deleteMany({});
        res.json({ message: `Deleted ${result.deletedCount} testcases` });
    } catch (error) {
        console.error('Error deleting testcases:', error);
        res.status(500).json({ error: 'Failed to delete testcases' });
    }
});

module.exports = router;
