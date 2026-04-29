// routes/judge.js — LLM đánh giá nội dung + thời gian phản hồi chatbot

const OpenAI = require('openai');

let _openai = null;
function getOpenAI() {
    if (!_openai) _openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
    return _openai;
}

// Ngưỡng thời gian phản hồi (ms)
const TIME_THRESHOLD = {
    GOOD: 2000,   // <= 2s: tốt
    OK: 3000,   // <= 3s: chấp nhận được
    // > 3s : chậm
};

const GROUP_DESC = {
    A: 'Hỏi đầy đủ thông tin — bot phải cung cấp đúng và đủ thông tin về thủ tục hành chính.',
    B: `Hỏi ngoại lệ / ngoài phạm vi — bot phải từ chối và chuyển hướng về hành chính công.
      Cách từ chối mặc định HỢP LỆ của bot là: KHÔNG trả lời nội dung ngoài phạm vi, sau đó
      hỏi lại người dùng có cần hỗ trợ thủ tục hành chính không.
      Ví dụ hợp lệ: "Dạ em rất sẵn lòng a, nhưng em xin phép hỗ trợ các nội dung hành chính
      công thôi, anh cần em tra cứu thủ tục nào không ạ?"
      Đây là hành vi ĐÚNG — phải chấm PASSED nếu bot từ chối và chuyển hướng như vậy.`,
    C: 'Hỏi chuyển topic đột ngột — bot phải xử lý chuyển chủ đề hợp lý, không bị lạc.',
    D: 'Hỏi tài liệu không có trong CSDL — bot phải thừa nhận không có thông tin và hướng dẫn đến văn phòng 1 cửa, tuyệt đối không bịa.',
};

const GREETING_PATTERNS = [
    /em chào anh/i,
    /em chào chị/i,
    /xin chào/i,
    /tổng đài.*hành chính/i,
    /hành chính công.*tỉnh/i,
    /em có thể hỗ trợ gì/i,
    /em có thể giúp gì/i,
];

function isGreetingResponse(text) {
    return GREETING_PATTERNS.some(p => p.test(text));
}

function classifyTime(ms) {
    if (ms <= TIME_THRESHOLD.GOOD) return { label: 'Nhanh', level: 'good' };
    if (ms <= TIME_THRESHOLD.OK) return { label: 'Chấp nhận được', level: 'ok' };
    return { label: 'Chậm', level: 'slow' };
}

/**
 * Đánh giá nội dung + thời gian phản hồi
 * Trả về null nếu là câu chào mở đầu
 *
 * @returns {{
 *   verdict: 'PASSED'|'FAILED',
 *   error_desc: string,
 *   suggestion: string,
 *   suggested_response: string,
 *   tone_note: string,
 *   brevity_note: string,
 *   time_verdict: 'good'|'ok'|'slow',
 *   time_note: string
 * } | null}
 */
async function judgeOne({ question, expected, actual, group, responseTimeMs }) {
    if (isGreetingResponse(actual)) return null;

    const timeInfo = classifyTime(responseTimeMs ?? 0);
    const timeLabel = `${responseTimeMs}ms (${timeInfo.label})`;

    const prompt = `Bạn là chuyên gia kiểm thử chatbot hành chính công.
Nhiệm vụ: đánh giá toàn diện câu trả lời của chatbot theo 3 tiêu chí.

---
NHÓM KỊCH BẢN: ${group}
MÔ TẢ NHÓM: ${GROUP_DESC[group] ?? ''}

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
- Câu trả lời truyền đạt đúng và đủ thông tin cốt lõi so với kỳ vọng (không cần giống từng chữ)
- Với nhóm B: bot từ chối nội dung ngoài phạm vi VÀ chuyển hướng về hành chính công → PASSED

FAILED khi:
- Thiếu thông tin quan trọng mà kỳ vọng có
- Cung cấp thông tin sai lệch hoặc mâu thuẫn với kỳ vọng
- Bịa thông tin không có cơ sở — áp dụng cho TẤT CẢ nhóm, không chỉ B và D
- Với nhóm B: bot trả lời nội dung ngoài phạm vi thay vì từ chối → FAILED
- Với nhóm D: bot bịa thông tin thay vì hướng dẫn đến văn phòng 1 cửa → FAILED

## TIÊU CHÍ 2 — ĐỘ TỰ NHIÊN & GIỌNG ĐIỆU (dành cho voicebot)
Đánh giá xem câu trả lời có phù hợp để đọc thành tiếng không:
- Xưng hô lịch sự, đúng mực (anh/chị, dạ vâng...)
- Không cộc lốc, không quá máy móc
- Câu văn tự nhiên khi nghe, không vấp

## TIÊU CHÍ 3 — ĐỘ NGẮN GỌN & SÚC TÍCH (quan trọng với voicebot)
Đánh giá xem câu trả lời có quá dài không:
- Trả lời đúng trọng tâm, không lan man
- Không lặp lại thông tin không cần thiết
- Người dùng nghe xong không bị mất tập trung

## ĐÁNH GIÁ THỜI GIAN PHẢN HỒI:
- Nhận xét ngắn gọn về thời gian phản hồi ${timeLabel}
- Nếu chậm (> 3s): nêu ảnh hưởng đến trải nghiệm người dùng

Trả về JSON với đúng 8 trường:
{
  "verdict": "PASSED" hoặc "FAILED",
  "error_desc": "Mô tả cụ thể lỗi nội dung nếu FAILED. Để trống nếu PASSED.",
  "suggestion": "Đề xuất cụ thể để cải thiện nếu FAILED. Để trống nếu PASSED.",
  "suggested_response": "MẪU CÂU TRẢ LỜI ĐỀ XUẤT hoàn chỉnh để người dùng tham khảo và sửa nếu FAILED. Viết câu trả lời mẫu đầy đủ, tự nhiên, phù hợp với voicebot. Để trống nếu PASSED.",
  "tone_note": "Nhận xét 1 câu về độ tự nhiên và giọng điệu (tốt/cần cải thiện điểm gì).",
  "brevity_note": "Nhận xét 1 câu về độ ngắn gọn (súc tích/hơi dài/quá dài và lý do).",
  "time_verdict": "good" hoặc "ok" hoặc "slow",
  "time_note": "Nhận xét ngắn về tốc độ phản hồi (1 câu)."
}

Chỉ trả về JSON, không giải thích thêm.`;

    const response = await getOpenAI().chat.completions.create({
        model: 'gpt-4o-mini',
        messages: [{ role: 'user', content: prompt }],
        response_format: { type: 'json_object' },
        temperature: 0.1,
    });

    const parsed = JSON.parse(response.choices[0].message.content);
    return {
        verdict: ['PASSED', 'FAILED'].includes(parsed.verdict) ? parsed.verdict : 'FAILED',
        error_desc: parsed.error_desc ?? '',
        suggestion: parsed.suggestion ?? '',
        suggested_response: parsed.suggested_response ?? '',
        tone_note: parsed.tone_note ?? '',
        brevity_note: parsed.brevity_note ?? '',
        time_verdict: ['good', 'ok', 'slow'].includes(parsed.time_verdict)
            ? parsed.time_verdict : timeInfo.level,
        time_note: parsed.time_note ?? timeLabel,
    };
}

module.exports = { judgeOne };
