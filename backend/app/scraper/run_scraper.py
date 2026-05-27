"""
netkeiba スクレイパー & DB シーダー

使い方:
  cd backend
  python -m app.scraper.run_scraper                     # デフォルト馬リスト
  python -m app.scraper.run_scraper 2002110019 2008105106  # 馬ID指定

IMPORTANT: プロトタイプ専用。商用公開前に JRA-VAN へ移行すること。
"""
import asyncio
import sys
import logging
from sqlalchemy.orm import Session

from .netkeiba import scrape_horses
from ..database import engine, SessionLocal
from ..models import Base, Horse, Race

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── JRA 主要馬の netkeiba ID（プロトタイプ用）──────────────────────────
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
    """Insert or update a Horse record from scraped data."""
    horse = db.query(Horse).filter(Horse.name == data.get("name")).first()

    horse_fields = {
        k: v for k, v in data.items()
        if k not in ("races", "netkeiba_id") and hasattr(Horse, k)
    }

    if horse:
        for k, v in horse_fields.items():
            setattr(horse, k, v)
    else:
        horse = Horse(**horse_fields)
        db.add(horse)

    db.flush()  # get horse.id before adding races

    # 既存レース削除 → 再挿入
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


async def main(horse_ids: list[str]) -> None:
    # テーブルが存在しない場合は作成
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
    finally:
        db.close()


if __name__ == "__main__":
    ids = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_HORSE_IDS
    asyncio.run(main(ids))
