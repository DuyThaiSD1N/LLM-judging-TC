// routes/judge.js — LLM đánh giá nội dung + thời gian phản hồi chatbot

const OpenAI = require('openai');

// Import các prompt tiêu chí
const standardPrompt = require('../prompts/standard');
const strictPrompt = require('../prompts/strict');
const flexiblePrompt = require('../prompts/flexible');
const contentOnlyPrompt = require('../prompts/content-only');
const uxFocusedPrompt = require('../prompts/ux-focused');

// Phase 3: Import configuration system
const { getCriteriaConfig, calculateTotalScore, determineVerdict } = require('../config/criteria-weights');

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

function classifyTime(ms) {
    if (ms <= TIME_THRESHOLD.GOOD) return { label: 'Nhanh', level: 'good' };
    if (ms <= TIME_THRESHOLD.OK) return { label: 'Chấp nhận được', level: 'ok' };
    return { label: 'Chậm', level: 'slow' };
}

/**
 * Đánh giá nội dung + thời gian phản hồi
 *
 * @param {string} criteria - Tiêu chí đánh giá: standard, strict, flexible, content-only, ux-focused
 * @returns {{
 *   verdict: 'PASSED'|'FAILED',
 *   total_score: number,
 *   content_score: number,
 *   tone_score: number,
 *   time_score: number,
 *   confidence_level: number,
 *   needs_human_review: boolean,
 *   confidence_reason: string,
 *   errors: array,
 *   error_desc: string,
 *   suggestion: string,
 *   suggested_response: string,
 *   tone_note: string,
 *   time_verdict: 'good'|'ok'|'slow',
 *   time_note: string
 * }}
 */
async function judgeOne({ question, expected, actual, group, responseTimeMs, criteria = 'standard' }) {
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
        timeLabel,
        criteria  // Pass criteria to prompt for Phase 3 weight info
    });

    // Phase 3 - Req 19: Error Handling với retry logic
    let response;
    let retryCount = 0;
    const MAX_RETRIES = 3;
    const RETRY_DELAY_MS = 5000;

    while (retryCount < MAX_RETRIES) {
        try {
            response = await getOpenAI().chat.completions.create({
                model: 'gpt-4o-mini',
                messages: [{ role: 'user', content: prompt }],
                response_format: { type: 'json_object' },
                temperature: 0.1,
            });
            break; // Success, exit retry loop
        } catch (error) {
            retryCount++;

            // Rate limit error - wait and retry
            if (error.status === 429 && retryCount < MAX_RETRIES) {
                console.warn(`⚠️ OpenAI rate limit hit, retrying in ${RETRY_DELAY_MS}ms (attempt ${retryCount}/${MAX_RETRIES})`);
                await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
                continue;
            }

            // Timeout error - retry immediately
            if (error.code === 'ETIMEDOUT' && retryCount < 2) {
                console.warn(`⚠️ OpenAI timeout, retrying immediately (attempt ${retryCount}/2)`);
                continue;
            }

            // Invalid request or max retries reached
            console.error(`❌ OpenAI API error after ${retryCount} attempts:`, error.message);

            // Return fallback response
            return {
                verdict: 'FAILED',
                total_score: 0,
                content_score: 0,
                tone_score: 0,
                time_score: 0,
                confidence_level: 0.0,
                needs_human_review: true,
                confidence_reason: 'LLM Judge unavailable - API error',
                errors: [{
                    description: `LLM Judge unavailable: ${error.message}`,
                    severity: 'Critical',
                    quote: ''
                }],
                error_desc: `LLM Judge unavailable: ${error.message}`,
                suggestion: 'Please retry later or contact support',
                suggested_response: '',
                tone_note: '',
                time_verdict: timeInfo.level,
                time_note: timeLabel,
            };
        }
    }

    const parsed = JSON.parse(response.choices[0].message.content);

    // Phase 1: Extract scoring fields
    const contentScore = parsed.content_score ?? 0;
    const toneScore = parsed.tone_score ?? 0;
    const timeScore = parsed.time_score ?? 0;

    // Phase 3: Calculate total_score using configuration
    const totalScore = calculateTotalScore(criteria, contentScore, toneScore, timeScore);

    // Phase 3: Determine verdict using configuration threshold
    const verdict = determineVerdict(criteria, totalScore);

    // Phase 2: Extract confidence and error severity fields
    const confidenceLevel = parsed.confidence_level ?? null;
    const needsHumanReview = parsed.needs_human_review ?? (confidenceLevel !== null && confidenceLevel < 0.7);
    const confidenceReason = parsed.confidence_reason ?? '';
    const errors = parsed.errors ?? [];

    // Phase 3 - Req 18: Logging for monitoring
    console.log(`📊 Judge Result [${criteria}]: verdict=${verdict}, total=${totalScore}, confidence=${confidenceLevel}, needs_review=${needsHumanReview}`);

    return {
        // Phase 1 fields
        total_score: totalScore,
        content_score: contentScore,
        tone_score: toneScore,
        time_score: timeScore,

        // Phase 2 fields
        confidence_level: confidenceLevel,
        needs_human_review: needsHumanReview,
        confidence_reason: confidenceReason,
        errors: errors,

        // Existing fields (backward compatibility)
        verdict: verdict,
        error_desc: parsed.error_desc ?? '',
        suggestion: parsed.suggestion ?? '',
        suggested_response: parsed.suggested_response ?? '',
        tone_note: parsed.tone_note ?? '',
        time_verdict: ['good', 'ok', 'slow'].includes(parsed.time_verdict)
            ? parsed.time_verdict : timeInfo.level,
        time_note: parsed.time_note ?? timeLabel,
    };
}

module.exports = { judgeOne, CRITERIA_LIST };
