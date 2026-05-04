# Requirements Document: LLM Judge Enhancement

## Introduction

Hệ thống LLM Judge hiện tại đánh giá chatbot hành chính công với verdict nhị phân PASSED/FAILED dựa trên 5 tiêu chí (standard, strict, flexible, content-only, ux-focused). Feature này nâng cấp toàn diện hệ thống đánh giá để tăng độ tin cậy, giảm false positive/negative, và cung cấp feedback chi tiết hơn thông qua scoring system, confidence level, error severity classification, domain glossary, và rubric đánh giá.

## Glossary

- **LLM_Judge**: Hệ thống sử dụng GPT-4o-mini để đánh giá chất lượng phản hồi của chatbot
- **Verdict**: Kết quả đánh giá cuối cùng (PASSED hoặc FAILED)
- **Scoring_System**: Hệ thống chấm điểm 0-100 với trọng số: Nội dung 50% + Giọng điệu 30% + Thời gian 20%
- **Confidence_Level**: Mức độ tự tin của LLM về đánh giá (0.0-1.0)
- **Error_Severity**: Mức độ nghiêm trọng của lỗi (Critical, Major, Minor)
- **Domain_Glossary**: Từ điển thuật ngữ hành chính công và các biến thể tương đương
- **Rubric**: Bảng tiêu chí chấm điểm chi tiết cho từng thành phần
- **Self_Consistency_Check**: Cơ chế kiểm tra tính nhất quán logic của kết quả đánh giá
- **Prompt_Template**: Template prompt cho mỗi tiêu chí đánh giá
- **Edge_Case**: Trường hợp biên khó đánh giá (giọng điệu tốt nhưng thiếu info, thông tin gần đúng, v.v.)
- **False_Positive**: Đánh giá PASSED nhưng thực tế nên FAILED
- **False_Negative**: Đánh giá FAILED nhưng thực tế nên PASSED

## Requirements

### Requirement 1: Scoring System với Trọng Số

**User Story:** Là một QA engineer, tôi muốn có điểm số chi tiết 0-100 thay vì chỉ PASSED/FAILED, để tôi có thể phân tích xu hướng chất lượng và xác định vùng cần cải thiện.

#### Acceptance Criteria

1. WHEN LLM_Judge đánh giá một phản hồi, THE Scoring_System SHALL tính toán điểm tổng từ 0-100 với công thức: `total_score = content_score * 0.5 + tone_score * 0.3 + time_score * 0.2`
2. THE Scoring_System SHALL tính content_score từ 0-100 dựa trên tỷ lệ thông tin đúng và đầy đủ so với kỳ vọng
3. THE Scoring_System SHALL tính tone_score từ 0-100 dựa trên chất lượng xưng hô, lịch sự, và tự nhiên
4. THE Scoring_System SHALL tính time_score từ 0-100 dựa trên thời gian phản hồi (100 điểm nếu ≤2s, 70 điểm nếu ≤3s, 0 điểm nếu >5s)
5. WHEN total_score ≥ 70, THE Scoring_System SHALL gán verdict = "PASSED"
6. WHEN total_score < 70, THE Scoring_System SHALL gán verdict = "FAILED"
7. THE Scoring_System SHALL trả về JSON với các trường: `total_score`, `content_score`, `tone_score`, `time_score`, `verdict`

### Requirement 2: Confidence Level và Human Review Threshold

**User Story:** Là một QA manager, tôi muốn biết LLM có chắc chắn về đánh giá không, để tôi có thể ưu tiên review các trường hợp không chắc chắn.

#### Acceptance Criteria

