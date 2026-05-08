"""
Upload Excel router - Import testcases từ Excel với hỗ trợ merged cells
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
import openpyxl
from io import BytesIO

from models.schemas import UploadExcelResponse, TestcaseBase, Turn


router = APIRouter()


def parse_excel_with_merged_cells(file_content: bytes):
    """
    Đọc Excel và xử lý merged cells
    Các dòng có cùng Mã TC (merged cells) sẽ được gộp thành 1 testcase với nhiều turns
    
    Returns:
        List[dict]: Danh sách testcases đã group theo Mã TC
    """
    workbook = openpyxl.load_workbook(BytesIO(file_content))
    sheet = workbook.active
    
    # Get all rows
    all_rows = []
    for row in sheet.iter_rows(values_only=False):  # Get cell objects, not just values
        if row and any(cell.value for cell in row if cell.value):
            all_rows.append(row)
    
    if len(all_rows) < 2:
        return []
    
    # Header row (skip it)
    data_rows = all_rows[1:]
    
    # Parse data with merged cell handling
    testcases_dict = {}  # {tc_code: {name, code, criteria, bot_url, turns: []}}
    
    last_name = None
    last_code = None
    last_executor = None  # NEW: Track executor for merged cells
    last_criteria = None
    last_bot_url = None
    last_scenario = None  # NEW: Track scenario for merged cells
    
    for row_idx, row in enumerate(data_rows):
        # Extract values from cells
        name = row[0].value if len(row) > 0 else None
        code = row[1].value if len(row) > 1 else None
        executor = row[2].value if len(row) > 2 else None  # NEW: Người thực hiện
        scenario = row[3].value if len(row) > 3 else None  # Setup lịch sử (shift +1)
        question = row[4].value if len(row) > 4 else None
        expected = row[5].value if len(row) > 5 else None
        required_keywords = row[6].value if len(row) > 6 else None
        forbidden_keywords = row[7].value if len(row) > 7 else None
        criteria = row[8].value if len(row) > 8 else None
        bot_url = row[9].value if len(row) > 9 else None
        
        # Handle merged cells: if value is None, use last value
        if name is None or str(name).strip() == "":
            name = last_name
        else:
            last_name = name
            
        if code is None or str(code).strip() == "":
            code = last_code
        else:
            last_code = code

        if executor is None or str(executor).strip() == "":
            executor = last_executor  # Inherit executor from previous row
        else:
            last_executor = executor  # Update last_executor
            
        if scenario is None or str(scenario).strip() == "":
            scenario = last_scenario  # NEW: Inherit scenario from previous row
        else:
            last_scenario = scenario  # NEW: Update last_scenario
            
        if criteria is None or str(criteria).strip() == "":
            criteria = last_criteria
        else:
            last_criteria = criteria
            
        if bot_url is None or str(bot_url).strip() == "":
            bot_url = last_bot_url
        else:
            last_bot_url = bot_url
        
        # Skip if essential fields are missing
        if not code or not question or not expected:
            print(f"⚠️ Skipping row {row_idx + 2}: Missing essential fields")
            continue
        
        # Normalize values
        code = str(code).strip()
        name = str(name).strip() if name else code
        executor = str(executor).strip() if executor and str(executor).strip() else None  # NEW
        scenario = str(scenario).strip() if scenario and str(scenario).strip() else None  # NEW
        question = str(question).strip()
        expected = str(expected).strip()
        required_keywords = str(required_keywords).strip() if required_keywords and str(required_keywords).strip() else None
        forbidden_keywords = str(forbidden_keywords).strip() if forbidden_keywords and str(forbidden_keywords).strip() else None
        criteria = str(criteria).strip().lower() if criteria else "standard"
        bot_url = str(bot_url).strip() if bot_url and str(bot_url).strip() else None
        
        # Group by code
        if code not in testcases_dict:
            testcases_dict[code] = {
                "name": name,
                "code": code,
                "executor": executor,  # NEW: Người thực hiện
                "criteria": criteria,
                "bot_url": bot_url,
                "turns": []
            }
        
        # Add turn
        testcases_dict[code]["turns"].append({
            "scenario": scenario,  # NEW
            "question": question,
            "expected": expected,
            "required_keywords": required_keywords,
            "forbidden_keywords": forbidden_keywords
        })
    
    # Convert dict to list
    testcases = list(testcases_dict.values())
    
    print(f"📊 Parsed {len(testcases)} testcases from Excel:")
    for tc in testcases:
        print(f"  - {tc['code']}: {tc['name']} ({len(tc['turns'])} turns)")
    
    return testcases


@router.post("/upload-excel", response_model=UploadExcelResponse)
async def upload_excel(file: UploadFile = File(...)):
    """
    Upload Excel file và parse thành testcases
    
    HỖ TRỢ MERGED CELLS:
    - Các dòng có cùng Mã TC (ô gộp) sẽ được gộp thành 1 testcase với nhiều turns
    - Mỗi dòng = 1 lượt hội thoại (1 turn)
    
    FORMAT EXCEL:
    | Tên TC | Mã TC | Setup lịch sử | Câu hỏi | Yêu cầu kỳ vọng | Từ khóa BẮT BUỘC | Từ khóa CẤM | LLM Judge | Bot URL |
    |--------|-------|---------------|---------|-----------------|-------------------|-------------|-----------|---------|
    | Hỏi vợ | TC-001| [user]Q1\n[assistant]A1 | Q2 | A2 | keyword1 | keyword2 | standard | http... |
    |        |       |               | Q3      | A3      |           |         |           |         |  <- Merged cells
    
    LƯU Ý: Setup lịch sử - Bot chỉ nhận câu hỏi [user] để warmup, [assistant] chỉ để tham khảo
    
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
        
        # Parse with merged cell support
        testcases_data = parse_excel_with_merged_cells(content)
        
        if not testcases_data:
            raise HTTPException(status_code=400, detail="File Excel không có dữ liệu testcase hợp lệ")
        
        # Validate criteria
        valid_criteria = ["standard", "strict", "speed-focused", "content-only", "ux-focused"]
        for tc in testcases_data:
            if tc["criteria"] not in valid_criteria:
                raise HTTPException(
                    status_code=400,
                    detail=f"Testcase {tc['code']}: LLM Judge '{tc['criteria']}' không hợp lệ. "
                           f"Chỉ chấp nhận: {', '.join(valid_criteria)}"
                )
        
        # Convert to Pydantic models
        testcases = []
        for tc in testcases_data:
            turns = [
                Turn(
                    scenario=turn.get("scenario"),  # NEW
                    question=turn["question"],
                    expected=turn["expected"],
                    required_keywords=turn.get("required_keywords"),
                    forbidden_keywords=turn.get("forbidden_keywords")
                )
                for turn in tc["turns"]
            ]
            
            testcases.append(
                TestcaseBase(
                    code=tc["code"],
                    name=tc["name"],
                    group="GENERAL",
                    turns=turns,
                    criteria=tc["criteria"],
                    bot_url=tc["bot_url"],
                    executor=tc.get("executor")  # NEW: Người thực hiện
                )
            )
        
        print(f"✅ Successfully parsed {len(testcases)} testcases with {sum(len(tc.turns) for tc in testcases)} total turns")
        return UploadExcelResponse(testcases=testcases)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error parsing Excel: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý file Excel: {str(e)}")
