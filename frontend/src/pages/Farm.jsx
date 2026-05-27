import { useParams, Link } from 'react-router-dom';
import { getHorsesByFarm } from '../mockData.js';
import HorseCard from '../components/HorseCard.jsx';

export default function Farm() {
  const { name } = useParams();
  const farmName = decodeURIComponent(name);
  const horses = getHorsesByFarm(farmName);

  if (horses.length === 0) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-center">
          <p className="font-serif text-2xl text-stone-400">牧場が見つかりませんでした</p>
          <Link to="/" className="mt-4 inline-block text-gold font-sans hover:underline">← トップに戻る</Link>
        </div>
      </div>
    );
  }

  const location = horses[0]?.birthplace || '';
  const totalG1 = horses.reduce((s, h) => s + h.g1_wins, 0);
  const totalEarnings = horses.reduce((s, h) => s + h.earnings, 0);

  return (
    <div className="min-h-screen bg-cream">
      <header className="sticky top-0 z-30 bg-cream/90 backdrop-blur-md border-b border-stone-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-3">
          <Link to="/" className="text-stone-400 hover:text-stone-700 transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <Link to="/" className="font-serif text-lg font-bold text-stone-900">馬録</Link>
          <span className="text-stone-200">/</span>
          <span className="font-serif text-lg text-stone-600">{farmName}</span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <div className="mb-8 animate-fade-up">
          <h1 className="font-serif text-4xl font-bold text-stone-900 mb-1">{farmName}</h1>
          <p className="text-stone-400 font-sans">{location}</p>

          <div className="flex gap-8 mt-4">
            <div>
              <div className="font-mono text-2xl font-semibold text-stone-900">{horses.length}<span className="text-sm text-stone-400 font-sans ml-1">頭</span></div>
              <div className="text-xs text-stone-400 font-sans">登録馬数</div>
            </div>
            <div>
              <div className="font-mono text-2xl font-semibold text-gold">{totalG1}<span className="text-sm text-stone-400 font-sans ml-1">勝</span></div>
              <div className="text-xs text-stone-400 font-sans">G1通算</div>
            </div>
            <div>
              <div className="font-mono text-2xl font-semibold text-stone-900">{(totalEarnings / 1e8).toFixed(1)}<span className="text-sm text-stone-400 font-sans ml-1">億円</span></div>
              <div className="text-xs text-stone-400 font-sans">通算賞金</div>
            </div>
          </div>
        </div>

        <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(270px, 1fr))' }}>
          {horses.map((horse, i) => (
            <HorseCard key={horse.id} horse={horse} index={i} />
          ))}
        </div>
      </main>

      <footer className="border-t border-stone-100 mt-16 py-8">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 text-center">
          <p className="text-xs text-stone-400 font-sans">
            © 2024 馬録 Baroku — 競馬情報は娯楽・参考目的のみです。
          </p>
        </div>
      </footer>
    </div>
  );
}
