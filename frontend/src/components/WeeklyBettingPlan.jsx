import { useState, useEffect } from 'react';
import Disclaimer from './Disclaimer.jsx';
import { fetchWeeklyPlan } from '../api.js';
import { mockWeeklyPlan } from '../mockData.js';

const BET_COLORS = {
  '複勝': 'bg-emerald-50 text-emerald-700 border-emerald-200',
  '単勝': 'bg-blue-50 text-blue-700 border-blue-200',
  '馬連': 'bg-purple-50 text-purple-700 border-purple-200',
  'ワイド': 'bg-purple-50 text-purple-700 border-purple-200',
  '三連複': 'bg-gold/10 text-gold-dark border-gold/30',
};

function yen(n) {
  return `¥${Number(n).toLocaleString()}`;
}

function RaceCard({ race }) {
  const { plan } = race;
  return (
    <div className="bg-white border border-stone-100 rounded-2xl p-4 sm:p-5 animate-fade-up">
      <div className="flex items-center gap-2 flex-wrap mb-3">
        <span className="font-mono text-xs text-stone-400">{race.date}</span>
        <h3 className="font-serif text-lg font-semibold text-stone-900">{race.race_name}</h3>
        <span className="text-xs bg-stone-100 text-stone-500 px-2 py-0.5 rounded font-sans">
          {race.racecourse}
        </span>
      </div>

      {/* Predicted ranking */}
      <div className="space-y-1.5 mb-4">
        {[...race.predictions]
          .sort((a, b) => b.p_place - a.p_place)
          .slice(0, 5)
          .map(p => (
            <div key={p.horse_id} className="flex items-center gap-2 text-sm">
              <span className="font-mono text-xs text-stone-400 w-6 text-right">{p.horse_number}</span>
              <span className="font-serif text-stone-800 flex-1 truncate">{p.horse_name}</span>
              <span className="font-mono text-xs text-stone-400">単勝 {p.odds_win ?? '-'}倍</span>
              <div className="w-20 h-1.5 bg-stone-100 rounded-full overflow-hidden shrink-0">
                <div
                  className="h-full bg-gold rounded-full"
                  style={{ width: `${Math.round(p.p_place * 100)}%` }}
                />
              </div>
              <span className="font-mono text-xs text-stone-500 w-10 text-right">
                {Math.round(p.p_place * 100)}%
              </span>
            </div>
          ))}
      </div>

      {/* Betting plan */}
      {plan.tickets.length > 0 ? (
        <div className="space-y-2 border-t border-stone-100 pt-3">
          {plan.tickets.map((t, i) => (
            <div key={i} className="flex items-center gap-2 flex-wrap text-sm">
              <span className={`text-xs px-2 py-0.5 rounded border font-sans font-medium shrink-0 ${BET_COLORS[t.bet_type] || 'bg-stone-100 text-stone-600 border-stone-200'}`}>
                {t.bet_type}
              </span>
              <span className="font-serif text-stone-800">{t.target}</span>
              <span className="font-mono text-xs text-stone-400">オッズ{t.odds}倍</span>
              <span className="ml-auto font-mono font-semibold text-stone-900">{yen(t.stake)}</span>
            </div>
          ))}
          <div className="flex items-center justify-between pt-2 border-t border-stone-50 text-xs text-stone-400 font-sans">
            <span>このレースの購入額合計</span>
            <span className="font-mono font-semibold text-gold">{yen(plan.total_stake)}</span>
          </div>
        </div>
      ) : (
        <p className="text-center text-stone-400 font-sans text-sm border-t border-stone-100 pt-3">
          {plan.note || '見送り推奨'}
        </p>
      )}
    </div>
  );
}

export default function WeeklyBettingPlan() {
  const [accepted, setAccepted] = useState(false);
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const today = new Date();
        const from = today.toISOString().slice(0, 10);
        const to = new Date(today.getTime() + 7 * 86400000).toISOString().slice(0, 10);
        const data = await fetchWeeklyPlan(from, to, 5000);
        if (!cancelled) setPlan(data && data.races.length > 0 ? data : mockWeeklyPlan);
      } catch {
        if (!cancelled) setPlan(mockWeeklyPlan);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return <p className="text-center text-stone-400 font-sans text-sm py-8">読み込み中…</p>;
  }
  if (!plan) {
    return <p className="text-center text-stone-400 font-sans text-sm py-8">データを取得できませんでした</p>;
  }

  return (
    <div className="space-y-5">
      {!accepted && <Disclaimer onAccept={() => setAccepted(true)} />}

      <div className={!accepted ? 'blur-sm pointer-events-none select-none' : ''}>
        {/* Weekly summary */}
        <div className="bg-stone-900 text-white rounded-2xl p-4 sm:p-5 mb-5 flex items-center gap-4 flex-wrap">
          <div>
            <div className="text-xs text-stone-400 font-sans">週間予算</div>
            <div className="font-mono text-xl font-semibold">{yen(plan.weekly_budget)}</div>
          </div>
          <div>
            <div className="text-xs text-stone-400 font-sans">今週の購入予定額</div>
            <div className="font-mono text-xl font-semibold text-gold">{yen(plan.total_stake)}</div>
          </div>
          <div>
            <div className="text-xs text-stone-400 font-sans">残し（資金温存）</div>
            <div className="font-mono text-xl font-semibold">{yen(plan.weekly_budget - plan.total_stake)}</div>
          </div>
          <div className="ml-auto text-xs text-stone-400 font-sans">
            モデル: {plan.model_status === 'trained' ? '学習済みモデル' : 'ヒューリスティック（学習データ蓄積中）'}
          </div>
        </div>

        <div className="space-y-4">
          {plan.races.map(race => (
            <RaceCard key={race.race_id} race={race} />
          ))}
        </div>

        <p className="text-center text-xs text-stone-300 font-sans pt-4">
          ⚠️ 複勝を中心に損失を抑えつつ、期待値プラスの買い目にのみ資金を配分しています。期待値プラスの買い目がない週は購入を見送ります。
        </p>
      </div>
    </div>
  );
}