1. WHEN LLM_Judge đánh giá một phản hồi, THE LLM_Judge SHALL tính toán confidence_level từ 0.0 đến 1.0
2. THE LLM_Judge SHALL gán confidence_level cao (≥0.9) khi thông tin rõ ràng thiếu/sai hoặc hoàn toàn đúng
3. THE LLM_Judge SHALL gán confidence_level trung bình (0.7-0.9) khi có thông tin gần đúng hoặc giọng điệu không rõ ràng
4. THE LLM_Judge SHALL gán confidence_level thấp (<0.7) khi gặp edge case hoặc không chắc chắn
5. WHEN confidence_level < 0.7, THE LLM_Judge SHALL gán trường `needs_human_review = true`
6. THE LLM_Judge SHALL trả về JSON với các trường: `confidence_level`, `needs_human_review`, `confidence_reason`

### Requirement 3: Error Severity Classification

**User Story:** Là một developer, tôi muốn biết lỗi nào nghiêm trọng nhất, để tôi có thể ưu tiên sửa các lỗi quan trọng trước.

#### Acceptance Criteria

1. WHEN verdict = "FAILED", THE LLM_Judge SHALL phân loại từng lỗi thành một trong ba mức: Critical, Major, Minor
2. THE LLM_Judge SHALL gán severity = "Critical" khi thông tin sai hoặc thiếu thông tin quan trọng ảnh hưởng đến quyết định của người dùng
3. THE LLM_Judge SHALL gán severity = "Major" khi giọng điệu tệ (thô lỗ, không xưng hô) hoặc thời gian quá chậm (>5s)
4. THE LLM_Judge SHALL gán severity = "Minor" khi thiếu chi tiết phụ hoặc thiếu dạ/ạ
5. THE LLM_Judge SHALL trả về JSON với trường `errors` là mảng các object chứa: `description`, `severity`, `quote`
6. THE LLM_Judge SHALL sắp xếp mảng `errors` theo thứ tự: Critical → Major → Minor

### Requirement 4: Domain Glossary cho Thuật Ngữ Hành Chính Công

**User Story:** Là một QA engineer, tôi muốn LLM hiểu các thuật ngữ tương đương trong hành chính công, để tránh đánh giá FAILED khi bot dùng từ đồng nghĩa hợp lệ.

#### Acceptance Criteria

1. THE Domain_Glossary SHALL chứa danh sách các nhóm thuật ngữ tương đương trong hành chính công
2. THE Domain_Glossary SHALL bao gồm nhóm: ["CMND", "CCCD", "Căn cước công dân", "Chứng minh nhân dân", "Thẻ căn cước"]
3. THE Domain_Glossary SHALL bao gồm nhóm: ["Giấy xác nhận độc thân", "Giấy xác nhận tình trạng hôn nhân", "Xác nhận hôn nhân"]
4. THE Domain_Glossary SHALL bao gồm nhóm: ["Sổ hộ khẩu", "Sổ đăng ký hộ khẩu", "Giấy đăng ký thường trú"]
5. THE Domain_Glossary SHALL bao gồm nhóm: ["Giấy khai sinh", "Bản sao giấy khai sinh", "Trích lục khai sinh"]
6. WHEN so sánh nội dung, THE LLM_Judge SHALL coi các thuật ngữ trong cùng nhóm là tương đương
7. THE Domain_Glossary SHALL được nhúng vào Prompt_Template của tất cả các tiêu chí

### Requirement 5: Rubric Chi Tiết cho Content Score

**User Story:** Là một QA engineer, tôi muốn có rubric rõ ràng để hiểu cách LLM chấm điểm nội dung, để đảm bảo tính nhất quán.

#### Acceptance Criteria

1. THE Rubric SHALL định nghĩa content_score = 100 khi có 100% thông tin kỳ vọng và 100% chính xác
2. THE Rubric SHALL định nghĩa content_score = 80-99 khi có 100% thông tin nhưng có chi tiết nhỏ không chính xác
3. THE Rubric SHALL định nghĩa content_score = 60-79 khi có 80-99% thông tin quan trọng
4. THE Rubric SHALL định nghĩa content_score = 40-59 khi có 60-79% thông tin quan trọng
5. THE Rubric SHALL định nghĩa content_score = 20-39 khi có 40-59% thông tin quan trọng
6. THE Rubric SHALL định nghĩa content_score = 0-19 khi có <40% thông tin hoặc thông tin sai nghiêm trọng
7. THE Rubric SHALL được nhúng vào Prompt_Template của tất cả các tiêu chí

