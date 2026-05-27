import { Link } from 'react-router-dom';

const STATUS_COLORS = {
  '現役': 'bg-emerald-100 text-emerald-700',
  '種牡馬': 'bg-blue-100 text-blue-700',
  '繁殖牝馬': 'bg-pink-100 text-pink-700',
  '引退': 'bg-stone-100 text-stone-600',
};

function WinRateArc({ rate }) {
  const r = 22;
  const cx = 28, cy = 28;
  const circumference = 2 * Math.PI * r;
  const offset = circumference * (1 - rate / 100);
  return (
    <svg width="56" height="56" viewBox="0 0 56 56" className="shrink-0">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#e7e5e4" strokeWidth="5" />
      <circle
        cx={cx} cy={cy} r={r} fill="none"
        stroke="#C4922A" strokeWidth="5"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        transform={`rotate(-90 ${cx} ${cy})`}
      />
      <text x={cx} y={cy + 4} textAnchor="middle"
        style={{ fontSize: '11px', fontFamily: 'DM Mono, monospace', fill: '#292524', fontWeight: 600 }}>
        {rate}%
      </text>
    </svg>
  );
}

function StatBar({ label, value, max, color }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-stone-400 font-sans w-4">{label}</span>
      <div className="flex-1 h-1.5 bg-stone-100 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-stone-600 w-4 text-right">{value}</span>
    </div>
  );
}

function MiniInfo({ icon, value }) {
  return (
    <div className="flex items-center gap-1.5 text-xs text-stone-500 font-sans">
      <span className="text-stone-300">{icon}</span>
      <span className="truncate">{value}</span>
    </div>
  );
}

export default function HorseCard({ horse, index }) {
  const delay = index < 6 ? `stagger-${(index % 6) + 1}` : '';
  return (
    <Link
      to={`/horse/${horse.id}`}
      className={`group block bg-white rounded-2xl border border-stone-100 p-4 opacity-0-init animate-fade-up ${delay}
        hover:border-gold hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200`}
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="min-w-0">
          <h3 className="font-serif text-lg font-semibold text-stone-900 group-hover:text-gold transition-colors leading-tight truncate">
            {horse.name}
          </h3>
          <p className="text-xs text-stone-400 font-sans truncate">{horse.name_en}</p>
        </div>
        <span className={`text-xs px-2 py-0.5 rounded-full font-sans font-medium shrink-0 ${STATUS_COLORS[horse.status] || STATUS_COLORS['引退']}`}>
          {horse.status}
        </span>
      </div>

      <div className="flex items-center gap-3 mb-3">
        <WinRateArc rate={horse.win_rate} />
        <div className="flex-1 space-y-1.5">
          <StatBar label="G1" value={horse.g1_wins} max={10} color="bg-gold" />
          <StatBar label="勝" value={horse.record.wins} max={20} color="bg-stone-400" />
        </div>
      </div>

      <div className="border-t border-stone-50 pt-2.5 space-y-1">
        <MiniInfo icon="♘" value={horse.sire} />
        <MiniInfo icon="⌂" value={horse.farm} />
      </div>
    </Link>
  );
}
