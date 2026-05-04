// routes/export.js — xuất testcase + kết quả đánh giá ra Excel

const express = require('express');
const XLSX = require('xlsx-js-style');
const router = express.Router();

router.post('/export', (req, res) => {
    const { testcases } = req.body;

    if (!testcases || testcases.length === 0) {
        return res.status(400).json({ error: 'Không có testcase nào để xuất' });
    }

    // Tạo dữ liệu cho Excel
    const rows = [];

    // Header
    const headers = [
        'Mã TC',
        'Tên Testcase',
        'Nhóm',
        'LLM Judge',
        'Lượt',
        'Câu hỏi từ User',
        'Câu trả lời kỳ vọng',
        'Câu trả lời thực tế',
        'Thời gian (ms)',
        'Kết quả',
        'Lỗi',
        'Đề xuất sửa',
        'Mẫu đề xuất',
        'Nhận xét giọng điệu'
    ];
    rows.push(headers);

    // Dữ liệu
    testcases.forEach(tc => {
        const criteriaNames = {
            'standard': 'Chuẩn',
            'strict': 'Nghiêm ngặt',
            'flexible': 'Linh hoạt',
            'content-only': 'Nội dung',
            'ux-focused': 'Trải nghiệm'
        };
        const criteriaDisplay = criteriaNames[tc.criteria] || tc.criteria;

        tc.turns.forEach((turn, idx) => {
            const row = [
                tc.code,
                tc.name,
                tc.group,
                criteriaDisplay,
                `Lượt ${idx + 1}`,
                turn.question,
                turn.expected,
                turn.actual || '',
                turn.response_time_ms || '',
                turn.verdict || '',
                turn.error_desc || '',
                turn.suggestion || '',
                turn.suggested_response || '',
                turn.tone_note || ''
            ];
            rows.push(row);
        });
    });

    const ws = XLSX.utils.aoa_to_sheet(rows);

    // Độ rộng cột
    ws['!cols'] = [
        { wch: 12 },  // Mã TC
        { wch: 35 },  // Tên
        { wch: 8 },   // Nhóm
        { wch: 15 },  // LLM Judge
        { wch: 10 },  // Lượt
        { wch: 40 },  // Câu hỏi
        { wch: 40 },  // Kỳ vọng
        { wch: 40 },  // Thực tế
        { wch: 12 },  // Thời gian
        { wch: 10 },  // Kết quả
        { wch: 40 },  // Lỗi
        { wch: 40 },  // Đề xuất
        { wch: 40 },  // Mẫu
        { wch: 40 }   // Giọng điệu
    ];

    // Style cho header (row 1)
    const headerCells = ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'I1', 'J1', 'K1', 'L1', 'M1', 'N1'];
    headerCells.forEach(ref => {
        if (!ws[ref]) return;
        ws[ref].s = {
            fill: {
                patternType: 'solid',
                fgColor: { rgb: 'FFFF00' }
            },
            font: {
                bold: true,
                sz: 11,
                color: { rgb: '000000' }
            },
            alignment: {
                horizontal: 'center',
                vertical: 'center',
                wrapText: true
            },
            border: {
                top: { style: 'thin', color: { rgb: '000000' } },
                bottom: { style: 'thin', color: { rgb: '000000' } },
                left: { style: 'thin', color: { rgb: '000000' } },
                right: { style: 'thin', color: { rgb: '000000' } }
            }
        };
    });

    // Style cho cột kết quả (PASSED = xanh, FAILED = đỏ)
    for (let i = 2; i <= rows.length; i++) {
        const cellRef = `J${i}`;
        if (ws[cellRef]) {
            const value = ws[cellRef].v;
            if (value === 'PASSED') {
                ws[cellRef].s = {
                    fill: { patternType: 'solid', fgColor: { rgb: 'C6EFCE' } },
                    font: { color: { rgb: '006100' }, bold: true }
                };
            } else if (value === 'FAILED') {
                ws[cellRef].s = {
                    fill: { patternType: 'solid', fgColor: { rgb: 'FFC7CE' } },
                    font: { color: { rgb: '9C0006' }, bold: true }
                };
            }
        }
    }

    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Testcases');

    const buf = XLSX.write(wb, {
        type: 'buffer',
        bookType: 'xlsx'
    });

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    res.setHeader('Content-Disposition', `attachment; filename="testcases_${timestamp}.xlsx"`);
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.send(buf);
});

module.exports = router;
