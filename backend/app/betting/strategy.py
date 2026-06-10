"""
予測確率とオッズから「買い方」を提案する。

方針:
  - 週5,000円という限られた資金の中で「損失は小さく・取れる時はしっかり取る」
    ことを両立させるため、低分散の複勝/単勝を中心に、
    余力があれば高配当の馬連・ワイド・三連複に少額を配分するバーベル戦略。
  - 期待値（モデル確率 × オッズ）が1を上回らないものは購入しない（見送りを推奨）。
  - ファイナンシャル・ケリー基準（の何分の1か）でベット額を決め、過剰投資を防ぐ。
  - JRA の最低購入単位100円に丸める。
"""
from __future__ import annotations
from itertools import permutations

MIN_BET = 100  # JRA最低購入単位(円)
KELLY_FRACTION = 0.25  # フラクショナル・ケリー（フルケリーの1/4で過剰投資を抑制）


# ── Harville モデル（単勝確率から連系馬券の的中確率を推定） ─────────────────

def _exacta_prob(p: list[float], i: int, j: int) -> float:
    """1着=i, 2着=j となる確率"""
    denom = 1 - p[i]
    if denom <= 1e-9:
        return 0.0
    return p[i] * p[j] / denom


def _trio_set_prob(p: list[float], idx: tuple[int, int, int]) -> float:
    """idx の3頭が（順不同で）上位3着を占める確率"""
    total = 0.0
    for a, b, c in permutations(idx):
        d1 = 1 - p[a]
        d2 = 1 - p[a] - p[b]
        if d1 <= 1e-9 or d2 <= 1e-9:
            continue
        total += p[a] * (p[b] / d1) * (p[c] / d2)
    return total


def quinella_prob(p: list[float], i: int, j: int) -> float:
    """馬連: 1-2着を i,j が（順不同で）独占する確率"""
    return _exacta_prob(p, i, j) + _exacta_prob(p, j, i)


def wide_prob(p: list[float], i: int, j: int, all_idx: list[int]) -> float:
    """ワイド: i,j が共に上位3着以内に入る確率"""
    total = 0.0
    for k in all_idx:
        if k == i or k == j:
            continue
        total += _trio_set_prob(p, (i, j, k))
    return total


def trio_prob(p: list[float], idx: tuple[int, int, int]) -> float:
    """三連複: idx の3頭が（順不同で）1-3着を独占する確率"""
    return _trio_set_prob(p, idx)


# ── ケリー基準 ──────────────────────────────────────────────────────────

def kelly_fraction(p: float, odds: float, fraction: float = KELLY_FRACTION, cap: float = 0.3) -> float:
    """フラクショナル・ケリー基準でのベット比率（資金に対する割合）"""
    b = odds - 1
    if b <= 0 or p <= 0:
        return 0.0
    f = (p * b - (1 - p)) / b
    return max(0.0, min(f * fraction, cap))


