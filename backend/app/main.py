from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

from .database import engine
from . import models
from .routers import horses, prediction

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="馬録 API", version="0.1.0")

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
