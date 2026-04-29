// routes/template.js — xuất file Excel mẫu để nhập testcase

const express = require('express');
const XLSX = require('xlsx');
const router = express.Router();

router.get('/template', (req, res) => {
    const headers = [
        'Tên Testcase',
        'Mã Testcase',
        'Nhóm (A/B/C/D)',
        'Câu hỏi từ User',
        'Câu trả lời kỳ vọng',
        'LLM Judge (standard/strict/flexible/content-only/ux-focused)'
    ];
    const sample = [
        'Hỏi thủ tục đăng ký kết hôn',
        'TC-001',
        'A',
        'đăng ký kết hôn cần giấy tờ gì',
        'Cần CMND/CCCD và giấy xác nhận tình trạng hôn nhân, nộp tại UBND cấp xã',
        'standard'
    ];

    const ws = XLSX.utils.aoa_to_sheet([headers, sample]);

    // Độ rộng cột
    ws['!cols'] = [
        { wch: 35 },
        { wch: 12 },
        { wch: 16 },
        { wch: 45 },
        { wch: 60 },
        { wch: 50 }
    ];

    // Highlight dòng header (row 1) — nền vàng, chữ đậm
    const headerCells = ['A1', 'B1', 'C1', 'D1', 'E1', 'F1'];
    headerCells.forEach(ref => {
        if (!ws[ref]) return;
        ws[ref].s = {
            fill: { patternType: 'solid', fgColor: { rgb: 'FFEB3B' } },
            font: { bold: true, sz: 11, color: { rgb: '000000' } },
            alignment: { horizontal: 'center', vertical: 'center', wrapText: true },
            border: {
                top: { style: 'thin', color: { rgb: '000000' } },
                bottom: { style: 'thin', color: { rgb: '000000' } },
                left: { style: 'thin', color: { rgb: '000000' } },
                right: { style: 'thin', color: { rgb: '000000' } }
            },
        };
    });

    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Testcases');

    const buf = XLSX.write(wb, { type: 'buffer', bookType: 'xlsx', cellStyles: true });

    res.setHeader('Content-Disposition', 'attachment; filename="testcase_mau.xlsx"');
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.send(buf);
});

module.exports = router;
