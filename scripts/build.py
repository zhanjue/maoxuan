# -*- coding: utf-8 -*-
"""知行录 · 毛泽东著作知识库 MVP — 静态站生成器。
读 data/works.json + data/concepts.json → 生成 site/ 下全站。
设计约束：数据全部内联（file:// 双击可用，无 fetch 依赖）；Ink 纸白主题；
溯源单元 = 卷/篇/段；段号为本库对求是网电子文本的编号，非纸质版页码。
"""
import json, os, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
WORKS = json.load(open(os.path.join(ROOT, "data", "works.json"), encoding="utf-8"))
CONCEPTS = json.load(open(os.path.join(ROOT, "data", "concepts.json"), encoding="utf-8"))

VOL = "卷一"
SRC = "人民出版社《毛泽东选集》第一卷（求是网电子文本）"
TOTAL_CHARS = sum(w["charCount"] for w in WORKS)
TOTAL_QUOTES = sum(len(c["quotes"]) for c in CONCEPTS)

def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

# ---------- 术语 → 页内链接（占位符法避免嵌套误匹配） ----------
# 高亮用复合词/专著名，不用单字词（避免「矛盾论」被拆成「矛盾」+「论」）
TERM_LINKS = [
    ("矛盾的普遍性", "pubianxing"), ("矛盾的特殊性", "teshuxing"), ("主要矛盾", "zhuyaomaodun"),
    ("调查研究", "diaocha"), ("本本主义", "benbenzhuyi"), ("工农武装割据", "gewuzhanshi"),
    ("统一战线", "tongyizhanxian"), ("集中兵力", "jizhongbingli"), ("积极防御", "jijifangyu"),
    ("运动战", "yundongzhan"), ("群众路线", "qunzhongluxian"), ("阶级分析", "jiejifenxi"),
    ("农民问题", "nongmin"), ("经济工作", "jingji"), ("党内错误思想", "jiuzhengcuowu"),
    ("星星之火", "xingxingzhihuo"), ("矛盾论", "maodun"), ("实践论", "shijian"),
    ("井冈山", "jinggangshan"), ("歼灭战", "jizhongbingli"),
]
TERM_LINKS.sort(key=lambda x: len(x[0]), reverse=True)

def link_terms(text, depth):
    t = esc(text)
    p = "../" * depth
    marks = []
    for i, (name, cid) in enumerate(TERM_LINKS):
        tok = "\x01%d\x01" % i
        if name in t:
            t = t.replace(name, tok)
            marks.append((tok, '<a class="term" href="%sconcepts/%s.html">%s</a>' % (p, cid, esc(name))))
    for tok, tag in marks:
        t = t.replace(tok, tag)
    return t

def date_disp(w):
    return (w["date"] or "").strip("（）") or "日期待考"

# ---------- 引文片段（以关键词为中心的窗口 + 高亮） ----------
def quote_snippet(text, keyword, width=64):
    idx = text.find(keyword)
    if idx < 0 and len(keyword) >= 6:
        idx = text.find(keyword[:6])
    if idx < 0:
        s, e, core, mark = 0, min(len(text), width * 2), None, None
    else:
        s = max(0, idx - width)
        e = min(len(text), idx + len(keyword) + width)
        core = text[idx:idx + len(keyword)]
    snip = text[s:e]
    lead = "……" if s > 0 else ""
    tail = "……" if e < len(text) else ""
    out = esc(lead + snip + tail)
    if core:
        out = out.replace(esc(core), "<mark>%s</mark>" % esc(core), 1)
    return out

# ---------- 页面骨架 ----------
NAV = [
    ("index.html", "首页", 0),
    ("works.html", "篇目", 0),
    ("concepts.html", "概念图谱", 0),
    ("timeline.html", "时期轴", 0),
    ("tool-maodun.html", "矛盾论工具", 0),
    ("search.html", "检索", 0),
]

