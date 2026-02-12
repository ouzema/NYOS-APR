import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import engine, Base
from app.routers import chat, data, analytics, reports, generation

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NYOS APR",
    description="Pharmaceutical Quality Analysis Assistant - Advanced Analytics",
    version="2.0.0",
)

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:5174,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(data.router)
app.include_router(analytics.router)
app.include_router(reports.router)
app.include_router(generation.router)


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Serve frontend static files (production: built React app in /app/static)
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

static_dir = Path(__file__).parent.parent / "static"

if static_dir.exists():
    @app.get("/")
    async def serve_index():
        return FileResponse(str(static_dir / "index.html"))

    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
else:
    @app.get("/")
    async def root():
        return {"status": "NYOS APR API Running", "version": "2.0.0"}
