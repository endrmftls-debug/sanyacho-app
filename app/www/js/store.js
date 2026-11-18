// 채집 일지: finds are kept only on this phone (IndexedDB).
const DB = "sanyacho";
const STORE = "finds";

function open() {
  return new Promise((resolve, reject) => {
    const r = indexedDB.open(DB, 1);
    r.onupgradeneeded = () => {
      if (!r.result.objectStoreNames.contains(STORE)) r.result.createObjectStore(STORE, { keyPath: "id" });
    };
    r.onsuccess = () => resolve(r.result);
    r.onerror = () => reject(r.error);
  });
}

async function tx(mode, fn) {
  const db = await open();
  return new Promise((resolve, reject) => {
    const t = db.transaction(STORE, mode);
    const s = t.objectStore(STORE);
    let out;
    Promise.resolve(fn(s)).then((v) => (out = v));
    t.oncomplete = () => resolve(out);
    t.onerror = () => reject(t.error);
  });
}

export function addFind(f) {
  const rec = { id: String(Date.now()) + Math.random().toString(36).slice(2, 6), time: Date.now(), ...f };
  return tx("readwrite", (s) => { s.put(rec); return rec; });
}

export function listFinds() {
  return tx("readonly", (s) => new Promise((resolve) => {
    const r = s.getAll();
    r.onsuccess = () => resolve((r.result || []).sort((a, b) => b.time - a.time));
  }));
}

export function getFind(id) {
  return tx("readonly", (s) => new Promise((resolve) => {
    const r = s.get(id);
    r.onsuccess = () => resolve(r.result || null);
  }));
}

export function deleteFind(id) {
  return tx("readwrite", (s) => { s.delete(id); });
}
