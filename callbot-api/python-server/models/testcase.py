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
        Lưu testcase mới
        
        Args:
            testcase: Dict với keys: code, name, group, turns
            
        Returns:
            testcase_id
        """
        conn = get_db()
        cursor = conn.cursor()
        
        # Insert testcase
        cursor.execute(
            """
            INSERT INTO testcases (code, name, group_type)
            VALUES (?, ?, ?)
            """,
            (testcase["code"], testcase["name"], testcase["group"])
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
