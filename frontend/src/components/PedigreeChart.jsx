export default function PedigreeChart({ horse }) {
  const gen3 = [
    horse.sire_of_sire, horse.dam_of_sire,
    horse.sire_of_dam, horse.dam_of_dam,
  ];

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[600px]">
        <div className="grid grid-cols-4 gap-2 items-center">
          {/* Generation labels */}
          <div className="col-span-1 text-xs text-stone-400 font-sans text-center mb-1">本馬</div>
          <div className="col-span-1 text-xs text-stone-400 font-sans text-center mb-1">父・母</div>
          <div className="col-span-2 text-xs text-stone-400 font-sans text-center mb-1">祖父・祖母</div>
        </div>

        <div className="grid gap-2" style={{ gridTemplateRows: 'repeat(4, auto)' }}>
          {/* Row 1: horse name spanning all */}
          <div className="grid grid-cols-4 gap-2">
            <div className="row-span-4 flex items-center justify-center bg-gold/10 border border-gold/30 rounded-xl p-3 col-span-1">
              <div className="text-center">
                <div className="font-serif text-base font-semibold text-stone-900">{horse.name}</div>
                <div className="text-xs text-stone-400 mt-1">{horse.name_en}</div>
                <div className="text-xs text-stone-500 mt-1">{horse.born_year}年生 {horse.sex}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Actual pedigree grid */}
        <div className="mt-2 grid grid-cols-4 gap-2">
          {/* Sire column */}
          <PedigreeCell name={horse.sire} label="父" className="col-start-2 row-start-1 row-span-2 self-center" />
          <PedigreeCell name={horse.sire_of_sire} label="父父" />
          <PedigreeCell name={horse.dam_of_sire} label="父母" />

          {/* Dam column */}
          <PedigreeCell name={horse.dam} label="母" className="col-start-2 row-start-3 row-span-2 self-center" />
          <PedigreeCell name={horse.sire_of_dam} label="母父" />
          <PedigreeCell name={horse.dam_of_dam} label="母母" />
        </div>

        {/* Simple 3-gen visual */}
        <div className="mt-6">
          <h4 className="text-sm font-sans font-medium text-stone-600 mb-3">3代血統</h4>
          <div className="grid grid-cols-7 gap-1 text-xs">
            {/* Col 1: Horse */}
            <div className="col-span-1 row-span-4 flex items-center">
              <PedigreeBox name={horse.name} highlight />
            </div>
            {/* Col 2-3: Parents */}
            <div className="col-span-2 col-start-2 row-span-2 flex items-center">
              <PedigreeBox name={horse.sire} label="父" />
            </div>
            <div className="col-span-2 col-start-2 row-span-2 flex items-center">
              <PedigreeBox name={horse.dam} label="母" />
            </div>
            {/* Col 4-7: Grandparents */}
            <div className="col-span-2 col-start-4">
              <PedigreeBox name={horse.sire_of_sire} label="父父" small />
            </div>
            <div className="col-span-2 col-start-6">
              <PedigreeBox name={horse.dam_of_sire} label="父母" small />
            </div>
            <div className="col-span-2 col-start-4">
              <PedigreeBox name={horse.sire_of_dam} label="母父" small />
            </div>
            <div className="col-span-2 col-start-6">
              <PedigreeBox name={horse.dam_of_dam} label="母母" small />
            </div>
          </div>
        </div>

        <div className="mt-6 p-4 bg-stone-50 rounded-xl">
          <h4 className="text-sm font-sans font-medium text-stone-600 mb-2">血統サマリー</h4>
          <p className="text-sm text-stone-700 font-sans leading-relaxed">
            {horse.name}は<strong>{horse.sire}</strong>を父に持ち、母方には<strong>{horse.sire_of_dam}</strong>の血を引く。
            {horse.sire === 'サンデーサイレンス' || horse.sire_of_sire === 'サンデーサイレンス'
              ? 'サンデーサイレンス系の底力と底力が受け継がれ、'
              : ''}
            {horse.g1_wins}つのG1タイトルが示す通り、一流の競走能力を持つ血統構成となっている。
          </p>
        </div>
      </div>
    </div>
  );
}

function PedigreeCell({ name, label, className }) {
  return (
    <div className={`bg-white border border-stone-100 rounded-lg p-2 text-center ${className || ''}`}>
      <div className="text-xs text-stone-400 font-sans">{label}</div>
      <div className="text-sm font-serif font-medium text-stone-800 mt-0.5">{name || '—'}</div>
    </div>
  );
}

function PedigreeBox({ name, label, highlight, small }) {
  return (
    <div className={`w-full p-2 rounded-lg border text-center
      ${highlight ? 'bg-gold/10 border-gold/40' : 'bg-white border-stone-100'}
      ${small ? 'py-1' : ''}`}>
      {label && <div className="text-stone-400" style={{ fontSize: '10px' }}>{label}</div>}
      <div className={`font-serif font-medium text-stone-800 ${small ? 'text-xs' : 'text-sm'}`}>
        {name || '—'}
      </div>
    </div>
  );
}
