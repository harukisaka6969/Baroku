from sqlalchemy import Column, Integer, String, BigInteger, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Horse(Base):
    __tablename__ = "horses"

    id = Column(Integer, primary_key=True, index=True)
    netkeiba_id = Column(String, index=True, unique=True, nullable=True)
    name = Column(String, index=True, nullable=False)
    name_en = Column(String)
    born_year = Column(Integer)
    sex = Column(String)
    color = Column(String)
    status = Column(String)
    farm = Column(String)
    birthplace = Column(String)
    trainer = Column(String)
    stable = Column(String)
    owner = Column(String)
    jockey = Column(String)
    sire = Column(String)
    dam = Column(String)
    sire_of_sire = Column(String)
    dam_of_sire = Column(String)
    sire_of_dam = Column(String)
    dam_of_dam = Column(String)
    best_time = Column(String)
    best_distance = Column(String)
    best_race = Column(String)
    earnings = Column(BigInteger, default=0)
    g1_wins = Column(Integer, default=0)
    win_rate = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    places = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    races = relationship("Race", back_populates="horse", cascade="all, delete-orphan")
    titles = relationship("Title", back_populates="horse", cascade="all, delete-orphan")


class Race(Base):
    __tablename__ = "races"

    id = Column(Integer, primary_key=True, index=True)
    horse_id = Column(Integer, ForeignKey("horses.id"), nullable=False)
    date = Column(String)
    race_name = Column(String)
    grade = Column(String)
    position = Column(Integer)
    jockey = Column(String)
    time = Column(String)
    distance = Column(String)
    course = Column(String)
    prize = Column(BigInteger, default=0)

    horse = relationship("Horse", back_populates="races")


class Title(Base):
    __tablename__ = "titles"

    id = Column(Integer, primary_key=True, index=True)
    horse_id = Column(Integer, ForeignKey("horses.id"), nullable=False)
    title_name = Column(String)

    horse = relationship("Horse", back_populates="titles")


# JRA 競馬場（中央競馬のみ対象）
JRA_RACECOURSES = ["札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"]


class JraRace(Base):
    """JRA レース（開催情報）。"""
    __tablename__ = "jra_races"

    id = Column(Integer, primary_key=True, index=True)
    netkeiba_race_id = Column(String, index=True, unique=True, nullable=True)  # 結果取得時の参照用
    date = Column(String, nullable=False)            # YYYY-MM-DD
    racecourse = Column(String, nullable=False)       # 東京, 中山, ... (JRA_RACECOURSES のいずれか)
    race_number = Column(Integer)                     # 第何レース
    race_name = Column(String)
    grade = Column(String)                            # G1/G2/G3/OP/...
    surface = Column(String)                          # 芝 / ダート
    distance = Column(Integer)                        # メートル
    direction = Column(String)                        # 右 / 左
    track_condition = Column(String)                  # 良/稍重/重/不良
    weather = Column(String)
    weekly_budget = Column(Integer, default=5000)     # このレースに割り当て可能な週間予算(円)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    entries = relationship("RaceEntry", back_populates="race", cascade="all, delete-orphan")


class RaceEntry(Base):
    """レース出走馬の出走情報・調教情報・結果。"""
    __tablename__ = "race_entries"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("jra_races.id"), nullable=False)
    horse_id = Column(Integer, ForeignKey("horses.id"), nullable=False)

    post_position = Column(Integer)       # 枠番
    horse_number = Column(Integer)        # 馬番
    jockey = Column(String)               # 騎手（その馬のレギュラー騎手と異なる場合あり）
    weight_carried = Column(Float)        # 斤量(kg)
    horse_weight = Column(Integer)        # 馬体重(kg)
    horse_weight_diff = Column(Integer)   # 馬体重 増減

    # 調教（トレーニング）情報
    training_time = Column(Float)         # 調教の終い1F(200m)タイム(秒) — 小さいほど良い
    training_eval = Column(String)        # 調教評価 (A/B/C/D)

    # オッズ・人気（締切直前 or 確定後）
    odds_win = Column(Float)              # 単勝オッズ
    odds_place_low = Column(Float)        # 複勝オッズ(下限)
    odds_place_high = Column(Float)       # 複勝オッズ(上限)
    popularity = Column(Integer)          # 人気順

    # 結果（レース後に更新）
    result_position = Column(Integer)     # 着順 (null = 未確定)

    race = relationship("JraRace", back_populates="entries")
    horse = relationship("Horse")
