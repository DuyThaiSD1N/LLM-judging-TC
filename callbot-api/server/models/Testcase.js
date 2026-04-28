// models/Testcase.js — Testcase schema

const mongoose = require('mongoose');

const TurnSchema = new mongoose.Schema({
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

const TestcaseSchema = new mongoose.Schema({
    code: { type: String, required: true, unique: true },
    name: { type: String, required: true },
    group: { type: String, required: true, enum: ['A', 'B', 'C', 'D'] },
    status: { type: String, default: 'pending', enum: ['pending', 'running', 'done', 'error'] },
    error: { type: String, default: '' },
    turns: [TurnSchema],
    createdAt: { type: Date, default: Date.now },
    updatedAt: { type: Date, default: Date.now },
});

// Update timestamp on save
TestcaseSchema.pre('save', function (next) {
    this.updatedAt = Date.now();
    next();
});

module.exports = mongoose.model('Testcase', TestcaseSchema);
