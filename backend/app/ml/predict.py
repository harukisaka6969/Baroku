"""
レースの出走表から各馬の「複勝(3着内)確率」「単勝(1着)確率」を予測する。

学習済みモデルがあればそれを使い、まだ学習データが少ない場合は
特徴量の重み付け合計による簡易ヒューリスティックにフォールバックする。
"""
from __future__ import annotations
import numpy as np

from .encoders import build_encoders
from .features import entry_feature_vector, FEATURE_NAMES
from .model import PredictionModel

_model_cache: PredictionModel | None = None


def get_model() -> PredictionModel:
    global _model_cache
    if _model_cache is None:
        _model_cache = PredictionModel.load()
    return _model_cache


def reload_model() -> None:
    global _model_cache
    _model_cache = PredictionModel.load()


# ヒューリスティック用の重み（モデル未学習時のフォールバック）
_HEURISTIC_WEIGHTS = {
    "win_rate": 0.20, "g1_wins": 0.05, "win_ratio": 0.10, "place_ratio": 0.10,
    "earnings_log": 0.05, "age": -0.02,
    "sire_score": 0.10, "jockey_score": 0.10, "trainer_score": 0.08, "farm_score": 0.05,
    "course_dist_score": 0.10, "surface_score": 0.05,
    "training_score": 0.08, "post_position": -0.02, "popularity_score": 0.10,
    "weight_carried": -0.02, "weight_diff": 0.0,
}


def _heuristic_predict(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    w = np.array([_HEURISTIC_WEIGHTS[name] for name in FEATURE_NAMES])
    raw = X @ w
    span = raw.max() - raw.min()
    norm = (raw - raw.min()) / span if span > 1e-9 else np.full_like(raw, 0.5)
    p_place = 0.2 + norm * 0.6   # 0.2 〜 0.8
    p_win = p_place * 0.4        # 単勝はより厳しめに評価
    return p_place, p_win


def predict_race(db, race) -> tuple[list[dict], str]:
    """
    race: models.JraRace（entries を含む）
    戻り値: (predictions, model_status)
    """
    model = get_model()
    entries = list(race.entries)

    if model.trained and model.encoders is not None:
        encoders = model.encoders
        status = "trained"
    else:
        encoders = build_encoders(db)
        status = "heuristic"

    X = np.array([
        entry_feature_vector(e, e.horse, race, encoders)
        for e in entries
    ])

    if status == "trained":
        p_place, p_win = model.predict(X)
    else:
        p_place, p_win = _heuristic_predict(X)

    predictions = []
    for e, pp, pw in zip(entries, p_place, p_win):
        odds_place = None
        if e.odds_place_low is not None and e.odds_place_high is not None:
            odds_place = (e.odds_place_low + e.odds_place_high) / 2
        elif e.odds_place_low is not None:
            odds_place = e.odds_place_low

        predictions.append({
            "horse_id": e.horse_id,
            "horse_number": e.horse_number,
            "horse_name": e.horse.name if e.horse else "?",
            "p_win": float(pw),
            "p_place": float(pp),
            "odds_win": e.odds_win,
            "odds_place": odds_place,
        })

    return predictions, status
