"""
Testcase Runner Graph sử dụng LangGraph
Workflow: warmup → run turns → judge → save history
"""

import time
import uuid
from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END
from langsmith import traceable
import httpx

from graphs.judge_agent import judge_agent
from models.history import History


# Callbot API URL mặc định
DEFAULT_CALLBOT_URL = "http://160.250.216.28:11005/api/v1/call/"

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


async def call_bot_warmup(conversation_id: str, bot_url: str) -> None:
    """
    Gọi warmup — dùng CHÍNH shared client để làm nóng connection pool.
    Thời gian warmup KHÔNG được tính vào response_time_ms của actual turns.
    """
    payload = {"conversation_id": conversation_id, "message": "xin chào"}
    print(f"[warmup] → {payload}")
    
    warmup_start = time.perf_counter()
    try:
        client = await get_http_client()
        await client.post(bot_url, json=payload)
        warmup_time = int((time.perf_counter() - warmup_start) * 1000)
        print(f"[warmup] ← completed in {warmup_time}ms (connection pool warmed, time NOT counted in results)")
    except Exception as e:
        warmup_time = int((time.perf_counter() - warmup_start) * 1000)
        print(f"[warmup] ← failed after {warmup_time}ms (ignored): {e}")


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
    bot_url: str  # URL bot (default hoặc tùy chỉnh)
    executor: Optional[str]  # NEW: Người thực hiện testcase

    # Unique conversation ID cho mỗi lần chạy (tránh bot nhớ context cũ)
    conversation_id: str

    # Runtime state
    current_turn_index: int
    turn_results: List[Dict[str, Any]]
    error: str


# ============================================================================
# Helper Functions
# ============================================================================

async def call_bot(conversation_id: str, message: str, bot_url: str) -> Dict[str, Any]:
    """
    Gọi Callbot API cho actual turns.
    Chỉ tính thời gian từ khi gửi request đến khi nhận response.
    """
    payload = {"conversation_id": conversation_id, "message": message}
    print(f"[callBot] → {payload}")

    client = await get_http_client()

    # Bắt đầu đo thời gian NGAY TRƯỚC KHI GỬI REQUEST
    start_time = time.perf_counter()
    response = await client.post(bot_url, json=payload)
    # Kết thúc đo thời gian NGAY SAU KHI NHẬN RESPONSE
    end_time = time.perf_counter()
    response_time_ms = int((end_time - start_time) * 1000)

    print(f"[callBot] ⏱️  Response time: {response_time_ms}ms (start={start_time:.6f}, end={end_time:.6f})")

    if response.status_code != 200:
        raise Exception(f"Callbot returned HTTP {response.status_code}")

    raw = response.text.strip()
    try:
        data = response.json()
    except ValueError:
        data = None

    if isinstance(data, dict):
        answer = str(data.get("content") or data.get("answer") or data.get("message") or "")
        action = str(data.get("action") or "")
    else:
        parts = raw.split("|")
        action = parts[-1].strip() if len(parts) > 1 else ""
        answer = "|".join(parts[:-1]).strip() if len(parts) > 1 else raw

    print(f"[callBot] ← answer={answer[:50]}..., action={action}, time={response_time_ms}ms")

    return {
        "answer": answer,
        "action": action,
        "response_time_ms": response_time_ms
    }


async def setup_scenario(conversation_id: str, scenario: str, bot_url: str) -> None:
    """
    Setup scenario bằng cách gửi các câu hỏi của user trong lịch sử hội thoại.
    Format: [user] message\n[assistant] response\n...
    
    CHỈ GỬI CÂU HỎI CỦA USER, BỎ QUA PHẦN ASSISTANT.
    Mục đích: Tạo context/lịch sử hội thoại cho bot.
    Thời gian setup scenario KHÔNG được tính vào response_time_ms.
    """
    if not scenario or not scenario.strip():
        return
    
    print(f"[setup_scenario] Parsing scenario...")
    
    # Parse scenario - CHỈ LẤY CÂU HỎI CỦA USER
    lines = scenario.strip().split('\n')
    user_messages = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('[user]'):
            msg = line.replace('[user]', '').strip()
            if msg:
                user_messages.append(msg)
        # BỎ QUA [assistant] - không cần parse
    
    print(f"[setup_scenario] Found {len(user_messages)} user messages in scenario")
    
    # Gửi các câu hỏi user để tạo context (không quan tâm response)
    for msg in user_messages:
        print(f"[setup_scenario] Sending user message: {msg[:50]}...")
        try:
            # Gọi bot để tạo context, không lưu response
            await call_bot(conversation_id, msg, bot_url)
            print(f"[setup_scenario] ✓ Context created (response ignored)")
        except Exception as e:
            print(f"[setup_scenario] Warning: Failed to send scenario message: {e}")
    
    print(f"[setup_scenario] Scenario setup completed - {len(user_messages)} messages sent")


