from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
import random

router = APIRouter(prefix="/prediction", tags=["prediction"])

DISCLAIMER = "本予想はアルゴリズムによる参考情報であり、的中を保証するものではありません。馬券の購入は自己責任で行ってください。当サイトは一切の損害について責任を負いません。18歳未満の方の利用はお断りします。"

WEIGHTS = {
    "ultra_safe": {"win_rate": 0.45, "stability": 0.35, "pedigree": 0.15, "dark_horse": 0.00, "course": 0.05},
    "safe":     {"win_rate": 0.40, "stability": 0.30, "pedigree": 0.20, "dark_horse": 0.00, "course": 0.10},
    "balanced": {"win_rate": 0.30, "stability": 0.20, "pedigree": 0.20, "dark_horse": 0.15, "course": 0.15},
    "risky":    {"win_rate": 0.10, "stability": 0.05, "pedigree": 0.20, "dark_horse": 0.40, "course": 0.25},
}

BET_TYPES = {
    "ultra_safe": "複勝（分散買い）",
    "safe": "単勝 / 複勝",
    "balanced": "馬連 / ワイド",
    "risky": "三連複 / 馬単",
}

ODDS_RANGES = {
    "ultra_safe": "1.0〜1.5倍",
    "safe": "1.2〜3.0倍",
    "balanced": "5〜20倍",
    "risky": "30〜200倍",
}

REASONS = {
    "ultra_safe": ["崩れない安定感で複勝圏内が濃厚", "堅実な人気馬で大きな波乱は考えにくい", "上位互換不在の鉄板評価"],
    "safe": ["勝率の高さと安定感が光る", "過去の実績から本命視", "調教師の腕と安定した成績"],
    "balanced": ["血統の底力に期待", "直近の成績から上昇気配", "コース適性が高い"],
    "risky": ["人気薄での一発に期待", "前走からの巻き返し候補", "穴馬として大穴を狙う"],
}

# 推奨頭数（軍資金をこの頭数に分散配分する）
PICK_COUNTS = {"ultra_safe": 3, "safe": 2, "balanced": 3, "risky": 5}

BUDGET_UNIT = 100  # 馬券は100円単位


def allocate_budget(budget: int, count: int) -> list[int]:
    """軍資金を頭数で100円単位に分散。端数は1頭目に寄せる。"""
    n = max(1, count)
    base_units = (budget // BUDGET_UNIT) // n
    base = base_units * BUDGET_UNIT
    remainder = budget - base * n
    return [base + remainder if i == 0 else base for i in range(n)]


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
    limit = min(PICK_COUNTS.get(request.mode, len(scored)), len(scored))
    top = scored[:limit]

    stakes = allocate_budget(request.budget, limit) if request.budget else [None] * limit

    recommendations = [
        schemas.RecommendationItem(
            horse_id=h.id,
            horse_name=h.name,
            reason=reason,
            confidence=confidence,
            stake=stake,
        )
        for (h, confidence, reason), stake in zip(top, stakes)
    ]

    return schemas.PredictionResponse(
        recommendations=recommendations,
        bet_type=BET_TYPES[request.mode],
        odds_range=ODDS_RANGES[request.mode],
        disclaimer=DISCLAIMER,
    )
