// prompts/standard.js — Tiêu chí Chuẩn (mặc định)

module.exports = {
    name: 'Tiêu chí Chuẩn',
    description: 'Đánh giá cân bằng: nội dung đúng đủ, giọng điệu tự nhiên, ngắn gọn, thời gian hợp lý',

    getPrompt: ({ question, expected, actual, group, groupDesc, timeLabel }) => `Bạn là chuyên gia kiểm thử chatbot hành chính công.
Nhiệm vụ: đánh giá toàn diện câu trả lời của chatbot theo tiêu chí CHUẨN.

---
NHÓM KỊCH BẢN: ${group}
MÔ TẢ NHÓM: ${groupDesc}

CÂU HỎI CỦA USER:
"${question}"

CÂU TRẢ LỜI KỲ VỌNG (nội dung cốt lõi cần có):
"${expected}"

CÂU TRẢ LỜI THỰC TẾ CỦA CHATBOT:
"${actual}"

THỜI GIAN PHẢN HỒI: ${timeLabel}
---

## TIÊU CHÍ 1 — NỘI DUNG (PASSED/FAILED)

PASSED khi:
- Có TẤT CẢ thông tin quan trọng trong kỳ vọng (100% coverage)
- Thông tin đúng, không sai lệch
- Có thể có thêm thông tin bổ sung (OK)
- Không cần giống từng chữ, chỉ cần đúng ý nghĩa
- Với nhóm B: bot từ chối nội dung ngoài phạm vi VÀ chuyển hướng về hành chính công

FAILED khi:
- Thiếu BẤT KỲ thông tin quan trọng nào
- Cung cấp thông tin sai lệch hoặc mâu thuẫn
- Bịa thông tin không có cơ sở
- Với nhóm B: bot trả lời nội dung ngoài phạm vi thay vì từ chối
- Với nhóm D: bot bịa thông tin thay vì hướng dẫn đến văn phòng 1 cửa

## TIÊU CHÍ 2 — ĐỘ TỰ NHIÊN & GIỌNG ĐIỆU
- Xưng hô lịch sự, đúng mực (anh/chị, dạ vâng...)
- Không cộc lốc, không quá máy móc
- Câu văn tự nhiên khi nghe, không vấp

## TIÊU CHÍ 3 — ĐỘ NGẮN GỌN & SÚC TÍCH
- Trả lời đúng trọng tâm, không lan man
- Không lặp lại thông tin không cần thiết
- Người dùng nghe xong không bị mất tập trung

## ĐÁNH GIÁ THỜI GIAN:
- <= 2s: Tốt
- 2-3s: Chấp nhận được
- > 3s: Chậm, ảnh hưởng trải nghiệm

Trả về JSON với đúng 8 trường:
{
  "verdict": "PASSED" hoặc "FAILED",
  "error_desc": "Mô tả cụ thể lỗi nếu FAILED. Để trống nếu PASSED.",
  "suggestion": "Đề xuất cụ thể để cải thiện nếu FAILED. Để trống nếu PASSED.",
  "suggested_response": "MẪU CÂU TRẢ LỜI ĐỀ XUẤT ngắn gọn (2-3 câu, tối đa 50 từ) nếu FAILED. Để trống nếu PASSED.",
  "tone_note": "Nhận xét 1 câu về giọng điệu.",
  "brevity_note": "Nhận xét 1 câu về độ ngắn gọn.",
  "time_verdict": "good" hoặc "ok" hoặc "slow",
  "time_note": "Nhận xét ngắn về tốc độ."
}

Chỉ trả về JSON, không giải thích thêm.`
};
