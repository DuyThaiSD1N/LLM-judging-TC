// models/testcase.js — Testcase model với SQLite

const db = require('../config/database');

class Testcase {
    // Lưu testcase mới
    static create(testcase) {
        const { code, name, group, turns } = testcase;

        // Insert testcase
        const insertTC = db.prepare(`
            INSERT INTO testcases (code, name, group_type)
            VALUES (?, ?, ?)
        `);

        const result = insertTC.run(code, name, group);
        const testcaseId = result.lastInsertRowid;

        // Insert turns
        const insertTurn = db.prepare(`
            INSERT INTO turns (testcase_id, turn_number, question, expected)
            VALUES (?, ?, ?, ?)
        `);

        turns.forEach((turn, index) => {
            insertTurn.run(testcaseId, index + 1, turn.question, turn.expected);
        });

        return testcaseId;
    }

    // Lấy tất cả testcases
    static getAll() {
        const testcases = db.prepare(`
            SELECT * FROM testcases ORDER BY created_at DESC
        `).all();

        return testcases.map(tc => {
            const turns = db.prepare(`
                SELECT turn_number, question, expected
                FROM turns
                WHERE testcase_id = ?
                ORDER BY turn_number
            `).all(tc.id);

            return {
                id: tc.id,
                code: tc.code,
                name: tc.name,
                group: tc.group_type,
                turns: turns.map(t => ({
                    question: t.question,
                    expected: t.expected
                })),
                created_at: tc.created_at
            };
        });
    }

    // Lấy testcase theo code
    static getByCode(code) {
        const tc = db.prepare(`
            SELECT * FROM testcases WHERE code = ?
        `).get(code);

        if (!tc) return null;

        const turns = db.prepare(`
            SELECT turn_number, question, expected
            FROM turns
            WHERE testcase_id = ?
            ORDER BY turn_number
        `).all(tc.id);

        return {
            id: tc.id,
            code: tc.code,
            name: tc.name,
            group: tc.group_type,
            turns: turns.map(t => ({
                question: t.question,
                expected: t.expected
            })),
            created_at: tc.created_at
        };
    }

    // Xóa testcase
    static delete(code) {
        const result = db.prepare(`
            DELETE FROM testcases WHERE code = ?
        `).run(code);

        return result.changes > 0;
    }

    // Xóa tất cả testcases
    static deleteAll() {
        db.prepare('DELETE FROM testcases').run();
        db.prepare('DELETE FROM turns').run();
        return true;
    }
}

module.exports = Testcase;
