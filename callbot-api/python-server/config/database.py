"""
Database configuration và initialization cho SQLite
"""

import sqlite3
from pathlib import Path


# Database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "testcases.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database schema"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Table: testcases
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS testcases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            group_type TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Table: turns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            testcase_id INTEGER NOT NULL,
            turn_number INTEGER NOT NULL,
            scenario TEXT,
            question TEXT NOT NULL,
            expected TEXT NOT NULL,
            FOREIGN KEY (testcase_id) REFERENCES testcases(id) ON DELETE CASCADE
        )
    """)
    
    # Table: history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            testcase_id INTEGER NOT NULL,
            turn_number INTEGER NOT NULL,
            scenario TEXT,
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
            run_at DATETIME DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (testcase_id) REFERENCES testcases(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")


# Initialize database on module load
init_db()
