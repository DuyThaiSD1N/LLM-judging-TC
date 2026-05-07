"""
Testcase CRUD router
"""

from fastapi import APIRouter, HTTPException
from typing import List

from models.schemas import TestcaseCreate, TestcaseResponse
from models.testcase import Testcase


router = APIRouter()


@router.get("/testcases")
async def get_testcases():
    """
    Lấy tất cả testcases
    
    GET /api/testcases
    """
    try:
        testcases = Testcase.get_all()
        return {"testcases": testcases}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/testcases")
async def create_testcase(testcase: TestcaseCreate):
    """
    Tạo testcase mới HOẶC thêm turns vào testcase đã tồn tại (conversation mode)
    
    POST /api/testcases
    Body: { code, name, group, bot_url, turns }
    
    - Nếu code chưa tồn tại → Tạo testcase mới
    - Nếu code đã tồn tại → Thêm turns mới vào testcase đó (như tiếp tục cuộc hội thoại)
    """
    try:
        testcase_dict = testcase.model_dump()
        testcase_dict["turns"] = [
            {"question": t.question, "expected": t.expected}
            for t in testcase.turns
        ]
        
        testcase_id = Testcase.create(testcase_dict)
        
        # Kiểm tra xem là tạo mới hay thêm turns
        existing = Testcase.get_by_code(testcase.code)
        is_new = len(existing["turns"]) == len(testcase.turns)
        
        return {
            "success": True,
            "id": testcase_id,
            "mode": "created" if is_new else "appended",
            "total_turns": len(existing["turns"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/testcases/{code}")
async def delete_testcase(code: str):
    """
    Xóa testcase
    
    DELETE /api/testcases/{code}
    """
    try:
        deleted = Testcase.delete(code)
        if not deleted:
            raise HTTPException(status_code=404, detail="Testcase not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/testcases")
async def delete_all_testcases():
    """
    Xóa tất cả testcases
    
    DELETE /api/testcases
    """
    try:
        Testcase.delete_all()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
