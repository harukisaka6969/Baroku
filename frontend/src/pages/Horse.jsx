import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import HorseDetail from '../components/HorseDetail.jsx';
import PedigreeChart from '../components/PedigreeChart.jsx';
import RaceHistory from '../components/RaceHistory.jsx';
import RelatedHorses from '../components/RelatedHorses.jsx';
import PredictionPanel from '../components/PredictionPanel.jsx';
import { getHorseById, getRelatedHorses, mockHorses } from '../mockData.js';

const STATUS_COLORS = {
  '現役': 'bg-emerald-100 text-emerald-700',
  '種牡馬': 'bg-blue-100 text-blue-700',
  '繁殖牝馬': 'bg-pink-100 text-pink-700',
  '引退': 'bg-stone-100 text-stone-600',
};

const TABS = [
  { id: 'overview', label: '概要' },
  { id: 'pedigree', label: '血統' },
  { id: 'races', label: 'レース歴' },
  { id: 'related', label: '関連' },
  { id: 'prediction', label: '予想' },
];

export default function Horse() {
  const { id } = useParams();
  const horse = getHorseById(id);
  const [tab, setTab] = useState('overview');

  if (!horse) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-center">
          <p className="font-serif text-2xl text-stone-400">馬が見つかりませんでした</p>
          <Link to="/" className="mt-4 inline-block text-gold font-sans hover:underline">← 一覧に戻る</Link>
        </div>
      </div>
    );
  }

  const related = getRelatedHorses(horse);

  return (
    <div className="min-h-screen bg-cream">
      <header className="sticky top-0 z-30 bg-cream/90 backdrop-blur-md border-b border-stone-100">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-3">
          <Link to="/" className="text-stone-400 hover:text-stone-700 transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <Link to="/" className="font-serif text-lg font-bold text-stone-900">馬録</Link>
          <span className="text-stone-200">/</span>
          <span className="font-serif text-lg text-stone-600">{horse.name}</span>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <div className="mb-8 animate-fade-up">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <div className="flex items-center gap-3 mb-1 flex-wrap">
                <h1 className="font-serif text-4xl font-bold text-stone-900">{horse.name}</h1>
                <span className={`text-sm px-2.5 py-0.5 rounded-full font-sans font-medium ${STATUS_COLORS[horse.status] || STATUS_COLORS['引退']}`}>
                  {horse.status}
                </span>
              </div>
              <p className="text-stone-400 font-sans">{horse.name_en} · {horse.born_year}年生 · {horse.sex} · {horse.color}</p>
            </div>
            <div className="flex gap-6">
              <StatBig label="G1勝利" value={String(horse.g1_wins)} unit="勝" />
              <StatBig label="勝率" value={String(horse.win_rate)} unit="%" />
              <StatBig label="賞金" value={(horse.earnings / 1e8).toFixed(1)} unit="億円" />
            </div>
          </div>
        </div>

        <div className="border-b border-stone-100 mb-6">
          <div className="flex gap-1 overflow-x-auto">
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`px-4 py-2.5 text-sm font-sans font-medium whitespace-nowrap border-b-2 transition-all duration-200
                  ${tab === t.id
                    ? 'border-gold text-gold'
                    : 'border-transparent text-stone-500 hover:text-stone-800'
                  }`}
              >
                {t.id === 'prediction' ? '🎯 ' : ''}{t.label}
              </button>
            ))}
          </div>
        </div>

        <div className="animate-fade-up">
          {tab === 'overview' && <HorseDetail horse={horse} />}
          {tab === 'pedigree' && <PedigreeChart horse={horse} />}
          {tab === 'races' && <RaceHistory races={horse.races} />}
          {tab === 'related' && <RelatedHorses related={related} horse={horse} />}
          {tab === 'prediction' && <PredictionPanel horse={horse} allHorses={mockHorses} />}
        </div>
      </main>

      <footer className="border-t border-stone-100 mt-16 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <p className="text-xs text-stone-400 font-sans">
            © 2024 馬録 Baroku — 競馬情報は娯楽・参考目的のみです。馬券の購入は自己責任で。
          </p>
        </div>
      </footer>
    </div>
  );
}

function StatBig({ label, value, unit }) {
  return (
    <div className="text-right">
      <div className="font-mono text-2xl font-semibold text-stone-900">
        {value}<span className="text-sm text-stone-400 font-sans ml-0.5">{unit}</span>
      </div>
      <div className="text-xs text-stone-400 font-sans">{label}</div>
    </div>
  );
}
