"""
過去のJRAレース結果をまとめて取得し、学習データを増やすためのバックフィル。

実行方法:
  - 手動: POST /admin/backfill?weeks=26 (要 ADMIN_SECRET)
  - CLI:  python -m app.scraper.backfill [weeks]
"""
from __future__ import annotations

import asyncio
import logging
import sys
import httpx
from sqlalchemy.orm import Session

from ..database import SessionLocal, engine
from .. import models
from .jra_races import (
    check_robots,
    fetch_race_list,
    fetch_result_entries,
    historical_weekend_dates,
    sleep_between_requests,
)
from .run_weekly import _get_or_create_horse, _enrich_horse_profile
from ..ml.train import train_model
from ..ml.predict import reload_model

logger = logging.getLogger(__name__)

DEFAULT_WEEKS = 26


async def fetch_and_store_historical_races(db: Session, weeks: int = DEFAULT_WEEKS) -> dict:
    """過去 `weeks` 週分の確定済みレース結果を取得し、未登録のものをDBに追加する。"""
    dates = historical_weekend_dates(weeks)
    created = 0
    skipped = 0
    new_horses = 0

    async with httpx.AsyncClient() as client:
        if not await check_robots(client):
            return {"created": 0, "reason": "robots.txt disallows scraping"}

        for kaisai_date in dates:
            race_list = await fetch_race_list(client, kaisai_date)
            await sleep_between_requests()

            for r in race_list:
                existing = (
                    db.query(models.JraRace)
                    .filter(models.JraRace.netkeiba_race_id == r["race_id"])
                    .first()
                )
                if existing:
                    skipped += 1
                    continue

                result = await fetch_result_entries(client, r["race_id"])
                await sleep_between_requests()
                if not result or not result.get("finished"):
                    continue

                race = models.JraRace(
                    netkeiba_race_id=r["race_id"],
                    date=r["date"],
                    racecourse=r["racecourse"],
                    race_number=r["race_number"],
                    race_name=result.get("race_name") or r["race_name_hint"],
                    grade=result.get("grade"),
                    surface=result.get("surface"),
                    distance=result.get("distance"),
                    direction=result.get("direction"),
                    track_condition=result.get("track_condition"),
                    weather=result.get("weather"),
                    weekly_budget=0,
                )
                db.add(race)
                db.flush()

                for e in result["entries"]:
                    horse = _get_or_create_horse(db, e)
                    if not horse.sire:
                        await _enrich_horse_profile(client, db, horse)
                        new_horses += 1

                    db.add(models.RaceEntry(
                        race_id=race.id,
                        horse_id=horse.id,
                        post_position=e.get("post_position"),
                        horse_number=e.get("horse_number"),
                        jockey=e.get("jockey"),
                        weight_carried=e.get("weight_carried"),
                        horse_weight=e.get("horse_weight"),
                        horse_weight_diff=e.get("horse_weight_diff"),
                        odds_win=e.get("odds_win"),
                        popularity=e.get("popularity"),
                        result_position=e.get("result_position"),
                    ))

                db.commit()
                created += 1

    return {"created": created, "skipped": skipped, "new_horses": new_horses}


async def run_backfill(weeks: int = DEFAULT_WEEKS) -> dict:
    """バックフィル本体: 過去レース結果取得 → モデル再学習。"""
    db = SessionLocal()
    try:
        backfill_result = await fetch_and_store_historical_races(db, weeks)
        train_result = train_model(db)
        if train_result["trained"]:
            reload_model()

        summary = {"backfill": backfill_result, "train": train_result}
        logger.info(f"過去データ取得ジョブ完了: {summary}")
        return summary
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    models.Base.metadata.create_all(bind=engine)
    weeks = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_WEEKS
    asyncio.run(run_backfill(weeks))
