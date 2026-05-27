import { Link } from 'react-router-dom';
import { getDescendants, getSiblings } from '../mockData.js';

export default function PedigreeChart({ horse }) {
  const descendants = getDescendants(horse.name);
  const siblings = getSiblings(horse);

  return (
    <div className="space-y-8">
      {/* Ancestor tree */}
      <div>
        <SectionLabel>祖先 — 3代血統</SectionLabel>
        <div className="overflow-x-auto pb-2">
          <AncestorTree horse={horse} />
        </div>
      </div>

      {/* Descendants */}
      {descendants.length > 0 && (
        <div>
          <SectionLabel>産駒 / 関連馬（データベース内）</SectionLabel>
          <div className="flex flex-wrap gap-2">
            {descendants.map(h => (
              <RelativeChip
                key={h.id}
                horse={h}
                badge={h.sire === horse.name ? '父系産駒' : '母系産駒'}
                badgeColor="bg-blue-50 text-blue-600 border-blue-200"
              />
            ))}
          </div>
        </div>
      )}

      {/* Same-sire siblings */}
      {siblings.length > 0 && (
        <div>
          <SectionLabel>同父馬 — {horse.sire}産駒</SectionLabel>
          <div className="flex flex-wrap gap-2">
            {siblings.map(h => (
              <RelativeChip
                key={h.id}
                horse={h}
                badge="同父"
                badgeColor="bg-emerald-50 text-emerald-600 border-emerald-200"
              />
            ))}
          </div>
        </div>
      )}

      {descendants.length === 0 && siblings.length === 0 && (
        <p className="text-sm text-stone-400 font-sans">
          データベース内に産駒・同父馬は登録されていません
        </p>
      )}
    </div>
  );
}

/* ── Ancestor tree ─────────────────────────────── */

function AncestorTree({ horse }) {
  const nodes = [
    { name: horse.name,          sub: horse.name_en, self: true },
    { name: horse.sire,          label: '父' },
    { name: horse.dam,           label: '母' },
    { name: horse.sire_of_sire,  label: '父父' },
    { name: horse.dam_of_sire,   label: '父母' },
    { name: horse.sire_of_dam,   label: '母父' },
    { name: horse.dam_of_dam,    label: '母母' },
  ];

  return (
    <div className="flex items-center min-w-[540px]" style={{ height: 240 }}>
      {/* Col 0: self */}
      <div className="flex items-center h-full w-36 shrink-0">
        <TreeBox node={nodes[0]} />
      </div>

      {/* Branch 0→1 */}
      <div className="relative flex-none w-8 h-full">
        {/* vertical centre line */}
        <div className="absolute left-0 top-1/4 bottom-1/4 border-l border-stone-200" />
        {/* top arm */}
        <div className="absolute left-0 top-1/4 w-full border-t border-stone-200" />
        {/* bottom arm */}
        <div className="absolute left-0 bottom-1/4 w-full border-t border-stone-200" />
      </div>

      {/* Col 1: parents */}
      <div className="flex flex-col h-full w-32 shrink-0 justify-around py-1">
        <TreeBox node={nodes[1]} />
        <TreeBox node={nodes[2]} />
      </div>

      {/* Branch 1→2 */}
      <div className="relative flex-none w-8 h-full">
        <div className="absolute left-0 top-[12.5%] bottom-[12.5%] border-l border-stone-200" />
        <div className="absolute left-0 top-[12.5%] w-full border-t border-stone-200" />
        <div className="absolute left-0 top-[37.5%] w-full border-t border-stone-200" />
        <div className="absolute left-0 top-[62.5%] w-full border-t border-stone-200" />
        <div className="absolute left-0 bottom-[12.5%] w-full border-t border-stone-200" />
      </div>

      {/* Col 2: grandparents */}
      <div className="flex flex-col h-full w-36 shrink-0 justify-around py-1">
        <TreeBox node={nodes[3]} small />
        <TreeBox node={nodes[4]} small />
        <TreeBox node={nodes[5]} small />
        <TreeBox node={nodes[6]} small />
      </div>
    </div>
  );
}

function TreeBox({ node, small }) {
  const base = `w-full rounded-xl border text-center transition-colors
    ${small ? 'py-1.5 px-2' : 'py-3 px-3'}
    ${node.self
      ? 'bg-gold/10 border-gold/40 shadow-sm'
      : 'bg-white border-stone-100 hover:border-gold/30'}`;
  return (
    <div className={base}>
      {node.label && (
        <div className="text-stone-400 font-sans leading-none mb-0.5" style={{ fontSize: 9 }}>
          {node.label}
        </div>
      )}
      <div className={`font-serif font-semibold text-stone-900 leading-tight
        ${small ? 'text-xs' : node.self ? 'text-base' : 'text-sm'}`}>
        {node.name || '—'}
      </div>
      {node.sub && (
        <div className="text-stone-400 font-sans mt-0.5" style={{ fontSize: 9 }}>{node.sub}</div>
      )}
    </div>
  );
}

/* ── Relative chip ─────────────────────────────── */

function RelativeChip({ horse, badge, badgeColor }) {
  return (
    <Link
      to={`/horse/${horse.id}`}
      className="flex items-center gap-2 bg-white border border-stone-100 rounded-xl px-3 py-2
        hover:border-gold hover:shadow-sm transition-all duration-200 group"
    >
      <div>
        <div className="font-serif text-sm font-semibold text-stone-900 group-hover:text-gold transition-colors">
          {horse.name}
        </div>
        <div className="text-xs text-stone-400 font-sans">{horse.born_year}年 · G1 {horse.g1_wins}勝</div>
      </div>
      <span className={`text-xs px-1.5 py-0.5 rounded border font-sans shrink-0 ${badgeColor}`}>
        {badge}
      </span>
    </Link>
  );
}

function SectionLabel({ children }) {
  return (
    <p className="text-xs text-stone-400 font-sans uppercase tracking-wider mb-3">{children}</p>
  );
}
