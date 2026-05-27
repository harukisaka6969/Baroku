import { useState } from 'react';

export default function Disclaimer({ onAccept }) {
  const [checked, setChecked] = useState(false);

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl animate-fade-up">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-2xl">⚠️</span>
          <h2 className="font-serif text-xl font-semibold text-stone-900">ご利用の前に</h2>
        </div>

        <div className="bg-stone-50 rounded-xl p-4 mb-4 text-sm text-stone-700 font-sans leading-relaxed space-y-2">
          <p>
            本予想はアルゴリズムによる参考情報であり、<strong>的中を保証するものではありません</strong>。
          </p>
          <p>
            馬券の購入は<strong>自己責任</strong>で行ってください。当サイトは一切の損害について責任を負いません。
          </p>
          <p className="text-red-600 font-medium">
            18歳未満の方の利用はお断りします。
          </p>
        </div>

        <label className="flex items-start gap-3 cursor-pointer mb-5">
          <input
            type="checkbox"
            checked={checked}
            onChange={e => setChecked(e.target.checked)}
            className="mt-0.5 w-4 h-4 accent-gold"
          />
          <span className="text-sm text-stone-700 font-sans">
            上記の免責事項を読み、内容を理解した上で同意します。私は18歳以上です。
          </span>
        </label>

        <button
          onClick={onAccept}
          disabled={!checked}
          className="w-full py-2.5 rounded-xl font-sans font-medium text-sm transition-all duration-200
            disabled:bg-stone-200 disabled:text-stone-400 disabled:cursor-not-allowed
            enabled:bg-gold enabled:text-white enabled:hover:bg-gold-dark enabled:shadow-sm"
        >
          同意して予想を見る
        </button>

        <p className="text-center text-xs text-stone-400 font-sans mt-3">
          同意しない場合はブラウザを閉じてください
        </p>
      </div>
    </div>
  );
}
