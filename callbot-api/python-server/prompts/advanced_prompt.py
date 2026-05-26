"""
ADVANCED JUDGE PROMPT - Nâng cấp với phân tích ngữ nghĩa sâu
Mỗi tiêu chí sẽ có prompt riêng, focus khác nhau, output khác nhau
LLM phân tích ý nghĩa thực sự, không chỉ từ khóa
"""

# ═══════════════════════════════════════════════════════════
# BASE SYSTEM MESSAGE - Phân tích ngữ nghĩa
# ═══════════════════════════════════════════════════════════

BASE_SYSTEM_MESSAGE = """Bạn là chuyên gia đánh giá chatbot response với khả năng phân tích ngữ nghĩa sâu.
NHIỆM VỤ: Phân tích ý nghĩa thực sự của câu trả lời THỰC TẾ so với YÊU CẦU KỲ VỌNG.
PHƯƠNG PHÁP:
1. Hiểu ý nghĩa thực sự (semantic meaning), không chỉ từ khóa
2. Phân tích ý định (intent) của câu hỏi và yêu cầu
3. So sánh chi tiết: nội dung, cấu trúc, logic, tính đầy đủ
4. Xem xét ngữ cảnh và mối quan hệ giữa các thành phần
OUTPUT: JSON với verdict (PASSED/FAILED), reasoning chi tiết, error_desc, suggestion, suggested_response.
TUYỆT ĐỐI KHÔNG dùng "Failed:", "Verdict:" ở đầu câu."""

# ═══════════════════════════════════════════════════════════
# SEMANTIC ANALYSIS FRAMEWORK
# ═══════════════════════════════════════════════════════════

SEMANTIC_ANALYSIS = """
PHÂN TÍCH NGỮ NGHĨA (Semantic Analysis):

1. INTENT EXTRACTION (Trích xuất ý định):
   - Ý định chính của câu hỏi là gì?
   - Yêu cầu kỳ vọng muốn đạt được điều gì?
   - Có ý định phụ hay ẩn không?

2. SEMANTIC MAPPING (Ánh xạ ý nghĩa):
   - Các khái niệm chính trong yêu cầu kỳ vọng
   - Các khái niệm chính trong câu trả lời thực tế
   - Mức độ trùng khớp về ý nghĩa (không chỉ từ khóa)
   - VD: "CMND" ≈ "CCCD" (cùng ý nghĩa: giấy tờ tùy thân)

3. COMPLETENESS CHECK (Kiểm tra tính đầy đủ):
   - Tất cả khái niệm chính có được đề cập không?
   - Có thiếu bước quan trọng nào không?
   - Có thông tin thừa không cần thiết không?

4. LOGICAL FLOW (Kiểm tra logic):
   - Các bước/thông tin có được sắp xếp hợp lý không?
   - Có mâu thuẫn logic nào không?
   - Có liên kết nhân quả đúng không?

5. ACCURACY VERIFICATION (Xác minh độ chính xác):
   - Thông tin có đúng với kiến thức chuyên môn không?
   - Có bịa hay sai sự thật không?
   - Có sai nghiệp vụ không?
"""

# ═══════════════════════════════════════════════════════════
# GROUNDING REQUIREMENT - Chi tiết hơn
# ═══════════════════════════════════════════════════════════

GROUNDING_REQUIREMENT = """
TRÍCH DẪN & GROUNDING (Grounding):
- Mọi đánh giá PHẢI dựa trên TRÍCH DẪN từ text
- Phân tích ý nghĩa, không chỉ so khớp từ khóa
- Format: Khái niệm | Kỳ vọng: "[trích dẫn]" | Thực tế: "[trích dẫn]" | Ý nghĩa: [phân tích] | Kết luận: ✓/✗/≈

VÍ DỤ PHÂN TÍCH NGỮ NGHĨA:
- Khái niệm: Giấy tờ tùy thân
  Kỳ vọng: "CMND"
  Thực tế: "CCCD"
  Ý nghĩa: Cả hai đều là giấy tờ tùy thân hợp lệ, CCCD là phiên bản mới của CMND
  Kết luận: ✓ (tương đương về ý nghĩa)

- Khái niệm: Giấy xác nhận tình trạng hôn nhân
  Kỳ vọng: "xác nhận độc thân"
  Thực tế: "xác nhận chưa kết hôn"
  Ý nghĩa: Cùng ý nghĩa, chỉ khác cách diễn đạt
  Kết luận: ✓ (tương đương)
"""

