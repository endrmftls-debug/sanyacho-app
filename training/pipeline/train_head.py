"""Step 3: train the classifier on top of BioCLIP features and measure how safe it is.

The final classifier is one linear layer (logistic regression blended with BioCLIP's zero-shot text
vectors), so it can be merged into the ONNX model. We calibrate probabilities (temperature) and pick a
confidence threshold so that toxic plants are almost never shown as a confident edible result.
"""
import json

import numpy as np
from sklearn.linear_model import LogisticRegression

from common import CI, DANGER, EDIBLE, OUT, load_config, run_main, status, verdict_categories, write_json


def softmax(z):
    z = z - z.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


def nll(p, y):
    return float(-np.mean(np.log(np.clip(p[np.arange(len(y)), y], 1e-9, 1))))


def fit_temperature(logits, y):
    best_t, best = 1.0, 1e9
    for t in np.exp(np.linspace(np.log(0.05), np.log(20), 120)):
        v = nll(softmax(logits / t), y)
        if v < best:
            best_t, best = float(t), v
    return best_t


def safety_curve(P, y, cats):
    """For each threshold: how often a toxic plant would be shown as a confident edible result."""
    edible = np.array([c in EDIBLE for c in cats])
    danger = np.array([c in DANGER for c in cats])
    top = P.argmax(1)
    pmax = P.max(1)
    true_danger = danger[y]
    true_edible = edible[y]
    rows = []
    for t in np.round(np.arange(0.30, 0.995, 0.01), 2):
        conf_edible = edible[top] & (pmax >= t)
        missed = int((conf_edible & true_danger).sum())
        rows.append({
            "t": float(t),
            "toxic_shown_as_edible": missed / max(1, true_danger.sum()),
            "toxic_shown_as_edible_n": missed,
            "danger_among_confident_edible": missed / max(1, conf_edible.sum()),
            "edible_coverage": float((conf_edible & true_edible & (top == y)).sum() / max(1, true_edible.sum())),
        })
    return rows


def evaluate(P, y, classes, cats, cfg, t_conf, warn):
    top = P.argmax(1)
    top3 = np.argsort(-P, 1)[:, :3]
    res = {"n": int(len(y)), "top1": float((top == y).mean()), "top3": float((top3 == y[:, None]).any(1).mean())}
    per = {}
    for i, c in enumerate(classes):
        m = y == i
        if m.sum():
            conf = {}
            for j in np.bincount(top[m], minlength=len(classes)).argsort()[::-1][:3]:
                cnt = int((top[m] == j).sum())
                if cnt and j != i:
                    conf[classes[j]] = cnt
            per[c] = {"n": int(m.sum()), "acc": float((top[m] == i).mean()), "confused_with": conf}
    res["per_class"] = per
    edible = np.array([c in EDIBLE for c in cats])
    danger = np.array([c in DANGER for c in cats])
    pmax = P.max(1)
    conf_edible = edible[top] & (pmax >= t_conf)
    td = danger[y]
    res["toxic_shown_as_edible"] = float((conf_edible & td).sum() / max(1, td.sum()))
    res["toxic_shown_as_edible_n"] = int((conf_edible & td).sum())
    res["toxic_images"] = int(td.sum())
    res["edible_coverage"] = float((conf_edible & edible[y] & (top == y)).sum() / max(1, edible[y].sum()))
    toxic_mass = P[:, danger].sum(1)
    res["toxic_warning_recall"] = float((toxic_mass[td] >= warn).mean()) if td.sum() else None
    res["edible_false_warning"] = float((toxic_mass[edible[y]] >= warn).mean()) if edible[y].sum() else None
    pairs = []
    idx = {c: i for i, c in enumerate(classes)}
    for a, b in cfg["lookalike_pairs"]:
        if a in idx and b in idx:
            ia, ib = idx[a], idx[b]
            ma, mb = y == ia, y == ib
            pairs.append({"edible": a, "lookalike": b,
                          "n_edible": int(ma.sum()), "n_lookalike": int(mb.sum()),
                          "edible_called_lookalike": int((top[ma] == ib).sum()),
                          "lookalike_called_edible": int((top[mb] == ia).sum()),
                          # a provisional edible class is never shown as a confident edible result
                          "lookalike_called_edible_confident":
                              int(((top[mb] == ia) & (pmax[mb] >= t_conf)).sum()) if edible[ia] else 0})
    res["pairs"] = pairs
    return res


