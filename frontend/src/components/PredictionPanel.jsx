import { useState } from 'react';
import Disclaimer from './Disclaimer.jsx';
import { getVenues, getRacesByVenue, getHorseById } from '../mockData.js';

const MODES = [
  { id: 'safe',     icon: '🔒', label: '確勝' },
  { id: 'balanced', icon: '⚖',  label: 'バランス' },
  { id: 'risky',    icon: '🔥', label: '穴狙い' },
];

const GRADE_COLORS = {
  'G1': 'bg-gold/10 text-gold border-gold/30',
  'G2': 'bg-purple-50 text-purple-600 border-purple-200',
  'G3': 'bg-blue-50 text-blue-600 border-blue-200',
  'OP': 'bg-stone-100 text-stone-500 border-stone-200',
};

const BET_LABELS   = { safe: '単勝 / 複勝', balanced: '馬連 / ワイド', risky: '三連複 / 馬単' };
const ODDS_LABELS  = { safe: '1〜3倍',       balanced: '5〜20倍',        risky: '30倍〜' };
const WEIGHTS = {
  safe:     { win: 0.40, stability: 0.30, pedigree: 0.20, dark: 0.00, course: 0.10 },
  balanced: { win: 0.30, stability: 0.20, pedigree: 0.20, dark: 0.15, course: 0.15 },
  risky:    { win: 0.10, stability: 0.05, pedigree: 0.20, dark: 0.40, course: 0.25 },
};
const REASONS = {
  safe:     ['安定感抜群', '本命視の実績', '信頼の実力馬'],
  balanced: ['血統の底力', '上昇気配あり', 'コース適性◎'],
  risky:    ['大穴一発', '巻き返し期待', '人気薄の伏兵'],
};

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

  const venues     = getVenues(weekend);
  const activeVenue = venue || venues[0];
  const races      = getRacesByVenue(weekend, activeVenue);
  const activeRace = race?.weekend === weekend && race?.venue === activeVenue ? race : null;
  const entries    = activeRace ? activeRace.entries.map(id => getHorseById(id)).filter(Boolean) : [];
  const prediction = accepted && activeRace ? calcPrediction(entries, mode) : [];

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
                  <div className={`font-mono text-sm font-bold shrink-0 ${i === 0 ? 'text-gold' : 'text-stone-400'}`}>
                    {confidence}%
                  </div>
                </div>
              ))}
            </div>

            {/* Bet info */}
            <div className="flex gap-2">
              <div className="flex-1 bg-stone-50 rounded-xl p-3 text-center">
                <div className="text-xs text-stone-400 font-sans">推奨馬券</div>
                <div className="text-sm font-sans font-medium text-stone-800 mt-0.5">{BET_LABELS[mode]}</div>
              </div>
              <div className="flex-1 bg-stone-50 rounded-xl p-3 text-center">
                <div className="text-xs text-stone-400 font-sans">想定オッズ</div>
                <div className="text-sm font-mono font-medium text-stone-800 mt-0.5">{ODDS_LABELS[mode]}</div>
              </div>
            </div>
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
