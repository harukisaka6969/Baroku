from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import os, asyncio, logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

from .database import engine, SessionLocal
from . import models
from .routers import horses, prediction
from .seed import seed_if_empty
from .ml.train import retrain

ADMIN_SECRET = os.getenv("ADMIN_SECRET", "")


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seeded = seed_if_empty(db)
        if seeded:
            logger.info("DB が空だったため初期データを投入しました")
        retrain(db)
    finally:
        db.close()
    yield


app = FastAPI(title="馬録 API", version="0.1.0", lifespan=lifespan)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(horses.router)
app.include_router(prediction.router)


@app.get("/")
def root():
    return {"message": "馬録 API", "version": "0.1.0"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/admin/scrape")
async def trigger_scrape(
    x_admin_secret: str = Header(default=""),
):
    """スクレイパーを手動実行してDBを更新する（ADMIN_SECRET が必要）。"""
    if ADMIN_SECRET and x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    from .scraper.run_scraper import run as run_scraper, DEFAULT_HORSE_IDS
    asyncio.create_task(run_scraper(DEFAULT_HORSE_IDS))
    return {"message": f"スクレイプ開始: {len(DEFAULT_HORSE_IDS)} 頭（バックグラウンド実行）"}
