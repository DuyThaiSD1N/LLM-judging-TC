// routes/template.js — xuất file Excel mẫu để nhập testcase

const express = require('express');
const XLSX = require('xlsx');
const router = express.Router();

router.get('/template', (req, res) => {
    const headers = ['Tên Testcase', 'Mã Testcase', 'Nhóm (A/B/C/D)', 'Câu hỏi từ User', 'Câu trả lời kỳ vọng', 'LLM Judge'];
    const sample = [
        'Hỏi thủ tục đăng ký kết hôn',
        'TC-001',
        'A',
        'đăng ký kết hôn cần giấy tờ gì',
        'Cần CMND/CCCD và giấy xác nhận tình trạng hôn nhân, nộp tại UBND cấp xã',
        'standard'
    ];
    const note = [
        '⚠️ LƯU Ý: Các giá trị hợp lệ cho LLM Judge:',
        '',
        '',
        'standard (Tiêu chí Chuẩn)',
        'strict (Tiêu chí Nghiêm ngặt)',
        'flexible (Tiêu chí Linh hoạt)'
    ];
    const note2 = [
        '',
        '',
        '',
        'content-only (Tiêu chí Nội dung)',
        'ux-focused (Tiêu chí Trải nghiệm)',
        ''
    ];

    const ws = XLSX.utils.aoa_to_sheet([headers, sample, [], note, note2]);

    // Độ rộng cột
    ws['!cols'] = [{ wch: 35 }, { wch: 12 }, { wch: 16 }, { wch: 45 }, { wch: 60 }, { wch: 20 }];

    // Highlight dòng header (row 1) — nền vàng, chữ đậm
    const headerCells = ['A1', 'B1', 'C1', 'D1', 'E1', 'F1'];
    headerCells.forEach(ref => {
        if (!ws[ref]) return;
        ws[ref].s = {
            fill: { patternType: 'solid', fgColor: { rgb: 'FFF59D' } },
            font: { bold: true, sz: 11 },
            alignment: { horizontal: 'center', vertical: 'center', wrapText: true },
            border: {
                bottom: { style: 'medium', color: { rgb: 'F9A825' } },
            },
        };
    });

    // Style cho dòng note (row 4)
    if (ws['A4']) {
        ws['A4'].s = {
            font: { bold: true, color: { rgb: 'D32F2F' }, sz: 10 },
            alignment: { horizontal: 'left', vertical: 'center' }
        };
    }

    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Testcases');

    const buf = XLSX.write(wb, { type: 'buffer', bookType: 'xlsx', cellStyles: true });

    res.setHeader('Content-Disposition', 'attachment; filename="testcase_mau.xlsx"');
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.send(buf);
});

module.exports = router;
