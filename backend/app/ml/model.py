"""
軽量ニューラルネットワーク（多層パーセプトロン）による着順予測モデル。

- 「3着以内（複勝）」確率 と 「1着（単勝）」確率 の2つを予測する小さな MLP。
- レース結果が DB に蓄積されるたびに /admin/train で再学習でき、
  学習データが増えるほど精度が向上していく仕組み。
- モデルは小さく(隠れ層 16-8)、CPU でも一瞬で学習・推論できるため
  ランタイムへの影響は最小限。
"""
from __future__ import annotations

import os
import logging
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

from .features import FEATURE_NAMES
from .encoders import Encoders

logger = logging.getLogger(__name__)

ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
MODEL_PATH = os.path.join(ARTIFACT_DIR, "model.joblib")

HIDDEN_LAYERS = (16, 8)


def _new_classifier() -> MLPClassifier:
    return MLPClassifier(
        hidden_layer_sizes=HIDDEN_LAYERS,
        activation="relu",
        solver="adam",
        alpha=1e-3,
        max_iter=500,
        random_state=42,
    )


class PredictionModel:
    """複勝(top3)モデルと単勝(win)モデルのペア。"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.place_clf = _new_classifier()
        self.win_clf = _new_classifier()
        self.encoders: Encoders | None = None
        self.trained = False
        self.train_samples = 0
        self.feature_names = FEATURE_NAMES

    def fit(self, X: list[list[float]], y_place: list[int], y_win: list[int], encoders: Encoders) -> bool:
        X = np.asarray(X, dtype=float)
        y_place = np.asarray(y_place, dtype=int)
        y_win = np.asarray(y_win, dtype=int)

        if len(np.unique(y_place)) < 2 or len(np.unique(y_win)) < 2:
            logger.warning("学習データのクラスが偏っているため学習をスキップします")
            return False

        Xs = self.scaler.fit_transform(X)
        self.place_clf.fit(Xs, y_place)
        self.win_clf.fit(Xs, y_win)
        self.encoders = encoders
        self.trained = True
        self.train_samples = len(y_place)
        return True

    def predict(self, X: list[list[float]]) -> tuple[np.ndarray, np.ndarray]:
        """戻り値: (p_place[], p_win[])"""
        if not self.trained:
            raise RuntimeError("モデルは未学習です")
        Xs = self.scaler.transform(np.asarray(X, dtype=float))
        p_place = self.place_clf.predict_proba(Xs)[:, 1]
        p_win = self.win_clf.predict_proba(Xs)[:, 1]
        return p_place, p_win

    def save(self) -> None:
        import joblib
        os.makedirs(ARTIFACT_DIR, exist_ok=True)
        joblib.dump(self, MODEL_PATH)

    @classmethod
    def load(cls) -> "PredictionModel":
        import joblib
        if os.path.exists(MODEL_PATH):
            try:
                return joblib.load(MODEL_PATH)
            except Exception as e:
                logger.warning(f"モデル読み込み失敗、新規作成します: {e}")
        return cls()
