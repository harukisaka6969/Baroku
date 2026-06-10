/**
 * API クライアント — FastAPI バックエンドへのリクエスト。
 * バックエンドが起動していない場合は自動的にモックデータにフォールバック。
 */
import {
  mockHorses,
  getHorseById as mockGetById,
  getRelatedHorses as mockGetRelated,
} from './mockData.js';

const BASE = import.meta.env.VITE_API_URL || '/api';
let _backendAlive = null; // null=未確認, true=生存, false=停止

async function ping() {
  if (_backendAlive !== null) return _backendAlive;
  try {
    const r = await fetch(`${BASE}/health`, { signal: AbortSignal.timeout(2000) });
    _backendAlive = r.ok;
  } catch {
    _backendAlive = false;
  }
  return _backendAlive;
}

async function apiFetch(path) {
  const r = await fetch(`${BASE}${path}`, { signal: AbortSignal.timeout(5000) });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

// ── 馬一覧 ──────────────────────────────────────────────────────────────
export async function fetchHorses(params = {}) {
  if (await ping()) {
    const q = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v))
    ).toString();
    return apiFetch(`/horses${q ? '?' + q : ''}`);
  }
  // フォールバック: モックデータをクライアント側でフィルタ
  let list = [...mockHorses];
  if (params.q) {
    const q = params.q;
    list = list.filter(h =>
      h.name.includes(q) ||
      (h.name_en || '').toLowerCase().includes(q.toLowerCase()) ||
      (h.trainer || '').includes(q) ||
      (h.farm || '').includes(q) ||
      (h.sire || '').includes(q)
    );
  }
  if (params.sex)    list = list.filter(h => h.sex === params.sex);
  if (params.status) list = list.filter(h => h.status === params.status);
  if (params.farm)   list = list.filter(h => h.farm === params.farm);
  if (params.sire)   list = list.filter(h => h.sire === params.sire);
  return list;
}

// ── 馬詳細 ──────────────────────────────────────────────────────────────
export async function fetchHorse(id) {
  if (await ping()) return apiFetch(`/horses/${id}`);
  const h = mockGetById(id);
  if (!h) throw new Error('Not found');
  return h;
}

// ── 関連馬 ──────────────────────────────────────────────────────────────
export async function fetchRelated(id) {
  if (await ping()) return apiFetch(`/horses/${id}/related`);
  const h = mockGetById(id);
  if (!h) return { same_farm: [], same_trainer: [], same_sire: [] };
  const rel = mockGetRelated(h);
  return {
    same_farm:    rel.sameFarm,
    same_trainer: rel.sameTrainer,
    same_sire:    rel.sameSire,
  };
}

// ── 予想 ────────────────────────────────────────────────────────────────
export async function postPrediction(body) {
  if (await ping()) {
    const r = await fetch(`${BASE}/prediction`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(10000),
    });
    if (!r.ok) throw new Error(`${r.status}`);
    return r.json();
  }
  return null; // フロント側ローカル計算にフォールバック
}

export function isUsingMock() {
  return _backendAlive === false;
}

// ── JRAレース一覧 ─────────────────────────────────────────────────────
export async function fetchRaces(params = {}) {
  if (await ping()) {
    const q = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v))
    ).toString();
    return apiFetch(`/races${q ? '?' + q : ''}`);
  }
  return null;
}

// ── レース予測＋買い方提案 ────────────────────────────────────────────
export async function fetchRacePrediction(raceId, budget = 5000) {
  if (await ping()) {
    return apiFetch(`/races/${raceId}/prediction?budget=${budget}`);
  }
  return null;
}

// ── 週間の買い方プラン（複数レースに5,000円を配分） ───────────────────
export async function fetchWeeklyPlan(dateFrom, dateTo, budget = 5000) {
  if (await ping()) {
    return apiFetch(`/races/weekly/plan?date_from=${dateFrom}&date_to=${dateTo}&budget=${budget}`);
  }
  return null;
}
