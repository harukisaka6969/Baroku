import { useState } from 'react';

export default function SearchBar({ value, onChange }) {
  return (
    <div className="relative">
      <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <input
        type="text"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder="馬名・調教師・牧場で検索..."
        className="w-full pl-10 pr-4 py-2 rounded-full border border-stone-200 bg-white text-sm focus:outline-none focus:border-gold focus:ring-1 focus:ring-gold font-sans"
      />
    </div>
  );
}
