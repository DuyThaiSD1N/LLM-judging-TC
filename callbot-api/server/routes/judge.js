// routes/judge.js — LLM đánh giá nội dung + thời gian phản hồi chatbot

const OpenAI = require('openai');

// Import các prompt tiêu chí
const standardPrompt = require('../prompts/standard');
const strictPrompt = require('../prompts/strict');
const flexiblePrompt = require('../prompts/flexible');
const contentOnlyPrompt = require('../prompts/content-only');
const uxFocusedPrompt = require('../prompts/ux-focused');

const CRITERIA_MAP = {
    standard: standardPrompt,
    strict: strictPrompt,
    flexible: flexiblePrompt,
    'content-only': contentOnlyPrompt,
    'ux-focused': uxFocusedPrompt,
};

// Export danh sách tiêu chí để frontend sử dụng
const CRITERIA_LIST = [
    { id: 'standard', name: 'Tiêu chí Chuẩn', description: 'Đánh giá cân bằng: nội dung đúng đủ, giọng điệu tự nhiên, ngắn gọn, thời gian hợp lý' },
    { id: 'strict', name: 'Tiêu chí Nghiêm ngặt', description: 'Đánh giá nghiêm ngặt: yêu cầu 100% thông tin, giọng điệu hoàn hảo, thời gian < 2s' },
    { id: 'flexible', name: 'Tiêu chí Linh hoạt', description: 'Đánh giá linh hoạt: chấp nhận thiếu thông tin phụ, giọng điệu OK, thời gian < 5s' },
    { id: 'content-only', name: 'Tiêu chí Nội dung', description: 'Chỉ đánh giá nội dung đúng/sai, bỏ qua giọng điệu và độ ngắn gọn' },
    { id: 'ux-focused', name: 'Tiêu chí Trải nghiệm', description: 'Tập trung vào giọng điệu, độ ngắn gọn, thời gian. Nội dung chỉ cần đủ 70%' },
];

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
 * @param {string} criteria - Tiêu chí đánh giá: standard, strict, flexible, content-only, ux-focused
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
async function judgeOne({ question, expected, actual, group, responseTimeMs, criteria = 'standard' }) {
    if (isGreetingResponse(actual)) return null;

    const timeInfo = classifyTime(responseTimeMs ?? 0);
    const timeLabel = `${responseTimeMs}ms (${timeInfo.label})`;

    // Lấy prompt theo tiêu chí
    const promptConfig = CRITERIA_MAP[criteria] || CRITERIA_MAP.standard;
    const groupDesc = GROUP_DESC[group] ?? '';

    const prompt = promptConfig.getPrompt({
        question,
        expected,
        actual,
        group,
        groupDesc,
        timeLabel
    });

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

module.exports = { judgeOne, CRITERIA_LIST };
