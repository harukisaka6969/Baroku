from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/horses", tags=["horses"])


@router.get("", response_model=List[schemas.HorseListItem])
def list_horses(
    q: Optional[str] = Query(None),
    sex: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    farm: Optional[str] = Query(None),
    sire: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(models.Horse)

    if q:
        query = query.filter(
            or_(
                models.Horse.name.contains(q),
                models.Horse.name_en.ilike(f"%{q}%"),
                models.Horse.trainer.contains(q),
                models.Horse.farm.contains(q),
            )
        )
    if sex:
        query = query.filter(models.Horse.sex == sex)
    if status:
        query = query.filter(models.Horse.status == status)
    if farm:
        query = query.filter(models.Horse.farm == farm)
    if sire:
        query = query.filter(models.Horse.sire == sire)

    return query.all()


@router.get("/{horse_id}", response_model=schemas.HorseDetail)
def get_horse(horse_id: int, db: Session = Depends(get_db)):
    horse = db.query(models.Horse).filter(models.Horse.id == horse_id).first()
    if not horse:
        raise HTTPException(status_code=404, detail="Horse not found")
    return horse


@router.get("/{horse_id}/related", response_model=schemas.RelatedHorsesResponse)
def get_related_horses(horse_id: int, db: Session = Depends(get_db)):
    horse = db.query(models.Horse).filter(models.Horse.id == horse_id).first()
    if not horse:
        raise HTTPException(status_code=404, detail="Horse not found")

    same_farm = (
        db.query(models.Horse)
        .filter(models.Horse.farm == horse.farm, models.Horse.id != horse_id)
        .limit(5)
        .all()
    )
    same_trainer = (
        db.query(models.Horse)
        .filter(models.Horse.trainer == horse.trainer, models.Horse.id != horse_id)
        .limit(5)
        .all()
    )
    same_sire = (
        db.query(models.Horse)
        .filter(models.Horse.sire == horse.sire, models.Horse.id != horse_id)
        .limit(5)
        .all()
    )

    return {
        "same_farm": same_farm,
        "same_trainer": same_trainer,
        "same_sire": same_sire,
    }
