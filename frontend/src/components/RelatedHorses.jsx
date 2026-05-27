import { Link } from 'react-router-dom';

export default function RelatedHorses({ related, horse }) {
  const sections = [
    { title: `同牧場（${horse.farm}）`, horses: related.sameFarm },
    { title: `同調教師（${horse.trainer}）`, horses: related.sameTrainer },
    { title: `同父（${horse.sire}）`, horses: related.sameSire },
  ].filter(s => s.horses.length > 0);

  if (sections.length === 0) {
    return <p className="text-stone-400 font-sans text-sm">関連馬データがありません。</p>;
  }

  return (
    <div className="space-y-6">
      {sections.map(({ title, horses }) => (
        <div key={title}>
          <h4 className="text-sm font-sans font-medium text-stone-600 mb-3">{title}</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {horses.map(h => (
              <Link
                key={h.id}
                to={`/horse/${h.id}`}
                className="bg-white border border-stone-100 rounded-xl p-3 hover:border-gold hover:shadow-md transition-all duration-200 group"
              >
                <div className="font-serif text-sm font-semibold text-stone-900 group-hover:text-gold transition-colors">
                  {h.name}
                </div>
                <div className="text-xs text-stone-400 font-sans mt-0.5">{h.name_en}</div>
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-xs text-stone-500 font-sans">G1 {h.g1_wins}勝</span>
                  <span className="text-xs text-stone-300">·</span>
                  <span className="text-xs text-stone-500 font-mono">{h.win_rate}%</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
