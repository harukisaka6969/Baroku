import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import SearchBar from '../components/SearchBar.jsx';
import HorseCard from '../components/HorseCard.jsx';
import { mockHorses, getFarms, upcomingRaces, getHorseById } from '../mockData.js';
import PredictionPanel from '../components/PredictionPanel.jsx';
import WeeklyBettingPlan from '../components/WeeklyBettingPlan.jsx';

const SEX_OPTIONS    = ['牡', '牝'];
const STATUS_OPTIONS = ['現役', '種牡馬', '繁殖牝馬', '引退'];

const GRADE_COLORS = {
  'G1': 'bg-gold/10 text-gold-dark border border-gold/30',
  'G2': 'bg-purple-50 text-purple-700 border border-purple-200',
  'G3': 'bg-blue-50 text-blue-700 border border-blue-200',
  'OP': 'bg-stone-100 text-stone-600 border border-stone-200',
};

const TABS = [
  { id: 'list',     label: '馬一覧' },
  { id: 'farm',     label: '牧場から選ぶ' },
  { id: 'schedule', label: '今週のレース' },
  { id: 'predict',  label: '🎯 週末予想' },
  { id: 'betting',  label: '💰 今週の買い目' },
];

function FarmSection() {
  const farms = getFarms();
  return (
    <div>
      <p className="text-stone-500 font-sans text-sm mb-6">
        牧場ごとに馬をまとめて確認できます
      </p>
      <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' }}>
        {farms.map((farm, i) => (
          <Link
            key={farm.name}
            to={`/farm/${encodeURIComponent(farm.name)}`}
            className="group bg-white border border-stone-100 rounded-2xl p-5 hover:border-gold hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 animate-fade-up"
            style={{ animationDelay: `${i * 0.05}s` }}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-serif text-lg font-semibold text-stone-900 group-hover:text-gold transition-colors">
                  {farm.name}
                </h3>
                <p className="text-xs text-stone-400 font-sans mt-0.5">{farm.location}</p>
              </div>
              <span className="text-xs bg-stone-100 text-stone-500 px-2 py-0.5 rounded font-sans">
                {farm.horses.length}頭
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5 mt-3">
              {farm.horses.slice(0, 4).map(h => (
                <span key={h.id} className="text-xs bg-stone-50 border border-stone-100 text-stone-600 px-2 py-0.5 rounded font-sans">
                  {h.name}
                </span>
              ))}
              {farm.horses.length > 4 && (
                <span className="text-xs text-stone-400 font-sans self-center">
                  +{farm.horses.length - 4}頭
                </span>
              )}
            </div>
            <div className="mt-3 flex items-center gap-1 text-xs text-stone-400 font-sans">
              <span>G1通算</span>
              <span className="font-mono text-gold font-medium ml-1">
                {farm.horses.reduce((s, h) => s + h.g1_wins, 0)}勝
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

function ScheduleSection() {
  const sorted = [...upcomingRaces].sort((a, b) => a.date.localeCompare(b.date));
  return (
    <div>
      <p className="text-stone-500 font-sans text-sm mb-6">
        今週出走予定の馬を確認できます（モックデータ）
      </p>
      <div className="space-y-4">
        {sorted.map(race => {
          const entries = race.entries.map(id => getHorseById(id)).filter(Boolean);
          return (
            <div key={race.id} className="bg-white border border-stone-100 rounded-2xl p-5 animate-fade-up">
              <div className="flex items-center gap-3 mb-4 flex-wrap">
                <span className="font-mono text-xs text-stone-400">{race.date}</span>
                <h3 className="font-serif text-xl font-semibold text-stone-900">{race.race_name}</h3>
                <span className={`text-xs px-2 py-0.5 rounded font-sans ${GRADE_COLORS[race.grade] || GRADE_COLORS['OP']}`}>
                  {race.grade}
                </span>
                <div className="ml-auto flex gap-3 text-xs text-stone-400 font-sans">
                  <span>{race.course}</span>
                  <span className="font-mono">{race.distance}</span>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {entries.map(horse => (
                  <Link
                    key={horse.id}
                    to={`/horse/${horse.id}`}
                    className="group flex items-center gap-2 bg-stone-50 border border-stone-100 rounded-xl px-3 py-2 hover:border-gold hover:bg-gold/5 transition-all duration-200"
                  >
                    <div>
                      <div className="font-serif text-sm font-medium text-stone-900 group-hover:text-gold transition-colors">
                        {horse.name}
                      </div>
                      <div className="text-xs text-stone-400 font-sans">
                        {horse.sex} · G1 {horse.g1_wins}勝
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function Home() {
  const [query, setQuery]         = useState('');
  const [sexSet, setSexSet]       = useState(new Set());
  const [statusSet, setStatusSet] = useState(new Set());
  const [tab, setTab]             = useState('list');

  const toggleFilter = (set, setter, value) => {
    setter(prev => {
      const next = new Set(prev);
      next.has(value) ? next.delete(value) : next.add(value);
      return next;
    });
  };

  const hasFilter = sexSet.size > 0 || statusSet.size > 0;

  const filtered = useMemo(() => {
    return mockHorses.filter(h => {
      const matchQuery = !query ||
        h.name.includes(query) ||
        h.name_en.toLowerCase().includes(query.toLowerCase()) ||
        h.trainer.includes(query) ||
        h.farm.includes(query) ||
        h.sire.includes(query);
      const matchSex    = sexSet.size === 0    || sexSet.has(h.sex);
      const matchStatus = statusSet.size === 0 || statusSet.has(h.status);
      return matchQuery && matchSex && matchStatus;
    });
  }, [query, sexSet, statusSet]);

  return (
    <div className="min-h-screen bg-cream">
      <header className="sticky top-0 z-30 bg-cream/90 backdrop-blur-md border-b border-stone-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-4">
          <div className="shrink-0">
            <h1 className="font-serif text-2xl font-bold text-stone-900 tracking-wide">馬録</h1>
            <p className="text-xs text-stone-400 font-sans -mt-0.5">Baroku — 競馬馬プロフィール</p>
          </div>
          <div className="flex-1 max-w-md">
            <SearchBar value={query} onChange={setQuery} />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <div className="mb-6 animate-fade-up">
          <h2 className="font-serif text-4xl font-semibold text-stone-900 mb-1">名馬たちの記録</h2>
          <p className="text-stone-500 font-sans text-sm">血統・戦績・牧場・調教師から日本競馬の名馬を探す</p>
        </div>

        {/* Tab navigation */}
        <div className="border-b border-stone-100 mb-6">
          <div className="flex gap-1">
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`px-4 py-2.5 text-sm font-sans font-medium border-b-2 transition-all duration-200
                  ${tab === t.id
                    ? 'border-gold text-gold'
                    : 'border-transparent text-stone-500 hover:text-stone-800'
                  }`}
              >
                {t.id === 'schedule' ? '🏇 ' : ''}{t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab: 馬一覧 */}
        {tab === 'list' && (
          <div>
            {/* Multi-filter */}
            <div className="bg-white border border-stone-100 rounded-2xl p-4 mb-6 space-y-3">
              <div className="flex items-center gap-3 flex-wrap">
                <span className="text-xs text-stone-400 font-sans w-10 shrink-0">性別</span>
                <div className="flex gap-1.5 flex-wrap">
                  {SEX_OPTIONS.map(f => (
                    <button
                      key={f}
                      onClick={() => toggleFilter(sexSet, setSexSet, f)}
                      className={`px-3 py-1 rounded-full text-xs font-sans font-medium border transition-all
                        ${sexSet.has(f)
                          ? 'bg-stone-900 text-white border-stone-900'
                          : 'bg-stone-50 text-stone-600 border-stone-200 hover:border-stone-400'}`}
                    >
                      {f}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-3 flex-wrap">
                <span className="text-xs text-stone-400 font-sans w-10 shrink-0">状態</span>
                <div className="flex gap-1.5 flex-wrap">
                  {STATUS_OPTIONS.map(f => (
                    <button
                      key={f}
                      onClick={() => toggleFilter(statusSet, setStatusSet, f)}
                      className={`px-3 py-1 rounded-full text-xs font-sans font-medium border transition-all
                        ${statusSet.has(f)
                          ? 'bg-stone-900 text-white border-stone-900'
                          : 'bg-stone-50 text-stone-600 border-stone-200 hover:border-stone-400'}`}
                    >
                      {f}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex items-center justify-between pt-1 border-t border-stone-50">
                <span className="text-xs text-stone-400 font-sans">{filtered.length}頭表示中</span>
                {hasFilter && (
                  <button
                    onClick={() => { setSexSet(new Set()); setStatusSet(new Set()); }}
                    className="text-xs text-gold font-sans hover:underline"
                  >
                    フィルターをクリア
                  </button>
                )}
              </div>
            </div>

            {filtered.length > 0 ? (
              <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(270px, 1fr))' }}>
                {filtered.map((horse, i) => (
                  <HorseCard key={horse.id} horse={horse} index={i} />
                ))}
              </div>
            ) : (
              <div className="text-center py-16">
                <p className="font-serif text-xl text-stone-400">該当する馬が見つかりませんでした</p>
                <button
                  onClick={() => { setQuery(''); setSexSet(new Set()); setStatusSet(new Set()); }}
                  className="mt-3 text-sm text-gold font-sans hover:underline"
                >
                  すべてリセット
                </button>
              </div>
            )}
          </div>
        )}

        {/* Tab: 牧場から選ぶ */}
        {tab === 'farm' && <FarmSection />}

        {/* Tab: 今週のレース */}
        {tab === 'schedule' && <ScheduleSection />}

        {/* Tab: 週末予想 */}
        {tab === 'predict' && (
          <div className="max-w-2xl">
            <PredictionPanel />
          </div>
        )}

        {/* Tab: 今週の買い目（AIモデル + 買い方提案） */}
        {tab === 'betting' && (
          <div className="max-w-3xl">
            <WeeklyBettingPlan />
          </div>
        )}
      </main>

      <footer className="border-t border-stone-100 mt-16 py-8">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 text-center">
          <p className="text-xs text-stone-400 font-sans">
            © 2024 馬録 Baroku — 競馬情報は娯楽・参考目的のみです。馬券の購入は自己責任で。
          </p>
        </div>
      </footer>
    </div>
  );
}
