"""
初回起動時にDBが空の場合、モックデータを投入する。
スクレイパー実行後は本物データで上書きされる。
"""
import random
from sqlalchemy.orm import Session
from .models import Horse, Race, Title, JraRace, RaceEntry

SEED_HORSES = [
    dict(name="ディープインパクト", name_en="Deep Impact", born_year=2002, sex="牡", color="鹿毛",
         status="種牡馬", farm="社台ファーム", birthplace="北海道千歳市",
         trainer="池江泰郎", stable="栗東", owner="金子真人ホールディングス", jockey="武豊",
         sire="サンデーサイレンス", dam="ウインドインハーヘア",
         sire_of_sire="Halo", dam_of_sire="Wishing Well",
         sire_of_dam="Alzao", dam_of_dam="Burghclere",
         best_time="2:23.3", best_distance="3000m", best_race="菊花賞",
         earnings=1173667000, g1_wins=7, win_rate=87, wins=14, losses=1, places=0),
    dict(name="オルフェーヴル", name_en="Orfevre", born_year=2008, sex="牡", color="栗毛",
         status="種牡馬", farm="社台ファーム", birthplace="北海道千歳市",
         trainer="池江泰寿", stable="栗東", owner="(有)サンデーレーシング", jockey="池添謙一",
         sire="ステイゴールド", dam="オリエンタルアート",
         sire_of_sire="サンデーサイレンス", dam_of_sire="ゴールデンサッシュ",
         sire_of_dam="メジロマックイーン", dam_of_dam="エレクトロアート",
         best_time="2:30.5", best_distance="2500m", best_race="有馬記念",
         earnings=1107700000, g1_wins=6, win_rate=73, wins=11, losses=3, places=3),
    dict(name="ジェンティルドンナ", name_en="Gentildonna", born_year=2009, sex="牝", color="鹿毛",
         status="繁殖牝馬", farm="ノーザンファーム", birthplace="北海道安平町",
         trainer="石坂正", stable="栗東", owner="(有)サンデーレーシング", jockey="岩田康誠",
         sire="ディープインパクト", dam="ドナブリーニ",
         sire_of_sire="サンデーサイレンス", dam_of_sire="ウインドインハーヘア",
         sire_of_dam="Bertolini", dam_of_dam="Moonlight's Box",
         best_time="2:23.6", best_distance="2400m", best_race="ジャパンカップ",
         earnings=1168800000, g1_wins=7, win_rate=58, wins=14, losses=4, places=2),
    dict(name="キタサンブラック", name_en="Kitasan Black", born_year=2012, sex="牡", color="鹿毛",
         status="種牡馬", farm="大野ファーム", birthplace="北海道新冠町",
         trainer="清水久詞", stable="栗東", owner="北島三郎", jockey="武豊",
         sire="ブラックタイド", dam="シュガーハート",
         sire_of_sire="サンデーサイレンス", dam_of_sire="ウインドインハーヘア",
         sire_of_dam="Sakura Bakushin O", dam_of_dam="カーリーエンジェル",
         best_time="2:24.0", best_distance="2400m", best_race="ジャパンカップ",
         earnings=1884364000, g1_wins=7, win_rate=67, wins=12, losses=5, places=3),
    dict(name="アーモンドアイ", name_en="Almond Eye", born_year=2015, sex="牝", color="鹿毛",
         status="繁殖牝馬", farm="ノーザンファーム", birthplace="北海道安平町",
         trainer="国枝栄", stable="美浦", owner="(有)シルクレーシング", jockey="C.ルメール",
         sire="ロードカナロア", dam="フサイチパンドラ",
         sire_of_sire="キングカメハメハ", dam_of_sire="Invincible Spirit",
         sire_of_dam="サンデーサイレンス", dam_of_dam="Danseur Fabuleux",
         best_time="1:57.8", best_distance="2000m", best_race="天皇賞（秋）",
         earnings=1936814600, g1_wins=9, win_rate=75, wins=11, losses=3, places=1),
    dict(name="コントレイル", name_en="Contrail", born_year=2017, sex="牡", color="青鹿毛",
         status="種牡馬", farm="ノーザンファーム", birthplace="北海道安平町",
         trainer="矢作芳人", stable="栗東", owner="前田晋二", jockey="C.ルメール",
         sire="ディープインパクト", dam="ロードクロノス",
         sire_of_sire="サンデーサイレンス", dam_of_sire="ウインドインハーヘア",
         sire_of_dam="Unbridled's Song", dam_of_dam="Pretend",
         best_time="2:24.1", best_distance="2400m", best_race="ジャパンカップ",
         earnings=980570000, g1_wins=8, win_rate=80, wins=8, losses=1, places=2),
    dict(name="エフフォーリア", name_en="Efforia", born_year=2018, sex="牡", color="黒鹿毛",
         status="現役", farm="社台ファーム", birthplace="北海道千歳市",
         trainer="鹿戸雄一", stable="美浦", owner="(有)シルクレーシング", jockey="横山武史",
         sire="エピファネイア", dam="ケイティーズハート",
         sire_of_sire="シンボリクリスエス", dam_of_sire="スペシャルウィーク",
         sire_of_dam="Heart's Cry", dam_of_dam="Lady Marian",
         best_time="1:57.9", best_distance="2000m", best_race="天皇賞（秋）",
         earnings=741100000, g1_wins=3, win_rate=50, wins=6, losses=4, places=1),
    dict(name="イクイノックス", name_en="Equinox", born_year=2019, sex="牡", color="鹿毛",
         status="種牡馬", farm="ノーザンファーム", birthplace="北海道安平町",
         trainer="木村哲也", stable="美浦", owner="(有)シルクレーシング", jockey="C.ルメール",
         sire="キタサンブラック", dam="シルヴァーサニー",
         sire_of_sire="ブラックタイド", dam_of_sire="シュガーハート",
         sire_of_dam="Silver Deputy", dam_of_dam="Gold Land",
         best_time="1:55.2", best_distance="2000m", best_race="天皇賞（秋）",
         earnings=2048559600, g1_wins=7, win_rate=78, wins=7, losses=1, places=2),
    dict(name="リバティアイランド", name_en="Liberty Island", born_year=2020, sex="牝", color="黒鹿毛",
         status="現役", farm="ノーザンファーム", birthplace="北海道安平町",
         trainer="中内田充正", stable="栗東", owner="(有)サンデーレーシング", jockey="川田将雅",
         sire="ドゥラメンテ", dam="ヤンキーローズ",
         sire_of_sire="キングカメハメハ", dam_of_sire="アドマイヤグルーヴ",
         sire_of_dam="All American", dam_of_dam="Naturalize",
         best_time="1:32.4", best_distance="1600m", best_race="桜花賞",
         earnings=584470000, g1_wins=4, win_rate=73, wins=8, losses=2, places=1),
    dict(name="ドウデュース", name_en="Do Deuce", born_year=2019, sex="牡", color="鹿毛",
         status="現役", farm="追分ファーム", birthplace="北海道日高町",
         trainer="友道康夫", stable="栗東", owner="(株)キャロットファーム", jockey="武豊",
         sire="ハーツクライ", dam="ダストアンドダイヤモンズ",
         sire_of_sire="サンデーサイレンス", dam_of_sire="アイリッシュダンス",
         sire_of_dam="Vindication", dam_of_dam="Dusty Diva",
         best_time="2:21.9", best_distance="2400m", best_race="日本ダービー",
         earnings=874640000, g1_wins=4, win_rate=63, wins=7, losses=3, places=3),
]


