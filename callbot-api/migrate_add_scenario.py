"""
Migration script - Thêm cột scenario vào tables turns và history
"""

import sys
from pathlib import Path

# Add python-server to path
sys.path.insert(0, str(Path(__file__).parent / "python-server"))

from config.database import get_db


def migrate_add_scenario():
    """Thêm cột scenario vào tables turns và history"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check if scenario column exists in turns table
        cursor.execute("PRAGMA table_info(turns)")
        turns_columns = [col[1] for col in cursor.fetchall()]
        
        if 'scenario' not in turns_columns:
            print("📝 Adding 'scenario' column to 'turns' table...")
            cursor.execute("ALTER TABLE turns ADD COLUMN scenario TEXT")
            print("✅ Added 'scenario' to 'turns' table")
        else:
            print("ℹ️  'scenario' column already exists in 'turns' table")
        
        # Check if scenario column exists in history table
        cursor.execute("PRAGMA table_info(history)")
        history_columns = [col[1] for col in cursor.fetchall()]
        
        if 'scenario' not in history_columns:
            print("📝 Adding 'scenario' column to 'history' table...")
            cursor.execute("ALTER TABLE history ADD COLUMN scenario TEXT")
            print("✅ Added 'scenario' to 'history' table")
        else:
            print("ℹ️  'scenario' column already exists in 'history' table")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("🎉 Database is now ready to use scenario feature")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("MIGRATION: Add scenario column to database")
    print("=" * 60)
    print()
    
    migrate_add_scenario()
