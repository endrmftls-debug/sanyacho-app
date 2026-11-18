"""Step 5: write a human-readable report and package the release files."""
import json
import shutil
import zipfile

from common import CI, OUT, REF, RELEASE, run_main, status, write_json


def pct(x):
    return "-" if x is None else f"{x * 100:.1f}%"


def main():
    mh = json.load(open(OUT / "metrics_head.json", encoding="utf-8"))
    me = json.load(open(OUT / "metrics_export.json", encoding="utf-8"))
    cs = json.load(open(OUT / "collect_summary.json", encoding="utf-8"))
    labels = json.load(open(RELEASE / "labels.json", encoding="utf-8"))
    plain = {c["id"]: c["ko"] for c in labels["classes"]}
    ko = {c["id"]: c["ko"] + (" (AI 참고용)" if c.get("provisional") else "") for c in labels["classes"]}
    t8 = me["chosen_test"]
    L = []
    L.append("# 산야초 AI 모델 학습 리포트\n")
    L.append(f"- 생성: {labels['created']}  /  기반 모델: `{labels['model']}`")
    L.append(f"- 학습 클래스 {len(labels['classes'])}개, 사진 {cs['n_images']}장 (iNaturalist 연구등급, CC 라이선스)")
    L.append(f"- 폰용 모델: {me['chosen']} 방식, {me['chosen_mb']} MB  /  원본 {me['variants']['fp32']['mb']} MB")
    vs = ", ".join(f"{k}: {v.get('top1', 0) * 100:.1f}% ({v.get('mb', '?')}MB)" for k, v in me["variants"].items() if "top1" in v)
    L.append(f"- 경량화 후보 정답률: {vs}")
    L.append(f"- ONNX 변환 오차(최대): {me['onnx_vs_torch_max_abs_diff']:.2e}\n")
    L.append("## 정확도 (처음 보는 테스트 사진, 폰용 모델)\n")
    L.append("| 항목 | 값 |\n|---|---|")
    L.append(f"| 1순위 정답률 | {pct(t8['top1'])} |")
    L.append(f"| 3순위 안에 정답 | {pct(t8['top3'])} |")
    L.append(f"| 확신 기준값 | {labels['thresholds']['confident']:.2f} |")
    L.append(f"| 독초 사진을 '확신 있는 식용'으로 잘못 보인 비율 | {pct(t8['toxic_shown_as_edible'])} "
             f"({t8['toxic_shown_as_edible_n']}/{t8['toxic_images']}장) |")
    L.append(f"| 식용 사진에 확신 있게 맞힌 비율(커버리지) | {pct(t8['edible_coverage'])} |")
    L.append(f"| 독초 사진에 '독초 가능성' 경고가 뜬 비율 | {pct(t8['toxic_warning_recall'])} |")
    L.append(f"| 식용 사진에 경고가 같이 뜬 비율 | {pct(t8['edible_false_warning'])} |")
    L.append(f"\n(선형분류기 검증 정답률 {pct(mh['val_acc_linear'])}, 학습 없이 BioCLIP만 쓸 때 {pct(mh['val_acc_zero_shot'])})\n")
    L.append("## 헷갈리는 독초 짝 (테스트 사진)\n")
    L.append("| 식용 | 닮은 독초/비식용 | 식용→독초로 봄 | 독초→식용으로 봄 | 그중 확신 있게 |\n|---|---|---|---|---|")
    for p in t8["pairs"]:
        L.append(f"| {ko.get(p['edible'], p['edible'])} ({p['n_edible']}) | {ko.get(p['lookalike'], p['lookalike'])} "
                 f"({p['n_lookalike']}) | {p['edible_called_lookalike']} | {p['lookalike_called_edible']} | "
                 f"{p['lookalike_called_edible_confident']} |")
    L.append("\n## 종류별 정답률 (낮은 순)\n")
    L.append("| 종류 | 테스트 사진 | 정답률 | 주로 헷갈린 것 |\n|---|---|---|---|")
    for cid, r in sorted(t8["per_class"].items(), key=lambda kv: kv[1]["acc"]):
        conf = ", ".join(f"{ko.get(k, k)} {v}" for k, v in r["confused_with"].items())
        L.append(f"| {ko.get(cid, cid)} | {r['n']} | {pct(r['acc'])} | {conf} |")
    if cs.get("provisional"):
        L.append("\n## AI 참고용으로 넣은 종류\n")
        L.append(f"사진이 {cs.get('min_per_class', 40)}장보다 적어 덜 배운 종류예요. 앱은 이 종류를 '먹을 수 있는 후보'로 "
                 "보여주지 않고 'AI 참고용'으로 따로 표시해요. 독초라면 경고는 그대로 보여줘요.\n")
        for cid, n in cs["provisional"].items():
            L.append(f"- {plain.get(cid, cid)}: 사진 {n['total']}장 (학습 {n['train']}, 검증 {n['val']}, 시험 {n['test']})")
    if cs.get("dropped"):
        L.append("\n## 사진이 부족해 이번에 빠진 종류\n")
        for cid, n in cs["dropped"].items():
            L.append(f"- {cid}: {n}")
    text = "\n".join(L) + "\n"
    (RELEASE / "report.md").write_text(text, encoding="utf-8")
    (CI / "report.md").write_text(text, encoding="utf-8")

    with zipfile.ZipFile(RELEASE / "ref_photos.zip", "w", zipfile.ZIP_STORED) as z:
        for p in sorted(REF.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(REF).as_posix())
    shutil.copy(OUT / "taxa_resolved.json", RELEASE / "taxa_resolved.json")
    write_json(RELEASE / "metrics.json", {"head": {k: v for k, v in mh.items() if k != "val_safety_curve"},
                                          "export": me, "safety_curve_val": mh["val_safety_curve"]})
    status("report", note="done", files=sorted(p.name for p in RELEASE.iterdir()))


if __name__ == "__main__":
    run_main("report", main)
