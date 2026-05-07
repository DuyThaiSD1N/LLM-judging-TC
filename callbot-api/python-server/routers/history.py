"""
History router - Lịch sử đánh giá
"""

from fastapi import APIRouter, HTTPException, Query

from models.history import History


router = APIRouter()


@router.get("/history")
async def get_history(limit: int = Query(50, ge=1, le=1000)):
    """
    Lấy lịch sử gần nhất
    
    GET /api/history?limit=50
    """
    try:
        history = History.get_recent(limit)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/stats")
async def get_stats():
    """
    Lấy thống kê
    
    GET /api/history/stats
    """
    try:
        stats = History.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{code}")
async def get_testcase_history(code: str, limit: int = Query(10, ge=1, le=100)):
    """
    Lấy lịch sử theo testcase
    
    GET /api/history/{code}?limit=10
    """
    try:
        history = History.get_by_testcase(code, limit)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/cleanup")
async def cleanup_history(days: int = Query(30, ge=1, le=365)):
    """
    Xóa lịch sử cũ
    
    DELETE /api/history/cleanup?days=30
    """
    try:
        deleted = History.cleanup(days)
        return {"success": True, "deleted": deleted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/history/fix-timezone")
async def fix_timezone():
    """
    Fix timezone cho các records cũ (chuyển từ UTC sang localtime)
    
    POST /api/history/fix-timezone
    """
    try:
        from config.database import get_db
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Update all records to use localtime
        # Note: This assumes records were saved in UTC and need to be converted
        cursor.execute("""
            UPDATE history
            SET run_at = datetime(run_at, 'localtime')
            WHERE run_at IS NOT NULL
        """)
        
        updated = cursor.rowcount
        conn.commit()
        conn.close()
        
        return {"success": True, "updated": updated, "message": f"Fixed {updated} records"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
