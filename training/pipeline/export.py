"""Step 4: build the on-phone model: BioCLIP image encoder + trained classifier in one ONNX file.

Exports fp32, then tries smaller variants in order of phone speed (int8 per-channel, int8, 8-bit and 4-bit
weight-only). The first variant whose accuracy and toxic-confusion stay within tolerance of fp32 on the
test photos is shipped.
"""
import json
import logging
import os
import shutil
import time

import numpy as np
import onnx
import onnxruntime as ort
import torch
from onnxruntime.quantization import QuantType, quantize_dynamic
from onnxruntime.quantization.matmul_nbits_quantizer import DefaultWeightOnlyQuantConfig, MatMulNBitsQuantizer
from PIL import Image

from common import OUT, RELEASE, WORK, load_config, run_main, status, write_json
from embed import MEAN, STD, build
from train_head import evaluate, softmax

MAX_TOP1_DROP = 0.01
MAX_TOXIC_INCREASE = 0.002


class PlantNet(torch.nn.Module):
    def __init__(self, visual, W, b, T):
        super().__init__()
        self.visual = visual
        self.register_buffer("W", torch.from_numpy(W / T).float())
        self.register_buffer("b", torch.from_numpy(b / T).float())

    def forward(self, pixel_values):
        f = self.visual(pixel_values)
        if isinstance(f, (tuple, list)):
            f = f[0]
        f = torch.nn.functional.normalize(f.float(), dim=-1)
        logits = f @ self.W.t() + self.b
        return logits, f


def quantize_variant(name, fp32):
    out = OUT / f"plant_{name}.onnx"
    if name in ("int8pc", "int8"):
        quantize_dynamic(str(fp32), str(out), weight_type=QuantType.QInt8, per_channel=(name == "int8pc"),
                         op_types_to_quantize=["MatMul", "Gemm"])
    else:
        bits = int(name[1:])
        logging.disable(logging.INFO)
        q = MatMulNBitsQuantizer(onnx.load(str(fp32)), algo_config=DefaultWeightOnlyQuantConfig(
            block_size=64, is_symmetric=True, bits=bits))
        q.process()
        q.model.save_model_to_file(str(out), use_external_data_format=False)
        logging.disable(logging.NOTSET)
    return out


def run_model(path, X):
    so = ort.SessionOptions()
    so.intra_op_num_threads = os.cpu_count() or 1
    s = ort.InferenceSession(str(path), so, providers=["CPUExecutionProvider"])
    t0 = time.time()
    out = [s.run(["logits"], {"pixel_values": X[i:i + 32]})[0] for i in range(0, len(X), 32)]
    ms = (time.time() - t0) / max(1, len(X)) * 1000
    return np.concatenate(out), ms


