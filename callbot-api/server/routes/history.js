// routes/history.js — API endpoints cho lịch sử đánh giá

const express = require('express');
const router = express.Router();
const History = require('../models/history');

// GET /api/history - Lấy lịch sử gần nhất
router.get('/history', (req, res) => {
    try {
        const limit = parseInt(req.query.limit) || 50;
        const history = History.getRecent(limit);
        res.json({ history });
    } catch (err) {
        console.error('Error getting history:', err);
        res.status(500).json({ error: err.message });
    }
});

// GET /api/history/stats - Lấy thống kê
router.get('/history/stats', (req, res) => {
    try {
        const stats = History.getStats();
        res.json(stats);
    } catch (err) {
        console.error('Error getting stats:', err);
        res.status(500).json({ error: err.message });
    }
});

// GET /api/history/:code - Lấy lịch sử theo testcase
router.get('/history/:code', (req, res) => {
    try {
        const { code } = req.params;
        const limit = parseInt(req.query.limit) || 10;
        const history = History.getByTestcase(code, limit);
        res.json({ history });
    } catch (err) {
        console.error('Error getting testcase history:', err);
        res.status(500).json({ error: err.message });
    }
});

// DELETE /api/history/cleanup - Xóa lịch sử cũ
router.delete('/history/cleanup', (req, res) => {
    try {
        const days = parseInt(req.query.days) || 30;
        const deleted = History.cleanup(days);
        res.json({ success: true, deleted });
    } catch (err) {
        console.error('Error cleaning up history:', err);
        res.status(500).json({ error: err.message });
    }
});

module.exports = router;
