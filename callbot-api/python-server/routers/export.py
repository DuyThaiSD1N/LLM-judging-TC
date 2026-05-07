"""
Export Excel router - Xuất testcases ra Excel
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from io import BytesIO
from datetime import datetime

from models.schemas import ExportRequest


router = APIRouter()


@router.post("/export")
async def export_testcases(request: ExportRequest):
    """
    Xuất testcases + kết quả ra Excel
    
    POST /api/export
    Body: { testcases: [...] }
    """
    if not request.testcases:
        raise HTTPException(status_code=400, detail="Không có testcase nào để xuất")
    
    try:
        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Testcases"
        
        # Headers - SAME ORDER AS TEMPLATE
        headers = [
            "Tên Testcase", "Mã TC", "Câu hỏi từ User", "Câu trả lời kỳ vọng",
            "Từ khóa BẮT BUỘC", "Từ khóa CẤM", "LLM Judge", "Bot URL",
            "Lượt", "Câu trả lời thực tế", "Thời gian (ms)", "Kết quả",
            "Lỗi", "Đề xuất sửa", "Mẫu đề xuất", "Nhận xét giọng điệu"
        ]
        ws.append(headers)
        
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
        
        # Criteria names mapping
        criteria_names = {
            "standard": "Chuẩn",
            "strict": "Nghiêm ngặt",
            "speed-focused": "Tốc độ",
            "content-only": "Nội dung",
            "ux-focused": "Trải nghiệm"
        }
        
        # Data rows
        for tc in request.testcases:
            criteria_display = criteria_names.get(tc.criteria, tc.criteria)
            bot_url_display = tc.bot_url if tc.bot_url else "mặc định"
            
            for idx, turn in enumerate(tc.turns):
                # Get keywords for this turn
                required_kw = getattr(turn, 'required_keywords', '') or ''
                forbidden_kw = getattr(turn, 'forbidden_keywords', '') or ''
                
                row = [
                    tc.name,
                    tc.code,
                    turn.question,
                    turn.expected,
                    required_kw,
                    forbidden_kw,
                    criteria_display,
                    bot_url_display,
                    f"Lượt {idx + 1}",
                    turn.actual or "",
                    turn.response_time_ms or "",
                    turn.verdict or "",
                    turn.error_desc or "",
                    turn.suggestion or "",
                    turn.suggested_response or "",
                    turn.tone_note or ""
                ]
                ws.append(row)
        
        # Column widths - SAME ORDER AS TEMPLATE
        column_widths = [35, 12, 45, 60, 30, 30, 15, 35, 10, 40, 12, 10, 40, 40, 40, 40]
        for idx, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + idx)].width = width
        
        # Style verdict cells (PASSED = green, FAILED = red) - Column L (12)
        passed_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        passed_font = Font(color="006100", bold=True)
        failed_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        failed_font = Font(color="9C0006", bold=True)
        
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=12, max_col=12):
            cell = row[0]
            if cell.value == "PASSED":
                cell.fill = passed_fill
                cell.font = passed_font
            elif cell.value == "FAILED":
                cell.fill = failed_fill
                cell.font = failed_font
        
        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"testcases_{timestamp}.xlsx"
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
