// models/history.js — History model để lưu kết quả chạy testcase

const db = require('../config/database');

class History {
    // Lưu lịch sử theo testcase với criteria
    static save(testcaseCode, testcaseName, testcaseGroup, turnResults, criteria = 'standard') {
        // Tìm hoặc tạo testcase
        let tc = db.prepare('SELECT id FROM testcases WHERE code = ?').get(testcaseCode);

        if (!tc) {
            // Tạo testcase mới nếu chưa có
            const insertTC = db.prepare(`
                INSERT INTO testcases (code, name, group_type)
                VALUES (?, ?, ?)
            `);
            const result = insertTC.run(testcaseCode, testcaseName || testcaseCode, testcaseGroup || 'A');

            // Lưu turns
            const insertTurn = db.prepare(`
                INSERT INTO turns (testcase_id, turn_number, question, expected)
                VALUES (?, ?, ?, ?)
            `);
            turnResults.forEach((turn, index) => {
                insertTurn.run(result.lastInsertRowid, index + 1, turn.question, turn.expected);
            });

            tc = { id: result.lastInsertRowid };
            console.log(`✅ Created testcase ${testcaseCode} in database`);
        }

        // Lưu history với criteria
        const insert = db.prepare(`
            INSERT INTO history (
                testcase_id, turn_number, question, expected, actual, action,
                response_time_ms, verdict, error_desc, suggestion, suggested_response,
                tone_note, brevity_note, time_verdict, time_note, criteria, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `);

        turnResults.forEach((turn, index) => {
            insert.run(
                tc.id,
                index + 1,
                turn.question,
                turn.expected,
                turn.actual || null,
                turn.action || null,
                turn.response_time_ms || null,
                turn.verdict || null,
                turn.error_desc || null,
                turn.suggestion || null,
                turn.suggested_response || null,
                turn.tone_note || null,
                turn.brevity_note || null,
                turn.time_verdict || null,
                turn.time_note || null,
                criteria,
                turn.error || null
            );
        });

        console.log(`✅ Saved history for ${testcaseCode} (${turnResults.length} turns) with criteria: ${criteria}`);
    }

    // Lấy lịch sử theo testcase code
    static getByTestcase(testcaseCode, limit = 10) {
        const tc = db.prepare('SELECT id FROM testcases WHERE code = ?').get(testcaseCode);
        if (!tc) return [];

        return db.prepare(`
            SELECT * FROM history
            WHERE testcase_id = ?
            ORDER BY run_at DESC
            LIMIT ?
        `).all(tc.id, limit);
    }

    // Lấy tất cả lịch sử (gần nhất)
    static getRecent(limit = 50) {
        return db.prepare(`
            SELECT 
                h.*,
                t.code as testcase_code,
                t.name as testcase_name,
                t.group_type
            FROM history h
            JOIN testcases t ON h.testcase_id = t.id
            ORDER BY h.run_at DESC
            LIMIT ?
        `).all(limit);
    }

    // Thống kê tổng quan
    static getStats() {
        const total = db.prepare('SELECT COUNT(*) as count FROM history').get();
        const passed = db.prepare("SELECT COUNT(*) as count FROM history WHERE verdict = 'PASS'").get();
        const failed = db.prepare("SELECT COUNT(*) as count FROM history WHERE verdict = 'FAIL'").get();

        const avgTime = db.prepare(`
            SELECT AVG(response_time_ms) as avg_time 
            FROM history 
            WHERE response_time_ms IS NOT NULL
        `).get();

        return {
            total_runs: total.count,
            passed: passed.count,
            failed: failed.count,
            pass_rate: total.count > 0 ? ((passed.count / total.count) * 100).toFixed(1) : 0,
            avg_response_time: avgTime.avg_time ? Math.round(avgTime.avg_time) : 0
        };
    }

    // Xóa lịch sử cũ (giữ lại N ngày gần nhất)
    static cleanup(daysToKeep = 30) {
        const result = db.prepare(`
            DELETE FROM history
            WHERE run_at < datetime('now', '-' || ? || ' days')
        `).run(daysToKeep);

        console.log(`🗑️ Cleaned up ${result.changes} old history records`);
        return result.changes;
    }
}

module.exports = History;
