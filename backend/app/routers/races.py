import os
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from ..database import get_db
from .. import models, schemas
from ..ml.predict import predict_race, reload_model
from ..ml.train import train_model
from ..betting.strategy import build_betting_plan, allocate_weekly_budget

router = APIRouter(prefix="/races", tags=["races"])

ADMIN_SECRET = os.getenv("ADMIN_SECRET", "")
DEFAULT_BUDGET = 5000

DISCLAIMER = (
    "本予想・買い方提案はアルゴリズムによる参考情報であり、的中や利益を保証するものではありません。"
    "馬券の購入は自己責任で行ってください。当サイトは一切の損害について責任を負いません。"
    "18歳未満の方の利用はお断りします。"
)


def _check_admin(x_admin_secret: str):
    if ADMIN_SECRET and x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")


def _serialize_race(race: models.JraRace) -> schemas.JraRaceSchema:
    return schemas.JraRaceSchema(
        id=race.id,
        date=race.date,
        racecourse=race.racecourse,
        race_number=race.race_number,
        race_name=race.race_name,
        grade=race.grade,
        surface=race.surface,
        distance=race.distance,
        direction=race.direction,
        track_condition=race.track_condition,
        weather=race.weather,
        weekly_budget=race.weekly_budget,
        entries=[
            schemas.RaceEntrySchema(
                id=e.id,
                horse_id=e.horse_id,
                horse_name=e.horse.name if e.horse else None,
                post_position=e.post_position,
                horse_number=e.horse_number,
                jockey=e.jockey,
                weight_carried=e.weight_carried,
                horse_weight=e.horse_weight,
                horse_weight_diff=e.horse_weight_diff,
                training_time=e.training_time,
                training_eval=e.training_eval,
                odds_win=e.odds_win,
                odds_place_low=e.odds_place_low,
                odds_place_high=e.odds_place_high,
                popularity=e.popularity,
                result_position=e.result_position,
            )
            for e in race.entries
        ],
    )


@router.get("", response_model=List[schemas.JraRaceSchema])
def list_races(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    racecourse: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(models.JraRace)
    if date_from:
        q = q.filter(models.JraRace.date >= date_from)
    if date_to:
        q = q.filter(models.JraRace.date <= date_to)
    if racecourse:
        q = q.filter(models.JraRace.racecourse == racecourse)
    races = q.order_by(models.JraRace.date, models.JraRace.race_number).all()
    return [_serialize_race(r) for r in races]


@router.get("/{race_id}", response_model=schemas.JraRaceSchema)
def get_race(race_id: int, db: Session = Depends(get_db)):
    race = db.query(models.JraRace).filter(models.JraRace.id == race_id).first()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    return _serialize_race(race)


@router.post("", response_model=schemas.JraRaceSchema)
def create_race(
    payload: schemas.JraRaceCreate,
    db: Session = Depends(get_db),
    x_admin_secret: str = Header(default=""),
):
    """JRAレースと出走表を登録する（要 ADMIN_SECRET）。中央競馬場のみ登録可能。"""
    _check_admin(x_admin_secret)

    if payload.racecourse not in models.JRA_RACECOURSES:
        raise HTTPException(
            status_code=400,
            detail=f"racecourse must be a JRA racecourse: {models.JRA_RACECOURSES}",
        )

    race = models.JraRace(
        date=payload.date,
        racecourse=payload.racecourse,
        race_number=payload.race_number,
        race_name=payload.race_name,
        grade=payload.grade,
        surface=payload.surface,
        distance=payload.distance,
        direction=payload.direction,
        track_condition=payload.track_condition,
        weather=payload.weather,
        weekly_budget=payload.weekly_budget or DEFAULT_BUDGET,
    )
    db.add(race)
    db.flush()

    for entry in payload.entries:
        horse = db.query(models.Horse).filter(models.Horse.id == entry.horse_id).first()
        if not horse:
            raise HTTPException(status_code=404, detail=f"Horse {entry.horse_id} not found")
        db.add(models.RaceEntry(race_id=race.id, **entry.model_dump()))

    db.commit()
    db.refresh(race)
    return _serialize_race(race)


@router.patch("/{race_id}/results", response_model=schemas.TrainResultSchema)
def update_results(
    race_id: int,
    payload: schemas.RaceResultsUpdate,
    db: Session = Depends(get_db),
    x_admin_secret: str = Header(default=""),
):
    """レース結果（着順）を確定し、モデルを再学習する（要 ADMIN_SECRET）。"""
    _check_admin(x_admin_secret)

    race = db.query(models.JraRace).filter(models.JraRace.id == race_id).first()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    for entry_id, position in payload.results.items():
        entry = db.query(models.RaceEntry).filter(
            models.RaceEntry.id == entry_id, models.RaceEntry.race_id == race_id
        ).first()
        if entry:
            entry.result_position = position

    db.commit()

    result = train_model(db)
    if result["trained"]:
        reload_model()
    return result


@router.get("/{race_id}/prediction", response_model=schemas.RacePredictionResponse)
def get_race_prediction(
    race_id: int,
    budget: int = Query(DEFAULT_BUDGET, ge=0, le=20000),
    db: Session = Depends(get_db),
):
    """レースの予測と、予算内での買い方を提案する。"""
    race = db.query(models.JraRace).filter(models.JraRace.id == race_id).first()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    if not race.entries:
        raise HTTPException(status_code=400, detail="このレースには出走馬が登録されていません")

    predictions, status = predict_race(db, race)
    plan = build_betting_plan(predictions, budget=budget)

    return schemas.RacePredictionResponse(
        race_id=race.id,
        race_name=race.race_name,
        racecourse=race.racecourse,
        date=race.date,
        model_status=status,
        predictions=[schemas.HorsePredictionSchema(**p) for p in predictions],
        plan=schemas.BettingPlanSchema(**plan),
        disclaimer=DISCLAIMER,
    )


@router.get("/weekly/plan", response_model=schemas.WeeklyPlanResponse)
def get_weekly_plan(
    date_from: str = Query(...),
    date_to: str = Query(...),
    budget: int = Query(DEFAULT_BUDGET, ge=0, le=20000),
    db: Session = Depends(get_db),
):
    """指定期間内のJRAレースに対し、週予算を配分した買い方プランを返す。"""
    races = (
        db.query(models.JraRace)
        .filter(models.JraRace.date >= date_from, models.JraRace.date <= date_to)
        .order_by(models.JraRace.date, models.JraRace.race_number)
        .all()
    )

    race_plans = []
    model_status = "heuristic"
    for race in races:
        if not race.entries:
            continue
        predictions, status = predict_race(db, race)
        if status == "trained":
            model_status = "trained"
        race_plans.append({
            "race_id": race.id,
            "race_name": race.race_name,
            "racecourse": race.racecourse,
            "date": race.date,
            "_predictions": predictions,
            "_combo_bets": None,
        })

    allocated = allocate_weekly_budget(race_plans, total_budget=budget)

    items = [
        schemas.WeeklyPlanRaceItem(
            race_id=rp["race_id"],
            race_name=rp["race_name"],
            racecourse=rp["racecourse"],
            date=rp["date"],
            predictions=[schemas.HorsePredictionSchema(**p) for p in rp["_predictions"]],
            plan=schemas.BettingPlanSchema(**rp["plan"]),
        )
        for rp in allocated
    ]
    total_stake = sum(item.plan.total_stake for item in items)

    return schemas.WeeklyPlanResponse(
        weekly_budget=budget,
        total_stake=total_stake,
        races=items,
        model_status=model_status,
        disclaimer=DISCLAIMER,
    )
