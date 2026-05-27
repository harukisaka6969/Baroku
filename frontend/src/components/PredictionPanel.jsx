import { useState } from 'react';
import Disclaimer from './Disclaimer.jsx';

const MODES = [
  {
    id: 'safe',
    icon: '🔒',
    label: '確勝モード',
    desc: '本命軸1〜2頭に絞り、人気・安定感重視。低配当だが安定。',
    note: '的中率重視。配当は低めですが着実に回収を狙えます。',
    color: 'border-emerald-300 bg-emerald-50',
    badge: 'bg-emerald-100 text-emerald-700',
  },
  {
    id: 'balanced',
    icon: '⚖',
    label: 'バランス',
    desc: '本命＋穴1頭。期待値と安定性のバランス型。',
    note: '的中率と配当のバランスを重視したスタンダードな予想です。',
    color: 'border-blue-300 bg-blue-50',
    badge: 'bg-blue-100 text-blue-700',
  },
  {
    id: 'risky',
    icon: '🔥',
    label: 'ハイリスク',
    desc: '伏兵・穴馬中心。大穴狙い。的中率は低い。',
    note: '的中率は低いですが、大きな配当を狙います。余剰金でお楽しみください。',
    color: 'border-red-300 bg-red-50',
    badge: 'bg-red-100 text-red-700',
  },
];

function generatePrediction(horse, mode, allHorses) {
  const related = allHorses.filter(h => h.id !== horse.id).slice(0, 9);
  const candidates = [horse, ...related].slice(0, 6);

  const weights = {
    safe: { win_rate: 0.40, stability: 0.30, pedigree: 0.20, dark_horse: 0.00, course: 0.10 },
    balanced: { win_rate: 0.30, stability: 0.20, pedigree: 0.20, dark_horse: 0.15, course: 0.15 },
    risky: { win_rate: 0.10, stability: 0.05, pedigree: 0.20, dark_horse: 0.40, course: 0.25 },
  }[mode];

  const scored = candidates.map(h => {
    const winScore = (h.win_rate / 100) * weights.win_rate * 100;
    const stability = (h.record.wins / Math.max(h.record.wins + h.record.losses, 1)) * weights.stability * 100;
    const pedigree = (h.g1_wins / 10) * weights.pedigree * 100;
    const darkHorse = (1 - h.win_rate / 100) * weights.dark_horse * 100;
    const course = Math.random() * weights.course * 100;
    const total = winScore + stability + pedigree + darkHorse + course;

    const reasons = {
      safe: [`勝率${h.win_rate}%の安定感`, `G1 ${h.g1_wins}勝の実績`, `${h.stable}所属の信頼度`],
      balanced: [`${h.sire}産駒の底力`, `直近の安定した成績`, `コース適性◎`],
      risky: [`人気薄でも侮れない血統`, `前走からの巻き返し期待`, `大穴一発の可能性`],
    }[mode];

    return {
      horse: h,
      score: Math.min(Math.round(total), 98),
      reason: reasons[Math.floor(Math.random() * reasons.length)],
    };
  });

  scored.sort((a, b) => b.score - a.score);
  const top = scored.slice(0, mode === 'safe' ? 2 : mode === 'balanced' ? 3 : 5);

  const betTypes = {
    safe: '単勝 / 複勝',
    balanced: '馬連 / ワイド',
    risky: '三連複 / 馬単',
  }[mode];

  const oddsRanges = {
    safe: '1.2〜3.0倍',
    balanced: '5〜20倍',
    risky: '30〜200倍',
  }[mode];

  return {
    recommendations: top,
    bet_type: betTypes,
    odds_range: oddsRanges,
    disclaimer: '本予想は娯楽目的の参考情報です。',
  };
}

export default function PredictionPanel({ horse, allHorses }) {
  const [accepted, setAccepted] = useState(false);
  const [mode, setMode] = useState('balanced');
  const [prediction, setPrediction] = useState(null);

  const handleAccept = () => {
    setAccepted(true);
    setPrediction(generatePrediction(horse, mode, allHorses));
  };

  const handleModeChange = (newMode) => {
    setMode(newMode);
    if (accepted) {
      setPrediction(generatePrediction(horse, newMode, allHorses));
    }
  };

  const currentMode = MODES.find(m => m.id === mode);

  return (
    <div>
      {!accepted && <Disclaimer onAccept={handleAccept} />}

      <div className={!accepted ? 'blur-sm pointer-events-none select-none' : ''}>
        {/* Mode selector */}
        <div className="flex gap-2 mb-6 flex-wrap">
          {MODES.map(m => (
            <button
              key={m.id}
              onClick={() => handleModeChange(m.id)}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-sans font-medium border transition-all duration-200
                ${mode === m.id
                  ? 'bg-stone-900 text-white border-stone-900 shadow-sm'
                  : 'bg-white text-stone-600 border-stone-200 hover:border-stone-400'
                }`}
            >
              <span>{m.icon}</span> {m.label}
            </button>
          ))}
        </div>

        {/* Mode description */}
        <div className={`rounded-xl border p-4 mb-6 ${currentMode.color}`}>
          <p className="text-sm font-sans text-stone-700">{currentMode.note}</p>
        </div>

        {prediction && (
          <>
            {/* Recommendations */}
            <div className="space-y-3 mb-6">
              <h4 className="text-sm font-sans font-medium text-stone-600">推奨馬リスト</h4>
              {prediction.recommendations.map(({ horse: h, score, reason }, i) => (
                <div key={h.id} className="bg-white border border-stone-100 rounded-xl p-4 flex items-center gap-4">
                  <div className="w-7 h-7 rounded-full bg-stone-100 flex items-center justify-center text-sm font-mono font-medium text-stone-600 shrink-0">
                    {i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-serif font-semibold text-stone-900">{h.name}</div>
                    <div className="text-xs text-stone-400 font-sans mt-0.5">{reason}</div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="font-mono text-lg font-semibold text-gold">{score}%</div>
                    <div className="text-xs text-stone-400 font-sans">信頼度</div>
                  </div>
                  <div className="w-16 h-1.5 bg-stone-100 rounded-full overflow-hidden">
                    <div className="h-full bg-gold rounded-full" style={{ width: `${score}%` }} />
                  </div>
                </div>
              ))}
            </div>

            {/* Bet info */}
            <div className="grid grid-cols-2 gap-3 mb-6">
              <div className="bg-stone-50 rounded-xl p-4">
                <div className="text-xs text-stone-400 font-sans mb-1">推奨馬券</div>
                <div className="font-sans font-medium text-stone-800">{prediction.bet_type}</div>
              </div>
              <div className="bg-stone-50 rounded-xl p-4">
                <div className="text-xs text-stone-400 font-sans mb-1">想定オッズ</div>
                <div className="font-mono font-medium text-stone-800">{prediction.odds_range}</div>
              </div>
            </div>
          </>
        )}

        {/* Footer disclaimer */}
        <div className="border-t border-stone-100 pt-4">
          <p className="text-xs text-stone-400 font-sans text-center">
            ⚠️ 本予想は娯楽目的の参考情報です。馬券の購入は自己責任で行ってください。
          </p>
        </div>
      </div>
    </div>
  );
}
