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
# 下划线开头的是 demo 草稿（未入库、未挂入口），只供版式对比，不参与正式站的检查：
# 它们指向的是旧 CSS 版本，混进来会报「版本号不一致」这种假错。
pages = []
for base, _, files in os.walk(SITE):
    for f in files:
        if f.endswith(".html") and not f.startswith("_"):
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

# ---------- 8. 语录：段号 / 原文子串 / 收藏钩子 ----------
# 语录曾经整体错位过一段：gen_quotes 用 0 基下标取段落，又把下标当段号输出，
# 页面上「第 N 段」比实际少 1，点过去落在上一段（死链检查查不出来，因为 id 存在）。
# 所以这里必须验「该段真的含这句话」，而不是「锚点存在」。
QUOTES = json.load(open(os.path.join(ROOT, "data", "quotes.json"), encoding="utf-8"))["items"]
qmap = {w["id"]: w for w in works}
qh = open(os.path.join(SITE, "quotes.html"), encoding="utf-8").read()
n_q2 = 0
for q in QUOTES:
    n_q2 += 1
    w = qmap.get(q["wid"])
    if not w:
        errors.append("语录 %s 指向不存在的篇目" % q["id"])
        continue
    n = q["para"]
    if not (0 < n <= len(w["paragraphs"])):
        errors.append("语录 %s 段号越界 p%d" % (q["id"], n))
    elif q["text"] not in w["paragraphs"][n - 1]:
        errors.append("语录 %s 不在第 %d 段原文里（段号可能整体位移）" % (q["id"], n))
    if 'data-id="%s"' % q["id"] not in qh:
        errors.append("语录 %s 没出现在页面上" % q["id"])
n_card = qh.count('class="qt" data-id')
if n_card != len(QUOTES):
    errors.append("语录页面卡片 %d 个，数据 %d 条" % (n_card, len(QUOTES)))
if qh.count('class="fav"') != len(QUOTES):
    errors.append("语录收藏按钮 %d 个，数据 %d 条" % (qh.count('class="fav"'), len(QUOTES)))

# ---------- 9. 附录「注释里的另一本书」（挂在概念图谱页末） ----------
# 这一节的所有段号都是「在正文里找〔N〕标记」反查出来的。注释编号一旦串篇
# （《中国共产党在抗日时期的任务》36 条里有 14 条属于紧接其后的一篇，编号从〔1〕重来），
# 反查会落在错误文章的段号上，而且死的只是「内容对不上」，链接照样存在。
cp = open(os.path.join(SITE, "concepts.html"), encoding="utf-8").read()
if 'id="notes"' not in cp:
    errors.append("概念图谱页缺附录锚点 #notes")
nb = cp[cp.find('id="notes"'):]
n_pp = nb.count('class="nb-pp"')
n_tm = nb.count('class="nb-tm-h"')
n_ev = nb.count("<details")
if n_pp < 10:
    errors.append("附录人物卡只有 %d 条（预期 15 上下）" % n_pp)
if n_tm < 10:
    errors.append("附录词表只有 %d 条（预期 18 上下）" % n_tm)

# 附录里每条溯源都要落到「带注释标记的那一段」；否则就是把注挂到了别的段落上
for wid, para in set(re.findall(r'href="works/([\w-]+)\.html#p(\d+)"', nb)):
    w = qmap.get(wid)
    if not w:
        errors.append("附录引用了不存在的篇目 %s" % wid)
        continue
    n = int(para)
    if not (0 < n <= len(w["paragraphs"])):
        errors.append("附录 %s 段号越界 p%d" % (wid, n))
    elif "〔" not in w["paragraphs"][n - 1]:
        errors.append("附录 %s p%d 里没有注释标记，这条溯源挂错了段" % (wid, n))

# 四格数字：按「编号首次出现者为准」独立重算一遍，与页面上的数字对账
def _notes_first_wins(raw):
    out, seen = set(), set()
    for t in raw or []:
        m = re.match(r"〔(\d+)〕", (t or "").strip())
        if not m:
            continue
        k = int(m.group(1))
        if k in seen:
            continue
        seen.add(k)
        out.add(k)
    return out

_total = sum(len(_notes_first_wins(w.get("notes"))) for w in works)
_foreign = sum(len(w.get("notes") or []) for w in works) - _total
_shown = re.findall(r'<div class="n">(\d+)</div>', nb)
if not _shown:
    errors.append("附录缺数字块")
elif int(_shown[0]) != _total:
    errors.append("附录注释条数写 %s，实际本篇注释 %d 条" % (_shown[0], _total))
if _foreign and "%d 条注释" % _foreign not in nb:
    warns.append("有 %d 条外篇注释未在附录里交代（应从〔1〕重来的那批）" % _foreign)

print("页面 %d 个 | 链接 %d 条 | CSS v%s" % (len(pages), checked, css_ver))
print("注释：正文上标 %d、注释条目 %d、回链 %d" % (n_ref, n_item, n_back))
print("导读：%d 篇、%d 个问题 | 概念引文 %d 条 | 语录 %d 条" % (
    len([w for w in works if w["id"] in reading]), n_q, n_quote, n_q2))
print("附录：人物 %d、词条 %d、年表 %d 年 | 本篇注释 %d 条、外篇 %d 条" % (
    n_pp, n_tm, n_ev, _total, _foreign))
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
