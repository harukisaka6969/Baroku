"""
血統・騎手・牧場・調教師・距離・コース・競馬場・調教タイムなどを
数値特徴量に変換する。

FEATURE_NAMES の順序はモデル学習時と推論時で必ず一致させること。
"""
import math
from datetime import datetime
from .encoders import Encoders, course_dist_key, surface_key

FEATURE_NAMES = [
    "win_rate",          # 通算勝率
    "g1_wins",           # G1勝利数（正規化）
    "win_ratio",         # 勝利割合
    "place_ratio",       # 複勝（3着内）割合
    "earnings_log",      # 獲得賞金（log正規化）
    "age",               # 馬齢（正規化）
    "sire_score",        # 血統（父）の複勝率エンコーディング
    "jockey_score",      # 騎手の複勝率エンコーディング
    "trainer_score",     # 調教師の複勝率エンコーディング
    "stable_score",      # 所属トレーニングセンター（美浦/栗東）の複勝率エンコーディング
    "farm_score",        # 生産牧場の複勝率エンコーディング
    "course_dist_score", # 競馬場×コース×距離適性
    "surface_score",     # 芝・ダート適性
    "training_score",    # 調教タイム評価
    "post_position",     # 枠番（正規化）
    "popularity_score",  # 人気（市場の評価）
    "weight_carried",    # 斤量（正規化）
    "weight_diff",       # 馬体重増減（正規化）
]

TRAINING_TIME_GOOD = 11.0   # 優秀な終い1Fタイム(秒)
TRAINING_TIME_BAD = 14.0    # 平凡な終い1Fタイム(秒)


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def training_score(training_time: float | None) -> float:
    if not training_time:
        return 0.5  # データなしは中立
    span = TRAINING_TIME_BAD - TRAINING_TIME_GOOD
    return _clamp((TRAINING_TIME_BAD - training_time) / span)


def horse_base_features(horse) -> dict:
    total = max((horse.wins or 0) + (horse.losses or 0) + (horse.places or 0), 1)
    current_year = datetime.now().year
    return {
        "win_rate": (horse.win_rate or 0) / 100,
        "g1_wins": min((horse.g1_wins or 0) / 10, 1.0),
        "win_ratio": (horse.wins or 0) / total,
        "place_ratio": ((horse.wins or 0) + (horse.places or 0)) / total,
        "earnings_log": math.log10((horse.earnings or 0) + 1) / 10,
        "age": _clamp(((current_year - (horse.born_year or current_year)) / 10)),
    }


def entry_feature_vector(entry, horse, race, encoders: Encoders) -> list[float]:
    """RaceEntry + Horse + JraRace -> 特徴ベクトル（FEATURE_NAMES の順）"""
    feats = horse_base_features(horse)
    feats["sire_score"] = encoders.score("sire", horse.sire)
    feats["jockey_score"] = encoders.score("jockey", entry.jockey or horse.jockey)
    feats["trainer_score"] = encoders.score("trainer", horse.trainer)
    feats["stable_score"] = encoders.score("stable", horse.stable)
    feats["farm_score"] = encoders.score("farm", horse.farm)
    feats["course_dist_score"] = encoders.score(
        "course_dist", course_dist_key(race.racecourse, race.surface, race.distance)
    )
    feats["surface_score"] = encoders.score("surface", surface_key(race.surface))
    feats["training_score"] = training_score(entry.training_time)
    feats["post_position"] = _clamp((entry.post_position or 4) / 8)
    feats["popularity_score"] = 1 / (entry.popularity or 8)
    feats["weight_carried"] = _clamp((entry.weight_carried or 56) / 60)
    feats["weight_diff"] = _clamp(((entry.horse_weight_diff or 0) + 20) / 40)

    return [feats[name] for name in FEATURE_NAMES]