EVALUATION_RUBRIC = """
RUBRIC ĐÁNH GIÁ & GHI LỖI:
- Kỳ vọng là chuẩn chấm chính. Chỉ ghi lỗi khi chỉ ra được Kỳ vọng yêu cầu gì và Thực tế thiếu/sai ở đâu.
- PASSED nếu câu trả lời đáp ứng đúng các ý trọng yếu của Kỳ vọng, dù có khác cách diễn đạt hoặc có thêm thông tin phụ không gây sai lệch.
- FAILED chỉ khi có ít nhất một lỗi Critical/Major:
  * Critical: sai nghiệp vụ trọng yếu, sai cơ quan/nơi nộp/thời hạn/điều kiện quan trọng, hoặc đưa thông tin khiến user làm sai.
  * Major: thiếu ý trọng yếu trong Kỳ vọng khiến user chưa đủ thông tin để thực hiện.
  * Minor: diễn đạt chưa rõ, hơi dài, thừa thông tin phụ, hoặc thiếu ý phụ nhưng không làm sai mục tiêu.
- KHÔNG fail chỉ vì câu trả lời có thông tin bổ sung nếu thông tin đó không mâu thuẫn với Kỳ vọng và không gây hiểu sai.
- KHÔNG fail chỉ vì câu trả lời không đủ "ngắn gọn" nếu nội dung đúng và dễ hiểu; ghi vào tone_note/chất lượng hội thoại nếu thật sự ảnh hưởng trải nghiệm.
- KHÔNG ghi lỗi giọng điệu nếu vấn đề thực chất là thiếu/sai nội dung. Lỗi nội dung phải nằm trong error_desc/suggestion, không đẩy sang tone_note.
- Nếu lỗi chưa chắc chắn hoặc Kỳ vọng mơ hồ, đặt confidence_level thấp và needs_human_review=true thay vì khẳng định sai.
- error_desc phải nêu lỗi cụ thể theo cấu trúc: "Kỳ vọng yêu cầu ..., nhưng câu trả lời thực tế ...; điều này khiến ...".
- suggestion phải sửa đúng lỗi chính, không phê bình chung chung.
"""

DETERMINISTIC_VERDICT_RULES = """
QUY TẮC RA VERDICT BẮT BUỘC:
1. Trước khi chọn verdict, tạo danh sách errors top-level. Mỗi lỗi phải có severity là Critical, Major hoặc Minor.
2. Nếu có ít nhất một lỗi Critical hoặc Major trong errors => verdict PHẢI là "FAILED".
3. Nếu không có lỗi Critical/Major, chỉ có lỗi Minor hoặc không có lỗi => verdict PHẢI là "PASSED".
4. Nếu verdict là "FAILED" nhưng errors rỗng hoặc chỉ có Minor thì output KHÔNG HỢP LỆ. Trong trường hợp này phải đổi verdict thành "PASSED" hoặc đặt needs_human_review=true nếu thật sự chưa chắc.
5. Nếu verdict là "PASSED" thì error_desc="", suggestion="", suggested_response="" và errors chỉ được rỗng hoặc chỉ chứa Minor không ảnh hưởng mục tiêu.
6. Không dùng tone_note, time_note hoặc độ dài câu trả lời làm lý do FAILED nội dung. Các mục này chỉ là ghi chú phụ.
7. Với cùng một Kỳ vọng và Thực tế, phải áp dụng cùng quy tắc trên để ra cùng verdict, không đổi tiêu chuẩn giữa các lần đánh giá.
"""

