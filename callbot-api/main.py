"""
main.py — FastAPI entry point với LangChain + LangGraph + LangSmith
"""

import os
import sys
from pathlib import Path

# Add python-server to Python path
sys.path.insert(0, str(Path(__file__).parent / "python-server"))

from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")

# Setup LangSmith tracing (chỉ set nếu chưa có trong .env)
if not os.getenv("LANGCHAIN_TRACING_V2"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
if not os.getenv("LANGCHAIN_PROJECT"):
    os.environ["LANGCHAIN_PROJECT"] = "callbot-testcase-runner"
# LANGCHAIN_API_KEY should be in .env if you want to use LangSmith

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import routers
from routers import run, testcase, history, upload, template, export, comparison, criteria

# Initialize database
from config.database import init_db
init_db()

app = FastAPI(
    title="Callbot HCC Testcase API",
    description="API để chạy và đánh giá testcase cho chatbot hành chính công với LangChain + LangGraph",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

# ── API routes (phải đăng ký TRƯỚC static files) ─────────────────────────
app.include_router(run.router, prefix="/api", tags=["Run"])
app.include_router(testcase.router, prefix="/api", tags=["Testcase"])
app.include_router(history.router, prefix="/api", tags=["History"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(template.router, prefix="/api", tags=["Template"])
app.include_router(export.router, prefix="/api", tags=["Export"])
app.include_router(comparison.router, prefix="/api", tags=["Comparison"])
app.include_router(criteria.router, prefix="/api", tags=["Criteria"])

# ── Health check endpoint ─────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint cho Render"""
    from datetime import datetime
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "stack": "LangChain + LangGraph + LangSmith"
    }

# ── Serve frontend static files ───────────────────────────────────────────
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

class NoCacheMiddleware(BaseHTTPMiddleware):
    """Middleware to add no-cache headers for static files"""
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        # Add no-cache headers for JS/CSS files
        if request.url.path.endswith(('.js', '.css', '.html')):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response

# Add no-cache middleware
app.add_middleware(NoCacheMiddleware)

frontend_path = Path(__file__).parent / "testcase-form"

if frontend_path.exists():
    # Mount assets (css, js, images)
    app.mount("/css", StaticFiles(directory=str(frontend_path / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(frontend_path / "js")), name="js")
    app.mount("/assets", StaticFiles(directory=str(frontend_path / "assets")), name="assets")
    
    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(str(frontend_path / "index.html"))

# ── Startup event ─────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    """Startup event"""
    langsmith_key = os.getenv('LANGCHAIN_API_KEY', '')
    langsmith_key_display = f"{langsmith_key[:20]}..." if langsmith_key else "❌ Not Set"
    
    print("=" * 60)
    print("🚀 Callbot Testcase API v2.0.0")
    print("=" * 60)
    print(f"📍 Environment: {os.getenv('NODE_ENV', 'development')}")
    print(f"🔑 OpenAI API Key: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
    print(f"📊 LangSmith Tracing: {'✅ Enabled' if langsmith_key else '⚠️ Disabled (no API key)'}")
    print(f"📊 LangSmith Project: {os.getenv('LANGCHAIN_PROJECT', 'N/A')}")
    print(f"📊 LangSmith API Key: {langsmith_key_display}")
    print(f"🗄️ Database: {Path(__file__).parent / 'data' / 'testcases.db'}")
    print("=" * 60)
    print("🎯 Stack: LangChain + LangGraph + LangSmith")
    print("=" * 60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8099)),
        reload=True
    )
