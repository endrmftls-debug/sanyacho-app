# -*- coding: utf-8 -*-
"""Merge the 도감 source files into app/www/data/species.json and check them against the AI class list."""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import db_food_trees  # noqa: E402
import db_greens_roots  # noqa: E402
import db_toxic_fungi  # noqa: E402

VALID_V = {"edible", "edible_caution", "inedible", "toxic", "deadly", "mushroom", "other"}
CAT_TO_V = {"edible": {"edible"}, "edible_caution": {"edible_caution"}, "inedible": {"inedible"},
            "toxic": {"toxic"}, "deadly": {"deadly"}, "other": {"other", "mushroom"},
            "mushroom_edible": {"mushroom"}, "mushroom_toxic": {"mushroom"},
            "mushroom_deadly": {"mushroom"}, "mushroom_other": {"mushroom"}}


def main(out_path):
    entries = db_food_trees.ENTRIES + db_greens_roots.ENTRIES + db_toxic_fungi.ENTRIES
    by_id = {}
    errors = []
    for e in entries:
        if e["id"] in by_id:
            errors.append(f"duplicate id {e['id']}")
        by_id[e["id"]] = e
    classes = list(csv.DictReader(open(ROOT / "training" / "classes.csv", encoding="utf-8")))
    for c in classes:
        e = by_id.get(c["id"])
        if not e:
            errors.append(f"missing entry for class {c['id']}")
            continue
        if e["v"] not in CAT_TO_V[c["category"]]:
            errors.append(f"{c['id']}: class category {c['category']} vs entry v={e['v']}")
    for e in entries:
        if e["v"] not in VALID_V:
            errors.append(f"{e['id']}: bad v {e['v']}")
        for lid, _ in e.get("like", []):
            if lid not in by_id:
                errors.append(f"{e['id']}: lookalike {lid} unknown")
        if e["v"] in ("edible", "edible_caution"):
            if not e.get("check"):
                errors.append(f"{e['id']}: edible entry needs a checklist")
            if not e.get("eat"):
                errors.append(f"{e['id']}: edible entry needs eat info")
        if e["v"] in ("toxic", "deadly", "inedible") and not e.get("tox"):
            errors.append(f"{e['id']}: toxic entry needs tox info")
        for m in e.get("months", []):
            if not 1 <= m <= 12:
                errors.append(f"{e['id']}: bad month {m}")
        if e["v"] == "mushroom":
            e.setdefault("warn", [])
            if db_toxic_fungi.MUSHROOM_NOTE not in e["warn"]:
                e["warn"].insert(0, db_toxic_fungi.MUSHROOM_NOTE)
    # make look-alike links two-way so every page shows its dangerous twins
    for e in entries:
        for lid, why in e.get("like", []):
            other = by_id[lid]
            if not any(x[0] == e["id"] for x in other.get("like", [])):
                other.setdefault("like_auto", []).append([e["id"], f"{e['ko']}와(과) 헷갈릴 수 있어요. {e['ko']} 페이지의 구별 포인트를 함께 확인하세요."])
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"version": 1, "entries": entries}, ensure_ascii=False, indent=0), encoding="utf-8")
    n = {}
    for e in entries:
        n[e["v"]] = n.get(e["v"], 0) + 1
    print(f"wrote {out} with {len(entries)} entries: {n}")
    import guide
    gout = out.parent / "guide.json"
    secs = [{"id": g["id"], "icon": g["icon"], "title": g["title"],
             "items": [{"t": t, "v": v} for t, v in g["items"]]} for g in guide.SECTIONS]
    gout.write_text(json.dumps({"sections": secs}, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"wrote {gout} with {len(secs)} sections")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ROOT / "app" / "www" / "data" / "species.json")