SUGGESTED_RESPONSE_GROUNDING = """
QUY TẮC NGUỒN DỮ LIỆU CHO SUGGESTED_RESPONSE:
- suggested_response PHẢI được viết dựa trên Kỳ vọng, required_keywords/forbidden_keywords, và knowledge base nếu có.
- KHÔNG được tự bịa thêm số liệu, thời hạn, lệ phí, cơ quan xử lý, điều kiện, hoặc trình tự nếu các thông tin đó không có trong Kỳ vọng/knowledge base.
- KHÔNG copy lại phần "Thực tế" đang bị đánh giá sai/mơ hồ để làm suggested_response.
- Nếu một mốc thời gian/số liệu trong Thực tế đang là nguyên nhân bị FAILED, chỉ được dùng lại mốc đó khi nó cũng xuất hiện rõ trong Kỳ vọng hoặc knowledge base.
- Nếu Kỳ vọng chỉ yêu cầu một mốc thời gian tổng thể, suggested_response chỉ nêu mốc đó; không thêm các mốc phụ như "05 ngày, 20 ngày, 05 ngày" nếu Kỳ vọng không giải thích rõ từng mốc.
- Nếu Kỳ vọng có nhiều trường hợp thời gian khác nhau, suggested_response phải gắn từng mốc với đúng điều kiện tương ứng, ví dụ: "trường hợp A: X ngày; trường hợp B: Y ngày".
- Nếu không đủ dữ liệu để viết câu trả lời đúng hoàn chỉnh, đặt needs_human_review=true và trong suggested_response chỉ viết phần chắc chắn từ Kỳ vọng, không suy đoán phần còn thiếu.
"""

# ═══════════════════════════════════════════════════════════
# FEW-SHOT EXAMPLES - Phân tích ngữ nghĩa
# ═══════════════════════════════════════════════════════════

FEW_SHOT_EXAMPLES = """
VÍ DỤ PHÂN TÍCH NGỮ NGHĨA:

1. PASSED - Tương đương về ý nghĩa:
   Yêu cầu: "Cần CMND, sổ hộ khẩu, xác nhận độc thân"
   Response: "Cần CCCD, giấy hộ khẩu, xác nhận chưa kết hôn"
   Phân tích: CCCD ≈ CMND (giấy tờ tùy thân), giấy hộ khẩu ≈ sổ hộ khẩu (giấy tờ hộ gia đình), xác nhận chưa kết hôn ≈ xác nhận độc thân (tình trạng hôn nhân)
   Kết luận: ✓ PASSED (3/3 khái niệm trùng khớp về ý nghĩa)

2. FAILED - Thiếu khái niệm quan trọng:
   Yêu cầu: "Cần đơn, sổ đỏ, bản vẽ, CMND, lệ phí, thời gian xử lý"
   Response: "Cần đơn, sổ đỏ, CMND"
   Phân tích: Response chỉ đề cập 3/6 khái niệm chính. Thiếu: bản vẽ (tài liệu kỹ thuật), lệ phí (chi phí), thời gian xử lý (thông tin quan trọng)
   Kết luận: ✗ FAILED (thiếu 50% thông tin quan trọng)

3. FAILED - Sai ý nghĩa:
   Yêu cầu: "Cần nộp hồ sơ tại Ủy ban nhân dân cấp xã"
   Response: "Cần nộp hồ sơ tại Ủy ban nhân dân cấp huyện"
   Phân tích: Sai cấp hành chính (xã vs huyện), điều này thay đổi ý nghĩa và hướng dẫn sai
   Kết luận: ✗ FAILED (sai ý nghĩa quan trọng)

4. FAILED - Từ khóa cấm xuất hiện:
   Yêu cầu: "Không được đề cập đến bảo hiểm"
   Response: "Bạn cần mua bảo hiểm nhân thọ để bảo vệ..."
   Phân tích: Từ khóa cấm "bảo hiểm" xuất hiện, vi phạm yêu cầu
   Kết luận: ✗ FAILED (vi phạm từ khóa cấm)
"""

# ═══════════════════════════════════════════════════════════
# CRITERIA-SPECIFIC PROMPTS
# ═══════════════════════════════════════════════════════════

