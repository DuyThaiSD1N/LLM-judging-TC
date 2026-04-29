// config/database.js — SQLite database setup

const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

// Tạo thư mục data nếu chưa có
const dataDir = path.join(__dirname, '../../data');
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
  console.log('📁 Created data directory:', dataDir);
}

// Tạo database file trong thư mục data
const dbPath = path.join(dataDir, 'testcases.db');
const db = new Database(dbPath);

// Enable WAL mode for better performance
db.pragma('journal_mode = WAL');

// Tạo bảng testcases
db.exec(`
  CREATE TABLE IF NOT EXISTS testcases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    group_type TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )
`);

// Tạo bảng turns (lượt hỏi/đáp)
db.exec(`
  CREATE TABLE IF NOT EXISTS turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    testcase_id INTEGER NOT NULL,
    turn_number INTEGER NOT NULL,
    question TEXT NOT NULL,
    expected TEXT NOT NULL,
    FOREIGN KEY (testcase_id) REFERENCES testcases(id) ON DELETE CASCADE
  )
`);

// Tạo bảng history (lịch sử chạy testcase)
db.exec(`
  CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    testcase_id INTEGER NOT NULL,
    turn_number INTEGER NOT NULL,
    question TEXT NOT NULL,
    expected TEXT NOT NULL,
    actual TEXT,
    action TEXT,
    response_time_ms INTEGER,
    verdict TEXT,
    error_desc TEXT,
    suggestion TEXT,
    suggested_response TEXT,
    tone_note TEXT,
    brevity_note TEXT,
    time_verdict TEXT,
    time_note TEXT,
    error TEXT,
    run_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (testcase_id) REFERENCES testcases(id) ON DELETE CASCADE
  )
`);

// Tạo index cho tìm kiếm nhanh
db.exec(`
  CREATE INDEX IF NOT EXISTS idx_testcase_code ON testcases(code);
  CREATE INDEX IF NOT EXISTS idx_history_testcase ON history(testcase_id);
  CREATE INDEX IF NOT EXISTS idx_history_run_at ON history(run_at);
`);

console.log('✅ SQLite database initialized:', dbPath);

module.exports = db;
