"""
Run testcases router - Chạy testcases với LangGraph
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
import json
import asyncio
from langsmith import traceable

from models.schemas import (
    RunSingleRequest,
    RunTestcasesRequest,
    RunTestcasesResponse,
    TestcaseRunResult
)
from graphs.testcase_runner import run_testcase
from config.criteria_weights import CRITERIA_LIST


router = APIRouter()


@router.post("/run-testcases", response_model=RunTestcasesResponse)
@traceable(name="run_testcases_endpoint", run_type="chain")
async def run_testcases(request: RunTestcasesRequest):
    """
    Chạy multiple testcases
    
    POST /api/run-testcases
    Body: { testcases: [...] }
    """
    if not request.testcases:
        raise HTTPException(status_code=400, detail="Không có testcase nào được gửi lên.")
    
    results: List[TestcaseRunResult] = []
    
    for tc in request.testcases:
        # Chuẩn hoá: hỗ trợ format với turns
        turns = [{"question": t.question, "expected": t.expected} for t in tc.turns]
        
        try:
            # Run testcase với LangGraph
            # Ưu tiên bot_url của testcase, fallback về request.bot_url
            bot_url = tc.bot_url if tc.bot_url else request.bot_url
            result = await run_testcase(
                code=tc.code,
                name=tc.name,
                group=tc.group,
                turns=turns,
                criteria=tc.criteria,
                bot_url=bot_url
            )
            
            results.append(
                TestcaseRunResult(
                    code=tc.code,
                    name=tc.name,
                    group=tc.group,
                    turns=result["turns"],
                    criteria=tc.criteria,
                    status=result["status"],
                    error=result.get("error")
                )
            )
        except Exception as e:
            results.append(
                TestcaseRunResult(
                    code=tc.code,
                    name=tc.name,
                    group=tc.group,
                    turns=[],
                    criteria=tc.criteria,
                    status="error",
                    error=str(e)
                )
            )
    
    return RunTestcasesResponse(results=results)


@router.post("/run-single")
@traceable(name="run_single_endpoint", run_type="chain")
async def run_single(request: RunSingleRequest):
    """
    Chạy single testcase
    
    POST /api/run-single
    Body: { code, group, turns?, question?, expected?, criteria? }
    """
    # Hỗ trợ cả format cũ và mới
    if request.turns:
        turns = [{"question": t.question, "expected": t.expected} for t in request.turns]
    elif request.question and request.expected:
        turns = [{"question": request.question, "expected": request.expected}]
    else:
        raise HTTPException(status_code=400, detail="Thiếu câu hỏi.")
    
    try:
        # Run testcase với LangGraph
        result = await run_testcase(
            code=request.code,
            name=request.code,
            group=request.group,
            turns=turns,
            criteria=request.criteria,
            bot_url=request.bot_url
        )
        
        return {
            "turns": result["turns"],
            "status": result["status"],
            "error": result.get("error")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/criteria")
async def get_criteria():
    """
    Lấy danh sách tiêu chí đánh giá
    
    GET /api/criteria
    """
    return {"criteria": CRITERIA_LIST}


@router.post("/run-testcases-stream")
@traceable(name="run_testcases_stream_endpoint", run_type="chain")
async def run_testcases_stream(request: RunTestcasesRequest):
    """
    Chạy multiple testcases với streaming results
    Mỗi testcase xong sẽ stream về client ngay
    
    POST /api/run-testcases-stream
    Body: { testcases: [...] }
    
    Response: Server-Sent Events (SSE)
    """
    if not request.testcases:
        raise HTTPException(status_code=400, detail="Không có testcase nào được gửi lên.")
    
    async def event_generator():
        """Generator để stream results"""

        async def run_one(index: int, testcase) -> dict:
            """
            Run một testcase và trả về kết quả.
            turns được tạo bên trong hàm này để tránh closure bug —
            mỗi coroutine giữ bản sao riêng của turns.
            """
            # ⚠️ QUAN TRỌNG: tạo turns ngay tại đây, không dùng biến ngoài
            tc_turns = [{"question": t.question, "expected": t.expected} for t in testcase.turns]
            try:
                # Ưu tiên bot_url của testcase, fallback về request.bot_url
                bot_url = testcase.bot_url if testcase.bot_url else request.bot_url
                result = await run_testcase(
                    code=testcase.code,
                    name=testcase.name,
                    group=testcase.group,
                    turns=tc_turns,
                    criteria=testcase.criteria,
                    bot_url=bot_url
                )
                return {
                    "index": index,
                    "code": testcase.code,
                    "name": testcase.name,
                    "group": testcase.group,
                    "turns": result["turns"],
                    "criteria": testcase.criteria,
                    "status": result["status"],
                    "error": result.get("error")
                }
            except Exception as e:
                return {
                    "index": index,
                    "code": testcase.code,
                    "name": testcase.name,
                    "group": testcase.group,
                    "turns": [],
                    "criteria": testcase.criteria,
                    "status": "error",
                    "error": str(e)
                }

        # Tạo tasks — mỗi task giữ bản sao turns riêng
        tasks = [run_one(idx, tc) for idx, tc in enumerate(request.testcases)]

        # Chạy tất cả tasks concurrently và yield khi nào xong
        for coro in asyncio.as_completed(tasks):
            result = await coro
            yield f"data: {json.dumps(result)}\n\n"

        # Signal hoàn thành
        yield "data: {\"done\": true}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