def page(title, body, depth, active=""):
    p = "../" * depth
    nav = []
    for href, label, _ in NAV:
        cls = ' class="on"' if href.startswith(active) and active else ""
        nav.append('<a href="%s%s"%s>%s</a>' % (p, href, cls, label))
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%s · 知行录</title>
<meta name="description" content="知行录：《毛泽东选集》第一卷结构化知识库。17 篇正式出版文本，20 个概念节点，46 条溯源引文，每一段都可回溯到卷/篇/段。">
<link rel="stylesheet" href="%sassets/style.css?v=3">
</head>
<body>
<header class="topbar"><div class="topbar-in">
<a class="brand" href="%sindex.html">知行录<small>MAO WORKS · VOL.1</small></a>
<nav class="nav">%s</nav>
<div class="searchbox"><input id="q" type="search" placeholder="检索全文…" autocomplete="off"><span style="font-size:11px;color:var(--ink-3)">↵</span></div>
</div></header>
%s
<footer class="footer"><div class="wrap"><div class="bd">
<p><b>知行录</b>——文献检索与阅读工具。语料仅采自%s，经求是网（qstheory.cn，官方渠道）电子文本整理，逐字收录，未作任何改写。</p>
<p>本站只作阅读与检索之用，不作历史评价与政治表达。文中「段号」为本库对电子文本的段落编号，非纸质版页码；引文均可点击出处跳转核对。</p>
</div></div></footer>
<script src="%sassets/app.js"></script>
</body>
</html>""" % (title, p, p, "".join(nav), body, SRC, p)

def write(path, content):
    full = os.path.join(SITE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)

# ---------- 1. 首页 ----------
def build_index():
    cats = []
    for c in CONCEPTS[:6]:
        cats.append("""<a class="cc" href="concepts/%s.html"><div class="cat">%s</div><div class="nm">%s</div><div class="one">%s</div></a>""" % (
            c["id"], esc(c["category"]), esc(c["name"]), esc(c["oneliner"])))
    body = """
<div class="wrap"><section class="hero">
<h1>把《毛选》第一卷<br>读成一座可检索的图书馆</h1>
<p class="sub">17 篇正式出版文本，20 个概念节点，46 条溯源引文。<b>每一个判断都挂回原话</b>——点开任何一条引文，都能跳到它在某卷某篇某段的位置。</p>
<div class="stats">
<div class="stat"><div class="n">17</div><div class="l">篇目（第一卷全量）</div></div>
<div class="stat"><div class="n">%s</div><div class="l">字正文</div></div>
<div class="stat"><div class="n">%d</div><div class="l">概念节点</div></div>
<div class="stat"><div class="n">%d</div><div class="l">溯源引文</div></div>
<div class="stat"><div class="n">%d</div><div class="l">条注释</div></div>
</div>
</section>

<section class="section">
<h2>从这里进</h2>
<p class="desc">四种读法：顺着时期读原文、按概念查、用工具理解、随机开一篇。</p>
<div class="entries">
<a class="entry" href="works.html"><div class="t">按时期读</div><div class="d">第一次国内革命战争时期 · 第二次国内革命战争时期，共 17 篇</div></a>
<a class="entry" href="concepts.html"><div class="t">概念图谱</div><div class="d">实践 · 矛盾 · 调查研究 · 工农武装割据……每个概念都有出处和演变</div></a>
<a class="entry" href="tool-maodun.html"><div class="t">矛盾论工具</div><div class="d">交互演示主要矛盾与矛盾主要方面的转化——把「读」变成「用」</div></a>
<a class="entry" href="search.html"><div class="t">全文检索</div><div class="d">段落级检索，命中直接跳到段</div></a>
</div>
</section>

<section class="section">
<h2>今日一篇</h2>
<p class="desc">每次打开随机开一篇——像翻一本书那样翻完 17 篇。</p>
<div class="today" id="today"></div>
</section>

