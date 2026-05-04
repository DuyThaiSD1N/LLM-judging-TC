"""
Template router - Xuất file Excel mẫu
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from io import BytesIO


router = APIRouter()


@router.get("/template")
async def get_template():
    """
    Xuất file Excel mẫu để nhập testcase
    
    GET /api/template
    """
    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Testcases"
    
    # Headers
    headers = [
        "Tên Testcase",
        "Mã Testcase",
        "Nhóm (A/B/C/D)",
        "Câu hỏi từ User",
        "Câu trả lời kỳ vọng",
        "LLM Judge (standard/strict/speed-focused/content-only/ux-focused)"
    ]
    ws.append(headers)
    
    # Sample data
    sample = [
        "Hỏi thủ tục đăng ký kết hôn",
        "TC-001",
        "A",
        "đăng ký kết hôn cần giấy tờ gì",
        "Cần CMND/CCCD và giấy xác nhận tình trạng hôn nhân, nộp tại UBND cấp xã",
        "standard"
    ]
    ws.append(sample)
    
    # Column widths
    column_widths = [35, 12, 16, 45, 60, 50]
    for idx, width in enumerate(column_widths, 1):
        ws.column_dimensions[chr(64 + idx)].width = width
    
    # Style header
    header_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    header_font = Font(bold=True, size=11)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = thin_border
    
    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=testcase_mau.xlsx"}
    )
