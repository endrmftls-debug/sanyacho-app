"""Step 1: find each class on iNaturalist and download CC-licensed research-grade photos.

Writes:
  work/out/manifest.jsonl     one line per usable photo (class, split, path, licence ...)
  work/out/classes_used.json  classes that have enough photos, with resolved taxa
  work/out/prompts.json       text prompts for zero-shot (taxonomic names)
  work/ref/<class>/*.jpg      2-3 small reference photos per class for the app (+ attribution.json)
"""
import concurrent.futures as cf
import hashlib
import json
import threading
import time
from io import BytesIO

import requests
from PIL import Image

from common import (CI, IMAGES, OUT, REF, WORK, ensure_dirs, load_classes, load_config,
                    obs_split, read_json, run_main, status, write_json)

API = "https://api.inaturalist.org/v1"
UA = "sanyacho-app-training/1.0 (personal offline plant guide; GitHub Actions)"
OPEN_LIC = ["cc0", "cc-by", "cc-by-nc", "cc-by-sa", "cc-by-nc-sa", "cc-by-nd", "cc-by-nc-nd"]
REF_LIC = {"cc0", "cc-by", "cc-by-nc", "cc-by-sa", "cc-by-nc-sa"}  # no "ND": we resize them
SEASONS = [[3, 4, 5], [6, 7, 8], [9, 10, 11], [12, 1, 2]]
RECORDS_CACHE = IMAGES / "_records_cache.json"


class Api:
    def __init__(self, min_interval=1.05):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = UA
        self.last = 0.0
        self.min_interval = min_interval
        self.calls = 0

    def get(self, path, params):
        for attempt in range(7):
            wait = self.min_interval - (time.time() - self.last)
            if wait > 0:
                time.sleep(wait)
            self.last = time.time()
            self.calls += 1
            try:
                r = self.s.get(API + path, params=params, timeout=90)
            except requests.RequestException as e:
                print(f"  api error {e!r}, retrying", flush=True)
                time.sleep(5 * (attempt + 1))
                continue
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503, 504):
                print(f"  api {r.status_code}, backing off", flush=True)
                time.sleep(15 * (attempt + 1))
                continue
            raise RuntimeError(f"iNat {path} {params} -> {r.status_code} {r.text[:300]}")
        raise RuntimeError(f"iNat {path} failed after retries")


def resolve_places(api, cfg):
    out = {"kr": [], "ea": []}
    for n in cfg["places"]["kr"]:
        d = api.get("/places/autocomplete", {"q": n, "per_page": 20})
        for p in d.get("results", []):
            text = (p.get("name", "") + " " + p.get("display_name", "")).lower()
            if p.get("admin_level") == 0 and "korea" in text and "north" not in text and "dprk" not in text:
                out["kr"] = [(p["id"], p.get("name"))]
                break
        if out["kr"]:
            break
    for n in cfg["places"]["ea"]:
        d = api.get("/places/autocomplete", {"q": n, "per_page": 20})
        res = [p for p in d.get("results", []) if p.get("admin_level") == 0]
        exact = [p for p in res if p.get("name", "").lower() == n.lower()]
        pick = (exact or res)[:1]
        out["ea"] += [(p["id"], p.get("name")) for p in pick]
    if not out["kr"]:
        raise RuntimeError("could not resolve the South Korea place on iNaturalist")
    return out


def resolve_taxon(api, name):
    d = api.get("/taxa", {"q": name, "per_page": 30, "is_active": "true"})
    res = d.get("results", [])
    nl = name.lower()
    for t in res:
        if t.get("name", "").lower() == nl:
            return t
    for t in res:
        if (t.get("matched_term") or "").lower() == nl:
            return t
    return None


def lineage(api, tid):
    d = api.get(f"/taxa/{tid}", {})
    t = d["results"][0]
    keep = ("kingdom", "phylum", "class", "order", "family", "genus")
    names = [a["name"] for a in t.get("ancestors", []) if a.get("rank") in keep]
    if t.get("rank") in ("species", "subspecies", "variety", "form") and " " in t["name"]:
        return names + [t["name"].split(" ", 1)[1]]  # BioCLIP style: "... Ligularia fischeri"
    return names + [t["name"]]


