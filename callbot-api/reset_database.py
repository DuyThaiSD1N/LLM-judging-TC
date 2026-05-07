"""
Script để reset database - xóa và tạo lại với schema mới
"""

import sys
from pathlib import Path

# Add python-server to path
sys.path.insert(0, str(Path(__file__).parent / "python-server"))

from config.database import DB_PATH, init_db


def reset_database():
    """Xóa database cũ và tạo lại"""
    if DB_PATH.exists():
        print(f"🗑️  Deleting old database: {DB_PATH}")
        DB_PATH.unlink()
    else:
        print(f"ℹ️  No existing database found at: {DB_PATH}")
    
    print("🔨 Creating new database with updated schema...")
    init_db()
    print("✅ Database reset complete!")


if __name__ == "__main__":
    confirm = input("⚠️  This will DELETE all history data. Continue? (yes/no): ")
    if confirm.lower() == "yes":
        reset_database()
    else:
        print("❌ Cancelled")
