"""
予想モデルの学習・推論。

- predict_score(): 1頭分の特徴量をモデルに通し、0〜1の能力スコアを返す
- retrain(): 全馬の着順データから学習用データセットを作り、
  保存済みモデルをウォームスタートで増分学習して再保存する。
  スクレイパー実行後に呼び出すことで、新しいレース結果が
  蓄積されるたびにモデルの精度が向上していく。
"""
import json
import logging

import numpy as np
from sqlalchemy.orm import Session

from .. import models
from .features import INPUT_DIM, build_features
from .model import SimpleNN

logger = logging.getLogger(__name__)

WEIGHTS_KEY = "prediction_nn_v1"
MIN_TRAINING_SAMPLES = 5


def load_model(db: Session) -> SimpleNN:
    row = db.query(models.ModelWeights).filter(models.ModelWeights.key == WEIGHTS_KEY).first()
    if row:
        try:
            return SimpleNN.from_dict(json.loads(row.weights_json))
        except (ValueError, KeyError):
            logger.warning("保存済みモデルの読み込みに失敗したため初期化します")
    return SimpleNN(INPUT_DIM)


def save_model(db: Session, model: SimpleNN, sample_count: int) -> None:
    row = db.query(models.ModelWeights).filter(models.ModelWeights.key == WEIGHTS_KEY).first()
    payload = json.dumps(model.to_dict())
    if row:
        row.weights_json = payload
        row.trained_samples = sample_count
    else:
        row = models.ModelWeights(key=WEIGHTS_KEY, weights_json=payload, trained_samples=sample_count)
        db.add(row)
    db.commit()


def _label_for_position(position: int) -> float:
    if position == 1:
        return 1.0
    if position <= 3:
        return 0.6
    return 0.1


def retrain(db: Session, epochs: int = 300, lr: float = 0.05) -> int:
    """全馬のレース結果から増分学習する。学習に使ったサンプル数を返す。"""
    horses = db.query(models.Horse).all()

    X, y = [], []
    for horse in horses:
        races_with_position = [r for r in horse.races if r.position is not None]
        if not races_with_position:
            continue
        feat = build_features(db, horse)
        for race in races_with_position:
            X.append(feat)
            y.append(_label_for_position(race.position))

    if len(X) < MIN_TRAINING_SAMPLES:
        logger.info("学習データが不足しているため再学習をスキップしました（%d件）", len(X))
        return 0

    model = load_model(db)
    model.train(np.array(X), np.array(y), epochs=epochs, lr=lr)
    save_model(db, model, len(X))
    logger.info("予測モデルを再学習しました（%d件のレース結果データ）", len(X))
    return len(X)


def predict_score(db: Session, model: SimpleNN, horse: models.Horse) -> float:
    """0〜1の予測スコア（能力評価）を返す。"""
    feat = build_features(db, horse).reshape(1, -1)
    return float(model.predict(feat)[0])
