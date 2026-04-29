// test-db.js - Test SQLite database

const db = require('./config/database');
const History = require('./models/history');

console.log('🧪 Testing SQLite database...\n');

// Test 1: Tạo testcase và lưu history
console.log('Test 1: Save history with auto-create testcase');
const testResults = [
    {
        question: 'Câu hỏi test 1',
        expected: 'Kỳ vọng test 1',
        actual: 'Câu trả lời test 1',
        action: 'CHAT',
        response_time_ms: 1500,
        verdict: 'PASS',
        error_desc: '',
        suggestion: '',
        tone_note: 'Lịch sự',
        brevity_note: 'Ngắn gọn',
        time_verdict: 'good',
        time_note: 'Nhanh',
        error: ''
    },
    {
        question: 'Câu hỏi test 2',
        expected: 'Kỳ vọng test 2',
        actual: 'Câu trả lời test 2',
        action: 'CHAT',
        response_time_ms: 2000,
        verdict: 'FAIL',
        error_desc: 'Không đúng nội dung',
        suggestion: 'Cần trả lời chính xác hơn',
        tone_note: 'Lịch sự',
        brevity_note: 'Hơi dài',
        time_verdict: 'ok',
        time_note: 'Chấp nhận được',
        error: ''
    }
];

try {
    History.save('TC-TEST-001', 'Testcase thử nghiệm', 'A', testResults);
    console.log('✅ Test 1 passed!\n');
} catch (err) {
    console.error('❌ Test 1 failed:', err.message, '\n');
}

// Test 2: Lấy thống kê
console.log('Test 2: Get statistics');
try {
    const stats = History.getStats();
    console.log('Stats:', stats);
    console.log('✅ Test 2 passed!\n');
} catch (err) {
    console.error('❌ Test 2 failed:', err.message, '\n');
}

// Test 3: Lấy lịch sử gần nhất
console.log('Test 3: Get recent history');
try {
    const history = History.getRecent(10);
    console.log(`Found ${history.length} history records`);
    if (history.length > 0) {
        console.log('Latest:', {
            testcase: history[0].testcase_code,
            verdict: history[0].verdict,
            time: history[0].run_at
        });
    }
    console.log('✅ Test 3 passed!\n');
} catch (err) {
    console.error('❌ Test 3 failed:', err.message, '\n');
}

// Test 4: Kiểm tra database file
const fs = require('fs');
const path = require('path');
const dbPath = path.join(__dirname, '../data/testcases.db');
const exists = fs.existsSync(dbPath);
console.log('Test 4: Database file exists');
console.log('Path:', dbPath);
console.log('Exists:', exists);
if (exists) {
    const stats = fs.statSync(dbPath);
    console.log('Size:', Math.round(stats.size / 1024), 'KB');
    console.log('✅ Test 4 passed!\n');
} else {
    console.log('❌ Test 4 failed: Database file not found\n');
}

console.log('🎉 All tests completed!');