### Requirement 6: Rubric Chi Tiết cho Tone Score

**User Story:** Là một QA engineer, tôi muốn có rubric rõ ràng để hiểu cách LLM chấm điểm giọng điệu, để đảm bảo tính nhất quán.

#### Acceptance Criteria

1. THE Rubric SHALL định nghĩa tone_score = 100 khi có xưng hô + dạ/ạ + tự nhiên + thân thiện
2. THE Rubric SHALL định nghĩa tone_score = 80-99 khi có xưng hô + dạ/ạ nhưng hơi máy móc
3. THE Rubric SHALL định nghĩa tone_score = 60-79 khi có xưng hô nhưng thiếu dạ/ạ
4. THE Rubric SHALL định nghĩa tone_score = 40-59 khi thiếu xưng hô nhưng có dạ/ạ
5. THE Rubric SHALL định nghĩa tone_score = 20-39 khi không có xưng hô và không có dạ/ạ
6. THE Rubric SHALL định nghĩa tone_score = 0-19 khi giọng điệu thô lỗ hoặc không phù hợp
7. THE Rubric SHALL được nhúng vào Prompt_Template của tất cả các tiêu chí

### Requirement 7: Edge Case Examples trong Prompt

**User Story:** Là một QA engineer, tôi muốn LLM xử lý đúng các edge cases, để giảm false positive và false negative.

#### Acceptance Criteria

1. THE Prompt_Template SHALL bao gồm ít nhất 6 ví dụ edge cases
2. THE Prompt_Template SHALL bao gồm ví dụ: "Giọng điệu xuất sắc nhưng thiếu 50% thông tin quan trọng" → FAILED (content_score thấp)
3. THE Prompt_Template SHALL bao gồm ví dụ: "Đầy đủ thông tin nhưng không có xưng hô" → Tùy tiêu chí (standard: FAILED, content-only: PASSED)
4. THE Prompt_Template SHALL bao gồm ví dụ: "Nhóm B - Từ chối đúng nhưng không chuyển hướng" → FAILED (thiếu chuyển hướng)
5. THE Prompt_Template SHALL bao gồm ví dụ: "Nhóm B - Trả lời nội dung ngoài phạm vi" → FAILED (không từ chối)
6. THE Prompt_Template SHALL bao gồm ví dụ: "Thông tin gần đúng (95% chính xác)" → confidence_level = 0.75, needs_human_review = true
7. THE Prompt_Template SHALL bao gồm ví dụ: "Thông tin thừa nhưng đầy đủ" → PASSED (thông tin thừa không phạt)
8. THE Prompt_Template SHALL bao gồm ví dụ: "Dùng thuật ngữ tương đương từ Domain_Glossary" → PASSED (coi như đúng)

### Requirement 8: Self-Consistency Check

**User Story:** Là một QA engineer, tôi muốn LLM tự kiểm tra tính nhất quán của kết quả, để tránh output mâu thuẫn.

#### Acceptance Criteria

1. WHEN verdict = "PASSED", THE Self_Consistency_Check SHALL xác minh `error_desc` là chuỗi rỗng
2. WHEN verdict = "PASSED", THE Self_Consistency_Check SHALL xác minh `suggestion` là chuỗi rỗng
3. WHEN verdict = "PASSED", THE Self_Consistency_Check SHALL xác minh `suggested_response` là chuỗi rỗng
4. WHEN verdict = "FAILED", THE Self_Consistency_Check SHALL xác minh `errors` array có ít nhất 1 phần tử
5. WHEN total_score ≥ 70, THE Self_Consistency_Check SHALL xác minh verdict = "PASSED"
6. WHEN total_score < 70, THE Self_Consistency_Check SHALL xác minh verdict = "FAILED"
7. IF Self_Consistency_Check phát hiện mâu thuẫn, THE LLM_Judge SHALL ghi log warning và điều chỉnh verdict theo total_score

