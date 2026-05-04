"""
History model để lưu kết quả chạy testcase
"""

from typing import List, Dict, Any, Optional
from config.database import get_db


class History:
    """History model"""
    
    @staticmethod
    def save(
        testcase_code: str,
        testcase_name: str,
        testcase_group: str,
        turn_results: List[Dict[str, Any]],
        criteria: str = "standard"
    ):
        """
        Lưu lịch sử theo testcase với criteria
        
        Args:
            testcase_code: Mã testcase
            testcase_name: Tên testcase
            testcase_group: Nhóm testcase
            turn_results: Danh sách kết quả từng turn
            criteria: Tiêu chí đánh giá
        """
        conn = get_db()
        cursor = conn.cursor()
        
        # Tìm hoặc tạo testcase
        cursor.execute(
            "SELECT id FROM testcases WHERE code = ?",
            (testcase_code,)
        )
        tc = cursor.fetchone()
        
        if not tc:
            # Tạo testcase mới nếu chưa có
            cursor.execute(
                """
                INSERT INTO testcases (code, name, group_type)
                VALUES (?, ?, ?)
                """,
                (testcase_code, testcase_name or testcase_code, testcase_group or "A")
            )
            testcase_id = cursor.lastrowid
            
            # Lưu turns
            for idx, turn in enumerate(turn_results):
                cursor.execute(
                    """
                    INSERT INTO turns (testcase_id, turn_number, question, expected)
                    VALUES (?, ?, ?, ?)
                    """,
                    (testcase_id, idx + 1, turn["question"], turn["expected"])
                )
            
            print(f"✅ Created testcase {testcase_code} in database")
        else:
            testcase_id = tc["id"]
        
        # Lưu history với criteria
        for idx, turn in enumerate(turn_results):
            cursor.execute(
                """
                INSERT INTO history (
                    testcase_id, turn_number, question, expected, actual, action,
                    response_time_ms, verdict, error_desc, suggestion, suggested_response,
                    tone_note, time_verdict, time_note, criteria, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    testcase_id,
                    idx + 1,
                    turn["question"],
                    turn["expected"],
                    turn.get("actual"),
                    turn.get("action"),
                    turn.get("response_time_ms"),
                    turn.get("verdict"),
                    turn.get("error_desc"),
                    turn.get("suggestion"),
                    turn.get("suggested_response"),
                    turn.get("tone_note"),
                    turn.get("time_verdict"),
                    turn.get("time_note"),
                    criteria,
                    turn.get("error")
                )
            )
        
        conn.commit()
        conn.close()
        
        print(f"✅ Saved history for {testcase_code} ({len(turn_results)} turns) with criteria: {criteria}")
    
    @staticmethod
    def get_by_testcase(testcase_code: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Lấy lịch sử theo testcase code"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id FROM testcases WHERE code = ?",
            (testcase_code,)
        )
        tc = cursor.fetchone()
        
        if not tc:
            conn.close()
            return []
        
        cursor.execute(
            """
            SELECT * FROM history
            WHERE testcase_id = ?
            ORDER BY run_at DESC
            LIMIT ?
            """,
            (tc["id"], limit)
        )
        
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return history
    
    @staticmethod
    def get_recent(limit: int = 50) -> List[Dict[str, Any]]:
        """Lấy tất cả lịch sử (gần nhất)"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT 
                h.*,
                t.code as testcase_code,
                t.name as testcase_name,
                t.group_type
            FROM history h
            JOIN testcases t ON h.testcase_id = t.id
            ORDER BY h.run_at DESC
            LIMIT ?
            """,
            (limit,)
        )
        
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return history
    
    @staticmethod
    def get_stats() -> Dict[str, Any]:
        """Thống kê tổng quan"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM history")
        total = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM history WHERE verdict = 'PASSED'")
        passed = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM history WHERE verdict = 'FAILED'")
        failed = cursor.fetchone()["count"]
        
        cursor.execute(
            """
            SELECT AVG(response_time_ms) as avg_time 
            FROM history 
            WHERE response_time_ms IS NOT NULL
            """
        )
        avg_time_row = cursor.fetchone()
        avg_time = avg_time_row["avg_time"] if avg_time_row["avg_time"] else 0
        
        conn.close()
        
        return {
            "total_runs": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round((passed / total * 100), 1) if total > 0 else 0,
            "avg_response_time": round(avg_time) if avg_time else 0
        }
    
    @staticmethod
    def cleanup(days_to_keep: int = 30) -> int:
        """Xóa lịch sử cũ (giữ lại N ngày gần nhất)"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            DELETE FROM history
            WHERE run_at < datetime('now', '-' || ? || ' days')
            """,
            (days_to_keep,)
        )
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"🗑️ Cleaned up {deleted} old history records")
        return deleted
