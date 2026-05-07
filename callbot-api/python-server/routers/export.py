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
            "Tên Testcase", "Mã TC", "Setup lịch sử", "Câu hỏi từ User", "Yêu cầu kỳ vọng",
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
        
        # Data rows - xử lý dict thay vì object
        for tc in request.testcases:
            criteria_display = criteria_names.get(tc.get('criteria', 'standard'), tc.get('criteria', 'standard'))
            bot_url_display = tc.get('bot_url') if tc.get('bot_url') else "mặc định"
            
            turns = tc.get('turns', [])
            for idx, turn in enumerate(turns):
                # Lấy tất cả fields, hỗ trợ cả Turn và TurnResult
                scenario = turn.get('scenario', '') or ''  # NEW
                required_kw = turn.get('required_keywords', '') or ''
                forbidden_kw = turn.get('forbidden_keywords', '') or ''
                actual = turn.get('actual', '') or ''
                response_time = turn.get('response_time_ms', '') or ''
                verdict = turn.get('verdict', '') or ''
                error_desc = turn.get('error_desc', '') or ''
                suggestion = turn.get('suggestion', '') or ''
                suggested_response = turn.get('suggested_response', '') or ''
                tone_note = turn.get('tone_note', '') or ''
                
                row = [
                    tc.get('name', ''),
                    tc.get('code', ''),
                    scenario,  # NEW
                    turn.get('question', ''),
                    turn.get('expected', ''),
                    required_kw,
                    forbidden_kw,
                    criteria_display,
                    bot_url_display,
                    f"Lượt {idx + 1}",
                    actual,
                    response_time,
                    verdict,
                    error_desc,
                    suggestion,
                    suggested_response,
                    tone_note
                ]
                ws.append(row)
        
        # Column widths - SAME ORDER AS TEMPLATE
        column_widths = [35, 12, 50, 45, 60, 30, 30, 15, 35, 10, 40, 12, 10, 40, 40, 40, 40]
        for idx, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + idx)].width = width
        
        # Style verdict cells (PASSED = green, FAILED = red) - Column M (13) - shifted by 1
        passed_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        passed_font = Font(color="006100", bold=True)
        failed_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        failed_font = Font(color="9C0006", bold=True)
        
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=13, max_col=13):
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
