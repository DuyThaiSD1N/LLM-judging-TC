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
    Tạo testcase mới
    
    POST /api/testcases
    Body: { code, name, group, turns }
    """
    try:
        testcase_dict = testcase.model_dump()
        testcase_dict["turns"] = [
            {"question": t.question, "expected": t.expected}
            for t in testcase.turns
        ]
        
        testcase_id = Testcase.create(testcase_dict)
        return {"success": True, "id": testcase_id}
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            raise HTTPException(status_code=409, detail="Testcase code already exists")
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
