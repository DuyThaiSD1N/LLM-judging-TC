"""
Testcase Runner Graph sử dụng LangGraph
Workflow: warmup → run turns → judge → save history
"""

import time
import uuid
from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END
from langsmith import traceable
import httpx

from graphs.judge_agent import judge_agent
from models.history import History


# Callbot API URL
CALLBOT_URL = "http://160.250.216.28:11005/api/v1/call/"

# Shared HTTP client cho actual calls — tái sử dụng connection pool
_http_client: httpx.AsyncClient | None = None


async def get_http_client() -> httpx.AsyncClient:
    """Trả về shared HTTP client cho actual calls"""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "accept": "application/json",
                "Content-Type": "application/json"
            }
        )
    return _http_client


async def call_bot_warmup(conversation_id: str) -> None:
    """
    Gọi warmup — dùng CHÍNH shared client để làm nóng connection pool.
    Sau warmup, actual calls tái sử dụng connection đã có → không bị TCP handshake.
    Thời gian warmup KHÔNG được đo và KHÔNG tính vào response_time_ms.
    """
    payload = {"conversation_id": conversation_id, "message": "xin chào"}
    print(f"[warmup] → {payload}")
    try:
        client = await get_http_client()
        await client.post(CALLBOT_URL, json=payload)
        print(f"[warmup] ← completed (connection pool warmed up, time not counted)")
    except Exception as e:
        print(f"[warmup] ← failed (ignored): {e}")


# ============================================================================
# State Definition
# ============================================================================

class TestcaseState(TypedDict):
    """State cho testcase runner graph"""
    # Input
    code: str
    name: str
    group: str
    turns: List[Dict[str, str]]
    criteria: str
    
    # Unique conversation ID cho mỗi lần chạy (tránh bot nhớ context cũ)
    conversation_id: str
    
    # Runtime state
    current_turn_index: int
    turn_results: List[Dict[str, Any]]
    error: str


# ============================================================================
# Helper Functions
# ============================================================================

async def call_bot(conversation_id: str, message: str) -> Dict[str, Any]:
    """
    Gọi Callbot API cho actual turns.
    Dùng shared client để tái sử dụng connection — thời gian đo
    chỉ bao gồm thời gian bot xử lý câu hỏi thực tế.
    """
    payload = {"conversation_id": conversation_id, "message": message}
    print(f"[callBot] → {payload}")

    client = await get_http_client()

    # Đo thời gian chỉ bao gồm thời gian bot xử lý câu hỏi thực tế
    start_time = time.perf_counter()
    response = await client.post(CALLBOT_URL, json=payload)
    response_time_ms = int((time.perf_counter() - start_time) * 1000)

    if response.status_code != 200:
        raise Exception(f"Callbot returned HTTP {response.status_code}")

    # Parse response: format "answer|action"
    raw = response.text.strip()
    parts = raw.split("|")
    action = parts[-1].strip()
    answer = "|".join(parts[:-1]).strip()

    print(f"[callBot] ← answer={answer[:50]}..., action={action}, time={response_time_ms}ms")

    return {
        "answer": answer,
        "action": action,
        "response_time_ms": response_time_ms
    }


# ============================================================================
# Graph Nodes
# ============================================================================

@traceable(name="warmup_node", run_type="chain")
async def warmup_node(state: TestcaseState) -> TestcaseState:
    """
    Node 1: Warmup - Gửi "xin chào" để khởi động hội thoại.
    Dùng client riêng biệt để thời gian warmup KHÔNG ảnh hưởng
    đến response_time_ms của các actual turns.
    """
    print(f"[warmup] {state['code']} → conversation_id={state['conversation_id']}")
    await call_bot_warmup(state["conversation_id"])
    print(f"[warmup] {state['code']} → done")

    return {
        **state,
        "current_turn_index": 0,
        "turn_results": []
    }


@traceable(name="run_turn_node", run_type="chain")
async def run_turn_node(state: TestcaseState) -> TestcaseState:
    """
    Node 2: Run Turn - Chạy một lượt hội thoại
    """
    turn_index = state["current_turn_index"]
    turn = state["turns"][turn_index]
    
    print(f"[run_turn] {state['code']} turn {turn_index + 1}/{len(state['turns'])}")
    
    turn_result = {
        "question": turn["question"],
        "expected": turn["expected"],
        "actual": "",
        "action": "",
        "response_time_ms": None,
        "verdict": None,
        "error_desc": "",
        "suggestion": "",
        "suggested_response": "",
        "tone_note": "",
        "time_verdict": None,
        "time_note": "",
        "error": "",
    }
    
    try:
        # Call bot dùng conversation_id ngẫu nhiên (không phải mã testcase)
        bot_response = await call_bot(state["conversation_id"], turn["question"])
        turn_result["actual"] = bot_response["answer"]
        turn_result["action"] = bot_response["action"]
        turn_result["response_time_ms"] = bot_response["response_time_ms"]
        
    except Exception as e:
        turn_result["error"] = str(e)
        print(f"[run_turn] {state['code']} turn {turn_index + 1} → Error: {e}")
    
    # Add to results
    turn_results = state["turn_results"] + [turn_result]
    
    return {
        **state,
        "turn_results": turn_results
    }


