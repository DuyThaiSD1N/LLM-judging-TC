"""
Upload Excel router - Import testcases từ Excel
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import openpyxl
import os
from io import BytesIO

from models.schemas import UploadExcelResponse, TestcaseBase, Turn


router = APIRouter()


def parse_excel(file_content: bytes):
    """Đọc Excel và trả về rows"""
    workbook = openpyxl.load_workbook(BytesIO(file_content))
    sheet = workbook.active
    
    rows = []
    for row in sheet.iter_rows(values_only=True):
        if row and any(cell for cell in row if cell):
            rows.append(list(row))
    
    return rows


def validate_excel_data(rows):
    """Validate dữ liệu Excel"""
    errors = []
    
    # Lọc bỏ các dòng trống
    filtered_rows = [row for row in rows if row and any(cell for cell in row if cell)]
    
    if not filtered_rows:
        return {"valid": False, "error": "File Excel trống hoặc không đọc được"}
    
    # Kiểm tra header
    header = filtered_rows[0]
    if len(header) < 5:
        return {
            "valid": False,
            "error": f"File Excel không đúng định dạng. Cần ít nhất 5 cột. Hiện tại chỉ có {len(header)} cột."
        }
    
    # Kiểm tra dữ liệu
    data_rows = filtered_rows[1:]
    if not data_rows:
        return {"valid": False, "error": "File Excel không có dữ liệu testcase nào"}
    
    # Validate từng dòng
    valid_groups = ["A", "B", "C", "D"]
    valid_criteria = ["standard", "strict", "speed-focused", "content-only", "ux-focused"]
    
    for idx, row in enumerate(data_rows):
        row_num = idx + 2
        name, code, group, question, expected = row[:5] if len(row) >= 5 else [None] * 5
        criteria = row[5] if len(row) > 5 else None
        
        if not name or str(name).strip() == "":
            errors.append(f"Dòng {row_num}: Thiếu 'Tên Testcase'")
        if not code or str(code).strip() == "":
            errors.append(f"Dòng {row_num}: Thiếu 'Mã Testcase'")
        if not group or str(group).strip() == "":
            errors.append(f"Dòng {row_num}: Thiếu 'Nhóm (A/B/C/D)'")
        elif str(group).strip().upper() not in valid_groups:
            errors.append(f"Dòng {row_num}: Nhóm '{group}' không hợp lệ. Chỉ chấp nhận: A, B, C, D")
        if not question or str(question).strip() == "":
            errors.append(f"Dòng {row_num}: Thiếu 'Câu hỏi từ User'")
        if not expected or str(expected).strip() == "":
            errors.append(f"Dòng {row_num}: Thiếu 'Câu trả lời kỳ vọng'")
        
        if criteria and str(criteria).strip():
            criteria_value = str(criteria).strip().lower()
            if criteria_value not in valid_criteria:
                errors.append(
                    f"Dòng {row_num}: LLM Judge '{criteria}' không hợp lệ. "
                    f"Chỉ chấp nhận: standard, strict, speed-focused, content-only, ux-focused"
                )
    
    if errors:
        error_msg = f"File Excel có {len(errors)} lỗi:\n" + "\n".join(errors[:5])
        if len(errors) > 5:
            error_msg += f"\n... và {len(errors) - 5} lỗi khác"
        return {"valid": False, "error": error_msg}
    
    return {"valid": True, "filtered_rows": filtered_rows}


async def map_with_ai(rows):
    """Gọi OpenAI để map dữ liệu Excel → testcase"""
    table_text = "\n".join([f"Row {i}: {' | '.join(str(c) for c in r)}" for i, r in enumerate(rows)])
    
    prompt = ChatPromptTemplate.from_messages([
        ("user", """
Bạn nhận được dữ liệu từ file Excel (mỗi dòng cách nhau bởi |).
Hãy phân tích và trích xuất thành danh sách testcase theo định dạng JSON.

Mỗi testcase gồm:
- "name": Tên testcase
- "code": Mã testcase (dạng TC-XXX)
- "group": Mã kịch bản, chỉ được là một trong: "A", "B", "C", "D"
- "question": Câu hỏi từ user
- "expected": Câu trả lời kỳ vọng
- "criteria": Tiêu chí LLM Judge (standard/strict/speed-focused/content-only/ux-focused). Nếu không có thì để "standard"

Nếu một trường không tìm thấy, để chuỗi rỗng "" (trừ criteria thì để "standard").
Trả về JSON với key "testcases" chứa array các testcase.

Dữ liệu Excel:
{table_text}
""")
    ])
    
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    parser = JsonOutputParser()
    chain = prompt | llm | parser
    
    result = await chain.ainvoke({"table_text": table_text})
    
    # Extract testcases array
    if isinstance(result, dict) and "testcases" in result:
        return result["testcases"]
    elif isinstance(result, list):
        return result
    else:
        # Find first array in result
        for key, value in result.items():
            if isinstance(value, list):
                return value
    
    return []


@router.post("/upload-excel", response_model=UploadExcelResponse)
async def upload_excel(file: UploadFile = File(...)):
    """
    Upload Excel file và parse thành testcases
    
    POST /api/upload-excel
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Không có file được gửi lên.")
    
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["xlsx", "xls"]:
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file .xlsx hoặc .xls")
    
    try:
        # Read file
        content = await file.read()
        rows = parse_excel(content)
        
        # Validate
        validation = validate_excel_data(rows)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=validation["error"])
        
        # Map with AI
        testcases_data = await map_with_ai(validation["filtered_rows"])
        
        # Convert to Pydantic models
        testcases = []
        for tc in testcases_data:
            testcases.append(
                TestcaseBase(
                    code=tc.get("code", ""),
                    name=tc.get("name", ""),
                    group=tc.get("group", "A"),
                    turns=[Turn(
                        question=tc.get("question", ""),
                        expected=tc.get("expected", "")
                    )],
                    criteria=tc.get("criteria", "standard")
                )
            )
        
        return UploadExcelResponse(testcases=testcases)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
