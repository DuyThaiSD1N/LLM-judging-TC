const express = require('express');
const multer = require('multer');
const XLSX = require('xlsx');
const OpenAI = require('openai');

const router = express.Router();
const upload = multer({ storage: multer.memoryStorage() });
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

// ── Đọc Excel → trả về mảng rows thô ──────────────────────────────────────
function parseExcel(buffer) {
    const workbook = XLSX.read(buffer, { type: 'buffer' });
    const sheetName = workbook.SheetNames[0];
    const sheet = workbook.Sheets[sheetName];
    // header: 1 → trả về mảng các mảng (không dùng row đầu làm key)
    const rows = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' });
    return rows;
}

// ── Validate dữ liệu Excel ────────────────────────────────────────────────
function validateExcelData(rows) {
    const errors = [];

    // Kiểm tra có dữ liệu không
    if (!rows || rows.length === 0) {
        return { valid: false, error: 'File Excel trống hoặc không đọc được' };
    }

    // Kiểm tra header (row đầu tiên)
    const header = rows[0];
    const requiredHeaders = ['Tên Testcase', 'Mã Testcase', 'Nhóm', 'Câu hỏi', 'Câu trả lời', 'LLM Judge'];

    // Kiểm tra số cột tối thiểu (có thể có 5 hoặc 6 cột)
    if (header.length < 5) {
        return {
            valid: false,
            error: `File Excel không đúng định dạng. Cần ít nhất 5 cột: Tên Testcase, Mã Testcase, Nhóm (A/B/C/D), Câu hỏi từ User, Câu trả lời kỳ vọng. Hiện tại chỉ có ${header.length} cột.`
        };
    }

    // Kiểm tra từng dòng dữ liệu (bỏ qua header và dòng trống)
    const dataRows = rows.slice(1).filter(row => row.some(cell => cell && cell.toString().trim()));

    if (dataRows.length === 0) {
        return { valid: false, error: 'File Excel không có dữ liệu testcase nào' };
    }

    // Validate từng dòng
    const validGroups = ['A', 'B', 'C', 'D'];
    const validCriteria = ['standard', 'strict', 'flexible', 'content-only', 'ux-focused'];

    dataRows.forEach((row, idx) => {
        const rowNum = idx + 2; // +2 vì bỏ header và index bắt đầu từ 0
        const [name, code, group, question, expected, criteria] = row;

        // Kiểm tra các trường bắt buộc
        if (!name || name.toString().trim() === '') {
            errors.push(`Dòng ${rowNum}: Thiếu "Tên Testcase"`);
        }
        if (!code || code.toString().trim() === '') {
            errors.push(`Dòng ${rowNum}: Thiếu "Mã Testcase"`);
        }
        if (!group || group.toString().trim() === '') {
            errors.push(`Dòng ${rowNum}: Thiếu "Nhóm (A/B/C/D)"`);
        } else if (!validGroups.includes(group.toString().trim().toUpperCase())) {
            errors.push(`Dòng ${rowNum}: Nhóm "${group}" không hợp lệ. Chỉ chấp nhận: A, B, C, D`);
        }
        if (!question || question.toString().trim() === '') {
            errors.push(`Dòng ${rowNum}: Thiếu "Câu hỏi từ User"`);
        }
        if (!expected || expected.toString().trim() === '') {
            errors.push(`Dòng ${rowNum}: Thiếu "Câu trả lời kỳ vọng"`);
        }

        // Kiểm tra LLM Judge (nếu có cột này)
        if (header.length >= 6 && criteria && criteria.toString().trim() !== '') {
            const criteriaValue = criteria.toString().trim().toLowerCase();
            if (!validCriteria.includes(criteriaValue)) {
                errors.push(`Dòng ${rowNum}: LLM Judge "${criteria}" không hợp lệ. Chỉ chấp nhận: standard, strict, flexible, content-only, ux-focused`);
            }
        }
    });

    if (errors.length > 0) {
        return {
            valid: false,
            error: `File Excel có ${errors.length} lỗi:\n${errors.slice(0, 5).join('\n')}${errors.length > 5 ? `\n... và ${errors.length - 5} lỗi khác` : ''}`
        };
    }

    return { valid: true };
}

// ── Gọi OpenAI để map dữ liệu Excel → testcase ────────────────────────────
async function mapWithAI(rows) {
    const tableText = rows
        .map((r, i) => `Row ${i}: ${r.join(' | ')}`)
        .join('\n');

    const prompt = `
Bạn nhận được dữ liệu từ file Excel (mỗi dòng cách nhau bởi |).
Hãy phân tích và trích xuất thành danh sách testcase theo định dạng JSON.

Mỗi testcase gồm:
- "name": Tên testcase
- "code": Mã testcase (dạng TC-XXX)
- "group": Mã kịch bản, chỉ được là một trong: "A", "B", "C", "D"
  + A = Hỏi đầy đủ thông tin
  + B = Hỏi ngoại lệ / ngoài phạm vi
  + C = Hỏi chuyển topic đột ngột
  + D = Hỏi tài liệu không có trong CSDL
- "question": Câu hỏi từ user
- "expected": Câu trả lời kỳ vọng
- "criteria": Tiêu chí LLM Judge (standard/strict/flexible/content-only/ux-focused). Nếu không có thì để "standard"

Nếu một trường không tìm thấy, để chuỗi rỗng "" (trừ criteria thì để "standard").
Chỉ trả về JSON array, không giải thích thêm.

Dữ liệu Excel:
${tableText}
`;

    const response = await openai.chat.completions.create({
        model: 'gpt-4o-mini',
        messages: [{ role: 'user', content: prompt }],
        response_format: { type: 'json_object' },
        temperature: 0.2,
    });

    const content = response.choices[0].message.content;
    const parsed = JSON.parse(content);

    // OpenAI có thể trả về { testcases: [...] } hoặc { data: [...] } hoặc [...]
    if (Array.isArray(parsed)) return parsed;
    const key = Object.keys(parsed).find(k => Array.isArray(parsed[k]));
    return key ? parsed[key] : [];
}

// ── POST /api/upload-excel ─────────────────────────────────────────────────
router.post('/upload-excel', upload.single('file'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'Không có file được gửi lên.' });
        }

        const ext = req.file.originalname.split('.').pop().toLowerCase();
        if (!['xlsx', 'xls'].includes(ext)) {
            return res.status(400).json({ error: 'Chỉ chấp nhận file .xlsx hoặc .xls' });
        }

        const rows = parseExcel(req.file.buffer);

        // Validate dữ liệu trước khi xử lý
        const validation = validateExcelData(rows);
        if (!validation.valid) {
            return res.status(400).json({ error: validation.error });
        }

        const testcases = await mapWithAI(rows);

        res.json({ testcases });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: err.message || 'Lỗi server.' });
    }
});

module.exports = router;
