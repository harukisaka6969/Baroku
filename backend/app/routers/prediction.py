from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
import random

router = APIRouter(prefix="/prediction", tags=["prediction"])

DISCLAIMER = "本予想はアルゴリズムによる参考情報であり、的中を保証するものではありません。馬券の購入は自己責任で行ってください。当サイトは一切の損害について責任を負いません。18歳未満の方の利用はお断りします。"

WEIGHTS = {
    "safe":     {"win_rate": 0.40, "stability": 0.30, "pedigree": 0.20, "dark_horse": 0.00, "course": 0.10},
    "balanced": {"win_rate": 0.30, "stability": 0.20, "pedigree": 0.20, "dark_horse": 0.15, "course": 0.15},
    "risky":    {"win_rate": 0.10, "stability": 0.05, "pedigree": 0.20, "dark_horse": 0.40, "course": 0.25},
}

BET_TYPES = {
    "safe": "単勝 / 複勝",
    "balanced": "馬連 / ワイド",
    "risky": "三連複 / 馬単",
}

ODDS_RANGES = {
    "safe": "1.2〜3.0倍",
    "balanced": "5〜20倍",
    "risky": "30〜200倍",
}

REASONS = {
    "safe": ["勝率の高さと安定感が光る", "過去の実績から本命視", "調教師の腕と安定した成績"],
    "balanced": ["血統の底力に期待", "直近の成績から上昇気配", "コース適性が高い"],
    "risky": ["人気薄での一発に期待", "前走からの巻き返し候補", "穴馬として大穴を狙う"],
}


@router.post("", response_model=schemas.PredictionResponse)
def generate_prediction(
    request: schemas.PredictionRequest,
    db: Session = Depends(get_db),
):
    if request.mode not in WEIGHTS:
        raise HTTPException(status_code=400, detail="mode must be 'safe', 'balanced', or 'risky'")

    horses = db.query(models.Horse).filter(models.Horse.id.in_(request.horse_ids)).all()
    if not horses:
        raise HTTPException(status_code=404, detail="No horses found for given IDs")

    w = WEIGHTS[request.mode]
    scored = []
    for horse in horses:
        total_races = max(horse.wins + horse.losses, 1)
        win_score = (horse.win_rate / 100) * w["win_rate"] * 100
        stability = (horse.wins / total_races) * w["stability"] * 100
        pedigree = min(horse.g1_wins / 10, 1.0) * w["pedigree"] * 100
        dark_horse = (1 - horse.win_rate / 100) * w["dark_horse"] * 100
        course = random.random() * w["course"] * 100
        total = win_score + stability + pedigree + dark_horse + course
        confidence = min(int(total), 98)

        reason = random.choice(REASONS[request.mode])
        scored.append((horse, confidence, reason))

    scored.sort(key=lambda x: x[1], reverse=True)
    limit = 2 if request.mode == "safe" else 3 if request.mode == "balanced" else 5
    top = scored[:limit]

    recommendations = [
        schemas.RecommendationItem(
            horse_id=h.id,
            horse_name=h.name,
            reason=reason,
            confidence=confidence,
        )
        for h, confidence, reason in top
    ]

    return schemas.PredictionResponse(
        recommendations=recommendations,
        bet_type=BET_TYPES[request.mode],
        odds_range=ODDS_RANGES[request.mode],
        disclaimer=DISCLAIMER,
    )
