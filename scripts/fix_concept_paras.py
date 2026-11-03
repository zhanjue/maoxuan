# -*- coding: utf-8 -*-
"""按引文正文反查段号，修 concepts.json 里的 para 字段。

概念页的 quotes 同时存了段号（para）和引文全文（text）。段号会随数据清理
位移，正文不会——所以以 text 为准反查，para 只是它的缓存。

用法：python scripts/fix_concept_paras.py [--write]
不带 --write 只报告，不动文件。
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
works = json.load(open(os.path.join(ROOT, "data", "works.json"), encoding="utf-8"))
concepts = json.load(open(os.path.join(ROOT, "data", "concepts.json"), encoding="utf-8"))

by_title = {}
for w in works:
    if isinstance(w, dict):
        by_title[w["title"].strip()] = w

WRITE = "--write" in sys.argv
fixed = same = failed = 0

for c in concepts:
    if not isinstance(c, dict):
        continue
    for q in c.get("quotes", []):
        w = by_title.get(q["work"].strip())
        if not w:
            print("✗ 找不到篇目「%s」（概念 %s）" % (q["work"], c["id"]))
            failed += 1
            continue
        text = q["text"].strip()
        head = text[:40]
        hits = [i + 1 for i, p in enumerate(w["paragraphs"]) if head in p or p.strip()[:40] == head]
        if len(hits) != 1:
            # 退一步：用更长的片段
            head2 = text[:60]
            hits = [i + 1 for i, p in enumerate(w["paragraphs"]) if head2 in p]
        if len(hits) != 1:
            print("✗ 定位不到或有歧义（概念 %s / %s）：命中 %s | 开头「%s」"
                  % (c["id"], q["work"], hits, head))
            failed += 1
            continue
        new = hits[0]
        if new == q.get("para"):
            same += 1
        else:
            print("· %s / %s：para %s -> %d" % (c["id"], q["work"], q.get("para"), new))
            if WRITE:
                q["para"] = new
            fixed += 1

print("\n原值正确 %d 条 | 需修正 %d 条 | 失败 %d 条" % (same, fixed, failed))
if WRITE and fixed:
    json.dump(concepts, open(os.path.join(ROOT, "data", "concepts.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("已写回 data/concepts.json")
elif fixed:
    print("（只报告，未改动。加 --write 写回）")
sys.exit(1 if failed else 0)
