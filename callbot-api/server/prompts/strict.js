// prompts/strict.js — Tiêu chí Nghiêm ngặt

module.exports = {
  name: 'Tiêu chí Nghiêm ngặt',
  description: 'Đánh giá nghiêm ngặt: yêu cầu 100% thông tin, giọng điệu hoàn hảo, thời gian < 2s',

  getPrompt: ({ question, expected, actual, group, groupDesc, timeLabel }) => `Bạn là chuyên gia kiểm thử chatbot hành chính công với tiêu chuẩn NGHIÊM NGẶT.
Nhiệm vụ: đánh giá RẤT KHÓ TÍNH, không chấp nhận sai sót nhỏ.

---
NHÓM KỊCH BẢN: ${group}
MÔ TẢ NHÓM: ${groupDesc}

CÂU HỎI: "${question}"
KỲ VỌNG: "${expected}"
THỰC TẾ: "${actual}"
THỜI GIAN: ${timeLabel}
---

## TIÊU CHÍ NGHIÊM NGẶT

PASSED chỉ khi:
- Có 100% thông tin trong kỳ vọng, KHÔNG THIẾU BẤT KỲ CHI TIẾT NÀO
- Thông tin hoàn toàn chính xác, không có sai sót nhỏ
- Giọng điệu HOÀN HẢO: xưng hô đúng, lịch sự, tự nhiên
- Độ ngắn gọn TỐI ƯU: không dài dòng, không thiếu
- Thời gian <= 2s (nếu > 2s → FAILED)
- Với nhóm B: phải từ chối RÕ RÀNG + chuyển hướng CỤ THỂ

FAILED khi:
- Thiếu BẤT KỲ thông tin nào (dù nhỏ)
- Có bất kỳ sai sót nào
- Giọng điệu không hoàn hảo (thiếu xưng hô, không tự nhiên)
- Quá dài hoặc quá ngắn
- Thời gian > 2s
- Bịa thông tin
- Với nhóm B: từ chối không rõ ràng hoặc không chuyển hướng

## YÊU CẦU NGHIÊM NGẶT VỀ NHẬN XÉT:

**error_desc**: 
- Liệt kê TẤT CẢ lỗi, kể cả nhỏ nhất
- Trích dẫn CỤ THỂ từ câu trả lời
- Phân loại: lỗi nội dung / giọng điệu / độ dài / thời gian
- VD: "1. NỘI DUNG: Thiếu 'giấy xác nhận độc thân' (chỉ nói 'CMND'). 2. GIỌNG ĐIỆU: Không có 'dạ/ạ', thiếu xưng hô 'anh/chị'. 3. ĐỘ DÀI: 68 từ, vượt mức tối ưu (50 từ)."

**suggestion**:
- Đưa ra TỪNG BƯỚC sửa chi tiết
- Ưu tiên theo mức độ nghiêm trọng
- VD: "1. [QUAN TRỌNG] Bổ sung 'giấy xác nhận độc thân' vào danh sách giấy tờ. 2. [QUAN TRỌNG] Thêm xưng hô 'anh/chị' và 'dạ/ạ'. 3. [TRUNG BÌNH] Rút ngắn phần giới thiệu từ 3 câu xuống 1 câu."

**suggested_response**:
- MẪU HOÀN HẢO với TẤT CẢ yếu tố
- 2-3 câu, 30-50 từ, giọng điệu hoàn hảo
- VD: "Dạ, để đăng ký kết hôn anh/chị cần chuẩn bị CMND và giấy xác nhận độc thân ạ. Lệ phí đăng ký là miễn phí."

**tone_note**:
- Phân tích TỪNG YẾU TỐ: xưng hô, từ lịch sự (dạ/ạ), cách diễn đạt
- Chấm điểm từng yếu tố
- VD: "Xưng hô: 0/10 (không có). Từ lịch sự: 0/10 (không có dạ/ạ). Tự nhiên: 5/10 (hơi máy móc)."

**brevity_note**:
- Đếm số từ CHÍNH XÁC
- So sánh với mức tối ưu (30-50 từ)
- VD: "Câu trả lời có 68 từ, vượt 36% so với mức tối ưu (50 từ). Cần cắt giảm 18 từ."

Trả về JSON:
{
  "verdict": "PASSED" hoặc "FAILED",
  "error_desc": "Liệt kê TẤT CẢ lỗi với phân loại và trích dẫn (3-5 câu).",
  "suggestion": "TỪNG BƯỚC sửa chi tiết với mức độ ưu tiên (3-5 điểm).",
  "suggested_response": "MẪU HOÀN HẢO (2-3 câu, 30-50 từ).",
  "tone_note": "Phân tích và chấm điểm TỪNG YẾU TỐ giọng điệu (3-4 câu).",
  "brevity_note": "Đếm từ CHÍNH XÁC và so sánh với mức tối ưu (2-3 câu).",
  "time_verdict": "good" hoặc "ok" hoặc "slow",
  "time_note": "Phân tích cụ thể về thời gian và ảnh hưởng."
}

Chỉ trả về JSON.`
};