def main():
    cfg = load_config()
    classes = json.load(open(OUT / "classes_order.json", encoding="utf-8"))
    info = {c["id"]: c for c in json.load(open(OUT / "classes_used.json", encoding="utf-8"))}
    cats = verdict_categories(classes, info)
    d = {s: np.load(OUT / f"emb_{s}.npz") for s in ("train", "val", "test")}
    Xtr, ytr = d["train"]["X"], d["train"]["y"]
    Xva, yva = d["val"]["X"], d["val"]["y"]
    Xte, yte = d["test"]["X"], d["test"]["y"]
    Z = np.load(OUT / "text_emb.npy")
    status("train", note="start", train=int(len(ytr)), val=int(len(yva)), test=int(len(yte)), classes=len(classes))

    best = None
    for C in (0.5, 1.0, 2.0, 4.0, 8.0, 16.0):
        lr = LogisticRegression(C=C, max_iter=3000, class_weight="balanced")
        lr.fit(Xtr, ytr)
        for beta in (0.0, 2.0, 5.0, 10.0, 20.0):
            W = lr.coef_ + beta * Z
            b = lr.intercept_
            acc = float(((Xva @ W.T + b).argmax(1) == yva).mean())
            print(f"C={C} beta={beta} val_acc={acc:.4f}", flush=True)
            if best is None or acc > best[0]:
                best = (acc, C, beta, W.copy(), b.copy())
    acc, C, beta, W, b = best
    zs_acc = float(((Xva @ Z.T).argmax(1) == yva).mean())
    T = fit_temperature(Xva @ W.T + b, yva)
    Pva = softmax((Xva @ W.T + b) / T)
    curve = safety_curve(Pva, yva, cats)
    target = cfg["danger_target"]
    ok = [r for r in curve if r["toxic_shown_as_edible"] <= target]
    t_conf = ok[0]["t"] if ok else 0.95
    warn = float(cfg["toxic_warn"])
    Pte = softmax((Xte @ W.T + b) / T)
    test = evaluate(Pte, yte, classes, cats, cfg, t_conf, warn)
    val = evaluate(Pva, yva, classes, cats, cfg, t_conf, warn)
    np.savez(OUT / "head.npz", W=W.astype(np.float32), b=b.astype(np.float32), T=np.float32(T))
    metrics = {"C": C, "beta": beta, "temperature": T, "val_acc_linear": acc, "val_acc_zero_shot": zs_acc,
               "threshold_confident": t_conf, "threshold_toxic_warn": warn, "danger_target": target,
               "provisional": [c for c in classes if info[c].get("provisional")],
               "val": val, "test": test, "val_safety_curve": curve,
               "sizes": {"train": int(len(ytr)), "val": int(len(yva)), "test": int(len(yte))}}
    write_json(OUT / "metrics_head.json", metrics)
    write_json(CI / "metrics_head.json", {k: v for k, v in metrics.items() if k != "val_safety_curve"})
    status("train", note="done", val_acc=round(acc, 4), zero_shot_val_acc=round(zs_acc, 4),
           test_top1=round(test["top1"], 4), test_top3=round(test["top3"], 4), t_conf=t_conf,
           toxic_shown_as_edible_test=test["toxic_shown_as_edible"], edible_coverage_test=test["edible_coverage"])


if __name__ == "__main__":
    run_main("train", main)
