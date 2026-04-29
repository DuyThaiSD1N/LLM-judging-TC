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

Trả về JSON:
{
  "verdict": "PASSED" hoặc "FAILED",
  "error_desc": "Chỉ mô tả lỗi NỘI DUNG.",
  "suggestion": "Đề xuất về NỘI DUNG cần sửa.",
  "suggested_response": "MẪU với nội dung đúng (không cần đẹp) nếu FAILED.",
  "tone_note": "Không đánh giá",
  "brevity_note": "Không đánh giá",
  "time_verdict": "good" hoặc "ok" hoặc "slow",
  "time_note": "Nhận xét thời gian."
}

Chỉ trả về JSON.`
};
