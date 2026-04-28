# routers/upload.py — import Excel + AI parse testcase

import json
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from openai import AsyncOpenAI
import openpyxl

router = APIRouter()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def parse_excel(content: bytes) -> list[list]:
    from io import BytesIO
    wb   = openpyxl.load_workbook(BytesIO(content), data_only=True)
    ws   = wb.active
    rows = []
    for row in ws.iter_rows(values_only=True):
        rows.append([str(c) if c is not None else "" for c in row])
    return rows


async def map_with_ai(rows: list[list]) -> list[dict]:
    table_text = "\n".join(f"Row {i}: {' | '.join(r)}" for i, r in enumerate(rows))

    prompt = f"""Bạn nhận được dữ liệu từ file Excel (mỗi dòng cách nhau bởi |).
Hãy phân tích và trích xuất thành danh sách testcase theo định dạng JSON.

Mỗi testcase gồm:
- "name": Tên testcase
- "code": Mã testcase (dạng TC-XXX)
- "group": Mã kịch bản, chỉ được là một trong: "A", "B", "C", "D"
- "turns": mảng các lượt hỏi, mỗi lượt gồm "question" và "expected"
  (nếu cùng mã TC có nhiều dòng thì gộp thành nhiều turns)

Nếu một trường không tìm thấy, để chuỗi rỗng "".
Chỉ trả về JSON object với key "testcases", không giải thích thêm.

Dữ liệu Excel:
{table_text}"""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    parsed = json.loads(response.choices[0].message.content)
    if isinstance(parsed, list):
        return parsed
    for v in parsed.values():
        if isinstance(v, list):
            return v
    return []


@router.post("/upload-excel")
async def upload_excel(file: UploadFile = File(...)):
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("xlsx", "xls"):
        raise HTTPException(400, "Chỉ chấp nhận file .xlsx hoặc .xls")

    content   = await file.read()
    rows      = parse_excel(content)
    testcases = await map_with_ai(rows)
    return {"testcases": testcases}
