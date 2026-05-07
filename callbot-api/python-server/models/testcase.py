"""
Testcase model với SQLite operations
"""

from typing import List, Optional, Dict, Any
from config.database import get_db


class Testcase:
    """Testcase model"""
    
    @staticmethod
    def create(testcase: Dict[str, Any]) -> int:
        """
        Lưu testcase mới HOẶC thêm turns vào testcase đã tồn tại
        
        Args:
            testcase: Dict với keys: code, name, group, turns, bot_url (optional)
            
        Returns:
            testcase_id
        """
        conn = get_db()
        cursor = conn.cursor()
        
        # Kiểm tra xem testcase đã tồn tại chưa
        cursor.execute(
            "SELECT id FROM testcases WHERE code = ?",
            (testcase["code"],)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Testcase đã tồn tại → Thêm turns mới vào (conversation mode)
            testcase_id = existing["id"]
            
            # Lấy turn_number cao nhất hiện tại
            cursor.execute(
                "SELECT MAX(turn_number) as max_turn FROM turns WHERE testcase_id = ?",
                (testcase_id,)
            )
            max_turn_result = cursor.fetchone()
            next_turn_number = (max_turn_result["max_turn"] or 0) + 1
            
            # Thêm turns mới
            for idx, turn in enumerate(testcase["turns"]):
                cursor.execute(
                    """
                    INSERT INTO turns (testcase_id, turn_number, question, expected)
                    VALUES (?, ?, ?, ?)
                    """,
                    (testcase_id, next_turn_number + idx, turn["question"], turn["expected"])
                )
            
            print(f"✅ Added {len(testcase['turns'])} new turn(s) to existing testcase {testcase['code']}")
        else:
            # Testcase mới → Tạo mới
            cursor.execute(
                """
                INSERT INTO testcases (code, name, group_type, bot_url)
                VALUES (?, ?, ?, ?)
                """,
                (testcase["code"], testcase["name"], testcase["group"], testcase.get("bot_url"))
            )
            
            testcase_id = cursor.lastrowid
            
            # Insert turns
            for idx, turn in enumerate(testcase["turns"]):
                cursor.execute(
                    """
                    INSERT INTO turns (testcase_id, turn_number, question, expected)
                    VALUES (?, ?, ?, ?)
                    """,
                    (testcase_id, idx + 1, turn["question"], turn["expected"])
                )
            
            print(f"✅ Created new testcase {testcase['code']} with {len(testcase['turns'])} turn(s)")
        
        conn.commit()
        conn.close()
        
        return testcase_id
    
    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        """Lấy tất cả testcases"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM testcases ORDER BY created_at DESC"
        )
        testcases = cursor.fetchall()
        
        result = []
        for tc in testcases:
            cursor.execute(
                """
                SELECT turn_number, question, expected
                FROM turns
                WHERE testcase_id = ?
                ORDER BY turn_number
                """,
                (tc["id"],)
            )
            turns = cursor.fetchall()
            
            result.append({
                "id": tc["id"],
                "code": tc["code"],
                "name": tc["name"],
                "group": tc["group_type"],
                "turns": [
                    {"question": t["question"], "expected": t["expected"]}
                    for t in turns
                ],
                "created_at": tc["created_at"]
            })
        
        conn.close()
        return result
    
    @staticmethod
    def get_by_code(code: str) -> Optional[Dict[str, Any]]:
        """Lấy testcase theo code"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM testcases WHERE code = ?",
            (code,)
        )
        tc = cursor.fetchone()
        
        if not tc:
            conn.close()
            return None
        
        cursor.execute(
            """
            SELECT turn_number, question, expected
            FROM turns
            WHERE testcase_id = ?
            ORDER BY turn_number
            """,
            (tc["id"],)
        )
        turns = cursor.fetchall()
        
        result = {
            "id": tc["id"],
            "code": tc["code"],
            "name": tc["name"],
            "group": tc["group_type"],
            "turns": [
                {"question": t["question"], "expected": t["expected"]}
                for t in turns
            ],
            "created_at": tc["created_at"]
        }
        
        conn.close()
        return result
    
    @staticmethod
    def delete(code: str) -> bool:
        """Xóa testcase"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM testcases WHERE code = ?",
            (code,)
        )
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    
    @staticmethod
    def delete_all() -> bool:
        """Xóa tất cả testcases"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM testcases")
        cursor.execute("DELETE FROM turns")
        
        conn.commit()
        conn.close()
        
        return True