<section class="section">
<h2>概念精选</h2>
<p class="desc">20 个概念节点中的 6 个。<a href="concepts.html" style="color:var(--teal)">看全部 →</a></p>
<div class="concept-grid">%s</div>
</section>
</div>""" % ("{:,}".format(TOTAL_CHARS), len(CONCEPTS), TOTAL_QUOTES, sum(len(w["notes"]) for w in WORKS), "".join(cats))
    # 今日一篇数据内联
    brief = [{"t": w["title"], "d": date_disp(w), "c": w["charCount"], "u": "works/%s.html" % w["id"]} for w in WORKS]
    body += '<script>window.__TODAY__=%s;</script>' % json.dumps(brief, ensure_ascii=False)
    write("index.html", page("首页", body, 0, "index"))

# ---------- 2. 篇目库 ----------
def build_works():
    groups = []
    for period in ("第一次国内革命战争时期", "第二次国内革命战争时期"):
        ws = [w for w in WORKS if w["period"] == period]
        if not ws:
            continue
        rows = []
        for w in ws:
            rows.append("""<a class="work-row" href="works/%s.html"><span class="no">%03d</span><span class="tt">%s</span><span class="dt">%s</span><span class="ct">%s 字</span></a>""" % (
                w["id"], w["order"], esc(w["title"]), esc(date_disp(w)), "{:,}".format(w["charCount"])))
        span = "%s — %s" % (ws[0]["dateKey"], ws[-1]["dateKey"])
        groups.append("""<div class="period-group"><div class="period-head"><span class="pn">%s</span><span class="pr">%s · %d 篇</span></div>%s</div>""" % (
            esc(period), span, len(ws), "".join(rows)))
    body = """<div class="wrap" style="padding-top:40px">
<h1 style="font-family:var(--display);font-size:30px;font-weight:700">篇目库 · 第一卷全量</h1>
<p style="font-size:13.5px;color:var(--ink-3);margin:10px 0 28px">按写作时间排序。点击篇名进入阅读页——正文段落全部编号，段号即锚点。</p>
%s</div>""" % "".join(groups)
    write("works.html", page("篇目库", body, 0, "works"))

# ---------- 3. 阅读页 ----------
def build_work(w):
    idx = w["order"] - 1
    prev_w = WORKS[idx - 1] if idx > 0 else None
    next_w = WORKS[idx + 1] if idx < len(WORKS) - 1 else None
    # 关联概念：quotes 命中本篇的概念
    rel = [c for c in CONCEPTS if any(q["work"] == w["title"] for q in c["quotes"])]
    rel_tags = "".join('<a href="../concepts/%s.html">%s</a>' % (c["id"], esc(c["name"])) for c in rel)
    # 正文
    paras = []
    import re as _re
    for i, p in enumerate(w["paragraphs"], 1):
        is_sec = bool(_re.match(r"^[一二三四五六七八九十]+　|^第[一二三四五六七八九十]+章", p)) or (len(p) < 20 and p.endswith(("的问题", "失败", "策略")))
        cls = "para sec" if is_sec else "para"
        paras.append('<div class="%s" id="p%d">%s<a class="pno" href="#p%d">%d</a></div>' % (
            cls, i, link_terms(p, 1), i, i))
    intro = ""
    if w.get("intro"):
        intro = '<div class="intro-box"><span class="lb">题解</span>%s</div>' % esc(w["intro"])
    notes = ""
    if w["notes"]:
        items = "".join('<div class="note-item">%s</div>' % esc(n) for n in w["notes"])
        notes = '<details class="notes-toggle"><summary>注释 %d 条</summary><div class="notes-body">%s</div></details>' % (len(w["notes"]), items)
    prev_html = '<a href="../%s.html">← 上一篇 · %s</a>' % (prev_w["id"], esc(prev_w["title"])) if prev_w else "<span></span>"
    next_html = '<a class="next" href="../%s.html">下一篇 · %s →</a>' % (next_w["id"], esc(next_w["title"])) if next_w else "<span></span>"
    body = """<div class="narrow">
<div class="read-head">
<div class="crumb"><a href="../index.html">首页</a> / <a href="../works.html">篇目库</a> / %s · %s</div>
<h1>%s</h1>
<div class="read-meta"><span>%s</span><span>%d 段</span><span>%s 字</span><span>源：求是网</span></div>
%s
</div>
<article class="article">%s</article>
%s
<div style="margin-top:8px"><div style="font-size:12px;color:var(--ink-3);letter-spacing:0.2em">本篇涉及的概念</div><div class="related-concepts">%s</div></div>
<div class="read-foot">%s%s</div>
</div>""" % (esc(VOL), esc(w["period"] or ""), esc(w["title"]), esc(date_disp(w)),
             len(w["paragraphs"]), "{:,}".format(w["charCount"]), intro, "".join(paras), notes, rel_tags or "<span style='font-size:13px;color:var(--ink-3)'>暂无</span>", prev_html, next_html)
    write("works/%s.html" % w["id"], page(w["title"], body, 1, "works"))

# ---------- 4. 概念索引 ----------
def build_concepts_index():
    cats = {}
    for c in CONCEPTS:
        cats.setdefault(c["category"], []).append(c)
    blocks = []
    for cat, cs in cats.items():
        items = "".join("""<a class="cc" href="concepts/%s.html"><div class="nm">%s</div><div class="one">%s</div></a>""" % (c["id"], esc(c["name"]), esc(c["oneliner"])) for c in cs)
        blocks.append("""<div style="margin-bottom:34px"><div class="cat-head"><span class="pn">%s</span><span class="pr">%d 个节点</span></div><div class="concept-grid">%s</div></div>""" % (esc(cat), len(cs), items))
    body = """<div class="wrap" style="padding-top:40px">
