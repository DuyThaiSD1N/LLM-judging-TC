# main.py — FastAPI entry point

from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from routers import run, upload, template

app = FastAPI(title="Callbot HCC Testcase API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routes (phải đăng ký TRƯỚC static files) ─────────────────────────
app.include_router(run.router,      prefix="/api")
app.include_router(upload.router,   prefix="/api")
app.include_router(template.router, prefix="/api")

# ── Serve frontend static files ───────────────────────────────────────────
frontend_path = Path(__file__).parent.parent / "testcase-form"

if frontend_path.exists():
    # Mount assets (css, js) dưới /static để không đụng /api
    app.mount("/css", StaticFiles(directory=str(frontend_path / "css")), name="css")
    app.mount("/js",  StaticFiles(directory=str(frontend_path / "js")),  name="js")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(str(frontend_path / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8099, reload=True)
