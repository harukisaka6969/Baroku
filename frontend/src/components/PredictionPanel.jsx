import { useState, useEffect } from 'react';
import Disclaimer from './Disclaimer.jsx';
import { getVenues, getRacesByVenue, getHorseById } from '../mockData.js';
import { postPrediction } from '../api.js';

const MODES = [
  { id: 'ultra_safe', icon: '🛡', label: '鉄板' },
  { id: 'safe',       icon: '🔒', label: '確勝' },
  { id: 'balanced',   icon: '⚖',  label: 'バランス' },
  { id: 'risky',      icon: '🔥', label: '穴狙い' },
];

const GRADE_COLORS = {
  'G1': 'bg-gold/10 text-gold border-gold/30',
  'G2': 'bg-purple-50 text-purple-600 border-purple-200',
  'G3': 'bg-blue-50 text-blue-600 border-blue-200',
  'OP': 'bg-stone-100 text-stone-500 border-stone-200',
};

const BET_LABELS   = { ultra_safe: '複勝（分散買い）', safe: '単勝 / 複勝', balanced: '馬連 / ワイド', risky: '三連複 / 馬単' };
const ODDS_LABELS  = { ultra_safe: '1.0〜1.5倍', safe: '1〜3倍', balanced: '5〜20倍', risky: '30倍〜' };
const WEIGHTS = {
  ultra_safe: { win: 0.45, stability: 0.35, pedigree: 0.15, dark: 0.00, course: 0.05 },
  safe:       { win: 0.40, stability: 0.30, pedigree: 0.20, dark: 0.00, course: 0.10 },
  balanced:   { win: 0.30, stability: 0.20, pedigree: 0.20, dark: 0.15, course: 0.15 },
  risky:      { win: 0.10, stability: 0.05, pedigree: 0.20, dark: 0.40, course: 0.25 },
};
const REASONS = {
  ultra_safe: ['崩れない安定感', '複勝圏内が濃厚', '堅実な人気馬'],
  safe:       ['安定感抜群', '本命視の実績', '信頼の実力馬'],
  balanced:   ['血統の底力', '上昇気配あり', 'コース適性◎'],
  risky:      ['大穴一発', '巻き返し期待', '人気薄の伏兵'],
};

const MIN_BUDGET = 1000;
const MAX_BUDGET = 100000;
const BUDGET_UNIT = 100;

// 比率配分（100円単位、端数は1点目に寄せる）
function splitBudget(budget, ratios) {
  const total = ratios.reduce((a, b) => a + b, 0);
  const amounts = ratios.map(r => Math.floor(budget * r / total / BUDGET_UNIT) * BUDGET_UNIT);
  const remainder = budget - amounts.reduce((a, b) => a + b, 0);
  if (amounts.length > 0) amounts[0] += remainder;
  return amounts;
}

// 馬名の表示（馬単は →、それ以外は -）
function horseLabel(type, horses) {
  const sep = type === '馬単' || type === '三連単' ? ' → ' : ' - ';
  return horses.join(sep);
}

// モードごとの買い目プランを生成
function buildBetPlan(rankedNames, mode, budget) {
  const n = rankedNames.length;
  if (n === 0) return [];

  let items;
  if (mode === 'ultra_safe') {
    const tops = rankedNames.slice(0, Math.min(3, n));
    items = tops.map(h => ({ type: '複勝', horses: [h], ratio: 1 }));
  } else if (mode === 'safe') {
    items = [
      { type: '単勝', horses: [rankedNames[0]],                  ratio: 4 },
      { type: '複勝', horses: [rankedNames[0]],                  ratio: 3 },
      n > 1 ? { type: '複勝', horses: [rankedNames[1]],          ratio: 3 } : null,
    ].filter(Boolean);
  } else if (mode === 'balanced') {
    items = [
      { type: '単勝', horses: [rankedNames[0]],                              ratio: 2 },
      n > 1 ? { type: '馬連', horses: [rankedNames[0], rankedNames[1]],     ratio: 3 } : null,
      n > 1 ? { type: 'ワイド', horses: [rankedNames[0], rankedNames[1]],   ratio: 2 } : null,
      n > 2 ? { type: 'ワイド', horses: [rankedNames[0], rankedNames[2]],   ratio: 3 } : null,
    ].filter(Boolean);
  } else if (mode === 'risky') {
    items = [
      n > 2 ? { type: '三連複', horses: rankedNames.slice(0, 3),            ratio: 4 } : null,
      n > 1 ? { type: '馬単',   horses: [rankedNames[0], rankedNames[1]],   ratio: 2 } : null,
      n > 1 ? { type: '馬単',   horses: [rankedNames[1], rankedNames[0]],   ratio: 2 } : null,
      n > 2 ? { type: 'ワイド', horses: [rankedNames[0], rankedNames[2]],   ratio: 2 } : null,
    ].filter(Boolean);
  } else {
    return [];
  }

  const amounts = splitBudget(budget, items.map(x => x.ratio));
  return items.map((item, i) => ({ type: item.type, horses: item.horses, amount: amounts[i] }));
}

