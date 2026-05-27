import { useState, useMemo } from 'react';
import SearchBar from '../components/SearchBar.jsx';
import HorseCard from '../components/HorseCard.jsx';
import { mockHorses } from '../mockData.js';

const FILTERS = ['すべて', '牡', '牝', '種牡馬', '繁殖牝馬', '現役'];

export default function Home() {
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('すべて');

  const filtered = useMemo(() => {
    return mockHorses.filter(h => {
      const matchQuery = !query ||
        h.name.includes(query) ||
        h.name_en.toLowerCase().includes(query.toLowerCase()) ||
        h.trainer.includes(query) ||
        h.farm.includes(query) ||
        h.sire.includes(query);

      const matchFilter = filter === 'すべて' ||
        (filter === '牡' && h.sex === '牡') ||
        (filter === '牝' && h.sex === '牝') ||
        h.status === filter;

      return matchQuery && matchFilter;
    });
  }, [query, filter]);

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
        <div className="mb-8 animate-fade-up">
          <h2 className="font-serif text-4xl font-semibold text-stone-900 mb-2">名馬たちの記録</h2>
          <p className="text-stone-500 font-sans">血統・戦績・牧場・調教師から日本競馬の名馬を探す</p>
        </div>

        <div className="flex gap-2 mb-6 flex-wrap animate-fade-up stagger-1">
          {FILTERS.map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-1.5 rounded-full text-sm font-sans font-medium border transition-all duration-200
                ${filter === f
                  ? 'bg-stone-900 text-white border-stone-900'
                  : 'bg-white text-stone-600 border-stone-200 hover:border-stone-400'
                }`}
            >
              {f}
            </button>
          ))}
          <span className="ml-auto text-xs text-stone-400 font-sans self-center">{filtered.length}頭</span>
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
              onClick={() => { setQuery(''); setFilter('すべて'); }}
              className="mt-3 text-sm text-gold font-sans hover:underline"
            >
              フィルターをリセット
            </button>
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