def _round_stake(amount: float, unit: int = MIN_BET) -> int:
    return int(amount // unit) * unit


# ── 買い目の組み立て ─────────────────────────────────────────────────────

def generate_candidates(predictions: list[dict], combo_bets: list[dict] | None = None) -> list[dict]:
    """期待値プラスの買い目候補を期待値の高い順に列挙する。"""
    n = len(predictions)
    if n == 0:
        return []

    # 単勝確率は1レース内で合計1になるよう正規化
    win_sum = sum(p["p_win"] for p in predictions) or 1.0
    p_win_norm = [p["p_win"] / win_sum for p in predictions]

    # 複勝確率は「払い戻し対象人数」を超えないようにスケーリング
    payout_slots = 3 if n >= 8 else 2
    place_sum = sum(p["p_place"] for p in predictions)
    place_scale = min(1.0, payout_slots / place_sum) if place_sum > 0 else 1.0
    p_place_norm = [p["p_place"] * place_scale for p in predictions]

    candidates = []

    # 複勝（ディフェンス・低分散の主力）
    for p, ppl in zip(predictions, p_place_norm):
        if p.get("odds_place") and ppl * p["odds_place"] > 1.05:
            candidates.append({
                "bet_type": "複勝",
                "target": f"{p['horse_number']} {p['horse_name']}",
                "probability": round(ppl, 3),
                "odds": p["odds_place"],
                "ev": ppl * p["odds_place"],
                "kelly": kelly_fraction(ppl, p["odds_place"], cap=0.35),
                "reason": "安定して3着内に入る確率が高く、オッズに対して割安",
            })

    # 単勝（本命の上積み）
    for p, pwn in zip(predictions, p_win_norm):
        if p.get("odds_win") and pwn * p["odds_win"] > 1.1:
            candidates.append({
                "bet_type": "単勝",
                "target": f"{p['horse_number']} {p['horse_name']}",
                "probability": round(pwn, 3),
                "odds": p["odds_win"],
                "ev": pwn * p["odds_win"],
                "kelly": kelly_fraction(pwn, p["odds_win"], cap=0.2),
                "reason": "勝率に対してオッズが高く、期待値がプラス",
            })

    # 連系馬券（オッズが手入力されている場合のみ・高配当の上積み枠）
    number_to_idx = {p["horse_number"]: i for i, p in enumerate(predictions)}
    all_idx = list(range(n))
    for combo in (combo_bets or []):
        nums = combo.get("horse_numbers", [])
        odds = combo.get("odds")
        bet_type = combo.get("type")
        if not odds or len(nums) < 2:
            continue
        idxs = [number_to_idx[num] for num in nums if num in number_to_idx]
        if len(idxs) != len(nums):
            continue

        if bet_type == "馬連" and len(idxs) == 2:
            prob = quinella_prob(p_win_norm, idxs[0], idxs[1])
        elif bet_type == "ワイド" and len(idxs) == 2:
            prob = wide_prob(p_win_norm, idxs[0], idxs[1], all_idx)
        elif bet_type == "三連複" and len(idxs) == 3:
            prob = trio_prob(p_win_norm, tuple(idxs))
        else:
            continue

        if prob * odds > 1.2:  # 高配当枠は期待値の閾値を高めに設定
            candidates.append({
                "bet_type": bet_type,
                "target": " - ".join(f"{n}" for n in nums),
                "probability": round(prob, 3),
                "odds": odds,
                "ev": prob * odds,
                "kelly": kelly_fraction(prob, odds, fraction=KELLY_FRACTION * 0.6, cap=0.15),
                "reason": "高配当が期待できる組み合わせ（小口の上積み枠）",
            })

    candidates.sort(key=lambda c: c["ev"], reverse=True)
    return candidates


def build_betting_plan(predictions: list[dict], budget: int = 5000, combo_bets: list[dict] | None = None) -> dict:
    """
    predictions: [{horse_number, horse_name, p_win, p_place, odds_win, odds_place}, ...]
        p_win, p_place はモデルの予測確率 (0-1)
        odds_win, odds_place は単勝・複勝オッズ (None可)
    combo_bets: [{"type": "馬連"|"ワイド"|"三連複", "horse_numbers": [..], "odds": float}, ...]
        オッズ表から手入力された連系馬券のオッズ（任意）

    戻り値: {"tickets": [...], "total_stake": int, "unallocated": int,
             "expected_value": float, "note": str}
    """
    if not predictions:
        return {"tickets": [], "total_stake": 0, "unallocated": budget,
                "expected_value": 0.0, "note": "出走馬データがありません"}

    candidates = generate_candidates(predictions, combo_bets)

    tickets = []
    remaining = budget
    for c in candidates:
        stake = _round_stake(budget * c["kelly"])
        stake = min(stake, remaining)
        if stake < MIN_BET:
            continue
        tickets.append({
            "bet_type": c["bet_type"],
            "target": c["target"],
            "stake": stake,
            "odds": c["odds"],
            "probability": c["probability"],
            "expected_return": round(stake * c["ev"]),
            "reason": c["reason"],
        })
        remaining -= stake

    total_stake = budget - remaining
    expected_value = sum(t["expected_return"] for t in tickets)

    note = (
        "期待値がプラスの買い目が見つかりませんでした。今回は見送りを推奨します（資金温存）。"
        if not tickets else
        "複勝中心に損失を抑えつつ、期待値プラスの買い目に資金を配分しています。"
    )

    return {
        "tickets": tickets,
        "total_stake": total_stake,
        "unallocated": remaining,
        "expected_value": expected_value,
        "note": note,
    }


def allocate_weekly_budget(race_plans: list[dict], total_budget: int = 5000) -> list[dict]:
    """
    複数レースに週予算を再配分する。
    各レースの「最良EV」が高いレースほど多く配分し、合計が total_budget を超えないようにする。

    race_plans: [{"_predictions": [...], "_combo_bets": [...] | None, ...other keys}, ...]
    各要素に "plan" キーが追加されて返る。
    """
    scored = []
    for rp in race_plans:
        candidates = generate_candidates(rp["_predictions"], rp.get("_combo_bets"))
        best_ev = max((c["ev"] for c in candidates), default=0)
        scored.append((rp, best_ev))

    positive = [(rp, ev) for rp, ev in scored if ev > 1.0]
    if not positive:
        for rp, _ in scored:
            rp["plan"] = {"tickets": [], "total_stake": 0, "unallocated": 0,
                           "expected_value": 0.0, "note": "今週は期待値プラスの買い目がなく、全レース見送りを推奨します。"}
        return [rp for rp, _ in scored]

    weight_sum = sum(ev - 1.0 for _, ev in positive)
    for rp, ev in scored:
        if ev <= 1.0:
            rp["plan"] = {"tickets": [], "total_stake": 0, "unallocated": 0,
                           "expected_value": 0.0, "note": "期待値プラスの買い目がないため見送り推奨です。"}
            continue
        share = (ev - 1.0) / weight_sum
        race_budget = _round_stake(total_budget * share)
        rp["plan"] = build_betting_plan(rp["_predictions"], budget=race_budget, combo_bets=rp.get("_combo_bets"))

    return [rp for rp, _ in scored]