function calcPrediction(entries, mode) {
  const w = WEIGHTS[mode];
  return entries
    .map(h => {
      const score =
        (h.win_rate / 100) * w.win * 100 +
        (h.record.wins / Math.max(h.record.wins + h.record.losses, 1)) * w.stability * 100 +
        Math.min(h.g1_wins / 10, 1) * w.pedigree * 100 +
        (1 - h.win_rate / 100) * w.dark * 100 +
        Math.random() * w.course * 100;
      const reasons = REASONS[mode];
      return {
        horse: h,
        confidence: Math.min(Math.round(score), 97),
        reason: reasons[Math.floor(Math.random() * reasons.length)],
      };
    })
    .sort((a, b) => b.confidence - a.confidence);
}

export default function PredictionPanel() {
  const [accepted, setAccepted] = useState(false);
  const [weekend, setWeekend]   = useState(1);
  const [venue, setVenue]       = useState(null);
  const [race, setRace]         = useState(null);
  const [mode, setMode]         = useState('balanced');
  const [budget, setBudget]     = useState(5000);

  const [apiResult, setApiResult] = useState(null);

  const venues     = getVenues(weekend);
  const activeVenue = venue || venues[0];
  const races      = getRacesByVenue(weekend, activeVenue);
  const activeRace = race?.weekend === weekend && race?.venue === activeVenue ? race : null;
  const entries    = activeRace ? activeRace.entries.map(id => getHorseById(id)).filter(Boolean) : [];

  // バックエンドのAI予想モデル（血統・騎手・調教師・牧場・コース実績を学習）を呼び出す。
  // 利用できない場合はクライアント側の簡易ロジックにフォールバック。
  useEffect(() => {
    let cancelled = false;
    if (!accepted || !activeRace || entries.length === 0) {
      setApiResult(null);
      return;
    }
    postPrediction({ horse_ids: entries.map(h => h.id), mode })
      .then(res => { if (!cancelled) setApiResult(res); })
      .catch(() => { if (!cancelled) setApiResult(null); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accepted, activeRace?.id, mode]);

  const prediction = apiResult
    ? apiResult.ranking
        .map(r => {
          const horse = getHorseById(r.horse_id);
          return horse ? { horse, confidence: r.confidence, reason: r.reason } : null;
        })
        .filter(Boolean)
    : (accepted && activeRace ? calcPrediction(entries, mode) : []);

  const rankedNames = prediction.map(p => p.horse.name);
  const betPlan = (accepted && activeRace) ? buildBetPlan(rankedNames, mode, budget) : [];

  const handleBudgetChange = (value) => {
    const n = Number(value);
    if (Number.isNaN(n)) return;
    setBudget(Math.min(MAX_BUDGET, Math.max(MIN_BUDGET, Math.round(n / BUDGET_UNIT) * BUDGET_UNIT)));
  };

  return (
    <div className="space-y-5">
      {!accepted && <Disclaimer onAccept={() => setAccepted(true)} />}

      <div className={!accepted ? 'blur-sm pointer-events-none select-none' : ''}>

        {/* Weekend selector */}
        <div className="flex gap-2 mb-4">
          {[{ w: 1, label: '第1週 5/30-31' }, { w: 2, label: '第2週 6/6-7' }].map(({ w, label }) => (
            <button
              key={w}
              onClick={() => { setWeekend(w); setVenue(null); setRace(null); }}
              className={`px-4 py-1.5 rounded-full text-sm font-sans font-medium border transition-all
                ${weekend === w
                  ? 'bg-stone-900 text-white border-stone-900'
                  : 'bg-white text-stone-600 border-stone-200 hover:border-stone-400'}`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Venue tabs */}
        <div className="flex gap-1.5 flex-wrap mb-4">
          {venues.map(v => (
            <button
              key={v}
              onClick={() => { setVenue(v); setRace(null); }}
              className={`px-3 py-1 rounded-lg text-sm font-sans border transition-all
                ${activeVenue === v
                  ? 'bg-gold text-white border-gold'
                  : 'bg-white text-stone-600 border-stone-200 hover:border-gold/50'}`}
            >
              🏟 {v}
            </button>
          ))}
        </div>

        {/* Race list */}
        <div className="space-y-2 mb-5">
          {races.map(r => (
            <button
              key={r.id}
              onClick={() => setRace(r)}
              className={`w-full text-left rounded-xl border p-3 transition-all
                ${activeRace?.id === r.id
                  ? 'border-gold bg-gold/5'
                  : 'border-stone-100 bg-white hover:border-stone-300'}`}
            >
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-mono text-xs text-stone-400">{r.date}</span>
                <span className="font-serif font-semibold text-stone-900">{r.race_name}</span>
                <span className={`text-xs px-1.5 py-0.5 rounded border ${GRADE_COLORS[r.grade] || GRADE_COLORS['OP']}`}>
                  {r.grade}
                </span>
                <span className="font-mono text-xs text-stone-400 ml-auto">{r.surface} {r.distance}</span>
              </div>
              <div className="mt-1.5 flex flex-wrap gap-1">
                {r.entries.map(id => {
                  const h = getHorseById(id);
                  return h ? (
                    <span key={id} className="text-xs bg-stone-50 text-stone-600 border border-stone-100 px-1.5 py-0.5 rounded font-sans">
                      {h.name}
                    </span>
                  ) : null;
                })}
              </div>
            </button>
          ))}
        </div>

        {/* Prediction result */}
        {accepted && activeRace && (
          <div className="border-t border-stone-100 pt-5 space-y-4">
            {/* Mode selector */}
            <div className="flex gap-2">
              {MODES.map(m => (
                <button
                  key={m.id}
                  onClick={() => setMode(m.id)}
                  className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-sans font-medium border transition-all
                    ${mode === m.id
                      ? 'bg-stone-900 text-white border-stone-900'
                      : 'bg-white text-stone-600 border-stone-200 hover:border-stone-400'}`}
                >
                  {m.icon} {m.label}
                </button>
              ))}
            </div>

            {/* Budget control */}
            <div className="bg-stone-50 rounded-xl p-3 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-stone-400 font-sans">軍資金</span>
                <div className="flex items-center gap-1">
                  <span className="font-mono text-sm text-stone-500">¥</span>
                  <input
                    type="number"
                    min={MIN_BUDGET}
                    max={MAX_BUDGET}
                    step={BUDGET_UNIT}
                    value={budget}
                    onChange={e => handleBudgetChange(e.target.value)}
                    className="w-24 font-mono text-sm font-bold text-stone-900 bg-white border border-stone-200 rounded-lg px-2 py-1 text-right"
                  />
                </div>
              </div>
              <input
                type="range"
                min={MIN_BUDGET}
                max={MAX_BUDGET}
                step={BUDGET_UNIT}
                value={budget}
                onChange={e => handleBudgetChange(e.target.value)}
                className="w-full accent-gold"
              />
            </div>

            {/* Visual horse ranking */}
            <div className="space-y-2">
              {prediction.map(({ horse: h, confidence, reason }, i) => (
                <div key={h.id} className="flex items-center gap-3 bg-white border border-stone-100 rounded-xl p-3">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-mono font-bold shrink-0
                    ${i === 0 ? 'bg-gold text-white' : 'bg-stone-100 text-stone-500'}`}>
                    {i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-baseline gap-1.5 flex-wrap">
                      <span className="font-serif font-semibold text-stone-900 text-sm">{h.name}</span>
                      <span className="text-xs text-stone-400 font-sans">{reason}</span>
                    </div>
                    <div className="mt-1 h-1.5 bg-stone-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${i === 0 ? 'bg-gold' : 'bg-stone-300'}`}
                        style={{ width: `${confidence}%` }}
                      />
                    </div>
                  </div>
                  <span className={`font-mono text-sm font-bold shrink-0 ${i === 0 ? 'text-gold' : 'text-stone-400'}`}>
                    {confidence}%
                  </span>
                </div>
              ))}
            </div>

            {/* 買い目プラン */}
            {betPlan.length > 0 && (
              <div className="bg-stone-50 rounded-xl p-3 space-y-2">
                <div className="text-xs text-stone-400 font-sans mb-2">買い目プラン</div>
                {betPlan.map((bet, i) => (
                  <div key={i} className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="shrink-0 text-[11px] font-sans font-semibold bg-stone-900 text-white rounded px-1.5 py-0.5">
                        {bet.type}
                      </span>
                      <span className="text-xs font-serif text-stone-700 truncate">
                        {horseLabel(bet.type, bet.horses)}
                      </span>
                    </div>
                    <span className="shrink-0 font-mono text-xs font-bold text-stone-900">
                      ¥{bet.amount.toLocaleString()}
                    </span>
                  </div>
                ))}
                <div className="border-t border-stone-200 pt-2 flex justify-between items-center">
                  <span className="text-xs text-stone-400 font-sans">合計</span>
                  <span className="font-mono font-bold text-stone-900 text-sm">
                    ¥{betPlan.reduce((s, b) => s + b.amount, 0).toLocaleString()}
                  </span>
                </div>
                <div className="text-[10px] text-stone-400 font-sans">想定オッズ: {ODDS_LABELS[mode]}</div>
              </div>
            )}

            {mode === 'ultra_safe' && (
              <p className="text-xs text-stone-400 font-sans bg-stone-50 rounded-xl p-3 leading-relaxed">
                複勝は的中率が高い反面オッズが低く、払戻合計が購入額を下回る場合があります。
              </p>
            )}
          </div>
        )}

        {accepted && !activeRace && (
          <p className="text-center text-stone-400 font-sans text-sm py-4">レースを選んでください</p>
        )}

        <p className="text-center text-xs text-stone-300 font-sans pt-4">
          ⚠️ 本予想は娯楽目的の参考情報です
        </p>
      </div>
    </div>
  );
}