### Requirement 9: Prompt Template Cấu Trúc Mới

**User Story:** Là một developer, tôi muốn prompt template có cấu trúc rõ ràng với tất cả các thành phần mới, để dễ maintain và mở rộng.

#### Acceptance Criteria

1. THE Prompt_Template SHALL bao gồm section "Domain Glossary" với danh sách thuật ngữ tương đương
2. THE Prompt_Template SHALL bao gồm section "Scoring Rubric" với bảng điểm chi tiết cho content, tone, time
3. THE Prompt_Template SHALL bao gồm section "Edge Case Examples" với ít nhất 6 ví dụ
4. THE Prompt_Template SHALL bao gồm section "Self-Consistency Rules" với các quy tắc kiểm tra
5. THE Prompt_Template SHALL bao gồm section "Output JSON Schema" với tất cả các trường mới
6. THE Prompt_Template SHALL yêu cầu LLM giải thích từng bước tính điểm trước khi output JSON
7. THE Prompt_Template SHALL được áp dụng cho tất cả 5 tiêu chí: standard, strict, flexible, content-only, ux-focused

### Requirement 10: JSON Output Schema Mở Rộng

**User Story:** Là một developer, tôi muốn JSON output chứa tất cả thông tin mới, để frontend có thể hiển thị chi tiết.

#### Acceptance Criteria

1. THE LLM_Judge SHALL trả về JSON với trường `total_score` (number, 0-100)
2. THE LLM_Judge SHALL trả về JSON với trường `content_score` (number, 0-100)
3. THE LLM_Judge SHALL trả về JSON với trường `tone_score` (number, 0-100)
4. THE LLM_Judge SHALL trả về JSON với trường `time_score` (number, 0-100)
5. THE LLM_Judge SHALL trả về JSON với trường `confidence_level` (number, 0.0-1.0)
6. THE LLM_Judge SHALL trả về JSON với trường `needs_human_review` (boolean)
7. THE LLM_Judge SHALL trả về JSON với trường `confidence_reason` (string)
8. THE LLM_Judge SHALL trả về JSON với trường `errors` (array of objects với `description`, `severity`, `quote`)
9. THE LLM_Judge SHALL trả về JSON với trường `verdict` (string: "PASSED" hoặc "FAILED")
10. THE LLM_Judge SHALL giữ nguyên các trường cũ: `error_desc`, `suggestion`, `suggested_response`, `tone_note`, `time_verdict`, `time_note` để backward compatibility

### Requirement 11: Tiêu Chí Standard Điều Chỉnh Trọng Số

**User Story:** Là một QA engineer, tôi muốn tiêu chí standard sử dụng trọng số mặc định, để cân bằng giữa nội dung và trải nghiệm.

#### Acceptance Criteria

1. WHERE tiêu chí = "standard", THE Scoring_System SHALL sử dụng trọng số: content 50%, tone 30%, time 20%
2. WHERE tiêu chí = "standard", THE Scoring_System SHALL yêu cầu total_score ≥ 70 để PASSED
3. WHERE tiêu chí = "standard", THE Prompt_Template SHALL nhấn mạnh cân bằng giữa nội dung và giọng điệu

### Requirement 12: Tiêu Chí Strict Điều Chỉnh Trọng Số

**User Story:** Là một QA engineer, tôi muốn tiêu chí strict yêu cầu cao hơn về tất cả các khía cạnh, để đảm bảo chất lượng tối đa.

#### Acceptance Criteria

1. WHERE tiêu chí = "strict", THE Scoring_System SHALL sử dụng trọng số: content 40%, tone 40%, time 20%
2. WHERE tiêu chí = "strict", THE Scoring_System SHALL yêu cầu total_score ≥ 85 để PASSED
3. WHERE tiêu chí = "strict", THE Rubric SHALL yêu cầu content_score ≥ 90 và tone_score ≥ 90 để đạt điểm cao