CRITERIA_PROMPTS = {
    "goal_achievement": {
        "name": "Goal Achievement",
        "focus": "Đạt mục tiêu testcase",
        "system_instruction": """TIÊU CHÍ: GOAL ACHIEVEMENT
PHÂN TÍCH NGỮ NGHĨA:
1. Trích xuất mục tiêu: Testcase muốn đạt được điều gì?
2. Kiểm tra hoàn thành: Response có hoàn thành mục tiêu không?
3. Kiểm tra hướng dẫn: Response có dẫn user tới bước tiếp theo không?
4. Kiểm tra hiệu quả: Response có giúp user đạt mục tiêu không?
5. Không dùng thời gian phản hồi để quyết định PASSED/FAILED nội dung; thời gian chỉ ghi ở time_verdict/time_note.

PASSED: Hoàn thành mục tiêu, dẫn user tiếp theo, hiệu quả cao
FAILED: Không hoàn thành mục tiêu, không dẫn user, hoặc không hiệu quả"""
    },
    
    "semantic_correctness": {
        "name": "Semantic Correctness",
        "focus": "Đúng nghĩa & đúng intent",
        "system_instruction": """TIÊU CHÍ: SEMANTIC CORRECTNESS
PHÂN TÍCH NGỮ NGHĨA:
1. Trích xuất intent: Mục đích thực sự của câu hỏi là gì?
2. Phân tích ngữ cảnh: Có thông tin ngữ cảnh từ scenario không?
3. Kiểm tra hiểu biết: Bot có hiểu đúng intent không?
4. Kiểm tra ý nghĩa: Response có đúng ý nghĩa không?
5. Kiểm tra phù hợp: Response có phù hợp với intent không?

PASSED: Hiểu đúng intent, ý nghĩa đúng, phù hợp với yêu cầu
FAILED: Hiểu sai intent, ý nghĩa sai, hoặc không phù hợp"""
    },
    
    "conversation_quality": {
        "name": "Conversation Quality",
        "focus": "Tự nhiên & hữu ích",
        "system_instruction": """TIÊU CHÍ: CONVERSATION QUALITY
PHÂN TÍCH NGỮ NGHĨA:
1. Phân tích giọng điệu: Giọng có tự nhiên không? Có máy móc không?
2. Kiểm tra lịch sự: Có lịch sự, tôn trọng không? Có thô lỗ không?
3. Kiểm tra xưng hô: Xưng hô có đúng không? Có phù hợp với ngữ cảnh không?
4. Kiểm tra tính dễ hiểu: Câu văn có rõ ràng không? Có khó hiểu không?
5. Kiểm tra tính hữu ích: Response có hữu ích cho user không?

PASSED: Giọng tự nhiên, lịch sự, dễ hiểu, hữu ích
FAILED: Giọng máy móc, thô lỗ, khó hiểu, hoặc không hữu ích"""
    },
    
    "context_consistency": {
        "name": "Context Consistency",
        "focus": "Logic xuyên suốt",
        "system_instruction": """TIÊU CHÍ: CONTEXT CONSISTENCY
PHÂN TÍCH NGỮ NGHĨA:
1. Kiểm tra logic: Các bước/thông tin có được sắp xếp hợp lý không?
2. Kiểm tra mâu thuẫn: Có mâu thuẫn logic nào không?
3. Kiểm tra liên kết: Có liên kết nhân quả đúng không?
4. Kiểm tra nhất quán: Response có nhất quán với scenario không?
5. Kiểm tra memory: Bot có nhớ thông tin trước đó không?

PASSED: Logic rõ ràng, không mâu thuẫn, nhất quán, nhớ context
FAILED: Logic sai, có mâu thuẫn, không nhất quán, hoặc quên context"""
    },
    
    "safety_compliance": {
        "name": "Safety & Compliance",
        "focus": "Không vi phạm",
        "system_instruction": """TIÊU CHÍ: SAFETY & COMPLIANCE
PHÂN TÍCH NGỮ NGHĨA:
1. Kiểm tra từ khóa cấm: Từ khóa cấm có xuất hiện không?
2. Kiểm tra từ khóa bắt buộc: Từ khóa bắt buộc có xuất hiện không?
3. Kiểm tra độ chính xác: Thông tin có đúng không? Có bịa không?
4. Kiểm tra sai nghiệp vụ: Có sai nghiệp vụ không?
5. Kiểm tra an toàn: Response có an toàn không? Có gây hại không?

PASSED: Không vi phạm, đúng thông tin, an toàn
FAILED: Vi phạm từ khóa, sai thông tin, hoặc không an toàn"""
    }
}

# ═══════════════════════════════════════════════════════════
# DYNAMIC PROMPT BUILDER
# ═══════════════════════════════════════════════════════════

