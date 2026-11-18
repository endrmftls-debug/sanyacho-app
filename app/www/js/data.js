// Loads the offline 도감, guide, model labels and reference-photo credits.
const state = { species: [], byId: new Map(), guide: [], labels: null, refs: {} };

async function getJSON(url, fallback) {
  try {
    const r = await fetch(url);
    if (!r.ok) return fallback;
    return await r.json();
  } catch (_) {
    return fallback;
  }
}

export async function loadData() {
  const [sp, gd, lb, refs] = await Promise.all([
    getJSON("data/species.json", { entries: [] }),
    getJSON("data/guide.json", { sections: [] }),
    getJSON("data/labels.json", null),
    getJSON("ref/attribution.json", {}),
  ]);
  state.species = sp.entries;
  state.byId = new Map(sp.entries.map((e) => [e.id, e]));
  state.guide = gd.sections;
  state.labels = lb;
  state.refs = refs || {};
  if (lb) {
    for (const c of lb.classes) {
      const e = state.byId.get(c.id);
      if (e) e.aiAcc = c.test_acc;
    }
  }
  return state;
}

export const data = state;
export const entry = (id) => state.byId.get(id);

export function photos(id) {
  return (state.refs[id] || []).map((r) => ({ src: "ref/" + r.file, credit: r.attribution || "", url: r.obs_url }));
}

export function firstPhoto(id) {
  const p = state.refs[id];
  return p && p.length ? "ref/" + p[0].file : null;
}

const ENERGY = { "매우 높음": 0, "높음": 1, "보통": 2, "낮음": 3 };

export function inSeason(month) {
  return state.species
    .filter((e) => (e.v === "edible" || e.v === "edible_caution") && (e.months || []).includes(month))
    .sort((a, b) => (ENERGY[a.energy] ?? 9) - (ENERGY[b.energy] ?? 9) || a.ko.localeCompare(b.ko, "ko"));
}
