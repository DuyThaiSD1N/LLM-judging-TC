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

## YÊU CẦU VỀ NHẬN XÉT & ĐỀ XUẤT:

**error_desc** (nếu FAILED):
- Liệt kê CỤ THỂ từng lỗi: thiếu thông tin gì? sai ở đâu? 
- Dẫn chứng bằng trích dẫn từ câu trả lời thực tế
- VD: "Thiếu thông tin về 'lệ phí'. Câu trả lời chỉ nói 'cần CMND' nhưng không đề cập đến chi phí."

**suggestion** (nếu FAILED):
- Đưa ra các bước cải thiện CỤ THỂ, TỪNG ĐIỂM
- VD: "1. Bổ sung thông tin về lệ phí (miễn phí). 2. Thêm thông tin về giấy xác nhận độc thân. 3. Rút ngắn phần giới thiệu."

**suggested_response** (nếu FAILED):
- Viết MẪU CÂU TRẢ LỜI HOÀN CHỈNH (2-3 câu, 30-50 từ)
- Phải bao gồm TẤT CẢ thông tin trong kỳ vọng
- Giọng điệu tự nhiên, lịch sự, ngắn gọn
- VD: "Dạ, để đăng ký kết hôn anh/chị cần chuẩn bị CMND và giấy xác nhận độc thân. Lệ phí đăng ký là miễn phí ạ."

**tone_note**:
- Phân tích CỤ THỂ: xưng hô thế nào? có lịch sự không? tự nhiên hay máy móc?
- VD: "Thiếu xưng hô 'anh/chị', không có 'dạ/ạ', nghe hơi cộc lốc."

**brevity_note**:
- Đếm số từ, đánh giá độ dài CỤ THỂ
- VD: "Câu trả lời 65 từ, hơi dài. Nên rút ngắn xuống 40-50 từ."

Trả về JSON với đúng 8 trường:
{
  "verdict": "PASSED" hoặc "FAILED",
  "error_desc": "Mô tả CHI TIẾT từng lỗi với dẫn chứng nếu FAILED. Để trống nếu PASSED.",
  "suggestion": "Liệt kê TỪNG BƯỚC cải thiện cụ thể nếu FAILED. Để trống nếu PASSED.",
  "suggested_response": "MẪU CÂU TRẢ LỜI HOÀN CHỈNH (2-3 câu, 30-50 từ) nếu FAILED. Để trống nếu PASSED.",
  "tone_note": "Phân tích CỤ THỂ về xưng hô, lịch sự, tự nhiên (2-3 câu).",
  "brevity_note": "Đánh giá CỤ THỂ về độ dài, số từ (1-2 câu).",
  "time_verdict": "good" hoặc "ok" hoặc "slow",
  "time_note": "Nhận xét cụ thể về tốc độ và ảnh hưởng đến trải nghiệm."
}

Chỉ trả về JSON, không giải thích thêm.`
};
