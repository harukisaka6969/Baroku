export default function HorseDetail({ horse }) {
  const total = horse.record.wins + horse.record.losses + horse.record.places;

  return (
    <div className="space-y-5">
      {/* Key stats */}
      <div className="grid grid-cols-3 gap-3">
        <BigStat label="G1勝利" value={horse.g1_wins} unit="勝" gold />
        <BigStat label="勝率" value={horse.win_rate} unit="%" />
        <BigStat label="獲得賞金" value={(horse.earnings / 1e8).toFixed(1)} unit="億" />
      </div>

      {/* Win rate visual bar */}
      <div className="bg-white border border-stone-100 rounded-xl p-4">
        <p className="text-xs text-stone-400 font-sans mb-2">戦績 {total}戦</p>
        <div className="flex h-3 rounded-full overflow-hidden gap-px mb-2">
          <div className="bg-gold" style={{ width: `${(horse.record.wins / total) * 100}%` }} />
          <div className="bg-stone-200" style={{ width: `${(horse.record.places / total) * 100}%` }} />
          <div className="bg-stone-100 flex-1" />
        </div>
        <div className="flex gap-4 text-xs font-sans text-stone-500">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-gold inline-block" />勝 {horse.record.wins}
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-stone-200 inline-block" />着外 {horse.record.places}
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-stone-100 border border-stone-200 inline-block" />負 {horse.record.losses}
          </span>
        </div>
      </div>

      {/* Basic info grid — minimal */}
      <div className="grid grid-cols-2 gap-x-6 gap-y-3">
        {[
          ['生年', horse.born_year],
          ['性別', `${horse.sex} · ${horse.color}`],
          ['牧場', horse.farm],
          ['調教師', horse.trainer],
          ['所属', horse.stable],
          ['主戦騎手', horse.jockey],
          ['ベストタイム', horse.best_time],
          ['ベストレース', horse.best_race],
        ].map(([label, val]) => (
          <div key={label}>
            <div className="text-xs text-stone-400 font-sans">{label}</div>
            <div className="text-sm font-sans text-stone-800 mt-0.5 truncate">{val || '—'}</div>
          </div>
        ))}
      </div>

      {/* Titles */}
      {horse.titles?.length > 0 && (
        <div>
          <div className="text-xs text-stone-400 font-sans mb-2">主要タイトル</div>
          <div className="flex flex-wrap gap-1.5">
            {horse.titles.map(t => (
              <span key={t} className="text-xs bg-gold/10 text-gold-dark border border-gold/20 px-2 py-0.5 rounded-full font-sans">
                {t}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function BigStat({ label, value, unit, gold }) {
  return (
    <div className="bg-white border border-stone-100 rounded-xl p-3 text-center">
      <div className={`font-mono text-2xl font-bold ${gold ? 'text-gold' : 'text-stone-900'}`}>
        {value}<span className="text-sm font-sans text-stone-400 ml-0.5">{unit}</span>
      </div>
      <div className="text-xs text-stone-400 font-sans mt-0.5">{label}</div>
    </div>
  );
}