def seed_if_empty(db: Session) -> bool:
    """DB が空なら初期データを投入。投入した場合は True を返す。"""
    if db.query(Horse).count() > 0:
        return False

    for h in SEED_HORSES:
        db.add(Horse(**h))
    db.commit()

    seed_jra_races(db)
    return True


# ── JRA レースサンプルデータ ─────────────────────────────────────────────
# モデルの初回学習に必要な「確定済みレース結果」のサンプルと、
# 予測・買い方提案のデモ用「今週の出走表」を投入する。

_PAST_RACES = [
    dict(date="2024-10-27", racecourse="東京", race_number=11, race_name="天皇賞（秋）",
         grade="G1", surface="芝", distance=2000, direction="左", track_condition="良", weather="晴"),
    dict(date="2024-11-24", racecourse="東京", race_number=11, race_name="ジャパンカップ",
         grade="G1", surface="芝", distance=2400, direction="左", track_condition="良", weather="曇"),
    dict(date="2024-12-22", racecourse="中山", race_number=11, race_name="有馬記念",
         grade="G1", surface="芝", distance=2500, direction="右", track_condition="稍重", weather="曇"),
]

_UPCOMING_RACE = dict(
    date="2026-06-14", racecourse="東京", race_number=11, race_name="安田記念",
    grade="G1", surface="芝", distance=1600, direction="左", track_condition="良", weather="晴",
    weekly_budget=5000,
)


def seed_jra_races(db: Session) -> None:
    horses = db.query(Horse).order_by(Horse.id).all()
    if not horses:
        return

    rng = random.Random(42)

    # 過去の確定済みレース（モデル学習用データ）
    for race_def in _PAST_RACES:
        race = JraRace(**race_def)
        db.add(race)
        db.flush()

        order = list(range(len(horses)))
        rng.shuffle(order)

        for rank, idx in enumerate(order, start=1):
            horse = horses[idx]
            db.add(RaceEntry(
                race_id=race.id,
                horse_id=horse.id,
                post_position=(rank - 1) % 8 + 1,
                horse_number=rank,
                jockey=horse.jockey,
                weight_carried=57.0 if horse.sex == "牡" else 55.0,
                horse_weight=460 + rng.randint(-20, 20),
                horse_weight_diff=rng.randint(-6, 6),
                training_time=round(11.0 + rng.random() * 2.5, 1),
                training_eval=rng.choice(["A", "B", "B", "C"]),
                odds_win=round(1.5 + rank * 1.8 + rng.random() * 2, 1),
                odds_place_low=round(1.1 + rank * 0.4, 1),
                odds_place_high=round(1.3 + rank * 0.5, 1),
                popularity=rank,
                result_position=rank,
            ))

    # 今週のレース（予測・買い方提案デモ用、結果未確定）
    upcoming = JraRace(**_UPCOMING_RACE)
    db.add(upcoming)
    db.flush()

    order = list(range(len(horses)))
    rng.shuffle(order)
    for num, idx in enumerate(order, start=1):
        horse = horses[idx]
        db.add(RaceEntry(
            race_id=upcoming.id,
            horse_id=horse.id,
            post_position=(num - 1) % 8 + 1,
            horse_number=num,
            jockey=horse.jockey,
            weight_carried=57.0 if horse.sex == "牡" else 55.0,
            horse_weight=460 + rng.randint(-20, 20),
            horse_weight_diff=rng.randint(-6, 6),
            training_time=round(11.0 + rng.random() * 2.5, 1),
            training_eval=rng.choice(["A", "B", "B", "C"]),
            odds_win=round(1.5 + num * 1.8 + rng.random() * 2, 1),
            odds_place_low=round(1.1 + num * 0.4, 1),
            odds_place_high=round(1.3 + num * 0.5, 1),
            popularity=num,
            result_position=None,
        ))

    db.commit()
