"""
予想モデルへの入力特徴量を組み立てる。

血統（父系の傾向）・騎手・調教師・管理牧場・コース実績 を
「同じ条件を持つ他の馬たちの平均勝率」として数値化（ターゲットエンコーディング）し、
基礎成績（勝率・安定感・G1実績）と合わせて特徴量ベクトルを作る。

データが増えるほど各カテゴリの平均値が実態に近づき、モデルの精度も向上する。
"""
import numpy as np
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models

FEATURE_NAMES = [
    "win_rate",       # 勝率
    "stability",      # 安定感（勝率 = 勝利数 / 総レース数）
    "pedigree_g1",    # 血統・実績（G1勝利数）
    "sire_score",     # 血統（父の産駒の平均勝率）
    "jockey_score",   # 騎手（同騎手の担当馬の平均勝率）
    "trainer_score",  # 調教師（同厩舎の管理馬の平均勝率）
    "farm_score",     # 管理牧場（同牧場の生産馬の平均勝率）
    "course_form",    # 競馬場のコース実績（複勝率）
]

INPUT_DIM = len(FEATURE_NAMES)


def _peer_avg_win_rate(db: Session, column, value, exclude_id: int):
    """同じ value を持つ他の馬の平均勝率（0-100）。該当馬がいなければ None。"""
    if not value:
        return None
    avg = (
        db.query(func.avg(models.Horse.win_rate))
        .filter(column == value, models.Horse.id != exclude_id)
        .scalar()
    )
    return float(avg) if avg is not None else None


def build_features(db: Session, horse: models.Horse) -> np.ndarray:
    own_win_rate = (horse.win_rate or 0) / 100

    total_races = horse.wins + horse.losses
    stability = (horse.wins / total_races) if total_races > 0 else 0.5

    pedigree_g1 = min((horse.g1_wins or 0) / 10, 1.0)

    sire_avg = _peer_avg_win_rate(db, models.Horse.sire, horse.sire, horse.id)
    jockey_avg = _peer_avg_win_rate(db, models.Horse.jockey, horse.jockey, horse.id)
    trainer_avg = _peer_avg_win_rate(db, models.Horse.trainer, horse.trainer, horse.id)
    farm_avg = _peer_avg_win_rate(db, models.Horse.farm, horse.farm, horse.id)

    # 同条件のデータがまだ無ければ、自身の勝率で代用（データ蓄積で徐々に上書きされる）
    sire_score = (sire_avg / 100) if sire_avg is not None else own_win_rate
    jockey_score = (jockey_avg / 100) if jockey_avg is not None else own_win_rate
    trainer_score = (trainer_avg / 100) if trainer_avg is not None else own_win_rate
    farm_score = (farm_avg / 100) if farm_avg is not None else own_win_rate

    races_with_position = [r for r in horse.races if r.position is not None]
    if races_with_position:
        course_form = sum(1 for r in races_with_position if r.position <= 3) / len(races_with_position)
    else:
        course_form = 0.5

    return np.array([
        own_win_rate,
        stability,
        pedigree_g1,
        sire_score,
        jockey_score,
        trainer_score,
        farm_score,
        course_form,
    ], dtype=float)
