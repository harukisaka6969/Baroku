import { Link } from 'react-router-dom';

const STATUS_COLORS = {
  '現役': 'bg-emerald-100 text-emerald-700',
  '種牡馬': 'bg-blue-100 text-blue-700',
  '繁殖牝馬': 'bg-pink-100 text-pink-700',
  '引退': 'bg-stone-100 text-stone-600',
};

export default function HorseCard({ horse, index }) {
  const delay = index < 6 ? `stagger-${(index % 6) + 1}` : '';
  return (
    <Link
      to={`/horse/${horse.id}`}
      className={`group block bg-white rounded-2xl border border-stone-100 p-5 opacity-0-init animate-fade-up ${delay}
        hover:border-gold hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200`}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-serif text-xl font-semibold text-stone-900 group-hover:text-gold transition-colors">
            {horse.name}
          </h3>
          <p className="text-xs text-stone-400 font-sans mt-0.5">{horse.name_en}</p>
        </div>
        <span className={`text-xs px-2 py-0.5 rounded-full font-sans font-medium ${STATUS_COLORS[horse.status] || STATUS_COLORS['引退']}`}>
          {horse.status}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-3">
        <Stat label="勝率" value={`${horse.win_rate}%`} />
        <Stat label="戦績" value={`${horse.record.wins}-${horse.record.losses}-${horse.record.places}`} />
        <Stat label="G1" value={`${horse.g1_wins}勝`} />
      </div>

      <div className="border-t border-stone-50 pt-3 space-y-1">
        <InfoRow label="父" value={horse.sire} />
        <InfoRow label="牧場" value={horse.farm} />
        <InfoRow label="調教師" value={horse.trainer} />
      </div>

      <div className="mt-3 flex items-center gap-2">
        <span className="text-xs bg-stone-100 text-stone-500 px-2 py-0.5 rounded font-sans">{horse.sex}</span>
        <span className="text-xs text-stone-400 font-sans">{horse.born_year}年生</span>
        {horse.g1_wins > 0 && (
          <span className="text-xs bg-gold/10 text-gold px-2 py-0.5 rounded font-sans ml-auto">
            G1 {horse.g1_wins}勝
          </span>
        )}
      </div>
    </Link>
  );
}

function Stat({ label, value }) {
  return (
    <div className="text-center">
      <div className="font-mono text-base font-medium text-stone-800">{value}</div>
      <div className="text-xs text-stone-400 font-sans">{label}</div>
    </div>
  );
}

function InfoRow({ label, value }) {
  return (
    <div className="flex gap-2 text-xs">
      <span className="text-stone-400 font-sans w-8 shrink-0">{label}</span>
      <span className="text-stone-700 font-sans truncate">{value}</span>
    </div>
  );
}