def main():
    cfg = load_config()
    model, preprocess, _ = build(cfg)
    head = np.load(OUT / "head.npz")
    W, b, T = head["W"], head["b"], float(head["T"])
    net = PlantNet(model.visual, W, b, T).eval()
    try:
        torch.backends.mha.set_fastpath_enabled(False)
    except Exception:  # noqa: BLE001 - older torch
        pass

    fp32 = OUT / "plant_fp32.onnx"
    status("export", note="exporting onnx")
    with torch.no_grad():
        torch.onnx.export(net, (torch.randn(1, 3, 224, 224),), str(fp32), input_names=["pixel_values"],
                          output_names=["logits", "embedding"],
                          dynamic_axes={"pixel_values": {0: "batch"}, "logits": {0: "batch"},
                                        "embedding": {0: "batch"}},
                          opset_version=17, do_constant_folding=True, dynamo=False)
    onnx.checker.check_model(str(fp32))

    classes = json.load(open(OUT / "classes_order.json", encoding="utf-8"))
    info = {c["id"]: c for c in json.load(open(OUT / "classes_used.json", encoding="utf-8"))}
    cats = [info[c]["category"] for c in classes]
    manifest = [json.loads(l) for l in open(OUT / "manifest.jsonl", encoding="utf-8")]
    test = [m for m in manifest if m["split"] == "test"]
    cidx = {c: i for i, c in enumerate(classes)}
    X = np.stack([preprocess(Image.open(WORK / m["path"]).convert("RGB")).numpy() for m in test]).astype(np.float32)
    y = np.array([cidx[m["cls"]] for m in test])
    mh = json.load(open(OUT / "metrics_head.json", encoding="utf-8"))
    t_conf, warn = mh["threshold_confident"], mh["threshold_toxic_warn"]

    with torch.no_grad():
        ref = net(torch.from_numpy(X[:16]))[0].numpy()
    L32, ms32 = run_model(fp32, X)
    max_diff = float(np.abs(ref - L32[:16]).max())
    base = evaluate(softmax(L32), y, classes, cats, cfg, t_conf, warn)
    cands = {"fp32": {"mb": round(os.path.getsize(fp32) / 2**20, 1), "ms_runner": round(ms32, 1),
                      "top1": base["top1"], "toxic_shown_as_edible": base["toxic_shown_as_edible"]}}
    status("export", note="fp32 evaluated", onnx_vs_torch_max_abs_diff=max_diff, fp32_top1=round(base["top1"], 4))

    chosen, chosen_res, chosen_path = None, None, None
    for name in ("int8pc", "int8", "w8", "w4"):
        try:
            p = quantize_variant(name, fp32)
            L, ms = run_model(p, X)
        except Exception as e:  # noqa: BLE001 - a variant failing to build is not fatal
            cands[name] = {"error": repr(e)[:300]}
            continue
        r = evaluate(softmax(L), y, classes, cats, cfg, t_conf, warn)
        ok = (r["top1"] >= base["top1"] - MAX_TOP1_DROP and
              r["toxic_shown_as_edible"] <= base["toxic_shown_as_edible"] + MAX_TOXIC_INCREASE)
        cands[name] = {"mb": round(os.path.getsize(p) / 2**20, 1), "ms_runner": round(ms, 1), "top1": r["top1"],
                       "toxic_shown_as_edible": r["toxic_shown_as_edible"], "accepted": ok}
        status("export", note=f"variant {name}", **cands[name])
        if ok:
            chosen, chosen_res, chosen_path = name, r, p
            break
    if chosen is None:
        chosen, chosen_res, chosen_path = "fp32", base, fp32

    metrics = {"onnx_vs_torch_max_abs_diff": max_diff, "variants": cands, "chosen": chosen,
               "chosen_mb": round(os.path.getsize(chosen_path) / 2**20, 1), "fp32_test": base,
               "chosen_test": chosen_res}
    write_json(OUT / "metrics_export.json", metrics)
    status("export", note="done", chosen=chosen, chosen_mb=metrics["chosen_mb"], top1=round(chosen_res["top1"], 4),
           toxic_shown_as_edible=chosen_res["toxic_shown_as_edible"])

    RELEASE.mkdir(parents=True, exist_ok=True)
    shutil.copy(chosen_path, RELEASE / "plant.onnx")
    labels = {
        "model": cfg["model_name"],
        "variant": chosen,
        "created": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
        "input": {"size": 224, "mean": list(MEAN), "std": list(STD),
                  "resize": "shorter side to 224 (bicubic) then center crop 224x224",
                  "layout": "NCHW float32 RGB 0-1 then normalised"},
        "outputs": {"logits": "already divided by temperature; softmax gives calibrated probabilities",
                    "embedding": "L2-normalised image feature"},
        "thresholds": {"confident": t_conf, "toxic_warn": warn},
        "classes": [{"id": c, "ko": info[c]["ko"], "category": info[c]["category"], "group": info[c]["group"],
                     "photos": info[c]["counts"]["total"],
                     "test_acc": chosen_res["per_class"].get(c, {}).get("acc"),
                     "taxa": [t["name"] for t in info[c]["taxa"]]} for c in classes],
        "metrics": {"test_top1": chosen_res["top1"], "test_top3": chosen_res["top3"],
                    "toxic_shown_as_edible": chosen_res["toxic_shown_as_edible"],
                    "edible_coverage": chosen_res["edible_coverage"],
                    "toxic_warning_recall": chosen_res["toxic_warning_recall"]},
    }
    write_json(RELEASE / "labels.json", labels)


if __name__ == "__main__":
    run_main("export", main)