@traceable(name="judge_turn_node", run_type="chain")
async def judge_turn_node(state: TestcaseState) -> TestcaseState:
    """
    Node 3: Judge Turn - Đánh giá lượt vừa chạy
    """
    turn_index = state["current_turn_index"]
    turn_result = state["turn_results"][-1]
    
    print(f"[judge_turn] {state['code']} turn {turn_index + 1} → Judging...")
    
    # Skip judge if there was an error calling bot
    if turn_result["error"]:
        print(f"[judge_turn] {state['code']} turn {turn_index + 1} → Skipped (bot error)")
        return {
            **state,
            "current_turn_index": turn_index + 1
        }
    
    try:
        # Judge with LLM
        judge_result = await judge_agent.judge_one(
            question=turn_result["question"],
            expected=turn_result["expected"],
            actual=turn_result["actual"],
            group=state["group"],
            response_time_ms=turn_result["response_time_ms"],
            criteria=state["criteria"]
        )
        
        # Update turn result with judge result
        turn_result.update(judge_result)
        
        print(
            f"[judge_turn] {state['code']} turn {turn_index + 1} → "
            f"{judge_result['verdict']}"
        )
        
    except Exception as e:
        turn_result["error"] = str(e)
        print(f"[judge_turn] {state['code']} turn {turn_index + 1} → Judge error: {e}")
    
    return {
        **state,
        "current_turn_index": turn_index + 1
    }


@traceable(name="save_history_node", run_type="chain")
async def save_history_node(state: TestcaseState) -> TestcaseState:
    """
    Node 4: Save History - Lưu kết quả vào database
    """
    print(f"[save_history] {state['code']} → Saving to database...")
    
    try:
        History.save(
            testcase_code=state["code"],
            testcase_name=state.get("name", state["code"]),
            testcase_group=state["group"],
            turn_results=state["turn_results"],
            criteria=state["criteria"]
        )
        print(f"[save_history] {state['code']} → Saved successfully")
    except Exception as e:
        print(f"[save_history] {state['code']} → Save failed: {e}")
    
    return state


# ============================================================================
# Conditional Edges
# ============================================================================

def should_continue(state: TestcaseState) -> str:
    """
    Quyết định có tiếp tục chạy turn tiếp theo không
    
    Returns:
        "run_turn" nếu còn turn, "save_history" nếu hết
    """
    if state["current_turn_index"] < len(state["turns"]):
        return "run_turn"
    return "save_history"


# ============================================================================
# Build Graph
# ============================================================================

def create_testcase_runner_graph() -> StateGraph:
    """
    Tạo LangGraph workflow cho testcase runner
    
    Workflow:
        START → warmup → run_turn → judge_turn → (loop or save_history) → END
    """
    workflow = StateGraph(TestcaseState)
    
    # Add nodes
    workflow.add_node("warmup", warmup_node)
    workflow.add_node("run_turn", run_turn_node)
    workflow.add_node("judge_turn", judge_turn_node)
    workflow.add_node("save_history", save_history_node)
    
    # Add edges
    workflow.set_entry_point("warmup")
    workflow.add_edge("warmup", "run_turn")
    workflow.add_edge("run_turn", "judge_turn")
    
    # Conditional edge: loop or finish
    workflow.add_conditional_edges(
        "judge_turn",
        should_continue,
        {
            "run_turn": "run_turn",
            "save_history": "save_history"
        }
    )
    
    workflow.add_edge("save_history", END)
    
    return workflow.compile()


# Global graph instance
testcase_runner_graph = create_testcase_runner_graph()


# ============================================================================
# Public API
# ============================================================================

@traceable(name="run_testcase", run_type="chain")
async def run_testcase(
    code: str,
    name: str,
    group: str,
    turns: List[Dict[str, str]],
    criteria: str = "standard"
) -> Dict[str, Any]:
    """
    Chạy một testcase với LangGraph
    
    Args:
        code: Mã testcase
        name: Tên testcase
        group: Nhóm (A/B/C/D)
        turns: Danh sách turns
        criteria: Tiêu chí đánh giá
        
    Returns:
        Dict với turn_results và status
    """
    initial_state: TestcaseState = {
        "code": code,
        "name": name,
        "group": group,
        "turns": turns,
        "criteria": criteria,
        # Tạo conversation_id ngẫu nhiên mỗi lần chạy
        # Đảm bảo bot không nhớ context từ lần chạy trước
        "conversation_id": f"{code}-{uuid.uuid4().hex[:8]}",
        "current_turn_index": 0,
        "turn_results": [],
        "error": ""
    }
    
    try:
        # Run graph
        final_state = await testcase_runner_graph.ainvoke(initial_state)
        
        return {
            "turns": final_state["turn_results"],
            "status": "done"
        }
    except Exception as e:
        print(f"❌ Testcase {code} failed: {e}")
        return {
            "turns": [],
            "status": "error",
            "error": str(e)
        }
