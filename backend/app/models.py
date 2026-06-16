from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Horse(Base):
    __tablename__ = "horses"

    id = Column(Integer, primary_key=True, index=True)
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
    netkeiba_id = Column(String, unique=True, index=True)  # netkeibaの馬ID（重複検出・スキップ用）
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


class ModelWeights(Base):
    """予想モデル（ニューラルネット）の学習済み重みを保存するテーブル。"""
    __tablename__ = "model_weights"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    weights_json = Column(String, nullable=False)
    trained_samples = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