### Requirement 13: Tiêu Chí Flexible Điều Chỉnh Trọng Số

**User Story:** Là một QA engineer, tôi muốn tiêu chí flexible khoan dung hơn, để chấp nhận các phản hồi đủ tốt.

#### Acceptance Criteria

1. WHERE tiêu chí = "flexible", THE Scoring_System SHALL sử dụng trọng số: content 60%, tone 20%, time 20%
2. WHERE tiêu chí = "flexible", THE Scoring_System SHALL yêu cầu total_score ≥ 60 để PASSED
3. WHERE tiêu chí = "flexible", THE Rubric SHALL chấp nhận content_score ≥ 70 là đủ tốt

### Requirement 14: Tiêu Chí Content-Only Điều Chỉnh Trọng Số

**User Story:** Là một QA engineer, tôi muốn tiêu chí content-only chỉ tập trung vào nội dung, để đánh giá độ chính xác thông tin.

#### Acceptance Criteria

1. WHERE tiêu chí = "content-only", THE Scoring_System SHALL sử dụng trọng số: content 80%, tone 0%, time 20%
2. WHERE tiêu chí = "content-only", THE Scoring_System SHALL yêu cầu total_score ≥ 70 để PASSED
3. WHERE tiêu chí = "content-only", THE Prompt_Template SHALL bỏ qua đánh giá giọng điệu (tone_score = 0)

### Requirement 15: Tiêu Chí UX-Focused Điều Chỉnh Trọng Số

**User Story:** Là một QA engineer, tôi muốn tiêu chí ux-focused ưu tiên trải nghiệm người dùng, để đảm bảo chatbot thân thiện.

#### Acceptance Criteria

1. WHERE tiêu chí = "ux-focused", THE Scoring_System SHALL sử dụng trọng số: content 30%, tone 50%, time 20%
2. WHERE tiêu chí = "ux-focused", THE Scoring_System SHALL yêu cầu total_score ≥ 70 để PASSED
3. WHERE tiêu chí = "ux-focused", THE Rubric SHALL yêu cầu tone_score ≥ 80 để đạt điểm cao

### Requirement 16: Backward Compatibility với API Hiện Tại

**User Story:** Là một developer, tôi muốn API mới tương thích ngược với code hiện tại, để không phá vỡ hệ thống đang chạy.

#### Acceptance Criteria

1. THE LLM_Judge SHALL giữ nguyên endpoint `/judge` với input parameters: `question`, `expected`, `actual`, `group`, `responseTimeMs`, `criteria`
2. THE LLM_Judge SHALL giữ nguyên các trường output cũ: `verdict`, `error_desc`, `suggestion`, `suggested_response`, `tone_note`, `time_verdict`, `time_note`
3. THE LLM_Judge SHALL thêm các trường mới vào JSON output mà không xóa trường cũ
4. THE LLM_Judge SHALL đảm bảo logic verdict (PASSED/FAILED) tương thích với hệ thống cũ khi không có trường mới

### Requirement 17: Parser và Pretty Printer cho JSON Output

**User Story:** Là một developer, tôi muốn có parser và pretty printer cho JSON output, để đảm bảo format đúng và dễ debug.

#### Acceptance Criteria

1. WHEN LLM_Judge nhận được response từ GPT-4o-mini, THE JSON_Parser SHALL parse JSON string thành object
2. WHEN JSON_Parser gặp lỗi parse, THE JSON_Parser SHALL trả về error với message mô tả vị trí lỗi
3. THE Pretty_Printer SHALL format JSON output với indentation 2 spaces
4. FOR ALL valid JSON objects, THE system SHALL thực hiện round-trip: parse → pretty print → parse và kết quả phải tương đương với object ban đầu
5. THE JSON_Parser SHALL validate schema với tất cả các trường bắt buộc trước khi trả về

### Requirement 18: Logging và Monitoring cho Confidence Level

**User Story:** Là một QA manager, tôi muốn theo dõi phân bố confidence level, để biết tỷ lệ cases cần human review.

