const FIELD_LABELS = {
  born_year: '生年',
  sex: '性別',
  color: '毛色',
  status: 'ステータス',
  farm: '牧場',
  birthplace: '生産地',
  trainer: '調教師',
  stable: '所属',
  owner: 'オーナー',
  jockey: '主戦騎手',
  best_time: 'ベストタイム',
  best_distance: 'ベスト距離',
  best_race: 'ベストレース',
};

export default function HorseDetail({ horse }) {
  const maxWins = Math.max(horse.g1_wins, 1);
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-3 gap-x-8 gap-y-3">
        {Object.entries(FIELD_LABELS).map(([key, label]) => (
          <div key={key} className="flex flex-col">
            <span className="text-xs text-stone-400 font-sans">{label}</span>
            <span className="text-sm text-stone-800 font-sans mt-0.5">
              {key === 'best_time' ? (
                <span className="font-mono">{horse[key]}</span>
              ) : horse[key] ?? '—'}
            </span>
          </div>
        ))}
        <div className="flex flex-col">
          <span className="text-xs text-stone-400 font-sans">総獲得賞金</span>
          <span className="text-sm text-stone-800 font-mono mt-0.5">
            {(horse.earnings / 1e8).toFixed(2)}億円
          </span>
        </div>
      </div>

      {horse.titles?.length > 0 && (
        <div>
          <h4 className="text-sm font-sans font-medium text-stone-600 mb-2">主要タイトル</h4>
          <div className="flex flex-wrap gap-2">
            {horse.titles.map(t => (
              <span key={t} className="text-xs bg-gold/10 text-gold-dark border border-gold/20 px-2 py-1 rounded font-sans">
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

      <div>
        <h4 className="text-sm font-sans font-medium text-stone-600 mb-3">成績</h4>
        <div className="space-y-2">
          {[
            { label: '勝利', value: horse.record.wins, color: 'bg-gold' },
            { label: '敗北', value: horse.record.losses, color: 'bg-stone-300' },
            { label: '着外', value: horse.record.places, color: 'bg-stone-200' },
          ].map(({ label, value, color }) => {
            const total = horse.record.wins + horse.record.losses + horse.record.places;
            const pct = total > 0 ? (value / total) * 100 : 0;
            return (
              <div key={label} className="flex items-center gap-3">
                <span className="text-xs text-stone-500 font-sans w-8">{label}</span>
                <div className="flex-1 h-2 bg-stone-100 rounded-full overflow-hidden">
                  <div className={`h-full ${color} rounded-full transition-all duration-700`} style={{ width: `${pct}%` }} />
                </div>
                <span className="text-xs font-mono text-stone-700 w-6 text-right">{value}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
