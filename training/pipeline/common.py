"""Shared helpers for the training pipeline (paths, config, class list, status files)."""
import csv
import hashlib
import json
import os
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRAINING = ROOT / "training"
WORK = Path(os.environ.get("WORK_DIR", ROOT / "work"))
IMAGES = WORK / "images"
REF = WORK / "ref"
EMB = WORK / "emb_cache"
OUT = WORK / "out"
RELEASE = WORK / "release"
CI = WORK / "ci"

EDIBLE = {"edible", "edible_caution"}
DANGER = {"toxic", "deadly"}
MUSHROOM = {"mushroom_edible", "mushroom_toxic", "mushroom_deadly", "mushroom_other"}


def verdict_categories(classes, info):
    """Categories as the app treats them: a provisional (few-photo) edible class is never shown as edible,
    so the safety numbers count it as 'provisional', not 'edible'."""
    return ["provisional" if info[c].get("provisional") and info[c]["category"] in EDIBLE else info[c]["category"]
            for c in classes]


def ensure_dirs():
    for d in (WORK, IMAGES, REF, EMB, OUT, RELEASE, CI):
        d.mkdir(parents=True, exist_ok=True)


def load_config():
    with open(TRAINING / "config.json", encoding="utf-8") as f:
        cfg = json.load(f)
    if os.environ.get("MODEL_OVERRIDE"):  # local tests use a small random-weight model
        cfg["model_name"] = os.environ["MODEL_OVERRIDE"]
        cfg["pretrained"] = None
    return cfg


def load_classes():
    rows = []
    with open(TRAINING / "classes.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["taxa"] = [t.strip() for t in r["taxa"].split(";") if t.strip()]
            r["spring"] = r["spring"].strip() == "1"
            rows.append(r)
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate class ids"
    return rows


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def status(stage, **info):
    """Record pipeline progress so it can be inspected from the ci-status branch."""
    ensure_dirs()
    st = read_json(CI / "status.json", {}) or {}
    st.setdefault("stages", {})
    st["stage"] = stage
    st["updated"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    st["stages"][stage] = {**st["stages"].get(stage, {}), **info, "at": st["updated"]}
    write_json(CI / "status.json", st)
    print(f"[status] {stage} {json.dumps(info, ensure_ascii=False)[:300]}", flush=True)


def run_main(stage, fn):
    try:
        fn()
    except Exception:
        tb = traceback.format_exc()
        status(stage, error=tb[-4000:])
        print(tb, flush=True)
        raise


def obs_split(obs_id, split_cfg):
    """Deterministic split by observation so photos of one plant never leak across splits."""
    h = int(hashlib.md5(str(obs_id).encode()).hexdigest(), 16) % 100
    if h < split_cfg["train"]:
        return "train"
    if h < split_cfg["train"] + split_cfg["val"]:
        return "val"
    return "test"