def photo_records(obs, per_obs, label, seen):
    recs = []
    oid = obs["id"]
    if oid in seen:
        return recs
    photos = [p for p in obs.get("photos", [])
              if (p.get("license_code") or "").lower() in OPEN_LIC and p.get("url")]
    if not photos:
        return recs
    seen.add(oid)
    od = obs.get("observed_on") or ""
    month = int(od[5:7]) if len(od) >= 7 and od[5:7].isdigit() else None
    for p in photos[:per_obs]:
        url = p["url"]
        for size in ("square", "small", "thumb", "large", "original"):
            url = url.replace(f"/{size}.", "/medium.")
        recs.append({
            "obs_id": oid, "photo_id": p["id"], "url": url,
            "license": (p.get("license_code") or "").lower(),
            "attribution": p.get("attribution", ""), "month": month,
            "taxon": (obs.get("taxon") or {}).get("name"),
            "obs_url": f"https://www.inaturalist.org/observations/{oid}", "query": label,
        })
    return recs


def query(api, params, need, seen, per_obs, label, max_pages=4):
    recs = []
    for page in range(1, max_pages + 1):
        p = {**params, "page": page, "per_page": 200, "quality_grade": "research",
             "photos": "true", "photo_license": ",".join(OPEN_LIC), "order_by": "id", "order": "desc"}
        d = api.get("/observations", p)
        results = d.get("results", [])
        for o in results:
            recs += photo_records(o, per_obs, label, seen)
            if len(recs) >= need:
                return recs[:need]
        if len(results) < 200:
            break
    return recs


def month_plan(c, cfg):
    """(months, share) buckets so photos cover different growth stages, not only flowering."""
    if c["spring"]:
        spring = cfg["spring_months"]
        rest = [m for m in range(1, 13) if m not in spring]
        return [(spring, cfg["spring_fraction"]), (rest, 1 - cfg["spring_fraction"])]
    return [(s, 0.25) for s in SEASONS]


def collect_class(api, c, cfg, places, taxon_ids):
    target = cfg["target_per_class"]
    per_obs = cfg["max_photos_per_obs"]
    kr = [p[0] for p in places["kr"]]
    ea = kr + [p[0] for p in places["ea"]]
    stages = [("KR", kr)]
    if c["mode"] in ("kr", "kr_ea"):
        stages.append(("EA", ea))
    if c["mode"] == "kr":
        stages.append(("GLOBAL", None))
    tid = ",".join(map(str, taxon_ids))
    seen, recs = set(), []
    for months, share in month_plan(c, cfg):
        quota = int(round(target * share))
        got = []
        for label, pl in stages:
            if len(got) >= quota:
                break
            params = {"taxon_id": tid, "month": ",".join(map(str, months))}
            if pl:
                params["place_id"] = ",".join(map(str, pl))
            got += query(api, params, quota - len(got), seen, per_obs, f"{label}-m{months[0]}", max_pages=2)
        recs += got
    for label, pl in stages:  # top up with any month if seasons were thin
        if len(recs) >= target:
            break
        params = {"taxon_id": tid}
        if pl:
            params["place_id"] = ",".join(map(str, pl))
        recs += query(api, params, target - len(recs), seen, per_obs, f"{label}-any")
    return recs[:target]


