# -*- coding: utf-8 -*-
"""毛选站交付前自检：死链 / CSS 版本 / 注释锚点配对 / 导读写全没有 / 段号有效。"""
import json, os, re, sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")

works = json.load(open(os.path.join(ROOT, "data", "works.json"), encoding="utf-8"))
reading = json.load(open(os.path.join(ROOT, "data", "reading.json"), encoding="utf-8"))
works = [w for w in works if isinstance(w, dict)]

errors, warns = [], []

# ---------- 1. 收集所有页面 ----------
pages = []
for base, _, files in os.walk(SITE):
    for f in files:
        if f.endswith(".html"):
            pages.append(os.path.join(base, f))
pages.sort()

# ---------- 2. 死链 ----------
href_re = re.compile(r'(?:href|src)="([^"]+)"')
checked = 0
for p in pages:
    html = open(p, encoding="utf-8").read()
    for link in href_re.findall(html):
        if link.startswith(("http://", "https://", "mailto:", "data:", "#", "javascript:")):
            continue
        path, _, frag = link.partition("#")
        if not path:
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(p), path.split("?")[0]))
        checked += 1
        if not os.path.exists(target):
            errors.append("死链 %s -> %s" % (os.path.relpath(p, SITE), link))
        elif frag and os.path.isfile(target) and target.endswith(".html"):
            th = open(target, encoding="utf-8").read()
            if 'id="%s"' % frag not in th:
                errors.append("锚点缺失 %s -> %s" % (os.path.relpath(p, SITE), link))

# ---------- 3. CSS 版本号一致 ----------
vers = set()
for p in pages:
    html = open(p, encoding="utf-8").read()
    for m in re.findall(r"style\.css\?v=(\d+)", html):
        vers.add(m)
if len(vers) != 1:
    errors.append("CSS 版本号不一致：%s" % sorted(vers))
css_ver = vers.pop() if vers else "?"

# ---------- 4. 注释锚点配对 ----------
n_ref = n_item = n_back = 0
for w in works:
    p = os.path.join(SITE, "works", "%s.html" % w["id"])
    if not os.path.exists(p):
        errors.append("缺篇目页 %s" % w["id"])
        continue
    html = open(p, encoding="utf-8").read()
    refs = set(re.findall(r'class="nref" id="r(\d+)"', html))
    items = set(re.findall(r'class="note-item" id="n(\d+)"', html))
    backs = set(re.findall(r'class="note-back" href="#r(\d+)"', html))
    n_ref += len(refs); n_item += len(items); n_back += len(backs)
    if refs - items:
        errors.append("%s：正文上标无对应注释 %s" % (w["id"], sorted(refs - items)))
    if backs - refs:
        errors.append("%s：注释回链无对应上标 %s" % (w["id"], sorted(backs - refs)))
    if backs != refs:
        warns.append("%s：上标 %d 个、回链 %d 个（无标记的注释不回链属正常）" % (w["id"], len(refs), len(backs)))

# ---------- 5. 导读覆盖 ----------
missing = [w["id"] for w in works if w["id"] not in reading]
if missing:
    errors.append("这些篇没有导读：%s" % missing)

n_q = 0
for w in works:
    rd = reading.get(w["id"])
    if not rd:
        continue
    p = os.path.join(SITE, "works", "%s.html" % w["id"])
    html = open(p, encoding="utf-8").read()
    if "guide-before" not in html:
        errors.append("%s：缺篇首导读" % w["id"])
    if "guide-after" not in html:
        errors.append("%s：缺篇尾导读" % w["id"])
    n_q += len(rd.get("before", [])) + len(rd.get("after", []))
    for item in rd.get("after", []):
        for n, cue in zip(item.get("paras", []), item.get("cue", [])):
            if not (0 < n <= len(w["paragraphs"])):
                errors.append("%s 导读段号越界 p%d" % (w["id"], n))
            elif cue not in w["paragraphs"][n - 1]:
                errors.append("%s 导读锚词失配 p%d「%s」" % (w["id"], n, cue))
            elif 'id="p%d"' % n not in html:
                errors.append("%s 导读指向的段 %d 页面里不存在" % (w["id"], n))

# ---------- 6. 概念页引文质量 ----------
# 概念页的每条引文都带 keyword（该引文的核心句）。曾经出过两种坏法：
# ① 把小节标题当引文引了（8~15 字，没有正文，读者看不到任何内容）；
# ② 同一段被引两次、配两个 note，页面上出现两段一模一样的长引文。
concepts = json.load(open(os.path.join(ROOT, "data", "concepts.json"), encoding="utf-8"))
by_title = {w["title"].strip(): w for w in works}
n_quote = 0
for c in concepts:
    if not isinstance(c, dict):
        continue
    seen = {}
    for i, q in enumerate(c.get("quotes", [])):
        n_quote += 1
        w = by_title.get(q["work"].strip())
        if not w:
            errors.append("概念 %s 引文指向不存在的篇目「%s」" % (c["id"], q["work"]))
            continue
        text, kw = q["text"].strip(), (q.get("keyword") or "").strip()
        if len(text) < 30 and "。" not in text:
            # 无句号的短引文＝小节标题（「一　没有调查，没有发言权〔1〕」那种），
            # 引了等于没引。有句号的短句是完整的一句话，不算问题。
            errors.append("概念 %s 第%d条引文只有 %d 字且无句号，像是把小标题当引文：%s"
                          % (c["id"], i, len(text), text))
        if kw and kw not in text:
            errors.append("概念 %s 第%d条引文不含 keyword「%s」" % (c["id"], i, kw))
        if not (0 < q.get("para", 0) <= len(w["paragraphs"])):
            errors.append("概念 %s 第%d条段号越界 p%s" % (c["id"], i, q.get("para")))
        elif text not in w["paragraphs"][q["para"] - 1]:
            errors.append("概念 %s 第%d条引文不是第 %d 段的原文子串" % (c["id"], i, q["para"]))
        if text in seen:
            errors.append("概念 %s 引文重复：第%d条与第%d条相同" % (c["id"], seen[text], i))
        seen[text] = i

# ---------- 7. 分页残留复查 ----------
for w in works:
    for i, t in enumerate(w["paragraphs"], 1):
        if "上一页" in t or "下一页" in t or t.strip() == w["title"].strip():
            errors.append("%s p%d 仍有采集残留：%s" % (w["id"], i, t[:30]))

print("页面 %d 个 | 链接 %d 条 | CSS v%s" % (len(pages), checked, css_ver))
print("注释：正文上标 %d、注释条目 %d、回链 %d" % (n_ref, n_item, n_back))
print("导读：%d 篇、%d 个问题 | 概念引文 %d 条" % (
    len([w for w in works if w["id"] in reading]), n_q, n_quote))
if warns:
    print("\n提示：")
    for x in warns:
        print("  - " + x)
if errors:
    print("\n❌ 错误 %d 条：" % len(errors))
    for x in errors[:30]:
        print("  - " + x)
    sys.exit(1)
print("\n✅ 全部通过")
