const GRADE_COLORS = {
  'G1': 'bg-gold/10 text-gold-dark border border-gold/30',
  'G2': 'bg-purple-50 text-purple-700 border border-purple-200',
  'G3': 'bg-blue-50 text-blue-700 border border-blue-200',
  'OP': 'bg-stone-100 text-stone-600 border border-stone-200',
};

const POS_COLORS = {
  1: 'text-gold font-bold',
  2: 'text-stone-500',
  3: 'text-amber-700',
};

export default function RaceHistory({ races }) {
  if (!races?.length) {
    return <p className="text-stone-400 font-sans text-sm">レース歴データがありません。</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm min-w-[640px]">
        <thead>
          <tr className="border-b border-stone-100">
            {['日付', 'レース名', '格', '着順', '騎手', 'タイム', '距離', '賞金'].map(h => (
              <th key={h} className="text-left text-xs text-stone-400 font-sans font-medium py-2 pr-4 last:pr-0">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {races.map((race, i) => (
            <tr key={race.id} className="border-b border-stone-50 hover:bg-stone-50/50 transition-colors">
              <td className="py-2.5 pr-4 text-stone-500 font-mono text-xs">{race.date}</td>
              <td className="py-2.5 pr-4 font-sans text-stone-800">{race.race_name}</td>
              <td className="py-2.5 pr-4">
                <span className={`text-xs px-1.5 py-0.5 rounded font-sans ${GRADE_COLORS[race.grade] || GRADE_COLORS['OP']}`}>
                  {race.grade}
                </span>
              </td>
              <td className={`py-2.5 pr-4 font-mono ${POS_COLORS[race.position] || 'text-stone-700'}`}>
                {race.position}着
              </td>
              <td className="py-2.5 pr-4 text-stone-600 font-sans">{race.jockey}</td>
              <td className="py-2.5 pr-4 text-stone-700 font-mono">{race.time}</td>
              <td className="py-2.5 pr-4 text-stone-600 font-mono">{race.distance}</td>
              <td className="py-2.5 text-stone-500 font-mono text-xs">
                {race.prize ? `${(race.prize / 1e6).toFixed(0)}万円` : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
