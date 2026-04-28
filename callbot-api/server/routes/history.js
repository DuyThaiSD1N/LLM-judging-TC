// routes/history.js — API cho lịch sử đánh giá testcase

const express = require('express');
const router = express.Router();
const mongoose = require('mongoose');

// Middleware để check database connection
function requireDB(req, res, next) {
    if (mongoose.connection.readyState !== 1) {
        return res.status(503).json({
            error: 'Database not available',
            message: 'History feature requires MongoDB. Set MONGODB_URI to enable.'
        });
    }
    next();
}

// Lazy load model
let TestcaseHistory;
try {
    TestcaseHistory = require('../models/TestcaseHistory');
} catch (error) {
    console.warn('⚠️  TestcaseHistory model not loaded');
}

// ── GET /api/history - Lấy tất cả lịch sử ───────────────────────────────
router.get('/history', requireDB, async (req, res) => {
    try {
        const {
            testcase_code,
            group,
            status,
            limit = 50,
            page = 1
        } = req.query;

        // Build query
        const query = {};
        if (testcase_code) query.testcase_code = testcase_code;
        if (group) query.group = group;
        if (status) query.status = status;

        // Pagination
        const skip = (parseInt(page) - 1) * parseInt(limit);

        const histories = await TestcaseHistory.find(query)
            .sort({ run_at: -1 })
            .limit(parseInt(limit))
            .skip(skip)
            .lean();

        const total = await TestcaseHistory.countDocuments(query);

        res.json({
            histories,
            pagination: {
                total,
                page: parseInt(page),
                limit: parseInt(limit),
                pages: Math.ceil(total / parseInt(limit))
            }
        });
    } catch (error) {
        console.error('Error fetching history:', error);
        res.status(500).json({ error: 'Failed to fetch history' });
    }
});

// ── GET /api/history/:id - Lấy 1 lịch sử chi tiết ───────────────────────
router.get('/history/:id', async (req, res) => {
    try {
        const history = await TestcaseHistory.findById(req.params.id);
        if (!history) {
            return res.status(404).json({ error: 'History not found' });
        }
        res.json({ history });
    } catch (error) {
        console.error('Error fetching history:', error);
        res.status(500).json({ error: 'Failed to fetch history' });
    }
});

// ── GET /api/history/testcase/:code - Lịch sử của 1 testcase ────────────
router.get('/history/testcase/:code', async (req, res) => {
    try {
        const { limit = 20 } = req.query;

        const histories = await TestcaseHistory.find({
            testcase_code: req.params.code
        })
            .sort({ run_at: -1 })
            .limit(parseInt(limit))
            .lean();

        res.json({ histories });
    } catch (error) {
        console.error('Error fetching testcase history:', error);
        res.status(500).json({ error: 'Failed to fetch testcase history' });
    }
});

// ── GET /api/history/stats - Thống kê tổng quan ─────────────────────────
router.get('/history/stats', async (req, res) => {
    try {
        const { days = 7 } = req.query;
        const fromDate = new Date();
        fromDate.setDate(fromDate.getDate() - parseInt(days));

        // Tổng số lần chạy
        const totalRuns = await TestcaseHistory.countDocuments({
            run_at: { $gte: fromDate }
        });

        // Tổng số testcase unique
        const uniqueTestcases = await TestcaseHistory.distinct('testcase_code', {
            run_at: { $gte: fromDate }
        });

        // Pass rate
        const allHistories = await TestcaseHistory.find({
            run_at: { $gte: fromDate }
        }).select('passed_turns total_turns').lean();

        const totalTurns = allHistories.reduce((sum, h) => sum + h.total_turns, 0);
        const totalPassed = allHistories.reduce((sum, h) => sum + h.passed_turns, 0);
        const passRate = totalTurns > 0 ? ((totalPassed / totalTurns) * 100).toFixed(1) : 0;

        // Avg response time
        const avgResponseTimes = allHistories
            .map(h => h.avg_response_time)
            .filter(t => t > 0);
        const overallAvgResponseTime = avgResponseTimes.length > 0
            ? Math.round(avgResponseTimes.reduce((a, b) => a + b, 0) / avgResponseTimes.length)
            : 0;

        // Group by status
        const byStatus = await TestcaseHistory.aggregate([
            { $match: { run_at: { $gte: fromDate } } },
            { $group: { _id: '$status', count: { $sum: 1 } } }
        ]);

        // Group by group
        const byGroup = await TestcaseHistory.aggregate([
            { $match: { run_at: { $gte: fromDate } } },
            { $group: { _id: '$group', count: { $sum: 1 } } }
        ]);

        res.json({
            period: `Last ${days} days`,
            total_runs: totalRuns,
            unique_testcases: uniqueTestcases.length,
            pass_rate: parseFloat(passRate),
            avg_response_time: overallAvgResponseTime,
            by_status: byStatus.reduce((acc, item) => {
                acc[item._id] = item.count;
                return acc;
            }, {}),
            by_group: byGroup.reduce((acc, item) => {
                acc[item._id] = item.count;
                return acc;
            }, {})
        });
    } catch (error) {
        console.error('Error fetching stats:', error);
        res.status(500).json({ error: 'Failed to fetch stats' });
    }
});

// ── DELETE /api/history/:id - Xóa 1 lịch sử ─────────────────────────────
router.delete('/history/:id', async (req, res) => {
    try {
        const history = await TestcaseHistory.findByIdAndDelete(req.params.id);
        if (!history) {
            return res.status(404).json({ error: 'History not found' });
        }
        res.json({ message: 'History deleted successfully' });
    } catch (error) {
        console.error('Error deleting history:', error);
        res.status(500).json({ error: 'Failed to delete history' });
    }
});

// ── DELETE /api/history - Xóa lịch sử cũ ────────────────────────────────
router.delete('/history', async (req, res) => {
    try {
        const { days = 30 } = req.query;
        const beforeDate = new Date();
        beforeDate.setDate(beforeDate.getDate() - parseInt(days));

        const result = await TestcaseHistory.deleteMany({
            run_at: { $lt: beforeDate }
        });

        res.json({
            message: `Deleted ${result.deletedCount} history records older than ${days} days`
        });
    } catch (error) {
        console.error('Error deleting old history:', error);
        res.status(500).json({ error: 'Failed to delete old history' });
    }
});

module.exports = router;
