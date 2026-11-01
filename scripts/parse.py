# -*- coding: utf-8 -*-
"""解析求是网选集 HTML → 结构化 works.json。
页面结构：class="text" 容器内 <p> 序列：
  时期标题（如「第一次国内革命战争时期」）
  篇名（如「中国社会各阶级的分析」）
  日期（如「（一九二五年十二月一日）」）
  [题解段（可选，以「毛泽东的《篇名》」开头）]
  正文段落若干
  「注释」
  注释条目（〔N〕……）
"""
import re, os, json, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")

CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "〇": 0, "零": 0}

def cn_year(s):
    """一九二五 -> 1925"""
    n = 0
    for ch in s:
        if ch in CN_NUM:
            n = n * 10 + CN_NUM[ch]
        elif ch == "十":
            n = n * 10 if n else 10
    return n

def parse_date(s):
    """（一九二五年十二月一日） -> 1925-12-01"""
    m = re.search(r"（([一二三四五六七八九〇零十]{2,4})年([一二三四五六七八九十]{1,3})月([一二三四五六七八九十]{1,3})日）", s)
    if not m:
        m2 = re.search(r"（([一二三四五六七八九〇零十]{2,4})年([一二三四五六七八九十]{1,3})月）", s)
        if not m2:
            return None, None
        return "%d-%02d" % (cn_year(m2.group(1)), cn_year(m2.group(2))), m2.group(0)
    def cn_int(x):
        if "十" in x:
            a, _, b = x.partition("十")
            return (CN_NUM.get(a, 1) * 10) + (CN_NUM.get(b, 0) if b else 0)
        return CN_NUM.get(x, 0)
    return "%d-%02d-%02d" % (cn_year(m.group(1)), cn_int(m.group(2)), cn_int(m.group(3))), m.group(0)

def extract_paras(html):
    # 从 h1 之后截取，避开头部导航；class="text" 容器嵌套 div 无法用正则闭合匹配
    m = re.search(r"<h1[^>]*>.*?</h1>", html, re.S)
    seg = html[m.end():] if m else html
    paras = []
    for p in re.findall(r"<p[^>]*>(.*?)</p>", seg, re.S):
        txt = re.sub(r"<[^>]+>", "", p)
        txt = txt.replace("&nbsp;", " ").replace("&quot;", chr(34)).replace("&amp;", "&")
        txt = txt.replace("　", "").strip()
        if txt:
            paras.append(txt)
    return paras

works = []
for path in sorted(glob.glob(os.path.join(RAW, "idx*.html"))):
    idx = int(re.search(r"idx(\d+)", path).group(1))
    html = open(path, encoding="utf-8").read()
    paras = extract_paras(html)
    if len(paras) < 4:
        print("SKIP idx%02d (only %d paras)" % (idx, len(paras)))
        continue
    period = paras[0] if paras[0].endswith("时期") else None
    title = paras[1] if period else paras[0]
    date_str = paras[2] if period else paras[1]
    date_key, date_norm = parse_date(date_str)
    if date_key is None:
        print("WARN idx%02d date parse fail: %r" % (idx, date_str[:30]))
    rest = paras[3:] if period else paras[2:]
    intro = None
    if rest and rest[0].startswith("毛泽东的《"):
        intro = rest[0]
        rest = rest[1:]
    body, notes = [], []
    in_notes = False
    for p in rest:
        if p == "注释":
            in_notes = True
            continue
        (notes if in_notes else body).append(p)
    if not title or len(title) > 40:
        print("WARN idx%02d bad title: %r" % (idx, title[:50]))
    works.append({
        "id": "v1-%03d" % idx,
        "vol": 1,
        "order": idx,
        "period": period,
        "title": title,
        "date": date_norm,
        "dateKey": date_key,
        "intro": intro,
        "paragraphs": body,
        "notes": notes,
        "charCount": sum(len(p) for p in body),
    })
    print("idx%02d | %-28s | %-12s | %4d段 %6d字 | 注释%d | %s" % (
        idx, title[:26], period or "-", len(body), sum(len(p) for p in body), len(notes), date_norm or "?"))

out = os.path.join(ROOT, "data", "works.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(works, f, ensure_ascii=False, indent=1)
print("\nTOTAL", len(works), "works ->", out)