<h1 style="font-family:var(--display);font-size:30px;font-weight:700">概念图谱</h1>
<p style="font-size:13.5px;color:var(--ink-3);margin:10px 0 28px">20 个概念节点，按 7 个领域归类。每个节点 = 一句话定义 + 核心要义 + 原话精选（逐字引文，精确到段）+ 演变时间线 + 自问自答。</p>
%s</div>""" % "".join(blocks)
    write("concepts.html", page("概念图谱", body, 0, "concepts"))

# ---------- 5. 概念页 ----------
def build_concept(c):
    quotes = []
    for q in c["quotes"]:
        w = [x for x in WORKS if x["title"] == q["work"]][0]
        quotes.append("""<div class="quote"><div class="qt">%s</div>
<div class="qm"><span>%s · %s · <a href="../works/%s.html#p%d">第 %d 段 ↗</a></span><span>%s</span></div></div>""" % (
            quote_snippet(q["text"], q.get("keyword", ""), 64), esc(VOL), esc(q["work"]), w["id"], q["para"], q["para"], esc(q["note"])))
    essence = "".join("<li>%s</li>" % esc(e) for e in c["essence"])
    evo = []
    for e in c["evolution"]:
        out = '<span class="out">（%s，本库未收电子文本）</span>' % e.get("vol", "后续卷次") if e.get("outside") else ""
        wk = '<a href="../works/%s.html">%s</a>%s' % ([x for x in WORKS if x["title"] == e["work"]][0]["id"], esc(e["work"]), out) if not e.get("outside") else esc(e["work"]) + out
        evo.append('<div class="evo-item"><span class="dt">%s</span><span class="wk">%s</span><span class="nt">%s</span></div>' % (esc(e["dateKey"]), wk, esc(e["note"])))
    related = []
    for rid in c["relatedIds"]:
        w = [x for x in WORKS if x["id"] == rid][0]
        related.append('<a href="../works/%s.html">%s</a>' % (rid, esc(w["title"])))
    qa = "".join('<div class="q">%s</div><div class="a">%s</div>' % (esc(x["q"]), esc(x["a"])) for x in c["qa"])
    body = """<div class="narrow">
<div class="concept-head">
<div class="cat">%s</div>
<h1>%s</h1>
<div class="oneliner">%s</div>
</div>
<div class="section"><h2>核心要义</h2><ul class="essence">%s</ul></div>
<div class="section"><h2>原话精选</h2><p class="desc">逐字引文，点击出处跳到原文段落核对。</p>%s</div>
<div class="section"><h2>思想演变</h2><div class="evo">%s</div></div>
<div class="section"><h2>关联篇目</h2><div class="related-concepts">%s</div></div>
<div class="section"><h2>问与答</h2><div class="qa">%s</div></div>
</div>""" % (esc(c["category"]), esc(c["name"]), esc(c["oneliner"]), essence, "".join(quotes), "".join(evo), "".join(related), qa)
    write("concepts/%s.html" % c["id"], page(c["name"], body, 1, "concepts"))

# ---------- 6. 时期轴 ----------
def build_timeline():
    items = []
    for w in WORKS:
        evos = [e for c in CONCEPTS for e in c["evolution"] if e["work"] == w["title"] and not e.get("outside")]
        tag = ""
        if evos:
            tag = " · " + "、".join(sorted({e["dateKey"] for e in evos})) + " 概念演变"
        items.append("""<div class="tl-item"><div class="d">%s</div><div class="t"><a href="works/%s.html">%s</a></div><div class="s">%s · %s 字%s</div></div>""" % (
            esc(w["dateKey"] or "—"), w["id"], esc(w["title"]), esc(w["period"] or ""), "{:,}".format(w["charCount"]), tag))
    # 概念演变汇总
    evo_rows = []
    for c in CONCEPTS:
        if len(c["evolution"]) >= 2:
            chain = " → ".join("%s《%s》" % (e["dateKey"], e["work"]) for e in c["evolution"])
            evo_rows.append('<div class="evo-item"><span class="dt">%d 节点</span><span class="wk"><a href="concepts/%s.html">%s</a></span><span class="nt">%s</span></div>' % (
                len(c["evolution"]), c["id"], esc(c["name"]), esc(chain)))
    body = """<div class="wrap" style="padding-top:40px">
