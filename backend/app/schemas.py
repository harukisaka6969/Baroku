from pydantic import BaseModel, ConfigDict
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
    mode: str  # "safe" | "balanced" | "risky"


class RecommendationItem(BaseModel):
    horse_id: int
    horse_name: str
    reason: str
    confidence: int  # 0-100


class PredictionResponse(BaseModel):
    recommendations: List[RecommendationItem]
    bet_type: str
    odds_range: str
    disclaimer: str


class RelatedHorsesResponse(BaseModel):
    same_farm: List[HorseListItem]
    same_trainer: List[HorseListItem]
    same_sire: List[HorseListItem]


# ── JRA レース・出走情報 ──────────────────────────────────────────────────

class RaceEntryCreate(BaseModel):
    horse_id: int
    post_position: Optional[int] = None
    horse_number: Optional[int] = None
    jockey: Optional[str] = None
    weight_carried: Optional[float] = None
    horse_weight: Optional[int] = None
    horse_weight_diff: Optional[int] = None
    training_time: Optional[float] = None
    training_eval: Optional[str] = None
    odds_win: Optional[float] = None
    odds_place_low: Optional[float] = None
    odds_place_high: Optional[float] = None
    popularity: Optional[int] = None
    result_position: Optional[int] = None


class RaceEntrySchema(RaceEntryCreate):
    id: int
    horse_name: Optional[str] = None

    class Config:
        from_attributes = True


class JraRaceCreate(BaseModel):
    date: str
    racecourse: str
    race_number: Optional[int] = None
    race_name: Optional[str] = None
    grade: Optional[str] = None
    surface: Optional[str] = None
    distance: Optional[int] = None
    direction: Optional[str] = None
    track_condition: Optional[str] = None
    weather: Optional[str] = None
    weekly_budget: Optional[int] = 5000
    entries: List[RaceEntryCreate] = []


class JraRaceSchema(BaseModel):
    id: int
    date: str
    racecourse: str
    race_number: Optional[int] = None
    race_name: Optional[str] = None
    grade: Optional[str] = None
    surface: Optional[str] = None
    distance: Optional[int] = None
    direction: Optional[str] = None
    track_condition: Optional[str] = None
    weather: Optional[str] = None
    weekly_budget: Optional[int] = None
    entries: List[RaceEntrySchema] = []

    class Config:
        from_attributes = True


class RaceResultsUpdate(BaseModel):
    """entry_id -> 着順 のマップでレース結果を確定する"""
    results: dict[int, int]


# ── 予測・買い方提案 ──────────────────────────────────────────────────────

class HorsePredictionSchema(BaseModel):
    horse_id: int
    horse_number: Optional[int] = None
    horse_name: str
    p_win: float
    p_place: float
    odds_win: Optional[float] = None
    odds_place: Optional[float] = None


class BettingTicketSchema(BaseModel):
    bet_type: str
    target: str
    stake: int
    odds: Optional[float] = None
    probability: float
    expected_return: int
    reason: str


class BettingPlanSchema(BaseModel):
    tickets: List[BettingTicketSchema]
    total_stake: int
    unallocated: int
    expected_value: float
    note: str


class RacePredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    race_id: int
    race_name: Optional[str] = None
    racecourse: str
    date: str
    model_status: str  # "trained" | "heuristic"
    predictions: List[HorsePredictionSchema]
    plan: BettingPlanSchema
    disclaimer: str


class WeeklyPlanRaceItem(BaseModel):
    race_id: int
    race_name: Optional[str] = None
    racecourse: str
    date: str
    predictions: List[HorsePredictionSchema]
    plan: BettingPlanSchema


class WeeklyPlanResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    weekly_budget: int
    total_stake: int
    races: List[WeeklyPlanRaceItem]
    model_status: str
    disclaimer: str


class TrainResultSchema(BaseModel):
    trained: bool
    samples: int
    min_samples: Optional[int] = None
    reason: Optional[str] = None
