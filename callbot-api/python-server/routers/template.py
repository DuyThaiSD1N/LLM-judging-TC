# routers/template.py — xuất file Excel mẫu (Times New Roman, header highlight)

from io import BytesIO
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

router = APIRouter()

HEADERS = ["Tên Testcase", "Mã Testcase", "Nhóm (A/B/C/D)", "Câu hỏi từ User", "Câu trả lời kỳ vọng"]
SAMPLE  = ["Hỏi thủ tục đăng ký kết hôn", "TC-001", "A",
           "đăng ký kết hôn cần giấy tờ gì",
           "Cần CMND/CCCD và giấy xác nhận tình trạng hôn nhân, nộp tại UBND cấp xã"]
COL_WIDTHS = [38, 14, 18, 48, 62]


@router.get("/template")
def download_template():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Testcases"

    # ── Style header ──────────────────────────────────────────────────────
    header_fill   = PatternFill("solid", fgColor="FFF59D")          # vàng nhạt
    header_font   = Font(name="Times New Roman", bold=True, size=11)
    header_border = Border(
        bottom=Side(style="medium", color="F9A825"),                 # cam đậm
        top=Side(style="thin", color="BDBDBD"),
        left=Side(style="thin", color="BDBDBD"),
        right=Side(style="thin", color="BDBDBD"),
    )
    header_align  = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws.append(HEADERS)
    for col_idx, cell in enumerate(ws[1], start=1):
        cell.fill      = header_fill
        cell.font      = header_font
        cell.border    = header_border
        cell.alignment = header_align
        ws.column_dimensions[get_column_letter(col_idx)].width = COL_WIDTHS[col_idx - 1]

    ws.row_dimensions[1].height = 28

    # ── Style dòng mẫu ────────────────────────────────────────────────────
    ws.append(SAMPLE)
    sample_font  = Font(name="Times New Roman", size=11)
    sample_align = Alignment(vertical="top", wrap_text=True)
    for cell in ws[2]:
        cell.font      = sample_font
        cell.alignment = sample_align

    ws.row_dimensions[2].height = 40

    # ── Xuất file ─────────────────────────────────────────────────────────
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=testcase_mau.xlsx"},
    )
