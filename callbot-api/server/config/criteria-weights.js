// config/criteria-weights.js — Configuration cho trọng số và ngưỡng của từng tiêu chí

/**
 * Phase 3: Criteria-Specific Weights and Thresholds
 * 
 * Mỗi tiêu chí có:
 * - weights: Trọng số cho content, tone, time (tổng = 1.0)
 * - threshold: Ngưỡng điểm để PASSED (0-100)
 * - description: Mô tả đặc điểm của tiêu chí
 */

const CRITERIA_CONFIG = {
    // Req 11: Standard - Cân bằng giữa nội dung và trải nghiệm
    standard: {
        weights: {
            content: 0.5,  // 50%
            tone: 0.3,     // 30%
            time: 0.2      // 20%
        },
        threshold: 70,
        description: 'Cân bằng: nội dung đúng đủ, giọng điệu tự nhiên, thời gian hợp lý'
    },

    // Req 12: Strict - Yêu cầu cao về tất cả khía cạnh
    strict: {
        weights: {
            content: 0.4,  // 40%
            tone: 0.4,     // 40%
            time: 0.2      // 20%
        },
        threshold: 85,
        description: 'Nghiêm ngặt: yêu cầu cao về nội dung, giọng điệu, và thời gian',
        minScores: {
            content: 90,   // Content phải ≥90 để đạt điểm cao
            tone: 90       // Tone phải ≥90 để đạt điểm cao
        }
    },

    // Req 13: Flexible - Khoan dung hơn, chấp nhận đủ tốt
    flexible: {
        weights: {
            content: 0.6,  // 60%
            tone: 0.2,     // 20%
            time: 0.2      // 20%
        },
        threshold: 60,
        description: 'Linh hoạt: ưu tiên nội dung, khoan dung về giọng điệu',
        minScores: {
            content: 70    // Content ≥70 là đủ tốt
        }
    },

    // Req 14: Content-Only - Chỉ tập trung vào nội dung
    'content-only': {
        weights: {
            content: 0.8,  // 80%
            tone: 0.0,     // 0% - Bỏ qua giọng điệu
            time: 0.2      // 20%
        },
        threshold: 70,
        description: 'Chỉ nội dung: đánh giá độ chính xác thông tin, bỏ qua giọng điệu'
    },

    // Req 15: UX-Focused - Ưu tiên trải nghiệm người dùng
    'ux-focused': {
        weights: {
            content: 0.3,  // 30%
            tone: 0.5,     // 50%
            time: 0.2      // 20%
        },
        threshold: 70,
        description: 'Trải nghiệm: ưu tiên giọng điệu thân thiện, tự nhiên',
        minScores: {
            tone: 80       // Tone phải ≥80 để đạt điểm cao
        }
    }
};

/**
 * Lấy config cho một tiêu chí
 * @param {string} criteria - Tên tiêu chí (standard, strict, flexible, content-only, ux-focused)
 * @returns {object} Config object với weights, threshold, description
 */
function getCriteriaConfig(criteria) {
    const config = CRITERIA_CONFIG[criteria];
    if (!config) {
        console.warn(`⚠️ Unknown criteria: ${criteria}, using standard config`);
        return CRITERIA_CONFIG.standard;
    }
    return config;
}

/**
 * Tính total_score dựa trên trọng số của tiêu chí
 * @param {string} criteria - Tên tiêu chí
 * @param {number} contentScore - Điểm nội dung (0-100)
 * @param {number} toneScore - Điểm giọng điệu (0-100)
 * @param {number} timeScore - Điểm thời gian (0-100)
 * @returns {number} Total score (0-100)
 */
function calculateTotalScore(criteria, contentScore, toneScore, timeScore) {
    const config = getCriteriaConfig(criteria);
    const { content, tone, time } = config.weights;

    const totalScore = contentScore * content + toneScore * tone + timeScore * time;
    return Math.round(totalScore * 10) / 10; // Round to 1 decimal place
}

/**
 * Xác định verdict dựa trên total_score và threshold
 * @param {string} criteria - Tên tiêu chí
 * @param {number} totalScore - Tổng điểm (0-100)
 * @returns {string} 'PASSED' hoặc 'FAILED'
 */
function determineVerdict(criteria, totalScore) {
    const config = getCriteriaConfig(criteria);
    return totalScore >= config.threshold ? 'PASSED' : 'FAILED';
}

/**
 * Validate config: tổng trọng số phải = 1.0
 */
function validateConfig() {
    for (const [criteria, config] of Object.entries(CRITERIA_CONFIG)) {
        const sum = config.weights.content + config.weights.tone + config.weights.time;
        if (Math.abs(sum - 1.0) > 0.001) {
            throw new Error(`❌ Invalid weights for ${criteria}: sum = ${sum}, expected 1.0`);
        }
    }
    console.log('✅ Criteria weights config validated');
}

// Validate khi load module
validateConfig();

module.exports = {
    CRITERIA_CONFIG,
    getCriteriaConfig,
    calculateTotalScore,
    determineVerdict
};
