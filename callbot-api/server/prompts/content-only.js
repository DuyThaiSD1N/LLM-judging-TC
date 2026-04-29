// prompts/content-only.js — Tiêu chí Nội dung

module.exports = {
  name: 'Tiêu chí Nội dung',
  description: 'Chỉ đánh giá nội dung đúng/sai, bỏ qua giọng điệu và độ ngắn gọn',

  getPrompt: ({ question, expected, actual, group, groupDesc, timeLabel }) => `Bạn là chuyên gia kiểm thử chatbot, CHỈ ĐÁNH GIÁ NỘI DUNG.
Nhiệm vụ: kiểm tra thông tin đúng/sai, BỎ QUA giọng điệu và độ dài.

---
NHÓM KỊCH BẢN: ${group}
MÔ TẢ NHÓM: ${groupDesc}

CÂU HỎI: "${question}"
KỲ VỌNG: "${expected}"
THỰC TẾ: "${actual}"
THỜI GIAN: ${timeLabel}
---

## CHỈ ĐÁNH GIÁ NỘI DUNG

PASSED khi:
- Có TẤT CẢ thông tin quan trọng trong kỳ vọng
- Thông tin đúng, không sai lệch
- Không bịa thông tin
- Với nhóm B: từ chối nội dung ngoài phạm vi
- Với nhóm D: thừa nhận không biết

FAILED khi:
- Thiếu thông tin quan trọng
- Thông tin sai
- Bịa thông tin
- Với nhóm B: trả lời nội dung ngoài phạm vi
- Với nhóm D: bịa thông tin

BỎ QUA:
- Giọng điệu (xưng hô, lịch sự) → KHÔNG ĐÁNH GIÁ
- Độ dài (ngắn/dài) → KHÔNG ĐÁNH GIÁ
- Cách diễn đạt → KHÔNG ĐÁNH GIÁ

## YÊU CẦU VỀ NHẬN XÉT NỘI DUNG:

**error_desc** (chỉ về NỘI DUNG):
- Liệt kê CỤ THỂ từng thông tin thiếu/sai
- So sánh với kỳ vọng
- Trích dẫn từ câu trả lời thực tế
- VD: "1. THIẾU: Không đề cập 'giấy xác nhận độc thân' (có trong kỳ vọng). 2. THIẾU: Không nói về 'lệ phí miễn phí'. 3. Câu trả lời chỉ nói 'cần CMND' là chưa đủ."

**suggestion** (chỉ về NỘI DUNG):
- Đưa ra TỪNG ĐIỂM cần bổ sung/sửa
- Liệt kê thông tin cần thêm vào
- VD: "1. Bổ sung 'giấy xác nhận độc thân' vào danh sách giấy tờ. 2. Thêm thông tin 'lệ phí miễn phí'. 3. Đảm bảo có đầy đủ 2 loại giấy tờ như kỳ vọng."

**suggested_response**:
- MẪU với NỘI DUNG ĐÚNG và ĐẦY ĐỦ
- Không cần đẹp, chỉ cần đúng
- VD: "Đăng ký kết hôn cần CMND và giấy xác nhận độc thân. Lệ phí miễn phí."

**tone_note**: "Không đánh giá giọng điệu"
**brevity_note**: "Không đánh giá độ dài"

Trả về JSON:
{
  "verdict": "PASSED" hoặc "FAILED",
  "error_desc": "Liệt kê CỤ THỂ từng thông tin thiếu/sai với so sánh và trích dẫn (2-4 câu).",
  "suggestion": "TỪNG ĐIỂM cần bổ sung/sửa về nội dung (2-4 điểm).",
  "suggested_response": "MẪU với nội dung ĐÚNG và ĐẦY ĐỦ (1-3 câu) nếu FAILED.",
  "tone_note": "Không đánh giá giọng điệu",
  "brevity_note": "Không đánh giá độ dài",
  "time_verdict": "good" hoặc "ok" hoặc "slow",
  "time_note": "Nhận xét về thời gian (1 câu)."
}

Chỉ trả về JSON.`
};
