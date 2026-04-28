// models/TestcaseHistory.js — Lịch sử đánh giá testcase

const mongoose = require('mongoose');

const TurnResultSchema = new mongoose.Schema({
    question: { type: String, required: true },
    expected: { type: String, required: true },
    actual: { type: String, default: null },
    action: { type: String, default: '' },
    response_time_ms: { type: Number, default: null },
    verdict: { type: String, enum: ['PASSED', 'FAILED', null], default: null },
    error_desc: { type: String, default: '' },
    suggestion: { type: String, default: '' },
    tone_note: { type: String, default: '' },
    brevity_note: { type: String, default: '' },
    time_verdict: { type: String, enum: ['good', 'ok', 'slow', null], default: null },
    time_note: { type: String, default: '' },
}, { _id: false });

const TestcaseHistorySchema = new mongoose.Schema({
    testcase_code: { type: String, required: true, index: true },
    testcase_name: { type: String, required: true },
    group: { type: String, required: true, enum: ['A', 'B', 'C', 'D'] },

    // Kết quả tổng quan
    status: { type: String, required: true, enum: ['done', 'error'] },
    error: { type: String, default: '' },

    // Kết quả từng lượt
    turns: [TurnResultSchema],

    // Thống kê
    total_turns: { type: Number, default: 0 },
    passed_turns: { type: Number, default: 0 },
    failed_turns: { type: Number, default: 0 },
    avg_response_time: { type: Number, default: 0 },

    // Metadata
    run_at: { type: Date, default: Date.now, index: true },
    run_by: { type: String, default: 'system' }, // Có thể thêm user info sau
}, {
    timestamps: true
});

// Index để query nhanh
TestcaseHistorySchema.index({ testcase_code: 1, run_at: -1 });
TestcaseHistorySchema.index({ group: 1, run_at: -1 });
TestcaseHistorySchema.index({ status: 1, run_at: -1 });

// Static method: Tạo history từ kết quả chạy testcase
TestcaseHistorySchema.statics.createFromResult = async function (testcase, turns) {
    const totalTurns = turns.length;
    const passedTurns = turns.filter(t => t.verdict === 'PASSED').length;
    const failedTurns = turns.filter(t => t.verdict === 'FAILED').length;

    const responseTimes = turns
        .map(t => t.response_time_ms)
        .filter(t => t !== null && t !== undefined);
    const avgResponseTime = responseTimes.length > 0
        ? Math.round(responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length)
        : 0;

    const history = new this({
        testcase_code: testcase.code,
        testcase_name: testcase.name,
        group: testcase.group,
        status: testcase.status === 'error' ? 'error' : 'done',
        error: testcase.error || '',
        turns: turns,
        total_turns: totalTurns,
        passed_turns: passedTurns,
        failed_turns: failedTurns,
        avg_response_time: avgResponseTime,
    });

    await history.save();
    return history;
};

module.exports = mongoose.model('TestcaseHistory', TestcaseHistorySchema);
