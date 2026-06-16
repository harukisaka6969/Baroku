from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RaceSchema(BaseModel):
    id: int
    date: Optional[str] = None
    race_name: Optional[str] = None
    grade: Optional[str] = None
    position: Optional[int] = None
    jockey: Optional[str] = None
    time: Optional[str] = None
    distance: Optional[str] = None
    course: Optional[str] = None
    prize: Optional[int] = None

    class Config:
        from_attributes = True


class TitleSchema(BaseModel):
    id: int
    title_name: str

    class Config:
        from_attributes = True


class HorseBase(BaseModel):
    name: str
    name_en: Optional[str] = None
    born_year: Optional[int] = None
    sex: Optional[str] = None
    color: Optional[str] = None
    status: Optional[str] = None
    farm: Optional[str] = None
    birthplace: Optional[str] = None
    trainer: Optional[str] = None
    stable: Optional[str] = None
    owner: Optional[str] = None
    jockey: Optional[str] = None
    sire: Optional[str] = None
    dam: Optional[str] = None
    sire_of_sire: Optional[str] = None
    dam_of_sire: Optional[str] = None
    sire_of_dam: Optional[str] = None
    dam_of_dam: Optional[str] = None
    best_time: Optional[str] = None
    best_distance: Optional[str] = None
    best_race: Optional[str] = None
    earnings: Optional[int] = 0
    g1_wins: Optional[int] = 0
    win_rate: Optional[int] = 0
    wins: Optional[int] = 0
    losses: Optional[int] = 0
    places: Optional[int] = 0


class HorseCreate(HorseBase):
    pass


class HorseListItem(HorseBase):
    id: int

    class Config:
        from_attributes = True


class HorseDetail(HorseBase):
    id: int
    races: List[RaceSchema] = []
    titles: List[TitleSchema] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PredictionRequest(BaseModel):
    horse_ids: List[int]
    race_id: Optional[int] = None
    mode: str  # "ultra_safe" | "safe" | "balanced" | "risky"
    budget: Optional[int] = None  # 軍資金（円）


class RecommendationItem(BaseModel):
    horse_id: int
    horse_name: str
    reason: str
    confidence: int  # 0-100
    stake: Optional[int] = None  # 推奨購入額（円）


class HorseScore(BaseModel):
    horse_id: int
    horse_name: str
    reason: str
    confidence: int  # 0-100


class PredictionResponse(BaseModel):
    ranking: List[HorseScore]
    recommendations: List[RecommendationItem]
    bet_type: str
    odds_range: str
    disclaimer: str


class RelatedHorsesResponse(BaseModel):
    same_farm: List[HorseListItem]
    same_trainer: List[HorseListItem]
    same_sire: List[HorseListItem]