#### Acceptance Criteria

1. WHEN LLM_Judge hoàn thành đánh giá, THE Logging_System SHALL ghi log với các trường: `testcase_id`, `criteria`, `verdict`, `total_score`, `confidence_level`, `needs_human_review`
2. THE Logging_System SHALL tính toán và ghi log tỷ lệ `needs_human_review = true` theo từng tiêu chí
3. THE Logging_System SHALL ghi log các edge cases với confidence_level < 0.7 vào file riêng để review
4. THE Logging_System SHALL ghi log thời gian xử lý của LLM_Judge để monitor performance

### Requirement 19: Error Handling cho OpenAI API

**User Story:** Là một developer, tôi muốn hệ thống xử lý lỗi từ OpenAI API một cách graceful, để tránh crash khi API lỗi.

#### Acceptance Criteria

1. WHEN OpenAI API trả về lỗi rate limit, THE LLM_Judge SHALL retry sau 5 giây với tối đa 3 lần
2. WHEN OpenAI API trả về lỗi timeout, THE LLM_Judge SHALL retry ngay lập tức với tối đa 2 lần
3. WHEN OpenAI API trả về lỗi invalid request, THE LLM_Judge SHALL trả về error response với message chi tiết
4. WHEN tất cả retry thất bại, THE LLM_Judge SHALL trả về fallback response với verdict = "FAILED", error_desc = "LLM Judge unavailable", confidence_level = 0.0
5. THE LLM_Judge SHALL ghi log tất cả các lỗi API để monitoring

### Requirement 20: Configuration cho Scoring Weights

**User Story:** Là một QA manager, tôi muốn có thể điều chỉnh trọng số scoring qua config, để thử nghiệm các công thức khác nhau.

#### Acceptance Criteria

1. THE Configuration_System SHALL cho phép định nghĩa trọng số cho từng tiêu chí trong file config
2. THE Configuration_System SHALL validate tổng trọng số (content + tone + time) = 100% cho mỗi tiêu chí
3. WHEN config file không tồn tại, THE Configuration_System SHALL sử dụng trọng số mặc định
4. THE Configuration_System SHALL cho phép định nghĩa ngưỡng PASSED (ví dụ: 70 cho standard, 85 cho strict)
5. THE Configuration_System SHALL reload config khi file thay đổi mà không cần restart server

## Implementation Notes

### Phased Rollout Strategy

**Phase 1 (Tuần 1-2): Foundation**
- Implement Scoring System (Req 1)
- Implement Domain Glossary (Req 4)
- Implement Edge Case Examples (Req 7)
- Implement Self-Consistency Check (Req 8)
- Update Prompt Templates (Req 9)

**Phase 2 (Tuần 3-4): Advanced Features**
- Implement Confidence Level (Req 2)
- Implement Error Severity (Req 3)
- Implement Rubrics (Req 5, 6)
- Update JSON Output Schema (Req 10)
- Implement Parser & Pretty Printer (Req 17)

**Phase 3 (Tuần 5-6): Criteria-Specific Tuning**
- Adjust weights for all criteria (Req 11-15)
- Implement Configuration System (Req 20)
- Implement Logging & Monitoring (Req 18)
- Implement Error Handling (Req 19)
- Ensure Backward Compatibility (Req 16)

### Testing Strategy

- Unit tests cho Scoring System với các edge cases
- Integration tests cho từng tiêu chí với 20+ test cases
- A/B testing so sánh hệ thống cũ vs mới trên 100+ test cases thực tế
- Human evaluation trên 50 cases có confidence_level < 0.7
- Performance testing để đảm bảo latency không tăng >20%

### Success Metrics

- Giảm false positive rate xuống <5% (hiện tại ~10%)
- Giảm false negative rate xuống <5% (hiện tại ~8%)
- Tỷ lệ needs_human_review <15%
- Độ nhất quán giữa các lần đánh giá cùng 1 case >95%
- Latency trung bình <2s cho mỗi đánh giá
