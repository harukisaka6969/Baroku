export default function PedigreeChart({ horse }) {
  return (
    <div className="space-y-8">
      {/* Visual pedigree tree */}
      <div>
        <h4 className="text-sm font-sans font-medium text-stone-500 mb-4 uppercase tracking-wider">3代血統表</h4>
        <div className="overflow-x-auto">
          <div className="min-w-[580px]">
            <PedigreeTree horse={horse} />
          </div>
        </div>
      </div>

      {/* Blood summary */}
      <div className="bg-stone-50 rounded-2xl p-5">
        <h4 className="text-sm font-sans font-medium text-stone-600 mb-3">血統サマリー</h4>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
          <InfoItem label="父" value={horse.sire} />
          <InfoItem label="母" value={horse.dam} />
          <InfoItem label="父父" value={horse.sire_of_sire} />
          <InfoItem label="父母" value={horse.dam_of_sire} />
          <InfoItem label="母父" value={horse.sire_of_dam} />
          <InfoItem label="母母" value={horse.dam_of_dam} />
        </div>
        <p className="text-sm text-stone-600 font-sans leading-relaxed">
          {horse.name}は<strong className="text-stone-800">{horse.sire}</strong>を父に持ち、
          母方には<strong className="text-stone-800">{horse.sire_of_dam}</strong>の血を引く。
          {(horse.sire === 'サンデーサイレンス' || horse.sire_of_sire === 'サンデーサイレンス') &&
            'サンデーサイレンス系の豊富なスタミナと切れ味を受け継ぐ。'}
          {horse.g1_wins}つのG1タイトルが示す通り、トップクラスの血統構成となっている。
        </p>
      </div>
    </div>
  );
}

function PedigreeTree({ horse }) {
  return (
    <div className="flex items-stretch gap-0">
      {/* Col 1: Self */}
      <div className="flex items-center w-36 shrink-0 pr-2">
        <PedigreeBox name={horse.name} sub={horse.name_en} highlight />
      </div>

      {/* Connector 1→2 */}
      <div className="flex flex-col justify-around w-4 shrink-0">
        <HBranch top />
        <HBranch bottom />
      </div>

      {/* Col 2: Parents */}
      <div className="flex flex-col gap-4 w-32 shrink-0 justify-around pr-2">
        <PedigreeBox name={horse.sire} label="父" />
        <PedigreeBox name={horse.dam} label="母" />
      </div>

      {/* Connector 2→3 */}
      <div className="flex flex-col w-4 shrink-0">
        <div className="flex-1 flex flex-col justify-around">
          <HBranch top small />
          <HBranch bottom small />
        </div>
        <div className="flex-1 flex flex-col justify-around">
          <HBranch top small />
          <HBranch bottom small />
        </div>
      </div>

      {/* Col 3: Grandparents */}
      <div className="flex flex-col gap-2 w-36 shrink-0 justify-around">
        <PedigreeBox name={horse.sire_of_sire} label="父父" small />
        <PedigreeBox name={horse.dam_of_sire} label="父母" small />
        <PedigreeBox name={horse.sire_of_dam} label="母父" small />
        <PedigreeBox name={horse.dam_of_dam} label="母母" small />
      </div>
    </div>
  );
}

function PedigreeBox({ name, sub, label, highlight, small }) {
  return (
    <div className={`w-full rounded-xl border text-center px-2
      ${small ? 'py-1.5' : 'py-3'}
      ${highlight
        ? 'bg-gold/10 border-gold/40 shadow-sm'
        : 'bg-white border-stone-100 hover:border-gold/40 transition-colors'
      }`}
    >
      {label && (
        <div className="text-stone-400 font-sans mb-0.5" style={{ fontSize: '10px' }}>{label}</div>
      )}
      <div className={`font-serif font-semibold text-stone-900 leading-tight
        ${small ? 'text-xs' : highlight ? 'text-base' : 'text-sm'}`}>
        {name || '—'}
      </div>
      {sub && (
        <div className="text-stone-400 font-sans mt-0.5" style={{ fontSize: '10px' }}>{sub}</div>
      )}
    </div>
  );
}

function HBranch({ top, bottom, small }) {
  return (
    <div className={`flex-1 relative ${small ? '' : ''}`}>
      <div className={`absolute inset-0 border-stone-200
        ${top ? 'border-r border-b rounded-br-md' : ''}
        ${bottom ? 'border-r border-t rounded-tr-md' : ''}
      `} />
    </div>
  );
}

function InfoItem({ label, value }) {
  return (
    <div>
      <div className="text-xs text-stone-400 font-sans">{label}</div>
      <div className="text-sm font-serif font-medium text-stone-800 mt-0.5">{value || '—'}</div>
    </div>
  );
}