def collect_other(api, c, cfg, places, kingdom_id, exclude_ids):
    target = cfg["target_other"]
    kr = [p[0] for p in places["kr"]]
    ea = kr + [p[0] for p in places["ea"]]
    seen, recs = set(), []
    per_month = max(1, target // 12)
    excl = ",".join(map(str, sorted(exclude_ids)))
    for m in range(1, 13):
        got = []
        for label, pl in (("KR", kr), ("EA", ea)):
            if len(got) >= per_month:
                break
            params = {"taxon_id": kingdom_id, "without_taxon_id": excl, "month": str(m),
                      "place_id": ",".join(map(str, pl))}
            got += query(api, params, per_month - len(got), seen, 1, f"{label}-m{m}", max_pages=1)
        recs += got
    return recs[:target]


_tl = threading.local()


def _session():
    if not hasattr(_tl, "s"):
        _tl.s = requests.Session()
        _tl.s.headers["User-Agent"] = UA
    return _tl.s


def download(r):
    p = WORK / r["path"]
    if p.exists() and p.stat().st_size > 1000:
        return True
    for attempt in range(4):
        try:
            resp = _session().get(r["url"], timeout=60)
            if resp.status_code == 200:
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                img.save(p, "JPEG", quality=90)
                return True
            if resp.status_code in (403, 404):
                return False
        except Exception as e:  # noqa: BLE001 - network / decode errors are retried
            print(f"  download error {r['url']}: {e!r}", flush=True)
        time.sleep(2 * (attempt + 1))
    return False


def pick_refs(recs, n, spring_months):
    cand = [r for r in recs if r["license"] in REF_LIC and r.get("ok")]
    cand.sort(key=lambda r: (not r["query"].startswith("KR"), r["obs_id"]))
    picked, obs = [], set()
    spring = [r for r in cand if r.get("month") in spring_months]
    for pool in (spring[:1], cand):
        for r in pool:
            if len(picked) >= n:
                break
            if r["obs_id"] in obs:
                continue
            picked.append(r)
            obs.add(r["obs_id"])
    return picked


def class_key(c, cfg):
    blob = json.dumps([c["taxa"], c["mode"], c["spring"], cfg["target_per_class"], cfg["target_other"],
                       cfg["spring_months"], cfg["spring_fraction"], cfg["max_photos_per_obs"]])
    return hashlib.md5(blob.encode()).hexdigest()


def main():
    ensure_dirs()
    cfg = load_config()
    classes = load_classes()
    api = Api()
    cache = read_json(RECORDS_CACHE, {}) or {}

    status("collect", note="resolving places and taxa")
    places = cache.get("_places") or resolve_places(api, cfg)
    cache["_places"] = places
    print("places:", places, flush=True)

    resolved = {}
    for c in classes:
        cached = cache.get(c["id"])
        if cached and cached.get("key") == class_key(c, cfg) and "resolved" in cached:
            resolved[c["id"]] = cached["resolved"]
            continue
        items, missing = [], []
        for name in c["taxa"]:
            t = resolve_taxon(api, name)
            if not t:
                missing.append(name)
                continue
            try:
                lin = lineage(api, t["id"])
            except Exception as e:  # noqa: BLE001
                print(f"  lineage failed for {name}: {e!r}", flush=True)
                lin = [t["name"]]
            items.append({"query": name, "id": t["id"], "name": t["name"], "rank": t.get("rank"),
                          "matched_term": t.get("matched_term"),
                          "observations_count": t.get("observations_count"), "lineage": lin})
        resolved[c["id"]] = {"taxa": items, "missing": missing}
        print(f"{c['id']}: {[i['name'] + '/' + str(i['rank']) for i in items]} missing={missing}", flush=True)
    write_json(OUT / "taxa_resolved.json", resolved)
    write_json(CI / "taxa_resolved.json", resolved)
    unresolved = {k: v["missing"] for k, v in resolved.items() if v["missing"]}
    status("collect", note="taxa resolved", unresolved=unresolved, api_calls=api.calls)

    exclude = {"plant": set(), "mushroom": set()}
    for c in classes:
        if c["group"] in exclude:
            exclude[c["group"]].update(t["id"] for t in resolved[c["id"]]["taxa"])

    records = {}
    for i, c in enumerate(classes):
        cid = c["id"]
        key = class_key(c, cfg)
        cached = cache.get(cid)
        if cached and cached.get("key") == key and cached.get("recs"):
            records[cid] = cached["recs"]
            continue
        ids = [t["id"] for t in resolved[cid]["taxa"]]
        if not ids:
            records[cid] = []
            continue
        if c["group"] == "other":
            recs = collect_other(api, c, cfg, places, ids[0], exclude["plant" if cid == "other_plant" else "mushroom"])
        else:
            recs = collect_class(api, c, cfg, places, ids)
        records[cid] = recs
        cache[cid] = {"key": key, "recs": recs, "resolved": resolved[cid]}
        write_json(RECORDS_CACHE, cache)
        print(f"[{i + 1}/{len(classes)}] {cid}: {len(recs)} photos listed", flush=True)
    status("collect", note="photo lists ready", listed={k: len(v) for k, v in records.items()}, api_calls=api.calls)

    tasks = []
    for cid, recs in records.items():
        (IMAGES / cid).mkdir(parents=True, exist_ok=True)
        for r in recs:
            r["path"] = f"images/{cid}/{r['obs_id']}_{r['photo_id']}.jpg"
            tasks.append(r)
    done = 0
    with cf.ThreadPoolExecutor(8) as ex:
        for r, ok in zip(tasks, ex.map(download, tasks)):
            r["ok"] = bool(ok)
            done += 1
            if done % 1000 == 0:
                print(f"  downloaded {done}/{len(tasks)}", flush=True)

    manifest, counts, used = [], {}, []
    for c in classes:
        cid = c["id"]
        ok = [r for r in records[cid] if r.get("ok")]
        n = {"train": 0, "val": 0, "test": 0}
        for r in ok:
            sp = obs_split(r["obs_id"], cfg["split"])
            n[sp] += 1
            manifest.append({"cls": cid, "path": r["path"], "split": sp, "obs_id": r["obs_id"],
                             "license": r["license"], "month": r.get("month"), "query": r["query"]})
        counts[cid] = {"total": len(ok), **n}
        if len(ok) >= cfg["min_per_class"] and n["val"] > 0 and n["test"] > 0:
            used.append(c)
    used_ids = {c["id"] for c in used}
    manifest = [m for m in manifest if m["cls"] in used_ids]
    with open(OUT / "manifest.jsonl", "w", encoding="utf-8") as f:
        for m in manifest:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

    prompts = {}
    for c in used:
        if c["id"] == "other_plant":
            prompts[c["id"]] = ["a photo of a plant.", "a photo of Plantae."]
        elif c["id"] == "other_fungi":
            prompts[c["id"]] = ["a photo of a mushroom.", "a photo of Fungi."]
        else:
            prompts[c["id"]] = [f"a photo of {' '.join(t['lineage'])}." for t in resolved[c["id"]]["taxa"]]
    write_json(OUT / "prompts.json", prompts)
    write_json(OUT / "classes_used.json", [{**{k: c[k] for k in ("id", "ko", "category", "group")},
                                           "taxa": resolved[c["id"]]["taxa"], "counts": counts[c["id"]]}
                                          for c in used])

    attributions = {}
    for c in used:
        cid = c["id"]
        if c["group"] == "other":
            continue
        refs = pick_refs(records[cid], cfg["ref_photos_per_class"], cfg["spring_months"])
        (REF / cid).mkdir(parents=True, exist_ok=True)
        attributions[cid] = []
        for j, r in enumerate(refs):
            img = Image.open(WORK / r["path"]).convert("RGB")
            img.thumbnail((480, 480))
            fn = f"{cid}/{j + 1}.jpg"
            img.save(REF / fn, "JPEG", quality=80)
            attributions[cid].append({"file": fn, "attribution": r["attribution"], "license": r["license"],
                                      "obs_url": r["obs_url"], "month": r.get("month"), "taxon": r.get("taxon")})
    write_json(REF / "attribution.json", attributions)

    dropped = {c["id"]: counts[c["id"]] for c in classes if c["id"] not in used_ids}
    summary = {"places": places, "counts": counts, "dropped": dropped, "n_classes": len(used),
               "n_images": len(manifest), "api_calls": api.calls}
    write_json(OUT / "collect_summary.json", summary)
    write_json(CI / "collect_summary.json", summary)
    status("collect", note="done", n_classes=len(used), n_images=len(manifest), dropped=list(dropped))


if __name__ == "__main__":
    run_main("collect", main)
