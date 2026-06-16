"""
netkeiba スクレイパー & DB シーダー

使い方:
  cd backend
  python -m app.scraper.run_scraper                        # デフォルト10頭
  python -m app.scraper.run_scraper 2002110019 2008105106  # 馬ID直接指定
  python -m app.scraper.run_scraper --discover             # レースページから自動収集（直近2週間）
  python -m app.scraper.run_scraper --discover --days-back 180  # 過去6ヶ月分を一括取得

IMPORTANT: プロトタイプ専用。商用公開前に JRA-VAN へ移行すること。
"""
import argparse
import asyncio
import logging
import sys
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .netkeiba import scrape_horses
from ..database import engine, SessionLocal
from ..models import Base, Horse, Race
from ..ml.train import retrain

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_HORSE_IDS = [
    "2002110019",  # ディープインパクト
    "2008105106",  # オルフェーヴル
    "2009106143",  # ジェンティルドンナ
    "2012104353",  # キタサンブラック
    "2015104364",  # アーモンドアイ
    "2017101602",  # コントレイル
    "2018100816",  # エフフォーリア
    "2019103186",  # イクイノックス
    "2020103128",  # リバティアイランド
    "2019104928",  # ドウデュース
]


def save_horse_to_db(data: dict, db: Session) -> Horse:
    """netkeiba_id → 名前の順でルックアップしてupsertする。"""
    netkeiba_id = data.get("netkeiba_id")
    horse = None

    if netkeiba_id:
        horse = db.query(Horse).filter(Horse.netkeiba_id == netkeiba_id).first()
    if not horse:
        horse = db.query(Horse).filter(Horse.name == data.get("name")).first()

    horse_fields = {
        k: v for k, v in data.items()
        if k not in ("races",) and hasattr(Horse, k)
    }

    if horse:
        for k, v in horse_fields.items():
            setattr(horse, k, v)
        # updated_at を手動セット（onupdate が効かない場合の保険）
        horse.updated_at = datetime.now(timezone.utc)
    else:
        horse = Horse(**horse_fields)
        db.add(horse)

    db.flush()

    db.query(Race).filter(Race.horse_id == horse.id).delete()
    for r in data.get("races", []):
        db.add(Race(
            horse_id=horse.id,
            date=r.get("date"),
            race_name=r.get("race_name"),
            grade=r.get("grade"),
            position=r.get("position"),
            jockey=r.get("jockey"),
            time=r.get("time"),
            distance=r.get("distance"),
            course=r.get("course"),
            prize=r.get("prize", 0),
        ))

    db.commit()
    db.refresh(horse)
    return horse


async def run(horse_ids: list[str]) -> None:
    Base.metadata.create_all(bind=engine)
    logger.info(f"スクレイプ開始: {len(horse_ids)} 頭")

    scraped = await scrape_horses(horse_ids)
    logger.info(f"取得完了: {len(scraped)} 頭 / {len(horse_ids)} 頭")

    db: Session = SessionLocal()
    try:
        saved = 0
        for data in scraped:
            try:
                horse = save_horse_to_db(data, db)
                logger.info(f"  保存: {horse.name} (id={horse.id})")
                saved += 1
            except Exception as e:
                logger.error(f"  DB保存失敗 [{data.get('name')}]: {e}")
                db.rollback()

        logger.info(f"DB保存完了: {saved} 頭")

        sample_count = retrain(db)
        if sample_count:
            logger.info(f"予測モデルを再学習しました（{sample_count}件のレース結果）")
    finally:
        db.close()


async def run_discover(days_back: int, days_forward: int) -> None:
    """レースカレンダーから馬IDを自動収集してスクレイプする。"""
    from .discover import discover_horse_ids

    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        logger.info(f"発見モード開始: 過去{days_back}日 + 未来{days_forward}日")
        horse_ids = await discover_horse_ids(db, days_back=days_back, days_forward=days_forward)
    finally:
        db.close()

    if not horse_ids:
        logger.info("新規スクレイプ対象の馬が見つかりませんでした")
        return

    await run(horse_ids)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="netkeiba スクレイパー")
    parser.add_argument(
        "horse_ids", nargs="*",
        help="馬IDを直接指定（省略時はデフォルトリストを使用）"
    )
    parser.add_argument(
        "--discover", action="store_true",
        help="レースカレンダーから馬IDを自動収集するモード"
    )
    parser.add_argument(
        "--days-back", type=int, default=14,
        help="発見モードで過去何日分のレースを対象にするか（デフォルト: 14）"
    )
    parser.add_argument(
        "--days-forward", type=int, default=14,
        help="発見モードで未来何日分の出走予定を対象にするか（デフォルト: 14）"
    )
    args = parser.parse_args()

    if args.discover:
        asyncio.run(run_discover(args.days_back, args.days_forward))
    else:
        ids = args.horse_ids if args.horse_ids else DEFAULT_HORSE_IDS
        asyncio.run(run(ids))