# ============================================================================
# Graph Nodes
# ============================================================================

@traceable(name="warmup_node", run_type="chain")
async def warmup_node(state: TestcaseState) -> TestcaseState:
    """
    Node 1: Warmup - Gửi "xin chào" để khởi động hội thoại và skip câu chào mặc định.
    Sau đó setup scenario nếu có (từ turn đầu tiên).
    Thời gian warmup KHÔNG được tính vào response_time_ms của các actual turns.
    """
    print(f"[warmup_node] {state['code']} → Starting warmup (conversation_id={state['conversation_id']})")
    await call_bot_warmup(state["conversation_id"], state["bot_url"])
    print(f"[warmup_node] {state['code']} → Warmup completed")
    
    # Setup scenario nếu có (lấy từ turn đầu tiên)
    if state["turns"] and state["turns"][0].get("scenario"):
        scenario = state["turns"][0]["scenario"]
        print(f"[warmup_node] {state['code']} → Setting up scenario...")
        await setup_scenario(state["conversation_id"], scenario, state["bot_url"])
        print(f"[warmup_node] {state['code']} → Scenario setup completed")
    
    print(f"[warmup_node] {state['code']} → Ready for actual turns")

    return {
        **state,
        "current_turn_index": 0,
        "turn_results": []
    }


@traceable(name="run_turn_node", run_type="chain")
async def run_turn_node(state: TestcaseState) -> TestcaseState:
    """
    Node 2: Run Turn - Chạy một lượt hội thoại
    Scenario đã được setup trong warmup_node, không cần setup lại ở đây
    """
    turn_index = state["current_turn_index"]
    turn = state["turns"][turn_index]
    
    print(f"[run_turn] {state['code']} turn {turn_index + 1}/{len(state['turns'])}")
    
    turn_result = {
        "scenario": turn.get("scenario"),
        "question": turn["question"],
        "expected": turn["expected"],
        "required_keywords": turn.get("required_keywords"),
        "forbidden_keywords": turn.get("forbidden_keywords"),
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
        # Call bot với câu hỏi chính (scenario đã được setup trong warmup)
        bot_response = await call_bot(state["conversation_id"], turn["question"], state["bot_url"])
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
        # Get keywords from turn (if available)
        turn_data = state["turns"][turn_index]
        required_keywords = turn_data.get("required_keywords")
        forbidden_keywords = turn_data.get("forbidden_keywords")
        
        # Judge with LLM (SIMPLIFIED - no group)
        judge_result = await judge_agent.judge_one(
            question=turn_result["question"],
            expected=turn_result["expected"],
            actual=turn_result["actual"],
            response_time_ms=turn_result["response_time_ms"],
            criteria=state["criteria"],
            required_keywords=required_keywords,
            forbidden_keywords=forbidden_keywords
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
            criteria=state["criteria"],
            executor=state.get("executor")  # NEW
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
    criteria: str = "goal_achievement",
    bot_url: Optional[str] = None,
    executor: Optional[str] = None  # NEW: Người thực hiện
) -> Dict[str, Any]:
    """
    Chạy một testcase với LangGraph
    
    CONVERSATION MODE:
    - Sử dụng `code` làm `conversation_id` để test memory của bot
    - Tất cả turns trong cùng testcase sẽ dùng chung conversation_id
    - Bot sẽ nhớ context từ các turn trước đó

    Args:
        code: Mã testcase (cũng là conversation_id)
        name: Tên testcase
        group: Nhóm (A/B/C/D)
        turns: Danh sách turns (sẽ được gửi tuần tự trong cùng conversation)
        criteria: Tiêu chí đánh giá
        bot_url: URL bot tùy chỉnh (None = dùng default)
    """
    resolved_url = bot_url.strip() if bot_url and bot_url.strip() else DEFAULT_CALLBOT_URL
    print(f"🤖 Bot URL: {resolved_url}")
    print(f"💬 Conversation ID: {code} (testing memory with {len(turns)} turn(s))")

    initial_state: TestcaseState = {
        "code": code,
        "name": name,
        "group": group,
        "turns": turns,
        "criteria": criteria,
        "bot_url": resolved_url,
        "executor": executor,  # NEW
        "conversation_id": code,  # ✅ Dùng code làm conversation_id để test memory
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
