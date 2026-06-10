"""
DB に蓄積された確定済みレース結果からモデルを（再）学習する。

実行方法:
  - API: POST /admin/train (要 ADMIN_SECRET)
  - CLI: python -m app.ml.train
"""
import logging
from sqlalchemy.orm import Session

from .. import models
from .encoders import build_encoders
from .features import entry_feature_vector
from .model import PredictionModel

logger = logging.getLogger(__name__)

MIN_SAMPLES = 20  # これ未満なら学習せずヒューリスティックを使い続ける


def train_model(db: Session) -> dict:
    rows = (
        db.query(models.RaceEntry, models.Horse, models.JraRace)
        .join(models.Horse, models.RaceEntry.horse_id == models.Horse.id)
        .join(models.JraRace, models.RaceEntry.race_id == models.JraRace.id)
        .filter(models.RaceEntry.result_position.isnot(None))
        .all()
    )

    if len(rows) < MIN_SAMPLES:
        return {
            "trained": False,
            "samples": len(rows),
            "min_samples": MIN_SAMPLES,
            "reason": f"確定済みレース結果が {MIN_SAMPLES} 件未満です（現在 {len(rows)} 件）",
        }

    encoders = build_encoders(db)

    X, y_place, y_win = [], [], []
    for entry, horse, race in rows:
        X.append(entry_feature_vector(entry, horse, race, encoders))
        y_place.append(1 if entry.result_position <= 3 else 0)
        y_win.append(1 if entry.result_position == 1 else 0)

    model = PredictionModel()
    ok = model.fit(X, y_place, y_win, encoders)
    if ok:
        model.save()
        logger.info(f"モデル再学習完了: {len(y_place)} サンプル")
        return {"trained": True, "samples": len(y_place)}

    return {"trained": False, "samples": len(y_place), "reason": "クラスの偏りにより学習不可"}


if __name__ == "__main__":
    from ..database import SessionLocal

    logging.basicConfig(level=logging.INFO)
    db = SessionLocal()
    try:
        result = train_model(db)
        logger.info(result)
    finally:
        db.close()