<h1 style="font-family:var(--display);font-size:30px;font-weight:700">时期轴</h1>
<p style="font-size:13.5px;color:var(--ink-3);margin:10px 0 12px">第一卷 17 篇按写作时间排列——1925 年《中国社会各阶级的分析》到 1937 年《矛盾论》，横跨第一次国内革命战争与第二次国内革命战争两个时期。</p>
<div class="tl">%s</div>
<div class="section" style="border-top:1px solid var(--line);margin-top:24px">
<h2>概念演变链</h2>
<p class="desc">同一个概念在不同时期的表述变化——这是 AI 聊天给不了的深度，也是本库对标 learnbuffett「思想演变时间线」的核心资产。</p>
<div class="evo">%s</div>
</div>
</div>""" % ("".join(items), "".join(evo_rows))
    write("timeline.html", page("时期轴", body, 0, "timeline"))

# ---------- 7. 矛盾论工具 ----------
def build_tool():
    body = """<div class="narrow" style="padding-top:40px">
<div class="crumb" style="font-size:12px;color:var(--ink-3)"><a href="index.html" style="color:var(--ink-3);text-decoration:none">首页</a> / 工具</div>
<h1 style="font-family:var(--display);font-size:30px;font-weight:700">主要矛盾演示器</h1>
<p style="font-size:13.5px;color:var(--ink-2);margin:12px 0 4px;line-height:1.9">《矛盾论》第四节说：<b>复杂事物的发展过程中有许多的矛盾存在，其中必有一种是主要的</b>——捉住了主要矛盾，一切问题就迎刃而解。下面用第一卷第 68、69 段的结构，演示主要矛盾如何随阶段转化。</p>
<div class="tool-legend">
<span class="k"><span class="sw" style="background:#0F766E"></span>主要矛盾（决定过程性质）</span>
<span class="k"><span class="sw" style="background:#C8C5BB"></span>次要矛盾（受主要矛盾规定和影响）</span>
<span class="k"><span class="sw" style="background:#fff;border:1px solid #0F766E"></span>矛盾主要方面（决定事物性质的一面）</span>
</div>
<div class="tool-stage">
<div style="display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap" id="tabs"></div>
<div id="scene"></div>
</div>
<div class="tool-explain" id="explain"></div>
<div class="section" style="border-top:1px solid var(--line);margin-top:36px">
<h2>语料依据</h2>
<p class="desc">工具中的结构判断均可在《矛盾论》第一卷第 68—72 段核对。</p>
%s
</div>
</div>""" % TOOL_QUOTES_HTML
    body += '<script>window.__TOOL__=%s;</script>' % json.dumps(TOOL_SCENES, ensure_ascii=False)
    write("tool-maodun.html", page("主要矛盾演示器", body, 0, "tool"))

TOOL_SCENES = [
    {"key": "a", "name": "半殖民地的中国 · 1925—1931", "phase": "阶段一",
     "main": "帝国主义和中华民族的矛盾", "mainAspect": "民族矛盾上升为矛盾主要方面",
     "secondary": ["封建主义和人民大众的矛盾", "工人阶级和资产阶级的矛盾", "农民阶级和地主阶级的矛盾"],
     "note": "两大根本矛盾并存，民族矛盾居于主导——统一战线策略的总依据。"},
    {"key": "b", "name": "抗日战争爆发 · 1931 九一八之后", "phase": "阶段二",
     "main": "日本帝国主义和中华民族的矛盾", "mainAspect": "中日矛盾成为最主要的矛盾",
     "secondary": ["国内阶级矛盾降为次要矛盾", "封建主义和人民大众的矛盾", "反动势力内部的矛盾"],
     "note": "当着日本帝国主义发动侵略，民族矛盾上升为主要矛盾，国内阶级矛盾降为次要和服从的地位——这正是《论反对日本帝国主义的策略》的形势判断。"},
    {"key": "c", "name": "资本主义社会 · 《矛盾论》原例", "phase": "阶段对照",
     "main": "无产阶级和资产阶级的矛盾", "mainAspect": "资产阶级在矛盾主要方面（资本主义社会性质）",
     "secondary": ["独占资本和自由资本的矛盾（帝国主义阶段新发生）", "宗主国和殖民地的矛盾", "生产社会化和占有私人性的矛盾"],
     "note": "根本矛盾（性质）未变，但在不同阶段采取了逐渐激化的形式，并激化/发生新的大小矛盾——过程显出阶段性。"},
]

TOOL_QUOTES_HTML = "".join("""<div class="quote"><div class="qt">%s</div><div class="qm"><span>卷一 · 矛盾论 · <a href="works/%s.html#p%d">第 %d 段 ↗</a></span><span>%s</span></div></div>""" % (
    quote_snippet(q["text"], q.get("keyword", ""), 60), [x for x in WORKS if x["title"] == "矛盾论"][0]["id"], q["para"], q["para"], esc(q["note"]))
    for q in [c for c in CONCEPTS if c["id"] == "zhuyaomaodun"][0]["quotes"])

# ---------- 8. 检索页 ----------
def build_search():
    index = []
    for w in WORKS:
        for i, p in enumerate(w["paragraphs"], 1):
            index.append({"w": w["title"], "p": i, "u": "works/%s.html#p%d" % (w["id"], i), "t": p})
    body = """<div class="narrow" style="padding-top:40px">
