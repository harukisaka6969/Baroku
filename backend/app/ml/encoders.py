"""
血統・騎手・調教師・牧場・コース適性などのカテゴリ変数を
過去の着順実績から「複勝(3着以内)率」へ変換するターゲットエンコーダ。

新しいレース結果が DB に蓄積されるほど、このエンコーディングの
精度（＝モデルの精度）が自動的に向上していく。
"""
from collections import defaultdict
from .. import models

GLOBAL_DEFAULT_TOP3_RATE = 0.375  # 8頭立て想定の複勝率(3/8)の目安
SMOOTHING = 5  # サンプル数が少ないカテゴリは全体平均に引き寄せる


def distance_bucket(distance: int | None) -> str:
    if not distance:
        return "unknown"
    return f"{(distance // 400) * 400}"


def course_dist_key(racecourse: str | None, surface: str | None, distance: int | None) -> str:
    return f"{racecourse or '?'}_{surface or '?'}_{distance_bucket(distance)}"


def surface_key(surface: str | None) -> str:
    return surface or "unknown"


class Encoders:
    """カテゴリ -> 複勝率 の対応表をまとめたコンテナ。"""

    def __init__(self, tables: dict[str, dict[str, float]], global_mean: float = GLOBAL_DEFAULT_TOP3_RATE):
        self.tables = tables
        self.global_mean = global_mean

    def score(self, category: str, value: str | None) -> float:
        table = self.tables.get(category, {})
        if value is None:
            return self.global_mean
        return table.get(value, self.global_mean)


def _build_table(rows: list[tuple[str, int]], global_mean: float) -> dict[str, float]:
    """rows: [(category_value, is_top3), ...] -> 平滑化された複勝率テーブル"""
    sums: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # value -> [count, top3_count]
    for value, is_top3 in rows:
        if not value:
            continue
        sums[value][0] += 1
        sums[value][1] += is_top3

    table = {}
    for value, (count, top3_count) in sums.items():
        table[value] = (top3_count + global_mean * SMOOTHING) / (count + SMOOTHING)
    return table


def build_encoders(db) -> Encoders:
    """確定済み(result_position が入っている)レースから各種エンコーダを構築する。"""
    rows = (
        db.query(models.RaceEntry, models.Horse, models.JraRace)
        .join(models.Horse, models.RaceEntry.horse_id == models.Horse.id)
        .join(models.JraRace, models.RaceEntry.race_id == models.JraRace.id)
        .filter(models.RaceEntry.result_position.isnot(None))
        .all()
    )

    if not rows:
        return Encoders({}, GLOBAL_DEFAULT_TOP3_RATE)

    is_top3_list = [1 if entry.result_position <= 3 else 0 for entry, _, _ in rows]
    global_mean = sum(is_top3_list) / len(is_top3_list)

    sire_rows = [(horse.sire, t) for (entry, horse, race), t in zip(rows, is_top3_list)]
    jockey_rows = [((entry.jockey or horse.jockey), t) for (entry, horse, race), t in zip(rows, is_top3_list)]
    trainer_rows = [(horse.trainer, t) for (entry, horse, race), t in zip(rows, is_top3_list)]
    stable_rows = [(horse.stable, t) for (entry, horse, race), t in zip(rows, is_top3_list)]
    farm_rows = [(horse.farm, t) for (entry, horse, race), t in zip(rows, is_top3_list)]
    course_dist_rows = [
        (course_dist_key(race.racecourse, race.surface, race.distance), t)
        for (entry, horse, race), t in zip(rows, is_top3_list)
    ]
    surface_rows = [(surface_key(race.surface), t) for (entry, horse, race), t in zip(rows, is_top3_list)]

    tables = {
        "sire": _build_table(sire_rows, global_mean),
        "jockey": _build_table(jockey_rows, global_mean),
        "trainer": _build_table(trainer_rows, global_mean),
        "stable": _build_table(stable_rows, global_mean),
        "farm": _build_table(farm_rows, global_mean),
        "course_dist": _build_table(course_dist_rows, global_mean),
        "surface": _build_table(surface_rows, global_mean),
    }
    return Encoders(tables, global_mean)
