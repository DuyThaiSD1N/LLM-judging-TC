// routes/run.js — chạy multi-turn testcase + LLM judge từng lượt

const express = require('express');
const router = express.Router();
const { judgeOne, CRITERIA_LIST } = require('./judge');
const History = require('../models/history');

const CALLBOT_URL = 'http://160.250.216.28:11005/api/v1/call/';

// ── Gọi Callbot 1 lượt ────────────────────────────────────────────────────
async function callBot(conversationId, message) {
    const payload = { conversation_id: conversationId, message };
    console.log('[callBot] →', JSON.stringify(payload));

    // Tính thời gian phản hồi từ 0s cho mỗi câu hỏi
    const startTime = Date.now();
    const res = await fetch(CALLBOT_URL, {
        method: 'POST',
        headers: { 'accept': 'application/json', 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    const endTime = Date.now();
    const responseTimeMs = endTime - startTime; // Reset về 0 cho mỗi câu hỏi

    if (!res.ok) throw new Error(`Callbot trả về HTTP ${res.status}`);

    const raw = await res.text();
    const parts = raw.trim().split('|');
    const action = parts[parts.length - 1].trim();
    const answer = parts.slice(0, -1).join('|').trim();

    console.log('[callBot] ←', { answer, action, responseTimeMs: `${responseTimeMs}ms` });
    return { answer, action, responseTimeMs };
}

// ── Chạy toàn bộ turns của 1 testcase ────────────────────────────────────
async function runTurns(tc) {
    // Bước 0: gửi "xin chào" để khởi động hội thoại, bỏ qua kết quả
    try {
        await callBot(tc.code, 'xin chào');
        console.log(`[warmup] ${tc.code} → đã chào, bắt đầu testcase`);
    } catch (err) {
        console.warn(`[warmup] ${tc.code} → lỗi chào:`, err.message);
    }

    const turnResults = [];
    const criteria = tc.criteria || 'standard';

    for (let j = 0; j < tc.turns.length; j++) {
        const turn = tc.turns[j];
        const turnResult = {
            question: turn.question,
            expected: turn.expected,
            actual: '',
            action: '',
            response_time_ms: null,
            verdict: null,
            error_desc: '',
            suggestion: '',
            suggested_response: '',
            tone_note: '',
            brevity_note: '',
            time_verdict: null,
            time_note: '',
            error: '',
        };

        try {
            // Mỗi câu hỏi tính thời gian phản hồi từ 0s đến khi nhận được response
            const { answer, action, responseTimeMs } = await callBot(tc.code, turn.question);
            turnResult.actual = answer;
            turnResult.action = action;
            turnResult.response_time_ms = responseTimeMs; // Thời gian riêng cho câu hỏi này

            const judge = await judgeOne({
                question: turn.question,
                expected: turn.expected,
                actual: answer,
                group: tc.group,
                responseTimeMs, // Truyền thời gian phản hồi của câu hỏi này
                criteria, // Truyền tiêu chí đánh giá
            });

            if (judge) {
                turnResult.verdict = judge.verdict;
                turnResult.error_desc = judge.error_desc;
                turnResult.suggestion = judge.suggestion;
                turnResult.suggested_response = judge.suggested_response;
                turnResult.tone_note = judge.tone_note;
                turnResult.brevity_note = judge.brevity_note;
                turnResult.time_verdict = judge.time_verdict;
                turnResult.time_note = judge.time_note;
                console.log(`[judge] ${tc.code} lượt ${j + 1} → ${judge.verdict} (${responseTimeMs}ms - reset cho câu tiếp theo)`);
            } else {
                console.log(`[judge] ${tc.code} lượt ${j + 1} → skipped (câu chào) (${responseTimeMs}ms)`);
            }
        } catch (err) {
            turnResult.error = err.message;
            console.error(`[error] ${tc.code} lượt ${j + 1}:`, err.message);
        }

        turnResults.push(turnResult);
        // Sau mỗi turn, thời gian sẽ tự động reset khi gọi callBot() lần tiếp theo
    }

    return turnResults;
}

// ── POST /api/run-testcases ───────────────────────────────────────────────
router.post('/run-testcases', async (req, res) => {
    const { testcases } = req.body;
    if (!Array.isArray(testcases) || testcases.length === 0)
        return res.status(400).json({ error: 'Không có testcase nào được gửi lên.' });

    const results = [];

    for (const tc of testcases) {
        // Chuẩn hoá: hỗ trợ cả format cũ (question/expected) và mới (turns)
        const turns = tc.turns ?? [{ question: tc.question, expected: tc.expected }];
        const tcNorm = { ...tc, turns };

        try {
            const turnResults = await runTurns(tcNorm);

            // Lưu lịch sử vào database
            try {
                History.save(tcNorm.code, tcNorm.name, tcNorm.group, turnResults);
            } catch (dbErr) {
                console.error('Failed to save history:', dbErr.message);
            }

            results.push({ ...tcNorm, turns: turnResults, status: 'done' });
        } catch (err) {
            results.push({ ...tcNorm, status: 'error', error: err.message });
        }
    }

    res.json({ results });
});

// ── POST /api/run-single ──────────────────────────────────────────────────
router.post('/run-single', async (req, res) => {
    const { code, group, turns, question, expected, criteria } = req.body;

    // Hỗ trợ cả format cũ và mới
    const tcTurns = turns ?? [{ question, expected }];
    if (!tcTurns[0]?.question)
        return res.status(400).json({ error: 'Thiếu câu hỏi.' });

    try {
        const turnResults = await runTurns({
            code,
            group: group ?? 'A',
            turns: tcTurns,
            criteria: criteria ?? 'standard'
        });

        // Lưu lịch sử vào database
        try {
            History.save(code, code, group ?? 'A', turnResults);
        } catch (dbErr) {
            console.error('Failed to save history:', dbErr.message);
        }

        res.json({ turns: turnResults, status: 'done' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ── GET /api/criteria ─────────────────────────────────────────────────────
router.get('/criteria', (req, res) => {
    res.json({ criteria: CRITERIA_LIST });
});

module.exports = router;
