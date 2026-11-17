"""Step 2: turn every photo into a BioCLIP feature vector (and text prompts into zero-shot vectors).

Train photos also get augmented views (random crops / flips / colour) so the classifier copes with
how people actually frame plants with a phone. Results are cached per image so re-runs only embed new photos.
"""
import json
import os
import time

import numpy as np
import open_clip
import torch
from PIL import Image
from torchvision import transforms as T

from common import EMB, OUT, WORK, load_config, run_main, status, write_json

MEAN = (0.48145466, 0.4578275, 0.40821073)
STD = (0.26862954, 0.26130258, 0.27577711)


def build(cfg):
    torch.set_num_threads(max(1, os.cpu_count() or 1))
    torch.manual_seed(0)  # only matters for random-weight test models
    name = cfg["model_name"]
    pretrained = cfg.get("pretrained")
    if name.startswith("hf-hub:"):
        model, _, preprocess = open_clip.create_model_and_transforms(name)
    else:
        model, _, preprocess = open_clip.create_model_and_transforms(name, pretrained=pretrained)
    model.eval()
    tokenizer = open_clip.get_tokenizer(name)
    return model, preprocess, tokenizer


def aug_transform():
    return T.Compose([
        T.RandomResizedCrop(224, scale=(0.35, 1.0), ratio=(0.75, 1.333), interpolation=T.InterpolationMode.BICUBIC),
        T.RandomHorizontalFlip(),
        T.ColorJitter(0.25, 0.25, 0.2, 0.02),
        T.ToTensor(),
        T.Normalize(MEAN, STD),
    ])


class Items(torch.utils.data.Dataset):
    def __init__(self, items, tf_center, tf_aug):
        self.items, self.tf_center, self.tf_aug = items, tf_center, tf_aug

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        path, view = self.items[i]
        img = Image.open(WORK / path).convert("RGB")
        tf = self.tf_center if view == 0 else self.tf_aug
        return tf(img), i


def main():
    cfg = load_config()
    model, preprocess, tokenizer = build(cfg)
    manifest = [json.loads(l) for l in open(OUT / "manifest.jsonl", encoding="utf-8")]
    n_aug = int(cfg.get("aug_views", 0))

    cache_file = EMB / "cache.npz"
    cache = {}
    if cache_file.exists():
        z = np.load(cache_file, allow_pickle=False)
        model_tag = str(z["model"]) if "model" in z else ""
        if model_tag == cfg["model_name"]:
            for k, v in zip(z["keys"], z["emb"]):
                cache[str(k)] = v
    print(f"cache has {len(cache)} vectors", flush=True)

    wanted = []
    for m in manifest:
        views = 1 + (n_aug if m["split"] == "train" else 0)
        for v in range(views):
            wanted.append((m["path"], v))
    todo = [w for w in wanted if f"{w[0]}#{w[1]}" not in cache]
    status("embed", note="start", total=len(wanted), todo=len(todo))

    loader = torch.utils.data.DataLoader(Items(todo, preprocess, aug_transform()), batch_size=32,
                                         num_workers=2, shuffle=False)
    t0 = time.time()
    done = 0
    with torch.no_grad():
        for x, idx in loader:
            f = model.encode_image(x).float()
            f = torch.nn.functional.normalize(f, dim=-1).numpy().astype(np.float16)
            for j, i in enumerate(idx.tolist()):
                p, v = todo[i]
                cache[f"{p}#{v}"] = f[j]
            done += len(idx)
            if done % 1024 < 32 or done == len(todo):
                rate = done / max(1e-6, time.time() - t0)
                eta = (len(todo) - done) / max(rate, 1e-6) / 60
                print(f"  embedded {done}/{len(todo)} ({rate:.1f} img/s, ~{eta:.0f} min left)", flush=True)
                if done % 4096 < 32:
                    status("embed", note="running", done=done, todo=len(todo))
            if done % 8192 < 32:  # periodic checkpoint so a cancelled run keeps its work
                keys = list(cache.keys())
                np.savez(cache_file, keys=np.array(keys), emb=np.stack([cache[k] for k in keys]),
                         model=np.array(cfg["model_name"]))

    keys = list(cache.keys())
    if keys:
        np.savez(cache_file, keys=np.array(keys), emb=np.stack([cache[k] for k in keys]),
                 model=np.array(cfg["model_name"]))

    classes = [c["id"] for c in json.load(open(OUT / "classes_used.json", encoding="utf-8"))]
    cidx = {c: i for i, c in enumerate(classes)}
    for split in ("train", "val", "test"):
        X, y, obs, paths, views = [], [], [], [], []
        for m in manifest:
            if m["split"] != split:
                continue
            nv = 1 + (n_aug if split == "train" else 0)
            for v in range(nv):
                X.append(cache[f"{m['path']}#{v}"])
                y.append(cidx[m["cls"]])
                obs.append(m["obs_id"])
                paths.append(m["path"])
                views.append(v)
        np.savez(OUT / f"emb_{split}.npz", X=np.stack(X).astype(np.float32), y=np.array(y), obs=np.array(obs),
                 paths=np.array(paths), views=np.array(views))
        print(f"{split}: {len(X)} vectors", flush=True)

    prompts = json.load(open(OUT / "prompts.json", encoding="utf-8"))
    Z = []
    with torch.no_grad():
        for c in classes:
            toks = tokenizer(prompts[c])
            e = torch.nn.functional.normalize(model.encode_text(toks).float(), dim=-1).mean(0)
            Z.append(torch.nn.functional.normalize(e, dim=0).numpy())
    np.save(OUT / "text_emb.npy", np.stack(Z).astype(np.float32))
    write_json(OUT / "classes_order.json", classes)
    status("embed", note="done", vectors=len(wanted), minutes=round((time.time() - t0) / 60, 1))


if __name__ == "__main__":
    run_main("embed", main)
