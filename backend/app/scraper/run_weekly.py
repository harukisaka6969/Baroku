"""
週次の自動データ取得ジョブ。

毎週実行することで:
  1. 今週末(土・日)に開催されるJRAレースの出馬表（騎手・枠番・斤量・馬体重・
     オッズ・血統情報を含む馬プロフィール）を取得し DB に登録する
  2. 先週末に開催されたJRAレースの着順を取得し、結果を確定する
  3. 確定結果が一定数たまったら予測モデルを再学習する

実行方法:
  - 自動: app.main の起動時に APScheduler で毎週スケジュール実行
  - 手動: POST /admin/scrape-races (要 ADMIN_SECRET)
  - CLI:  python -m app.scraper.run_weekly
"""
from __future__ import annotations

import asyncio
import logging
import httpx
from sqlalchemy.orm import Session

from ..database import SessionLocal, engine
from .. import models
from .jra_races import (
    check_robots,
    fetch_race_list,
    fetch_shutuba,
    fetch_results,
    upcoming_weekend_dates,
    previous_weekend_dates,
    sleep_between_requests,
)
from .netkeiba import fetch_horse
from ..ml.train import train_model
from ..ml.predict import reload_model

logger = logging.getLogger(__name__)


def _get_or_create_horse(db: Session, entry: dict) -> models.Horse:
    """出馬表の1行から Horse レコードを取得 or 新規作成する。"""
    netkeiba_id = entry.get("netkeiba_horse_id")
    name = entry.get("horse_name")

    horse = None
    if netkeiba_id:
        horse = db.query(models.Horse).filter(models.Horse.netkeiba_id == netkeiba_id).first()
    if not horse and name:
        horse = db.query(models.Horse).filter(models.Horse.name == name).first()

    if horse:
        if netkeiba_id and not horse.netkeiba_id:
            horse.netkeiba_id = netkeiba_id
        return horse

    horse = models.Horse(name=name, netkeiba_id=netkeiba_id, jockey=entry.get("jockey"))
    db.add(horse)
    db.flush()
    return horse


async def _enrich_horse_profile(client: httpx.AsyncClient, db: Session, horse: models.Horse) -> None:
    """新規馬の血統・調教師・牧場などのプロフィールを netkeiba から取得して補完する。"""
    if not horse.netkeiba_id or horse.sire:
        return  # 既にプロフィール取得済み、または ID 不明
    profile = await fetch_horse(client, horse.netkeiba_id)
    await sleep_between_requests()
    if not profile:
        return
    for key, value in profile.items():
        if key in ("races", "netkeiba_id"):
            continue
        if hasattr(horse, key) and value not in (None, ""):
            setattr(horse, key, value)


async def fetch_and_store_upcoming_races(db: Session) -> dict:
    """今週末のJRAレースの出馬表を取得し、未登録のものをDBに追加する。"""
    dates = upcoming_weekend_dates()
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

                shutuba = await fetch_shutuba(client, r["race_id"])
                await sleep_between_requests()
                if not shutuba or not shutuba.get("entries"):
                    continue

                race = models.JraRace(
                    netkeiba_race_id=r["race_id"],
                    date=r["date"],
                    racecourse=r["racecourse"],
                    race_number=r["race_number"],
                    race_name=shutuba.get("race_name") or r["race_name_hint"],
                    grade=shutuba.get("grade"),
                    surface=shutuba.get("surface"),
                    distance=shutuba.get("distance"),
                    direction=shutuba.get("direction"),
                    track_condition=shutuba.get("track_condition"),
                    weather=shutuba.get("weather"),
                    weekly_budget=5000,
                )
                db.add(race)
                db.flush()

                for e in shutuba["entries"]:
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
                    ))

                db.commit()
                created += 1

    return {"created": created, "skipped": skipped, "new_horses": new_horses}


async def fetch_and_store_results(db: Session) -> dict:
    """先週末のJRAレースの着順を取得し、確定済みレースの結果を更新する。"""
    dates = previous_weekend_dates()
    date_strs = {f"{d[:4]}-{d[4:6]}-{d[6:]}" for d in dates}

    races = (
        db.query(models.JraRace)
        .filter(models.JraRace.date.in_(date_strs))
        .filter(models.JraRace.netkeiba_race_id.isnot(None))
        .all()
    )
    races = [r for r in races if any(e.result_position is None for e in r.entries)]

    if not races:
        return {"updated_races": 0, "updated_entries": 0}

    updated_races = 0
    updated_entries = 0

    async with httpx.AsyncClient() as client:
        if not await check_robots(client):
            return {"updated_races": 0, "updated_entries": 0, "reason": "robots.txt disallows scraping"}

        for race in races:
            result = await fetch_results(client, race.netkeiba_race_id)
            await sleep_between_requests()
            if not result or not result["finished"]:
                continue

            entries_by_number = {e.horse_number: e for e in race.entries if e.horse_number is not None}
            for horse_number, position in result["results"].items():
                entry = entries_by_number.get(horse_number)
                if entry:
                    entry.result_position = position
                    updated_entries += 1

            db.commit()
            updated_races += 1

    return {"updated_races": updated_races, "updated_entries": updated_entries}


async def run_weekly_job() -> dict:
    """週次ジョブ本体: 出馬表取得 → 結果取得 → モデル再学習。"""
    db = SessionLocal()
    try:
        upcoming = await fetch_and_store_upcoming_races(db)
        results = await fetch_and_store_results(db)
        train_result = train_model(db)
        if train_result["trained"]:
            reload_model()

        summary = {"upcoming": upcoming, "results": results, "train": train_result}
        logger.info(f"週次データ取得ジョブ完了: {summary}")
        return summary
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    models.Base.metadata.create_all(bind=engine)
    asyncio.run(run_weekly_job())
