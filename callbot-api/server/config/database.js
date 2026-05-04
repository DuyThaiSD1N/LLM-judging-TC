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
    criteria TEXT DEFAULT 'standard',
    error TEXT,
    run_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (testcase_id) REFERENCES testcases(id) ON DELETE CASCADE
  )
`);

// Thêm cột suggested_response nếu chưa có (migration cho database cũ)
try {
  db.exec(`ALTER TABLE history ADD COLUMN suggested_response TEXT`);
  console.log('✅ Added suggested_response column to history table');
} catch (err) {
  // Cột đã tồn tại, bỏ qua
  if (!err.message.includes('duplicate column name')) {
    console.warn('⚠️ Migration warning:', err.message);
  }
}

// Thêm cột criteria nếu chưa có (migration cho database cũ)
try {
  db.exec(`ALTER TABLE history ADD COLUMN criteria TEXT DEFAULT 'standard'`);
  console.log('✅ Added criteria column to history table');
} catch (err) {
  // Cột đã tồn tại, bỏ qua
  if (!err.message.includes('duplicate column name')) {
    console.warn('⚠️ Migration warning:', err.message);
  }
}

// Xóa cột brevity_note (migration)
// SQLite không hỗ trợ DROP COLUMN trực tiếp, phải tạo lại bảng
try {
  // Check if brevity_note column exists
  const columns = db.pragma('table_info(history)');
  const hasBrevityNote = columns.some(col => col.name === 'brevity_note');

  if (hasBrevityNote) {
    console.log('🔄 Migrating: Removing brevity_note column from history table...');

    // Tạo bảng mới không có brevity_note
    db.exec(`
      CREATE TABLE history_new (
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
        time_verdict TEXT,
        time_note TEXT,
        criteria TEXT DEFAULT 'standard',
        error TEXT,
        run_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (testcase_id) REFERENCES testcases(id) ON DELETE CASCADE
      )
    `);

    // Copy dữ liệu từ bảng cũ sang bảng mới (bỏ qua brevity_note)
    db.exec(`
      INSERT INTO history_new (
        id, testcase_id, turn_number, question, expected, actual, action,
        response_time_ms, verdict, error_desc, suggestion, suggested_response,
        tone_note, time_verdict, time_note, criteria, error, run_at
      )
      SELECT 
        id, testcase_id, turn_number, question, expected, actual, action,
        response_time_ms, verdict, error_desc, suggestion, suggested_response,
        tone_note, time_verdict, time_note, criteria, error, run_at
      FROM history
    `);

    // Xóa bảng cũ
    db.exec(`DROP TABLE history`);

    // Đổi tên bảng mới thành history
    db.exec(`ALTER TABLE history_new RENAME TO history`);

    // Tạo lại index
    db.exec(`
      CREATE INDEX IF NOT EXISTS idx_history_testcase ON history(testcase_id);
      CREATE INDEX IF NOT EXISTS idx_history_run_at ON history(run_at);
    `);

    console.log('✅ Successfully removed brevity_note column from history table');
  }
} catch (err) {
  console.error('❌ Migration error:', err.message);
}

// Tạo index cho tìm kiếm nhanh
db.exec(`
  CREATE INDEX IF NOT EXISTS idx_testcase_code ON testcases(code);
  CREATE INDEX IF NOT EXISTS idx_history_testcase ON history(testcase_id);
  CREATE INDEX IF NOT EXISTS idx_history_run_at ON history(run_at);
`);

console.log('✅ SQLite database initialized:', dbPath);

module.exports = db;
