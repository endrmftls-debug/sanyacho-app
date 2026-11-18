"""Add 도감 reference photos for entries the AI model has no photos for (classes dropped from training).

Runs during the APK build (needs internet). Uses CC-licensed iNaturalist photos that allow adaptation
(no "ND"): research-grade observations from South Korea alternating with the photos the community picked
to represent the taxon, then observations from anywhere. Records the credit for each photo.
When an entry covers several species (e.g. 개구릿대·지리강활), each photo is labelled with its species.
Never fails the build: if iNaturalist can't be reached, the app simply shows those entries without photos.
"""
import csv
import json
import time
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REF = HERE / "www" / "ref"
API = "https://api.inaturalist.org/v1"
LICENSES = ["cc0", "cc-by", "cc-by-sa", "cc-by-nc", "cc-by-nc-sa"]
PER_CLASS = 3
# names to try first when the class list's name finds nothing useful on iNaturalist
ALIASES = {"sasa": ["Sasa borealis", "Sasa"]}

session = requests.Session()
session.headers.update({"User-Agent": "sanyacho-app-build/1.0 (offline plant guide; GitHub Actions)"})
_last = [0.0]


def get(path, params):
    for attempt in range(4):
        wait = 1.1 - (time.time() - _last[0])  # stay under iNaturalist's 1 request/second guideline
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            r = session.get(API + path, params=params, timeout=60)
            if r.status_code == 200:
                return r.json()
        except requests.RequestException:
            pass
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"iNaturalist {path} unavailable")


def resolve(name):
    res = get("/taxa", {"q": name, "per_page": 30, "is_active": "true"}).get("results", [])
    good = [t for t in res if t.get("iconic_taxon_name") in ("Plantae", "Fungi")] or res
    for key in ("name", "matched_term"):
        for t in good:
            if (t.get(key) or "").lower() == name.lower():
                return t
    return None


def korea_place():
    for q in ("South Korea", "Korea"):
        for p in get("/places/autocomplete", {"q": q, "per_page": 20}).get("results", []):
            text = (p.get("name", "") + " " + p.get("display_name", "")).lower()
            if p.get("admin_level") == 0 and "korea" in text and "north" not in text:
                return p["id"]
    return None


def usable(p):
    return (p.get("license_code") or "").lower() in LICENSES and (p.get("medium_url") or p.get("url")) and not p.get("flags")


def record(p, link):
    url = p.get("medium_url") or p["url"]
    for size in ("square", "small", "thumb", "large", "original"):
        url = url.replace(f"/{size}.", "/medium.")
    return {"key": p.get("id") or url, "url": url, "attribution": p.get("attribution", ""),
            "license": p["license_code"].lower(), "obs_url": link}


def observed(taxon_id, place):
    """First usable photo of the best-voted research-grade observations."""
    params = {"taxon_id": taxon_id, "quality_grade": "research", "photos": "true",
              "photo_license": ",".join(LICENSES), "per_page": 30, "order_by": "votes"}
    if place:
        params["place_id"] = place
    out = []
    for o in get("/observations", params).get("results", []):
        p = next((p for p in o.get("photos", []) if usable(p)), None)
        if p:
            out.append(record(p, f"https://www.inaturalist.org/observations/{o['id']}"))
        if len(out) >= PER_CLASS:
            break
    return out


def curated(taxon_id):
    """Photos the iNaturalist community picked to represent the taxon."""
    res = get(f"/taxa/{taxon_id}", {}).get("results", [])
    photos = [tp.get("photo") or {} for tp in ((res[0].get("taxon_photos") or []) if res else [])]
    return [record(p, f"https://www.inaturalist.org/photos/{p.get('id')}") for p in photos if usable(p)][:PER_CLASS]


def candidates(taxon_id, place):
    """Korean observations (the local form) take turns with the community's representative photos;
    observations from anywhere fill the rest. Observation photos alone can be odd (a carved stump),
    representative photos alone can show an unusual variety, so mixing them gives the steadiest set."""
    local = observed(taxon_id, place) if place else []
    picks = curated(taxon_id)
    mixed = [g[i] for i in range(PER_CLASS) for g in (local, picks) if i < len(g)]
    if len({r["key"] for r in mixed}) < PER_CLASS:
        mixed += observed(taxon_id, None)
    out, seen = [], set()
    for r in mixed:
        if r["key"] not in seen:
            seen.add(r["key"])
            out.append(r)
    return out[:PER_CLASS]


def plan(c):
    """(scientific name, Korean label) pairs; labels only when the entry names one species per taxon."""
    names = ALIASES.get(c["id"]) or [t.strip() for t in c["taxa"].split(";") if t.strip()]
    kos = [k.strip() for k in c["ko"].split("·")]
    labels = kos if len(names) > 1 and len(kos) == len(names) and c["id"] not in ALIASES else [None] * len(names)
    return list(zip(names, labels))


def main():
    att_path = REF / "attribution.json"
    att = json.loads(att_path.read_text(encoding="utf-8")) if att_path.exists() else {}
    classes = list(csv.DictReader(open(ROOT / "training" / "classes.csv", encoding="utf-8")))
    todo = [c for c in classes if c["group"] != "other" and not att.get(c["id"])]
    print("entries without photos:", [c["id"] for c in todo])
    if not todo:
        return
    try:
        place = korea_place()
    except Exception as e:  # noqa: BLE001
        print("iNaturalist unreachable, skipping extra photos:", e)
        return
    for c in todo:
        try:
            groups, ids = [], set()
            for name, label in plan(c):
                t = resolve(name)
                if not t:
                    print(f"  {c['id']}: {name} is not on iNaturalist")
                    continue
                if t["id"] in ids:
                    continue
                ids.add(t["id"])
                print(f"  {c['id']}: {name} -> {t['name']} ({t['id']})")
                groups.append([dict(r, name=label) for r in candidates(t["id"], place)])
            if any(r["name"] for g in groups for r in g):
                order = [g[i] for i in range(PER_CLASS) for g in groups if i < len(g)]  # take turns per species
            else:
                order = [r for g in groups for r in g]  # aliases: first name that has photos wins
            picked, used = [], set()
            for r in order:
                if r["key"] not in used and len(picked) < PER_CLASS:
                    used.add(r["key"])
                    picked.append(r)
            out = []
            (REF / c["id"]).mkdir(parents=True, exist_ok=True)
            for r in picked:
                resp = session.get(r["url"], timeout=60)
                if resp.status_code != 200:
                    continue
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                img.thumbnail((480, 480))
                fn = f"{c['id']}/{len(out) + 1}.jpg"
                img.save(REF / fn, "JPEG", quality=80)
                rec = {"file": fn, "attribution": r["attribution"], "license": r["license"], "obs_url": r["obs_url"]}
                if r["name"]:
                    rec["name"] = r["name"]
                out.append(rec)
            if out:
                att[c["id"]] = out
            print(f"{c['id']}: {len(out)} photo(s)", [o.get("name", "") for o in out])
        except Exception as e:  # noqa: BLE001 - one entry failing must not stop the build
            print(f"{c['id']}: skipped ({e})")
    att_path.write_text(json.dumps(att, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
