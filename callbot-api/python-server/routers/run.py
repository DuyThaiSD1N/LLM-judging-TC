# routers/run.py — chạy multi-turn testcase + LLM judge

import time
import httpx
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from .judge import judge_one

router = APIRouter()

CALLBOT_URL = "http://160.250.216.28:11005/api/v1/call/"


class Turn(BaseModel):
    question: str
    expected: str = ""


class Testcase(BaseModel):
    code:  str
    name:  str = ""
    group: str = "A"
    turns: list[Turn]


class RunRequest(BaseModel):
    testcases: list[Testcase]


class SingleRequest(BaseModel):
    code:  str
    group: str = "A"
    turns: list[Turn]


# ── Gọi Callbot 1 lượt ───────────────────────────────────────────────────
async def call_bot(conversation_id: str, message: str) -> dict:
    payload = {"conversation_id": conversation_id, "message": message}
    print(f"[callBot] → {payload}")

    t0 = time.time()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            CALLBOT_URL,
            json=payload,
            headers={"accept": "application/json", "Content-Type": "application/json"},
        )
    response_time_ms = int((time.time() - t0) * 1000)

    resp.raise_for_status()
    raw    = resp.text.strip()
    parts  = raw.split("|")
    action = parts[-1].strip()
    answer = "|".join(parts[:-1]).strip()

    print(f"[callBot] ← answer={answer[:60]} action={action} time={response_time_ms}ms")
    return {"answer": answer, "action": action, "response_time_ms": response_time_ms}


# ── Chạy toàn bộ turns của 1 testcase ────────────────────────────────────
async def run_turns(tc: Testcase) -> list[dict]:
    # Warmup: gửi "xin chào" để khởi động hội thoại
    try:
        await call_bot(tc.code, "xin chào")
        print(f"[warmup] {tc.code} → đã chào")
    except Exception as e:
        print(f"[warmup] {tc.code} → lỗi: {e}")

    results = []
    for j, turn in enumerate(tc.turns):
        turn_result = {
            "question":        turn.question,
            "expected":        turn.expected,
            "actual":          "",
            "action":          "",
            "response_time_ms": None,
            "verdict":         None,
            "error_desc":      "",
            "suggestion":      "",
            "tone_note":       "",
            "brevity_note":    "",
            "time_verdict":    None,
            "time_note":       "",
            "error":           "",
        }
        try:
            bot = await call_bot(tc.code, turn.question)
            turn_result["actual"]           = bot["answer"]
            turn_result["action"]           = bot["action"]
            turn_result["response_time_ms"] = bot["response_time_ms"]

            judge = await judge_one(
                question=turn.question,
                expected=turn.expected,
                actual=bot["answer"],
                group=tc.group,
                response_time_ms=bot["response_time_ms"],
            )
            if judge:
                turn_result.update(judge)
                print(f"[judge] {tc.code} lượt {j+1} → {judge['verdict']} ({bot['response_time_ms']}ms)")
            else:
                print(f"[judge] {tc.code} lượt {j+1} → skipped (câu chào)")
        except Exception as e:
            turn_result["error"] = str(e)
            print(f"[error] {tc.code} lượt {j+1}: {e}")

        results.append(turn_result)
    return results


# ── POST /api/run-testcases ───────────────────────────────────────────────
@router.post("/run-testcases")
async def run_testcases(body: RunRequest):
    results = []
    for tc in body.testcases:
        try:
            turn_results = await run_turns(tc)
            results.append({**tc.model_dump(), "turns": turn_results, "status": "done"})
        except Exception as e:
            results.append({**tc.model_dump(), "status": "error", "error": str(e)})
    return {"results": results}


# ── POST /api/run-single ──────────────────────────────────────────────────
@router.post("/run-single")
async def run_single(body: SingleRequest):
    if not body.turns or not body.turns[0].question:
        return {"error": "Thiếu câu hỏi."}, 400
    tc = Testcase(code=body.code, group=body.group, turns=body.turns)
    turn_results = await run_turns(tc)
    return {"turns": turn_results, "status": "done"}
