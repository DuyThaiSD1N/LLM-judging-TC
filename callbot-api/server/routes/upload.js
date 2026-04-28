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

Nếu một trường không tìm thấy, để chuỗi rỗng "".
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
        const testcases = await mapWithAI(rows);

        res.json({ testcases });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: err.message || 'Lỗi server.' });
    }
});

module.exports = router;
