import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from app.ingest import ingest_documents
from app.bot import run_bot

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

bot_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager untuk menjalankan bot Telegram di background polling."""
    global bot_task
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if telegram_token and telegram_token != "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.info("Memulai Telegram Bot polling task...")
        bot_task = asyncio.create_task(run_bot())
    else:
        logger.warning("TELEGRAM_BOT_TOKEN belum diatur. Bot polling tidak dijalankan.")
    
    yield
    
    if bot_task and not bot_task.done():
        logger.info("Menghentikan Telegram Bot task...")
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Desa Wisata Lembah Asri - AI Assistant Service",
    description="Backend service FastAPI & runner bot Telegram untuk Desa Wisata Lembah Asri",
    version="0.1.0",
    lifespan=lifespan,
)


class IngestResponse(BaseModel):
    status: str
    message: str


@app.get("/health", tags=["System"])
async def health_check():
    """Endpoint health check untuk memverifikasi kesiapan service."""
    return {
        "status": "ok",
        "service": "desa-desawisata",
        "version": "0.1.0",
    }


@app.post("/ingest", response_model=IngestResponse, tags=["RAG"])
async def trigger_ingest(background_tasks: BackgroundTasks):
    """Endpoint untuk memicu proses ingestion dokumen PDF ke ChromaDB."""
    docs_dir = os.getenv("DOCS_DIR", "docs")
    chroma_path = os.getenv("CHROMA_PATH", "chroma_data")
    
    background_tasks.add_task(ingest_documents, docs_dir=docs_dir, chroma_path=chroma_path)
    return IngestResponse(
        status="accepted",
        message="Proses ingestion dokumen PDF ke ChromaDB telah dijadwalkan di background task."
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