<h1 style="font-family:var(--display);font-size:30px;font-weight:700">全文检索</h1>
<p style="font-size:13.5px;color:var(--ink-3);margin:10px 0 4px">段落级检索——命中直接跳到段。全部 %s 个段落、%s 字。</p>
<input class="search-input" id="sq" type="search" placeholder="输入关键词，如：实践、矛盾、调查、集中兵力……" autofocus>
<div class="search-hint" id="hint">支持词片段匹配；点击结果跳转到阅读页对应段落。</div>
<div id="results"></div>
</div>""" % ("{:,}".format(len(index)), "{:,}".format(TOTAL_CHARS))
    body += '<script>window.__INDEX__=%s;</script>' % json.dumps(index, ensure_ascii=False)
    write("search.html", page("全文检索", body, 0, "search"))

# ---------- 9. app.js ----------
APP_JS = r"""
(function(){
  var $ = function(s){ return document.querySelector(s); };
  // 顶栏检索 → 跳检索页
  var q = document.getElementById('q');
  if (q) {
    q.addEventListener('keydown', function(e){
      if (e.key === 'Enter' && q.value.trim()) {
        location.href = 'search.html?q=' + encodeURIComponent(q.value.trim());
      }
    });
  }
  // 今日一篇
  var today = document.getElementById('today');
  if (today && window.__TODAY__) {
    var ws = window.__TODAY__;
    var w = ws[Math.floor(Math.random() * ws.length)];
    today.innerHTML = '<div class="k">今日一篇</div><div><a class="t" href="' + w.u + '">' + w.t + '</a>' +
      '<div class="m">' + w.d + ' · ' + w.c + ' 字</div></div>';
  }
  // 检索
  var sq = document.getElementById('sq');
  if (sq && window.__INDEX__) {
    var idx = window.__INDEX__, out = $('#results'), hint = $('#hint');
    var pre = new URLSearchParams(location.search).get('q');
    if (pre) { sq.value = pre; run(pre); }
    var timer = null;
    sq.addEventListener('input', function(){
      clearTimeout(timer);
      timer = setTimeout(function(){ run(sq.value.trim()); }, 120);
    });
    function esc(s){ var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
    function run(kw) {
      if (!kw) { out.innerHTML = ''; hint.textContent = '支持词片段匹配；点击结果跳转到阅读页对应段落。'; return; }
      var hits = [];
      for (var i = 0; i < idx.length; i++) {
        var it = idx[i];
        var at = it.t.indexOf(kw);
        if (at >= 0) {
          var s = Math.max(0, at - 30), e = Math.min(it.t.length, at + kw.length + 40);
          var snip = (s>0?'……':'') + it.t.slice(s, e) + (e<it.t.length?'……':'');
          hits.push({w: it.w, p: it.p, u: it.u, snip: snip, at: at - s});
          if (hits.length >= 60) break;
        }
      }
      hint.textContent = '命中 ' + hits.length + (hits.length >= 60 ? '+' : '') + ' 段';
      out.innerHTML = hits.map(function(h){
        var snip = esc(h.snip);
        var mk = esc(kw);
        var at = h.snip.indexOf(kw);
        if (at >= 0) snip = esc(h.snip.slice(0, at)) + '<em>' + mk + '</em>' + esc(h.snip.slice(at + kw.length));
        return '<a class="result" href="' + h.u + '"><div class="rw">' + esc(h.w) + ' · 第 ' + h.p + ' 段</div><div class="rt">' + snip + '</div></a>';
      }).join('') || '<div class="result-empty">没有命中。换个词试试——或去<a href="concepts.html" style="color:var(--teal)">概念图谱</a>按主题浏览。</div>';
    }
  }
  // 矛盾论工具
  if (window.__TOOL__) {
    var scenes = window.__TOOL__, tabs = document.getElementById('tabs'), stage = document.getElementById('scene'), ex = document.getElementById('explain');
    function render(i) {
      var s = scenes[i];
      tabs.innerHTML = scenes.map(function(x, j){
        return '<button data-i="' + j + '" style="font-family:var(--text);font-size:13px;padding:6px 14px;border-radius:999px;border:1px solid ' + (j===i?'#0F766E':'var(--line-2)') + ';background:' + (j===i?'#E6F2F0':'#fff') + ';color:' + (j===i?'#0F766E':'var(--ink-2)') + ';cursor:pointer">' + x.name + '</button>';
      }).join('');
      tabs.querySelectorAll('button').forEach(function(b){
        b.addEventListener('click', function(){ render(+b.dataset.i); });
      });
      var sec = s.secondary.map(function(x){
        return '<div style="padding:12px 16px;background:#F4F3EF;border:1px solid var(--line);border-radius:6px;font-size:14px;color:var(--ink-2)">' + x + '</div>';
      }).join('');
      stage.innerHTML =
        '<div style="font-size:11px;color:var(--ink-3);letter-spacing:0.2em;margin-bottom:10px">' + s.phase + '</div>' +
        '<div style="display:flex;flex-wrap:wrap;gap:14px;align-items:stretch">' +
          '<div style="flex:1 1 300px;padding:18px 20px;background:#E6F2F0;border:2px solid #0F766E;border-radius:8px">' +
            '<div style="font-size:11px;color:#0F766E;letter-spacing:0.2em">主要矛盾</div>' +
            '<div style="font-family:var(--display);font-size:20px;font-weight:700;margin-top:6px;color:#0F766E">' + s.main + '</div>' +
            '<div style="font-size:12.5px;color:var(--ink-2);margin-top:8px">' + s.mainAspect + '</div>' +
          '</div>' +
          '<div style="flex:2 1 340px;display:grid;grid-template-columns:1fr 1fr;gap:10px">' + sec + '</div>' +
        '</div>' +
        '<div style="font-size:12px;color:var(--ink-3);margin-top:14px">次要矛盾 · 受主要矛盾规定和影响，随阶段相互转化</div>';
      ex.innerHTML = '<b>读法</b>　' + s.note;
    }
    render(0);
  }
})();
"""
os.makedirs(os.path.join(SITE, "assets"), exist_ok=True)
with open(os.path.join(SITE, "assets", "app.js"), "w", encoding="utf-8") as f:
    f.write(APP_JS)

# ---------- 生成 ----------
build_index()
build_works()
for w in WORKS:
    build_work(w)
build_concepts_index()
for c in CONCEPTS:
    build_concept(c)
build_timeline()
build_tool()
build_search()

n = 0
for root, _, files in os.walk(SITE):
    for fn in files:
        n += 1
print("生成完毕：%d 个文件 -> %s" % (n, SITE))
