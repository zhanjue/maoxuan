# -*- coding: utf-8 -*-
"""聚合解析：求是网选集 HTML（按章节分页）→ works.json（按篇聚合）。
数据源：求是网 qstheory.cn《毛泽东选集第一卷》（官方渠道，2019-07-31 发布）。
注意：长文按章节分页，需按 WORKS 映射聚合；《为争取千百万群众进入抗日民族统一战线
而斗争》求是网未收录，MVP 暂缺，标记 TODO。
"""
import re, os, json, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")

P1 = "第一次国内革命战争时期"
P2 = "第二次国内革命战争时期"

# (标题, 页码范围, 时期) —— 页码范围对应 raw/idxNN.html
WORKS = [
    ("中国社会各阶级的分析", [1], P1),
    ("湖南农民运动考察报告", [2], P1),
    ("中国的红色政权为什么能够存在？", [3], P2),
    ("井冈山的斗争", [4], P2),
    ("关于纠正党内的错误思想", [5], P2),
    ("星星之火，可以燎原", [6], P2),
    ("反对本本主义", [7], P2),
    ("必须注意经济工作", [8], P2),
    ("怎样分析农村阶级", [9], P2),
    ("我们的经济政策", [10], P2),
    ("关心群众生活，注意工作方法", [11], P2),
    ("论反对日本帝国主义的策略", [12], P2),
    ("中国革命战争的战略问题", [13, 14, 15, 16, 17], P2),
    ("关于蒋介石声明的声明", [18], P2),
    ("中国共产党在抗日时期的任务", [19, 20], P2),
    ("实践论", [21, 22], P2),
    ("矛盾论", [22, 23, 24, 25, 26, 27, 28], P2),
]

NUM = "[一二三四五六七八九〇○零十]"
CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "〇": 0, "○": 0, "零": 0}

def cn_year(s):
    n = 0
    for ch in s:
        if ch in CN_NUM:
            n = n * 10 + CN_NUM[ch]
        elif ch == "十":
            n = n * 10 if n else 10
    return n

def cn_int(x):
    if "十" in x:
        a, _, b = x.partition("十")
        return (CN_NUM.get(a, 1) * 10) + (CN_NUM.get(b, 0) if b else 0)
    return CN_NUM.get(x, 0)

def parse_date(s):
    m = re.search(r"（(" + NUM + "{2,4})年([一二三四五六七八九十]{1,3})月([一二三四五六七八九十]{1,3})日）", s)
    if m:
        return "%d-%02d-%02d" % (cn_year(m.group(1)), cn_int(m.group(2)), cn_int(m.group(3))), m.group(0)
    m2 = re.search(r"（(" + NUM + "{2,4})年([一二三四五六七八九十]{1,3})月）", s)
    if m2:
        return "%d-%02d" % (cn_year(m2.group(1)), cn_int(m2.group(2))), m2.group(0)
    return None, None

def page_paras(idx):
    path = os.path.join(RAW, "idx%02d.html" % idx)
    t = open(path, encoding="utf-8").read()
    m = re.search(r"<h1[^>]*>.*?</h1>", t, re.S)
    seg = t[m.end():] if m else t
    out = []
    for p in re.findall(r"<p[^>]*>(.*?)</p>", seg, re.S):
        txt = re.sub(r"<[^>]+>", "", p)
        txt = txt.replace("&nbsp;", " ").replace("&quot;", chr(34)).replace("&amp;", "&")
        txt = re.sub(r"^　+", "", txt).strip()  # 只删段首缩进，保留章节标题内空格
        if txt:
            out.append(txt)
    return out

DATE_RE = re.compile(r"^（" + NUM + "{2,4}年")
works = []
for order, (title, pages, period) in enumerate(WORKS, 1):
    paras = []
    for pg in pages:
        paras.extend(page_paras(pg))
    body, notes, date_key, date_norm = [], [], None, None
    in_notes = False
    seen_title = False
    for p in paras:
        if p == "注释":
            in_notes = True
            continue
        if in_notes:
            if p.startswith("〔"):
                notes.append(p)
            # 非〔开头的段是页脚杂质（推荐阅读摘要等），忽略
            continue
        if p.startswith(title) and len(p) > len(title):
            p = p[len(title):].lstrip("　 ")  # 「矛盾论一　两种宇宙观」→「一　两种宇宙观」
        if p == title and not seen_title:
            seen_title = True
            continue
        if DATE_RE.match(p) and date_norm is None:
            date_key, date_norm = parse_date(p)
            continue
        if DATE_RE.match(p):
            continue  # 续页重复的日期段
        if p.startswith("毛泽东的《") and not body:
            continue  # 题解段（MVP 暂不收）
        body.append(p)
    # 矛盾论与后续篇的边界保护：本篇遇到下一篇篇名即止
    nxt = None
    for t2, pgs, _ in WORKS[order:]:
        if pgs[0] > pages[-1]:
            nxt = t2
            break
    if nxt:
        for i, p in enumerate(body):
            if p == nxt:
                body = body[:i]
                break
    if date_key is None:
        print("WARN %s date missing" % title)
    works.append({
        "id": "v1-%03d" % order,
        "vol": 1,
        "order": order,
        "period": period,
        "title": title,
        "date": date_norm,
        "dateKey": date_key,
        "paragraphs": body,
        "notes": notes,
        "charCount": sum(len(p) for p in body),
        "source": "求是网 qstheory.cn",
    })
    print("v1-%03d %-24s %-11s %4d段 %6d字 注%2d | %s" % (
        order, title[:22], period[:6], len(body), sum(len(p) for p in body), len(notes), date_norm or "?"))

out = os.path.join(ROOT, "data", "works.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(works, f, ensure_ascii=False, indent=1)
total = sum(w["charCount"] for w in works)
print("\nTOTAL %d works, %d chars -> %s" % (len(works), total, out))