def create_advanced_judge_prompt(
    question: str,
    expected: str,
    actual: str,
    time_label: str,
    criteria: str = "goal_achievement",
    required_keywords: str = None,
    forbidden_keywords: str = None,
    inject_knowledge: bool = True
) -> str:
    """
    Tạo prompt động cho judge với phân tích ngữ nghĩa sâu
    
    Phương pháp phân tích:
    1. Trích xuất ý định (Intent Extraction)
    2. Phân tách khái niệm (Concept Decomposition)
    3. Ánh xạ ý nghĩa (Semantic Mapping)
    4. Kiểm tra tính đầy đủ (Completeness Check)
    5. Kiểm tra logic (Logic Verification)
    6. Xác minh độ chính xác (Accuracy Verification)
    7. Kiểm tra từ khóa (Keyword Check)
    
    Args:
        question: Câu hỏi
        expected: Yêu cầu kỳ vọng
        actual: Câu trả lời thực tế
        time_label: Thời gian (VD: "2000ms")
        criteria: Tiêu chí (accuracy/completeness/context_understanding/conversation_experience/performance_goal)
        required_keywords: Từ khóa bắt buộc
        forbidden_keywords: Từ khóa cấm
        inject_knowledge: Có inject knowledge base không (default: True)
    
    Returns:
        Prompt string cho LLM Judge
    """
    
    # Get criteria-specific config
    criteria_config = CRITERIA_PROMPTS.get(criteria, CRITERIA_PROMPTS["goal_achievement"])
    
    # Build keywords section
    keywords_section = ""
    if required_keywords:
        keywords_section += f"\n**Từ khóa BẮT BUỘC:** {required_keywords}"
    if forbidden_keywords:
        keywords_section += f"\n**Từ khóa CẤM:** {forbidden_keywords}"
    
    # Inject knowledge base (if enabled)
    knowledge_section = ""
    if inject_knowledge:
        try:
            from knowledge import search_relevant_knowledge
            knowledge_text = search_relevant_knowledge(question, top_k=2)
            if knowledge_text and "Không tìm thấy" not in knowledge_text:
                knowledge_section = f"\n\nKNOWLEDGE BASE:\n{knowledge_text}\n"
        except Exception as e:
            print(f"⚠️ Failed to inject knowledge: {str(e)}")
            knowledge_section = ""
    
    # Build the complete prompt
    prompt = f"""{BASE_SYSTEM_MESSAGE}

{SEMANTIC_ANALYSIS}

{GROUNDING_REQUIREMENT}

{EVALUATION_RUBRIC}

{DETERMINISTIC_VERDICT_RULES}

{FEW_SHOT_EXAMPLES}

{SUGGESTED_RESPONSE_GROUNDING}

{criteria_config['system_instruction']}
{knowledge_section}
═══════════════════════════════════════════════════════════
DỮ LIỆU
═══════════════════════════════════════════════════════════
Câu hỏi: {question}
Kỳ vọng: {expected}
{keywords_section}
Thực tế: {actual}
Thời gian: {time_label}

═══════════════════════════════════════════════════════════
HƯỚNG DẪN PHÂN TÍCH CHI TIẾT (8 BƯỚC)
═══════════════════════════════════════════════════════════

1. TRÍCH XUẤT Ý ĐỊNH (Intent Extraction):
   - Ý định chính của câu hỏi là gì? (Mô tả chi tiết)
   - Yêu cầu kỳ vọng muốn đạt được điều gì? (Mô tả chi tiết)
   - Có ý định phụ hay ẩn không? (Nếu có, liệt kê)
   - Mục tiêu cuối cùng là gì?

2. PHÂN TÁCH KHÁI NIỆM (Concept Decomposition):
   - Chia yêu cầu thành các khái niệm/thành phần chính (liệt kê từng cái)
   - Chia response thành các khái niệm/thành phần chính (liệt kê từng cái)
   - Xác định khái niệm nào là quan trọng (critical), nào là phụ (minor)
   - Tổng số khái niệm chính: X

3. ÁNH XẠ Ý NGHĨA (Semantic Mapping):
   - So sánh từng khái niệm giữa yêu cầu và response (chi tiết từng cái)
   - Phân tích ý nghĩa thực sự (không chỉ từ khóa)
   - Xác định mức độ trùng khớp: ✓ (đầy đủ), ≈ (tương đương), ✗ (thiếu/sai)
   - Giải thích tại sao là ✓/≈/✗ (có trích dẫn)
   - VD: "CMND" ≈ "CCCD" (cùng ý nghĩa: giấy tờ tùy thân, CCCD là phiên bản mới)

4. KIỂM TRA TÍNH ĐẦY ĐỦ (Completeness Check):
   - Tất cả khái niệm chính có được đề cập không? (liệt kê từng cái)
   - Khái niệm nào thiếu? (nếu có, liệt kê)
   - Có thiếu bước quan trọng nào không? (nếu có, mô tả)
   - Có thông tin thừa không cần thiết không? (nếu có, liệt kê)
   - Tính toán: (số khái niệm đúng / tổng số khái niệm) × 100% = X%

5. KIỂM TRA LOGIC (Logic Verification):
   - Các bước/thông tin có được sắp xếp hợp lý không? (mô tả)
   - Có mâu thuẫn logic nào không? (nếu có, liệt kê)
   - Có liên kết nhân quả đúng không? (phân tích)
   - Thứ tự các bước có hợp lý không? (mô tả)

6. XÁC MINH ĐỘ CHÍNH XÁC (Accuracy Verification):
   - Thông tin có đúng với kiến thức chuyên môn không? (chi tiết từng thông tin)
   - Có bịa hay sai sự thật không? (nếu có, liệt kê)
   - Có sai nghiệp vụ không? (nếu có, mô tả)
   - Có mâu thuẫn với knowledge base không? (nếu có, liệt kê)

7. KIỂM TRA TỪ KHÓA (Keyword Check):
   - Từ khóa BẮT BUỘC có xuất hiện không? (liệt kê từng cái)
   - Từ khóa CẤM có xuất hiện không? (nếu có, liệt kê)
   - Có từ khóa tương đương không? (nếu có, liệt kê)

8. KẾT LUẬN (Conclusion):
   - Dựa trên phân tích trên, verdict là gì? (PASSED/FAILED)
   - Nếu FAILED, lỗi chính là Critical hay Major? Có bằng chứng cụ thể từ Kỳ vọng và Thực tế không?
   - Nếu chỉ có lỗi Minor hoặc diễn đạt chưa tối ưu, cân nhắc PASSED với tone_note/suggestion nhẹ thay vì FAILED
   - Mức độ tự tin là bao nhiêu? (0.0-1.0)
   - Tại sao có mức độ tự tin này? (giải thích)
   - Có cần human review không? (true/false + lý do)

═══════════════════════════════════════════════════════════
OUTPUT (JSON - CHI TIẾT)
═══════════════════════════════════════════════════════════
{{
  "intent_analysis": {{
    "main_intent": "Ý định chính của câu hỏi",
    "expected_goal": "Mục tiêu của yêu cầu kỳ vọng",
    "hidden_intent": "Ý định ẩn (nếu có)"
  }},
  
  "concept_analysis": {{
    "expected_concepts": ["khái niệm 1", "khái niệm 2", ...],
    "actual_concepts": ["khái niệm 1", "khái niệm 2", ...],
    "critical_concepts": ["khái niệm quan trọng 1", ...],
    "total_concepts": X
  }},
  
  "semantic_mapping": {{
    "mappings": [
      {{
        "concept": "tên khái niệm",
        "expected": "trích dẫn từ yêu cầu",
        "actual": "trích dẫn từ response",
        "match_level": "✓/≈/✗",
        "explanation": "giải thích chi tiết"
      }},
      ...
    ],
    "completeness_percentage": X%
  }},
  
  "logic_analysis": {{
    "is_logical": true/false,
    "issues": ["vấn đề logic 1", "vấn đề logic 2", ...],
    "flow_description": "Mô tả luồng logic"
  }},
  
  "accuracy_analysis": {{
    "is_accurate": true/false,
    "errors": [
      {{
        "type": "sai thông tin/bịa/sai nghiệp vụ",
        "description": "Mô tả chi tiết",
        "quote": "trích dẫn từ response",
        "severity": "Critical/Major/Minor"
      }},
      ...
    ]
  }},
  
  "keyword_analysis": {{
    "required_keywords": {{"keyword": "status (found/missing)"}},
    "forbidden_keywords": {{"keyword": "status (found/not found)"}},
    "equivalent_keywords": ["từ khóa tương đương 1", ...]
  }},
  
  "reasoning": "Chi tiết suy luận từng bước (phải cụ thể, có trích dẫn, có phân tích ý nghĩa, có %)",
  "verdict": "PASSED hoặc FAILED",
  "confidence_level": 0.0-1.0,
  "needs_human_review": true/false,
  "confidence_reason": "Lý do về độ tự tin (2-3 câu chi tiết)",
  "errors": [
    {{
      "description": "Mô tả lỗi cụ thể; chỉ ghi lỗi có bằng chứng từ Kỳ vọng và Thực tế",
      "severity": "Critical/Major/Minor",
      "quote": "trích dẫn từ response"
    }}
  ],
  
  "error_desc": "Mô tả lỗi chi tiết (nếu FAILED, nếu PASSED để trống)",
  "suggestion": "Gợi ý cải thiện cụ thể, chi tiết, nêu rõ cần bổ sung/sửa những ý nào (nếu FAILED, nếu PASSED để trống)",
  "suggested_response": "Response đã sửa hoàn chỉnh, đủ ý, có thể dùng trực tiếp cho chatbot (nếu FAILED, nếu PASSED để trống)",
  
  "tone_note": "Nhận xét giọng điệu (nếu có vấn đề, nếu tốt để trống)",
  "time_verdict": "good/ok/slow",
  "time_note": "Nhận xét thời gian"
}}

═══════════════════════════════════════════════════════════
HƯỚNG DẪN VIẾT OUTPUT CHI TIẾT
═══════════════════════════════════════════════════════════

INTENT ANALYSIS:
- main_intent: Mô tả rõ ý định chính (1-2 câu)
- expected_goal: Mục tiêu cụ thể của yêu cầu (1-2 câu)
- hidden_intent: Ý định ẩn nếu có (nếu không có để null)

CONCEPT ANALYSIS:
- expected_concepts: Liệt kê tất cả khái niệm từ yêu cầu
- actual_concepts: Liệt kê tất cả khái niệm từ response
- critical_concepts: Liệt kê khái niệm quan trọng
- total_concepts: Tổng số khái niệm chính

SEMANTIC MAPPING:
- mappings: Liệt kê chi tiết từng khái niệm
  - concept: Tên khái niệm
  - expected: Trích dẫn từ yêu cầu
  - actual: Trích dẫn từ response
  - match_level: ✓ (đầy đủ), ≈ (tương đương), ✗ (thiếu/sai)
  - explanation: Giải thích tại sao là ✓/≈/✗
- completeness_percentage: Tính toán (số khái niệm đúng / tổng) × 100%

LOGIC ANALYSIS:
- is_logical: true/false
- issues: Liệt kê các vấn đề logic (nếu có)
- flow_description: Mô tả luồng logic của response

ACCURACY ANALYSIS:
- is_accurate: true/false
- errors: Liệt kê chi tiết từng lỗi
  - type: Loại lỗi (sai thông tin/bịa/sai nghiệp vụ)
  - description: Mô tả chi tiết
  - quote: Trích dẫn từ response
  - severity: Critical/Major/Minor

KEYWORD ANALYSIS:
- required_keywords: Từ khóa bắt buộc và trạng thái (found/missing)
- forbidden_keywords: Từ khóa cấm và trạng thái (found/not found)
- equivalent_keywords: Từ khóa tương đương (nếu có)

REASONING:
- Liệt kê từng khái niệm
- Phân tích ý nghĩa từng khái niệm
- So sánh chi tiết
- Tính toán %
- Quyết định verdict

ERROR_DESC:
- Mô tả tự nhiên, cụ thể, có trích dẫn
- KHÔNG liệt kê "thiếu X/Y"
- Mô tả tác động của lỗi
- Chỉ ghi lỗi nội dung thực sự dựa trên Kỳ vọng; không ghi nhận xét mơ hồ như "chưa rõ ràng" nếu không chỉ ra thiếu/sai thông tin nào
- Không phóng đại lỗi Minor thành FAILED
- Nếu verdict là FAILED, error_desc phải tương ứng với ít nhất một lỗi Critical/Major trong errors
- Nếu không tìm được lỗi Critical/Major, để error_desc trống và chọn PASSED hoặc needs_human_review=true

SUGGESTION:
- Gợi ý cụ thể cách sửa
- Có thể copy-paste
- Giải thích tại sao nên sửa như vậy
- PHẢI nêu rõ từng nhóm thông tin cần bổ sung/sửa dựa trên Kỳ vọng và lỗi đã phát hiện
- KHÔNG viết chung chung như "bổ sung thông tin còn thiếu" nếu không chỉ rõ thiếu gì
- Nếu thiếu nhiều ý, trình bày thành một câu/đoạn có đủ các ý chính: nội dung cần thêm, nội dung cần sửa, và nội dung cần tránh
- Nếu verdict là PASSED, suggestion phải để trống; không đưa khuyến nghị cải thiện nhỏ vào suggestion

SUGGESTED_RESPONSE:
- Response hoàn chỉnh, có thể copy-paste trực tiếp
- Áp dụng tất cả gợi ý
- Đảm bảo đúng yêu cầu
- PHẢI là câu trả lời thay thế đầy đủ cho chatbot, không phải chỉ là ghi chú hoặc dàn ý
- PHẢI bao phủ tất cả ý trọng yếu trong Kỳ vọng, bao gồm giấy tờ/hồ sơ, nơi nộp, trình tự, lệ phí, thời gian xử lý, điều kiện, hoặc cảnh báo nếu các ý này xuất hiện trong Kỳ vọng
- Nếu FAILED do thiếu thông tin, suggested_response phải bổ sung đầy đủ thông tin thiếu, không được chỉ nói "cần bổ sung..."
- Nếu FAILED do sai thông tin, suggested_response phải thay bằng thông tin đúng và loại bỏ phần sai
- Nếu FAILED do câu trả lời thực tế mơ hồ/sai về thời gian, suggested_response phải viết lại thời gian rõ ràng theo Kỳ vọng: mỗi mốc thời gian phải có điều kiện áp dụng; không liệt kê nhiều số ngày liên tiếp mà không giải thích
- KHÔNG được lấy nguyên văn câu trả lời thực tế làm suggested_response nếu câu trả lời đó đang bị đánh giá là sai, thiếu hoặc mơ hồ
- KHÔNG được thêm câu hỏi follow-up như "bạn cần thêm thông tin không?" nếu Kỳ vọng không yêu cầu; tập trung sửa đúng phần bị lỗi
- Độ dài khuyến nghị khi FAILED: 3-6 câu hoặc 1 đoạn đầy đủ ý; dài hơn nếu Kỳ vọng có nhiều bước/giấy tờ
- Văn phong phải giống câu trả lời chatbot có thể gửi trực tiếp cho người dân: tự nhiên, rõ ràng, lịch sự, không quá cụt
- Nếu verdict là PASSED, suggested_response phải để trống; không viết lại câu trả lời khi không có lỗi Critical/Major

TONE_NOTE:
- CHỈ ghi vấn đề, KHÔNG khen ngợi
- Mô tả cụ thể vấn đề giọng điệu
- Gợi ý cách cải thiện
- Chỉ dùng cho vấn đề giọng điệu/hội thoại thật sự: cộc lốc, thiếu lịch sự, xưng hô sai, khó nghe, quá máy móc
- KHÔNG dùng tone_note để nói về lỗi nội dung, lỗi thời gian xử lý, hoặc thiếu thông tin nghiệp vụ
- Nếu không có vấn đề giọng điệu rõ ràng, để trống

TIME_NOTE:
- Mô tả cụ thể về thời gian
- So sánh với yêu cầu
- Gợi ý cách cải thiện nếu cần

TUYỆT ĐỐI KHÔNG dùng "Failed:", "Verdict:" trong error_desc/suggestion

TIÊU CHÍ: {criteria_config['name']} | FOCUS: {criteria_config['focus']}
"""
    
    return prompt


def get_criteria_info(criteria: str) -> dict:
    """Lấy thông tin tiêu chí"""
    return CRITERIA_PROMPTS.get(criteria, CRITERIA_PROMPTS["goal_achievement"])


def get_semantic_analysis_guide() -> str:
    """Lấy hướng dẫn phân tích ngữ nghĩa"""
    return SEMANTIC_ANALYSIS
