# -*- coding: utf-8 -*-
"""知行录 · 毛泽东著作知识库 MVP — 静态站生成器。
读 data/works.json + data/concepts.json → 生成 site/ 下全站。
设计约束：数据全部内联（file:// 双击可用，无 fetch 依赖）；Ink 纸白主题；
溯源单元 = 卷/篇/段；段号为本库对求是网电子文本的编号，非纸质版页码。
"""
import json, os, re, collections, html as H, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
WORKS = json.load(open(os.path.join(ROOT, "data", "works.json"), encoding="utf-8"))
CONCEPTS = json.load(open(os.path.join(ROOT, "data", "concepts.json"), encoding="utf-8"))
PYRAMID = json.load(open(os.path.join(ROOT, "data", "pyramid.json"), encoding="utf-8"))
QUOTES = json.load(open(os.path.join(ROOT, "data", "quotes.json"), encoding="utf-8"))
_reading_path = os.path.join(ROOT, "data", "reading.json")
READING = json.load(open(_reading_path, encoding="utf-8")) if os.path.exists(_reading_path) else {}
CONCEPT_BY_ID = {c["id"]: c for c in CONCEPTS}
WORK_BY_TITLE = {w["title"]: w for w in WORKS}

VOL = "卷一"
SRC = "人民出版社《毛泽东选集》第一卷"
TOTAL_CHARS = sum(w["charCount"] for w in WORKS)
TOTAL_QUOTES = sum(len(c["quotes"]) for c in CONCEPTS)
NW = len(WORKS)
# 阅读时长估算：370 字/分钟。这个数不是拍的——金字塔路线四站
# （3780/10、6288/18、9267/25、22937/60）反推是 349~382 字/分，取中位 370。
WPM = 370
# 纠错联络：就写「1035775998 at qq.com」——纯文本，不做 mailto、不做复制按钮。
# 用户 2026-11-08 两次明确：既不要可点的超链接（等于把地址白送爬虫），
# 也不要 GitHub issue 那种绕路；读者能看见、能自己抄下来就行。
CONTACT = "1035775998 at qq.com"

def read_minutes(chars):
    """字数 → 分钟（向上取到整数分钟，最少 1 分钟）。"""
    return max(1, int(round(chars / WPM)))

def fmt_minutes(mins):
    """448 → 7 小时 28 分钟；25 → 25 分钟。"""
    if mins < 60:
        return "%d 分钟" % mins
    h, m = divmod(mins, 60)
    return "%d 小时" % h if m < 5 else "%d 小时 %d 分钟" % (h, m)

def read_time(chars):
    """字数 → 「约 25 分钟」里的时长部分。"""
    return fmt_minutes(read_minutes(chars))

TOTAL_MINS = read_minutes(TOTAL_CHARS)
# 一处定义，全站引用：篇数写死过一次「17 篇」，补到 18 篇时六处文案全错
DESC = ("知行录：《毛泽东选集》第一卷结构化知识库。%d 篇正式出版文本，%d 个概念节点，"
        "%d 条溯源引文，每一段都可回溯到卷/篇/段。" % (NW, len(CONCEPTS), TOTAL_QUOTES))

def cn_num(n):
    """18 → 十八。文案里写「第一卷十八篇」比「第一卷18篇」自然。"""
    d = "〇一二三四五六七八九"
    if n < 10:
        return d[n]
    if n < 20:
        return "十" + (d[n % 10] if n % 10 else "")
    if n < 100:
        return d[n // 10] + "十" + (d[n % 10] if n % 10 else "")
    return str(n)

def _fill_n(o):
    """数据文件里的 {n} 填成实际篇数。

    pyramid.json 的三处文案曾写死「十七篇」，补到 18 篇后页面仍说十七篇，
    而 build 不报错。改成占位符后，篇数只有 NW 一个来源。
    """
    if isinstance(o, dict):
        return {k: _fill_n(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_fill_n(v) for v in o]
    if isinstance(o, str):
        return o.replace("{n}", cn_num(NW))
    return o

PYRAMID = _fill_n(PYRAMID)

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

# ---------- 原版注释：编号解析 + 正文锚点 ----------
# 原文正文里的注释标记是〔N〕，注释正文也以〔N〕开头。编号一律以注释文本自带的为准。
NOTE_PAT = __import__("re").compile(r"〔(\d+)〕")


def split_note_series(raw_notes):
    """拆开一篇的注释，返回 (本篇 {编号: 正文}, 混进来的外篇注释列表)。

    编号取自注释文本自带的〔N〕，**不依赖数组下标**：注释条数与正文标记数并不相等
    （《中国革命战争的战略问题》53 条注释／52 处标记，《中国共产党在抗日时期的任务》
    29 段里 25 处标记），按下标配对会整体错位。

    **编号一旦回退，就说明换了一篇。**《中国共产党在抗日时期的任务》36 条注里，
    前 22 条是本篇的，第 23 条起又从〔1〕开始——那是同日另一篇
    《为争取千百万群众进入抗日民族统一战线而斗争》的注，本篇正文里没有对应标记。
    旧实现直接按编号覆盖，结果是〔1〕—〔14〕的弹层全部显示成那另一篇的解释，
    正文上标点的却是本篇的事：14 处错注，构建和死链检查都发现不了。
    """
    out, foreign, seen = {}, [], set()
    for n in raw_notes or []:
        t = (n or "").strip()
        if not t:
            continue
        m = NOTE_PAT.match(t)
        if m:
            num = int(m.group(1))
            if num in seen:
                foreign.append(t)
                continue
            seen.add(num)
            out[num] = t[m.end():].strip()
        else:
            # 无编号的题解类：接在最大编号之后，且不与已有号冲突
            num = (max(out) if out else 0) + 1
            while num in seen:
                num += 1
            seen.add(num)
            out[num] = t
    return out, foreign


def parse_notes(raw_notes):
    """本篇注释 {编号: 正文}；外篇注释不参与渲染（由 check_site 单独报数）。"""
    return split_note_series(raw_notes)[0]


# 全卷注释计数只算各篇自己的。首页原先把 works.json 的数组长度当条数（314），
# 其中 14 条是另一篇的注，页面实际渲染不到，数字与内容对不上。
NOTE_MAPS = {w["id"]: parse_notes(w.get("notes")) for w in WORKS}
FOREIGN_NOTES = {w["id"]: split_note_series(w.get("notes"))[1] for w in WORKS}
TOTAL_NOTES = sum(len(m) for m in NOTE_MAPS.values())


def add_note_refs(html, notemap):
    """把正文里的〔N〕换成可点的上标。

    只有该编号的注释确实存在时才加，否则原样保留——有标记无注释时
    生成一个点不开的死锚点，比不加更糟。
    """
    if not notemap:
        return html

    def rep(m):
        n = int(m.group(1))
        if n not in notemap:
            return m.group(0)
        return ('<sup class="nref" id="r%d"><a href="#n%d" data-note="n%d"'
                ' title="注释 %d">%d</a></sup>') % (n, n, n, n, n)

    return NOTE_PAT.sub(rep, html)


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
    ("pyramid.html", "金字塔", 0),
    ("works.html", "时期轴", 0),
    ("concepts.html", "概念图谱", 0),
    ("quotes.html", "语录", 0),
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
<meta name="description" content="%s">
<link rel="stylesheet" href="%sassets/style.css?v=91">
</head>
<body>
<header class="topbar"><div class="topbar-in">
<a class="brand" href="%sindex.html">知行录<small>MAO WORKS · VOL.1</small></a>
<nav class="nav" id="nav" aria-label="主导航">%s</nav>
<div class="searchbox"><input id="q" type="search" placeholder="检索全文…" autocomplete="off" data-root="%s"><span style="font-size:11px;color:var(--ink-3)">↵</span></div>
</div></header>
%s
<footer class="footer"><div class="wrap"><div class="bd">
<p><b>知行录</b>——文献检索与阅读工具。正文与引文依据%s，电子文本核自求是网（qstheory.cn），逐字收录、未作改写；概念释义、导语、导读问题与页内说明文字为本站整理，不属原版文字。</p>
<p>不作历史评价与政治表达。文中「段号」为本库段落编号，非纸质版页码；引文可点出处核对原文。</p>
<p>概念释义、导读问题、金字塔答句等整理文字若与原文不合，欢迎指正：%s。</p>
</div></div></footer>
<script src="%sassets/app.js"></script>
</body>
</html>""" % (title, DESC, p, p, "".join(nav), p, body, SRC, CONTACT, p)

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
<h1>把<span class="mk mk-paper">《毛选》第一卷</span><br>变成一本可检索的<br class="m-br"><span class="mk mk-teal">知识笔记</span></h1>
<p class="sub"><b>同一段文字，可以按结构、按年代读、按概念读、按语录读、也可以只读脚注</b>。<br>释义是本站整理，出处逐条挂回原段，点开即核对。</p>
<div class="stats">
<div class="stat"><div class="n">%d</div><div class="l">篇目（第一卷全量）</div></div>
<div class="stat"><div class="n">%s</div><div class="l">字正文</div></div>
<div class="stat"><div class="n">%s</div><div class="l">读完（估）</div></div>
<div class="stat"><div class="n">%d</div><div class="l">溯源引文</div></div>
<div class="stat"><div class="n">%d</div><div class="l">条注释</div></div>
</div>
</section>

<section class="section">
<h2>从这里进</h2>
<p class="desc">四种读法：按结构看金字塔，按年代看时期轴，按关键词看概念图谱，回原文核对看语录。</p>
<div class="entries e4">
<a class="entry" href="pyramid.html"><span class="no">01</span><span class="go" aria-hidden="true">→</span><div class="t">金字塔</div><div class="d">全卷其实只答一个问题，答案底下三根支柱。先看清骨架，再进原文，细节不会散</div></a>
<a class="entry" href="works.html"><span class="no">02</span><span class="go" aria-hidden="true">→</span><div class="t">时期轴</div><div class="d">十八篇按写作时间排开，分两个时期，每篇标了字数和读完要多长；页末看主要矛盾在各阶段的样子</div></a>
<a class="entry" href="concepts.html"><span class="no">03</span><span class="go" aria-hidden="true">→</span><div class="t">概念图谱</div><div class="d">实践 · 矛盾 · 调查研究 · 工农武装割据……每个关键词都有出处和演变</div></a>
<a class="entry" href="quotes.html"><span class="no">04</span><span class="go" aria-hidden="true">→</span><div class="t">经典语录</div><div class="d">%d 句原文，一字未改；读着对不上原文，就点回去核对上下文</div></a>
</div>
</section>

<section class="section">
<h2>今日一篇</h2>
<p class="desc">每次打开随机开一篇——像翻一本书那样翻完 %d 篇。</p>
<div class="today" id="today"></div>
</section>

<section class="section">
<h2>概念精选</h2>
<p class="desc">%d 个概念节点中的 6 个。释义为本站整理，出处逐条挂回原文段落。<a href="concepts.html" style="color:var(--teal)">看全部 →</a></p>
<div class="concept-grid">%s</div>
</section>
</div>""" % (NW, "{:,}".format(TOTAL_CHARS), "%dh" % int(math.ceil(TOTAL_MINS / 60.0)),
               TOTAL_QUOTES, TOTAL_NOTES, len(QUOTES["items"]), NW, len(CONCEPTS),
               "".join(cats))
    # 今日一篇数据内联
    brief = [{"t": w["title"], "d": date_disp(w), "c": w["charCount"], "r": read_time(w["charCount"]), "u": "works/%s.html" % w["id"]} for w in WORKS]
    body += '<script>window.__TODAY__=%s;</script>' % json.dumps(brief, ensure_ascii=False)
    write("index.html", page("首页", body, 0, "index"))

# ---------- 2. 时期轴（篇目清单 + 页末各阶段的主要矛盾） ----------
def dk_disp(dk):
    """1925-12-01 -> 1925.12.01；只到月份的写成 1925.12"""
    return (dk or "—").replace("-", ".")


def build_works():
    groups = []
    for period in ("第一次国内革命战争时期", "第二次国内革命战争时期"):
        ws = [w for w in WORKS if w["period"] == period]
        if not ws:
            continue
        rows = []
        for w in ws:
            rows.append("""<a class="work-row" href="works/%s.html"><span class="no">%03d</span><span class="tt">%s</span><span class="dt">%s</span><span class="ct">%s 字 · 约 %s</span></a>""" % (
                w["id"], w["order"], esc(w["title"]), esc(date_disp(w)), "{:,}".format(w["charCount"]), read_time(w["charCount"])))
        # 时期头只留时期名。原先后面挂「始—末 · N 篇 · N 字 · 读完约 N」一串，
        # 与每行右端的字数、时长重复，且灰字挤在标题旁读着累，去掉
        groups.append("""<div class="period-group"><div class="period-head"><span class="pn">%s</span></div>%s</div>""" % (
            esc(period), "".join(rows)))
    body = """<div class="wrap" style="padding-top:40px">
<h1 style="font-family:var(--display);font-size:30px;font-weight:700">时期轴</h1>
<p style="font-size:13.5px;color:var(--ink-3);margin:10px 0 28px;line-height:1.9">%d 篇按写作时间排，分两个时期——从 1925 年《中国社会各阶级的分析》到 1937 年《矛盾论》。点篇名进阅读页：正文段落全部编号，段号即锚点。</p>
%s
%s</div>""" % (NW, "".join(groups), tool_section())
    write("works.html", page("时期轴", body, 0, "works"))

# ---------- 3. 阅读页 ----------
def build_work(w):
    idx = w["order"] - 1
    prev_w = WORKS[idx - 1] if idx > 0 else None
    next_w = WORKS[idx + 1] if idx < len(WORKS) - 1 else None
    # 关联概念：quotes 命中本篇的概念
    rel = [c for c in CONCEPTS if any(q["work"] == w["title"] for q in c["quotes"])]
    rel_tags = "".join('<a href="../concepts/%s.html">%s</a>' % (c["id"], esc(c["name"])) for c in rel)
    # 原版注释：编号 → 正文。正文里的〔N〕点开就是它
    notemap = parse_notes(w.get("notes"))
    used_notes = set()
    for p in w["paragraphs"]:
        for m in NOTE_PAT.findall(p):
            used_notes.add(int(m))
    # 正文
    paras = []
    import re as _re
    for i, p in enumerate(w["paragraphs"], 1):
        is_sec = bool(_re.match(r"^[一二三四五六七八九十]+　|^第[一二三四五六七八九十]+章", p)) or (len(p) < 20 and p.endswith(("的问题", "失败", "策略")))
        cls = "para sec" if is_sec else "para"
        paras.append('<div class="%s" id="p%d">%s<a class="pno" href="#p%d">%d</a></div>' % (
            cls, i, add_note_refs(link_terms(p, 1), notemap), i, i))
    intro = ""
    if w.get("intro"):
        intro = '<div class="intro-box"><span class="lb">题解</span>%s</div>' % esc(w["intro"])
    # 注释列表：只有正文里真的出现过这个编号，才给回链——否则是死锚点
    notes = ""
    if notemap:
        items = "".join(
            '<div class="note-item" id="n%d">'
            '<span class="note-no">%d</span>'
            '<span class="note-tx">%s</span>%s</div>' % (
                k, k, esc(v),
                ' <a class="note-back" href="#r%d" title="回到正文">↩</a>' % k if k in used_notes else "")
            for k, v in sorted(notemap.items()))
        notes = ('<details class="notes-toggle"><summary>原版注释 %d 条</summary>'
                 '<div class="notes-body">%s</div></details>') % (len(notemap), items)

    # 篇内导读：读之前摆问题（不给位置），读完了回头核对（给段落）
    rd = READING.get(w["id"]) or {}
    guide_before = guide_after = ""
    if rd.get("before"):
        gi = "".join("<li>%s</li>" % esc(q) for q in rd["before"])
        guide_before = ('<div class="guide guide-before">'
                        '<div class="guide-hd"><span class="guide-lb">读之前</span>先摆着这几个问题'
                        '<span class="guide-src">题目由本站整理</span></div>'
                        '<ol class="guide-list">%s</ol>'
                        '<div class="guide-ft">答案在正文里，这里不给位置。</div></div>') % gi
    if rd.get("after"):
        # 段号会随数据清理位移（清网页分页残留时整体前移过），cue 不会。
        # 逐条核对锚词，失配当场报错退出——导读指向错误段落比没有导读更糟。
        for _x in rd["after"]:
            for _n, _cue in zip(_x.get("paras", []), _x.get("cue", [])):
                _p = w["paragraphs"][_n - 1] if 0 < _n <= len(w["paragraphs"]) else ""
                if _cue not in _p:
                    raise SystemExit("导读锚词失配 %s 第%d段：期望含「%s」，实际「%s」"
                                     % (w["id"], _n, _cue, _p[:40].replace("\n", " ")))
        gi = "".join(
            '<li>%s <span class="guide-at">%s</span></li>' % (
                esc(x["q"]),
                " · ".join('<a href="#p%d">第 %d 段</a>' % (n, n) for n in x.get("paras", [])))
            for x in rd["after"])
        guide_after = ('<div class="guide guide-after">'
                       '<div class="guide-hd"><span class="guide-lb">读完了</span>回头核对这几件事'
                       '<span class="guide-src">题目由本站整理</span></div>'
                       '<ol class="guide-list">%s</ol>'
                       '<div class="guide-ft">只指位置，不给答案。</div></div>') % gi
    prev_html = '<a href="%s.html">← 上一篇 · %s</a>' % (prev_w["id"], esc(prev_w["title"])) if prev_w else "<span></span>"
    next_html = '<a class="next" href="%s.html">下一篇 · %s →</a>' % (next_w["id"], esc(next_w["title"])) if next_w else "<span></span>"
    body = """<div class="narrow read-wide">
<div class="read-head">
<div class="crumb"><a href="../index.html">首页</a> / <a href="../works.html">时期轴</a> / %s · %s</div>
<h1>%s</h1>
<div class="read-meta"><span>%s</span><span>%d 段</span><span>%s 字</span><span>%s</span><span class="src">源：求是网</span></div>
%s
%s
</div>
<article class="article">%s</article>
%s
%s
<div style="margin-top:8px"><div style="font-size:12px;color:var(--ink-3);letter-spacing:0.2em">本篇涉及的概念</div><div class="related-concepts">%s</div></div>
<div class="read-foot">%s%s</div>
</div>""" % (esc(VOL), esc(w["period"] or ""), esc(w["title"]), esc(date_disp(w)),
             len(w["paragraphs"]), "{:,}".format(w["charCount"]), read_time(w["charCount"]), intro, guide_before,
             "".join(paras), guide_after, notes,
             rel_tags or "<span style='font-size:13px;color:var(--ink-3)'>暂无</span>", prev_html, next_html)
    write("works/%s.html" % w["id"], page(w["title"], body, 1, "works"))

# ---------- 4a. 附：注释里的另一本书 ----------
# 只读注释、不读正文：把 314 条注按「人 / 事件 / 名词」重排一遍，就是一张 1925—1937 的政治地图。
# 全部在构建时从 works.json 现算，不另存数据文件——同一份东西存两处，早晚会走偏。
CN_NUM = str.maketrans("〇一二三四五六七八九", "0123456789")
DOC_PAT = re.compile(r"^([\u4e00-\u9fa5·]{2,6})[（(]([〇一二三四五六七八九]{4})[—―－\-─]+"
                     r"([〇一二三四五六七八九]{4})[）)](.*)$", re.S)
YEAR_PAT = re.compile(r"^([〇一二三四五六七八九]{4})年")
TERM_PAT = re.compile(r"^(这里|这|那时)?(是)?指")
ANY_YEAR = re.compile(r"([〇一二三四五六七八九]{4})")


def cn2num(s):
    s = s.translate(CN_NUM)
    return int(s) if s.isdigit() else None


def note_entries():
    """把原版注释拆成 (篇, 编号, 正文, 所在段号) 四元组。

    段号是注释标记〔N〕在正文里出现的那一段，用于「点回原文」——
    没有段号说明正文里没有对应标记，条目照样保留，只是不给链接。
    """
    out = []
    for w in WORKS:
        for num, text in parse_notes(w.get("notes")).items():
            para = None
            for i, p in enumerate(w["paragraphs"], 1):
                if "〔%d〕" % num in p:
                    para = i
                    break
            out.append((w, num, text, para))
    return out


def term_head(w, num, para):
    """取正文上标前面那几个字当词头，清理「如自耕农」「们从…的五卅运动」这类上下文。"""
    if not para:
        return ""
    ppr = w["paragraphs"][para - 1]
    i = ppr.find("〔%d〕" % num)
    if i <= 0:
        return ""
    m = re.search(r"([\u4e00-\u9fa5A-Za-z0-9“”\"]{2,12})$", ppr[max(0, i - 16):i])
    if not m:
        return ""
    h = m.group(1)
    if "的" in h:
        h = h.rsplit("的", 1)[1] or h
    h = re.sub(r"^(例如|比如|所谓|这些|那些|这个|一个|如|即|是|和|与|及|其)", "", h)
    if re.match(r"^[〇一二三四五六七八九十]+年$", h) or h.startswith(("那", "这")):
        return ""
    return h if 2 <= len(h) <= 7 else ""


def note_book():
    """附录节：四小节 —— 谁是谁 / 词与物 / 哪一年被解释得最多 / 注出来的年表。

    词与物紧跟谁是谁：两节都是「按条查」的索引（查人、查词），年份分布与年表
    是「按年读」的连续叙事，分开放，读者不必在两种读法之间来回跳。

    刻意不做「按人名聚合成百科」：314 条注里带生卒年的人物小传只有十几条，
    人名几乎不重复，聚不出词条空间，硬做只会得到一堆只有一条的空壳。
    """
    N = note_entries()

    people = {}
    for w, num, text, para in N:
        m = DOC_PAT.match(text)
        if m:
            people.setdefault(m.group(1), {
                "born": cn2num(m.group(2)), "died": cn2num(m.group(3)),
                "tail": m.group(4).lstrip("，,"), "items": []})["items"].append((w, para))

    events = []
    for w, num, text, para in N:
        m = YEAR_PAT.match(text)
        if m and cn2num(m.group(1)):
            events.append({"year": cn2num(m.group(1)), "brief": text.split("。")[0],
                           "w": w, "para": para, "dups": 0})

    terms = [(term_head(w, num, para), (w, para, text.split("。")[0] + "。"))
             for w, num, text, para in N if TERM_PAT.match(text)]
    terms = [(h, t) for h, t in terms if h]

    yearh = collections.Counter()
    for _, _, text, _ in N:
        for y in ANY_YEAR.findall(text):
            v = cn2num(y)
            if v and 1900 <= v <= 1949:
                yearh[v] += 1

    # --- 谁是谁 ---
    ppl = []
    for name, p in sorted(people.items(), key=lambda kv: (-len(kv[1]["items"]), kv[1]["born"])):
        multi = '<span class="nb-pp-cnt">%d 处</span>' % len(p["items"]) if len(p["items"]) > 1 else ""
        srcs = "、".join("《%s》<a href=\"works/%s.html#p%d\">p%d</a>" % (esc(w["title"]), w["id"], para, para)
                        for w, para in p["items"] if para) or "正文中未找到对应标记"
        ppl.append("""<div class="nb-pp">
<div class="nb-pp-hd"><span class="nb-pp-nm">%s</span>%s<span class="nb-pp-yr">%d—%d</span></div>
<div class="nb-pp-tx" onclick="this.classList.toggle('open')">%s</div>
<div class="nb-pp-ft">%s</div></div>""" % (esc(name), multi, p["born"], p["died"], esc(p["tail"]), srcs))

    # --- 年份分布（内联 SVG，颜色走 CSS 变量，不烤死色值） ---
    bars = [(y, c) for y, c in sorted(yearh.items()) if 1921 <= y <= 1939 and c >= 2]
    mx = max(c for _, c in bars) if bars else 1
    W_, H_ = 640, len(bars) * 21 + 4
    svg = ['<svg viewBox="0 0 640 %d" style="width:100%%;max-width:640px;height:auto" role="img" '
           'aria-label="注释里各年份被提到的次数">' % H_]
    for i, (y, c) in enumerate(bars):
        yy = i * 21
        svg.append('<text x="42" y="%d" font-size="11" fill="var(--ink-3)" text-anchor="end">%d</text>' % (yy + 11, y))
        # 一种颜色到底：曾按次数深浅分两档，但门槛 8 是人拍的，读者只会问「为什么这条浅」
        svg.append('<rect x="52" y="%d" width="%.1f" height="10" fill="var(--teal)" opacity="0.8"/>'
                   % (yy + 2, c / mx * 490))
        svg.append('<text x="%.1f" y="%d" font-size="10.5" fill="var(--ink-3)">%d</text>'
                   % (56 + c / mx * 490, yy + 11, c))
    svg.append("</svg>")
    top2 = collections.Counter(yearh).most_common(2)
    y_txt = "、".join("%d 年 %d 次" % (y, c) for y, c in top2)

    # --- 注出来的年表 ---
    seen, by_year = {}, collections.OrderedDict()
    for e in sorted(events, key=lambda x: x["year"]):
        key = re.sub(r"\s+", "", e["brief"])[:26]
        if key in seen:
            seen[key]["dups"] += 1
            continue
        seen[key] = e
        # 与年份分布图同一区间：这一节讲的是 1925—1937 的那个人事现场，
        # 1951 年那条是《选集》出版说明一类的后记，混进来会打断时间线
        if 1921 <= e["year"] <= 1949:
            by_year.setdefault(e["year"], []).append(e)

    ev = []
    for y in sorted(by_year):
        rows = by_year[y]
        inner = "".join('<div class="nb-ev-b">%s%s <a href="works/%s.html#p%d">p%d ↗</a></div>'
                        % (esc(r["brief"]), ("（另 %d 处同注）" % r["dups"]) if r["dups"] else "",
                           r["w"]["id"], r["para"] or 0, r["para"] or 0) for r in rows[:4])
        if len(rows) > 4:
            inner += ('<div class="nb-ev-b" style="border-left:0;color:var(--ink-3)">'
                      "另有 %d 条同年的注释未列出</div>") % (len(rows) - 4)
        ev.append("<details%s><summary><b>%d</b>%d 条注释解释这一年</summary>%s</details>"
                  % (" open" if y == (top2[0][0] if top2 else 0) else "", y, len(rows), inner))

    # --- 词与物（同名词头只留一条） ---
    uniq, used = [], set()
    for h, t in terms:
        if h in used:
            continue
        used.add(h)
        uniq.append((h, t))
    tm = "".join('<div><b class="nb-tm-h">%s</b>%s<span>《%s》<a href="works/%s.html#p%d">p%d ↗</a></span></div>'
                 % (esc(h), esc(t[2]), esc(t[0]["title"]), t[0]["id"], t[1] or 0, t[1] or 0)
                 for h, t in uniq[:24])

    foreign_n = sum(len(v) for v in FOREIGN_NOTES.values())
    foreign_txt = ""
    if foreign_n:
        foreign_txt = ("另有 %d 条注释的编号从〔1〕重新开始，属于紧接其后的一篇"
                       "（《为争取千百万群众进入抗日民族统一战线而斗争》）——本库尚未收录那一篇正文，"
                       "故不计入上面的总数，也不出现在下面各节。" % foreign_n)

    body = """<div class="nb" id="notes">
<div class="nb-kind">附录</div>
<h2>注释里的另一本书</h2>
<p class="nb-lede">上半页按概念读，这一节按人读。正文十六万字讲道理，脚注里三百多条讲人事——把注释单独抽出来按年代排，就是一张 1925—1937 年的中国政治地图：谁掌权、谁叛变、哪个组织成立、哪一年打什么仗。这一节不读正文，只读注。</p>
<div class="stats">
<div class="stat"><div class="n">%d</div><div class="l">条原版注释</div></div>
<div class="stat"><div class="n">%d</div><div class="l">条人物小传</div></div>
<div class="stat"><div class="n">%d</div><div class="l">条名词释义</div></div>
<div class="stat"><div class="n">%d</div><div class="l">条事件编年</div></div>
</div>
<p class="nb-note">数字由构建脚本从 works.json 现算，未作人工挑选；每条都能点回正文那一段。%s</p>

<section class="nb-sec"><h3>一 · 谁是谁</h3>
<p class="nb-hint">注释里带生卒年的条目，本身就是一篇小传：原名、籍贯、做过什么、怎么死的。点正文可展开全文，点段号回到他被提到的那一句。</p>
<div class="nb-ppl">%s</div></section>

<section class="nb-sec"><h3>二 · 词与物</h3>
<p class="nb-hint">正文里带〔N〕的地方，多数就是被解释的那个词。把词头抽成索引：自耕农、挨户团、五卅运动——今天听着陌生的，注释里一句讲清。</p>
<div class="nb-tm">%s</div></section>

<section class="nb-sec"><h3>三 · 注出来的年表</h3>
<p class="nb-hint">以年份开头的注释，本身就是记事条目。按年份归拢，不用读正文，也能排出一条时间线。</p>
<div class="nb-ev">%s</div></section>

<section class="nb-sec"><h3>四 · 哪一年被解释得最多</h3>
<p class="nb-hint">统计 %d 条注释里出现的年份（1921 年以前与 1939 年以后的零散条目未画）。出现最多的是 %s。同一个年份被反复解释，说明那一年的事，几乎每篇文章都要交代一次。</p>
<div style="max-width:640px">%s</div></section>
</div>""" % (len(N), sum(len(p["items"]) for p in people.values()), len(terms), len(events), foreign_txt,
             "".join(ppl), tm, "".join(ev), len(N), y_txt, "".join(svg))
    return body


# ---------- 4. 概念索引 ----------
def evolution_rows():
    """跨概念的演变链：只列有两个以上节点的概念，按数据里的时间顺序串起来。"""
    rows = []
    for c in CONCEPTS:
        if len(c["evolution"]) >= 2:
            # 卷外篇的目标题名自带书名号（《农村调查》的序言和跋），别再套一层
            chain = " → ".join("%s%s" % (e["dateKey"],
                                         e["work"] if e["work"].startswith("《") else "《%s》" % e["work"])
                               for e in c["evolution"])
            rows.append('<div class="evo-item"><span class="dt">%d 节点</span><span class="wk"><a href="concepts/%s.html">%s</a></span><span class="nt">%s</span></div>' % (
                len(c["evolution"]), c["id"], esc(c["name"]), esc(chain)))
    return "".join(rows)


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
<p style="font-size:13.5px;color:var(--ink-3);margin:10px 0 28px">%d 个概念节点，按 %d 个领域归类。点进去是一个概念的单独一页：一句话定义，几条核心要义，逐字原话（精确到段，可点回原文核对），演变时间线，最后是几个常见疑问的解答。<a href="#notes" style="color:var(--teal);text-decoration:none;margin-left:6px">↓ 页末另有「注释里的另一本书」</a></p>
%s<div class="section sec-end" style="border-top:1px solid var(--line);margin-top:10px">
<h2>概念演变链</h2>
<p class="desc">同一个概念在不同篇里的提法变化，按写作时间串成一条线。点概念名进那一页看逐条说明。</p>
<div class="evo">%s</div>
</div>%s</div>""" % (len(CONCEPTS), len(cats), "".join(blocks), evolution_rows(), note_book())
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
<div class="oneliner">%s<span class="guide-src">本站整理</span></div>
</div>
<div class="section"><h2>核心要义<span class="guide-src">本站概括</span></h2><ul class="essence">%s</ul></div>
<div class="section"><h2>原话精选</h2><p class="desc">逐字引文，点击出处跳到原文段落核对。</p>%s</div>
<div class="section"><h2>思想演变</h2><div class="evo">%s</div></div>
<div class="section"><h2>关联篇目</h2><div class="related-concepts">%s</div></div>
<div class="section"><h2>常见疑问<span class="guide-src">本站整理</span></h2><div class="qa">%s</div></div>
</div>""" % (esc(c["category"]), esc(c["name"]), esc(c["oneliner"]), essence, "".join(quotes), "".join(evo), "".join(related), qa)
    write("concepts/%s.html" % c["id"], page(c["name"], body, 1, "concepts"))

# ---------- 6. 旧地址跳转（timeline / tool-maodun 都收进时期轴页） ----------
def build_redirects():
    """早先 timeline.html / tool-maodun.html 是两个独立地址，都被外部链接过，
    现在内容合进 works.html，这两个地址只留跳转，别让老链接 404。"""
    pages = [
        ("timeline.html", "时期轴", "旧地址：时期轴已移到", "时期轴", "works.html", ""),
        ("tool-maodun.html", "各阶段的主要矛盾", "这一节已并入", "时期轴", "works.html", "#maodun"),
    ]
    for fn, title, label, dest, url, anchor in pages:
        write(fn, """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%s · 知行录</title>
<link rel="canonical" href="%s%s">
<meta http-equiv="refresh" content="0; url=%s%s">
</head>
<body>
<p style="font-family:system-ui,-apple-system,'Microsoft YaHei',sans-serif;padding:40px 24px;line-height:1.8">%s<a href="%s%s" style="color:#0F766E">%s</a>，正在跳转。</p>
</body>
</html>
""" % (title, url, anchor, url, anchor, label, url, anchor, dest))

# ---------- 7. 各阶段的主要矛盾（时期轴页末，旧地址留跳转） ----------
# 这一块的规矩（2026-11-09 用户定，别改回去）：只写原文说过的话。
# 原文没下的判断——哪一年算转折、哪一次事变之后主要矛盾变了——不进卡片，
# 只进块末的注；注里要写清「现在通行的说法是什么、出处是哪本书」。
# 宁可少写一格，也不替原文下判断。卡片名也照原文的说法起，不套党史分期。
def para_of(title, n):
    """某篇第 n 段原文（1 起算，与阅读页 #pn 锚点同一套编号）。"""
    ps = [p if isinstance(p, str) else p.get("text", "") for p in WORK_BY_TITLE[title]["paragraphs"]]
    return ps[n - 1]


def tool_section():
    """同一批矛盾在不同阶段，主要的那一对会变。每一格都落到原文：下面几段能按格点亮。"""
    quotes = []
    for q in TOOL_QUOTES:
        title = q.get("work", "矛盾论")
        wid = WORK_BY_TITLE[title]["id"]
        quotes.append("""<a class="quote yj-q" data-for="%s" href="works/%s.html#p%d"><div class="qt">%s</div><div class="qm"><span>《%s》第 %d 段 ↗</span><span>%s</span></div></a>""" % (
            ",".join(q["for"]), wid, q["para"], quote_snippet(para_of(title, q["para"]), q["kw"], 52),
            esc(title), q["para"], esc(q["note"])))
    html = """<div class="section" id="maodun" style="border-top:1px solid var(--line);margin-top:44px;padding-top:30px">
<h2>各阶段的主要矛盾</h2>
<p class="desc">上面按年份排，这里按原文排：每个阶段里互相拉扯的两方不一样，主要的那一对也会变。</p>
<p style="font-size:13.5px;color:var(--ink-2);margin:12px 0 4px;line-height:1.9">「矛盾」在这里的意思是：一个事物内部互相拉扯、又互相依赖的两方——它们你进我退，推动整个事物变化。一个社会里同时存在好几对这样的矛盾，<b>其中必有一种是主要的</b>：捉住了它，其余问题就有了头绪（《矛盾论》第 58、65 段）。</p>
<p style="font-size:13.5px;color:var(--ink-2);margin:8px 0 4px;line-height:1.9">下面五格全部按《矛盾论》第四节的原话组织：一格是贯穿全程的<b>根本矛盾</b>（第 45 段），三格是原文给半殖民地中国列出的三种情形（第 61—63 段），最后一格是原文拿来做对照的资本主义社会（第 59 段）。<b>原文没写的年份和事变，本站一律不补</b>——那些放在块末的注里，注里写明通行说法与出处。</p>
<div class="tool-legend">
<span class="k"><span class="sw" style="background:#0F766E"></span><b>主要矛盾</b>　它规定这一阶段整个过程的性质，谁说话算数看它</span>
<span class="k"><span class="sw" style="background:#C8C5BB"></span><b>次要矛盾</b>　被主要矛盾规定，暂时让位（让位不等于消失）</span>
<span class="k"><span class="sw" style="background:#fff;border:1px solid #0F766E"></span><b>矛盾主要方面</b>　一对矛盾内部占上风的那一方</span>
</div>
<p class="tool-hint">卡片名用的是原文的说法，不是党史分期。切换看每一格：原文点了哪些例子，哪些矛盾被让到次要。</p>
<div class="tool-stage">
<div class="tool-tabs" id="tabs"></div>
<div id="scene"></div>
</div>
<div class="tool-explain" id="explain"></div>
<div class="tool-quote">《矛盾论》第四节：「任何过程如果有多数矛盾存在的话，其中必定有一种是主要的，起着领导的、决定的作用，其他则处于次要和服从的地位。」<a href="works/@MD@.html#p65" style="color:var(--teal);text-decoration:none">第 65 段 ↗</a>　五格都有原文，段号可点。</div>
<div class="tool-fn">
<p id="fn1"><b>注 1　这一块为什么不按「大革命 / 土地革命 / 抗战」分期。</b>因为那是党史著作的分期，不是《矛盾论》原文的分法。本卷原文自己列过这二十多年的大事变——「辛亥革命失败和北洋军阀统治，第一次民族统一战线的建立和一九二四年至一九二七年的革命，统一战线破裂和资产阶级转入反革命，新的军阀战争，土地革命战争，第二次民族统一战线建立和抗日战争等等大事变」（第 45 段）；《毛泽东选集》第一卷也据此把篇目分成「第一次国内革命战争时期」「第二次国内革命战争时期」（见「时期轴」）。通行党史著作分得更细：大革命（国民革命）1924—1927、土地革命战争 1927—1937、全民族抗日战争 1937—1945，见中共中央党史研究室《中国共产党历史》第一卷（中共党史出版社，2011）、《中国共产党简史》（人民出版社，2021）。本站不把两套分期混用：卡片照原文，年份差异只在这里交代。</p>
<p id="fn2"><b>注 2　1931、1935、1937 是三个不同的年份，原文只说了其中一个。</b>第 61 段把「目前的中日战争」（1937 年全面抗战）当作民族战争成主要矛盾的例子，全段没有提 1931 年九一八，也没有提 1935 年。通行党史的表述是：九一八事变（1931）后中日民族矛盾急剧上升，1935 年华北事变后中日民族矛盾成为主要矛盾（见《中国共产党历史》第一卷、《中国共产党简史》）。<b>后一句在本卷原文里没有直接对应</b>；本卷能引的只有两处较近的话——1935 年 12 月《论反对日本帝国主义的策略》「在日本帝国主义打进中国本部来了这一个基本的变化上面，变化了中国各阶级之间的相互关系」；1937 年 5 月《中国共产党在抗日时期的任务》第 2 段「由于中日矛盾成为主要的矛盾、国内矛盾降到次要和服从的地位」。所以本站既不写「1931 年民族矛盾成为主要矛盾」，也不把 1935 年当成原文的判断。</p>
<p id="fn3"><b>注 3　「帝国主义和封建阶级的同盟」是原文，教科书写作「北洋军阀」。</b>第 62 段的原话是「去反对帝国主义和封建阶级的同盟」；通行教科书讲大革命时期，写作「中国人民同帝国主义支持的北洋军阀的矛盾」。差别只在称呼——北洋军阀是封建阶级当时的具体代表。本站从原文，因为原文正是用「同盟」把「一九二四年至一九二七年的革命战争」和「一九二七年以后的十年土地革命战争」放进同一格：变的只是代表，同盟没变。</p>
</div>
<div class="yj" id="yuju-wrap">
<h2>原文依据</h2>
<p class="desc" id="yuju-cap">切换上面的格子，下面标亮的几段就是那一格的原文；点段号回原文核对。</p>
<div id="yuju">%s</div>
</div>
</div>""" % "".join(quotes)
    html = html.replace("@MD@", WORK_BY_TITLE["矛盾论"]["id"])
    return html + '<script>window.__TOOL__=%s;</script>' % json.dumps(TOOL_SCENES, ensure_ascii=False)


def build_tool():
    """旧地址 tool-maodun.html：已并入时期轴页，跳转在 build_redirects 里生成。"""
    pass


# 五格＝《矛盾论》第四节原文的五处：第 45 段（根本矛盾，贯穿全程）、第 61 段（侵略战争）、
# 第 62 段（温和形式压迫＋统治阶级投降结盟）、第 63 段（阵线公开分成两极）、第 59 段（资本主义原例）。
# 每一格的 main / secondary / egs 都能在该段原文里找到对应词句；找不到的就不写，
# 宁可让「次要矛盾」空着，用 secnote 说明原文没列——不拿通行的史学叙述来填空。
TOOL_SCENES = [
    {"key": "a", "name": "根本矛盾 · 贯穿全程", "group": "中国 · 根本矛盾与三种情形",
     "phase": "《矛盾论》第 45 段",
     "tag": "根本矛盾 · 性质不变的那一层",
     "main": "反帝反封建的民主革命　对　半殖民地半封建的旧中国",
     "sides": ["反帝反封建的民主革命", "半殖民地半封建的旧中国"], "aspectMain": "",
     "secondary": [],
     "secnote": "原文：「整个过程中根本矛盾的性质，过程之反帝反封建的民主革命的性质（其反面是半殖民地半封建的性质），并没有变化」——它不随阶段换人，换的是下面三种情形。",
     "change": "二十多年里经过的大事变，原文自己数了一遍：辛亥革命失败和北洋军阀统治、第一次民族统一战线的建立和一九二四年至一九二七年的革命、统一战线破裂和资产阶级转入反革命、新的军阀战争、土地革命战争、第二次民族统一战线建立和抗日战争。阶段一直在换，这一层的性质没换。",
     "egs": [],
     "note": "这一格是底线：下面三格讲的「主要矛盾」都是阶段性的；反帝反封建这个性质从头到尾没变（第 45 段）。原文还点了这些阶段里矛盾怎么变：有的激化了（土地革命战争、日本侵入东北四省），有的部分或暂时解决了（北洋军阀被消灭、没收地主土地），有的又重新发生（新军阀之间的斗争）。",
     "fn": "1"},
    {"key": "b", "name": "情形一 · 侵略战争", "group": "中国 · 根本矛盾与三种情形",
     "phase": "《矛盾论》第 61 段",
     "main": "帝国主义　对　中国",
     "sides": ["帝国主义", "中国（内部各阶级暂时团结）"], "aspectMain": "",
     "secondary": ["这种国家内部各阶级的一切矛盾", "包括封建制度和人民大众之间那个主要矛盾"],
     "secnote": "原文：这些矛盾「便都暂时地降到次要和服从的地位」——不是消失了，是让位。",
     "change": "原文的写法：当着帝国主义举行侵略战争的时候，这种国家的内部各阶级，除开一些叛国分子以外，能够暂时地团结起来举行民族战争去反对帝国主义。",
     "egs": ["鸦片战争（一八四○）", "中日战争（一八九四）", "义和团战争（一九○○）", "目前的中日战争（一九三七）"],
     "note": "第 61 段。本卷另有一处说得更直接：《中国共产党在抗日时期的任务》第 2 段「由于中日矛盾成为主要的矛盾、国内矛盾降到次要和服从的地位」；第 9 段还补了一句，国内阶级间的矛盾「本身依然存在着，并没有减少或消灭」。",
     "fn": "2"},
    {"key": "c", "name": "情形二 · 温和压迫", "group": "中国 · 根本矛盾与三种情形",
     "phase": "《矛盾论》第 62 段",
     "main": "人民大众　对　帝国主义和封建阶级的同盟",
     "sides": ["帝国主义和封建阶级的同盟", "人民大众"], "aspectMain": "",
     "secondary": [],
     "secnote": "原文没有逐条列这种情形下的次要矛盾，只说帝国主义「往往采取间接的方式去援助半殖民地国家的反动派压迫人民，而不采取直接行动，显出了内部矛盾的特别尖锐性」。",
     "change": "帝国主义不用战争，改用政治、经济、文化等比较温和的形式压迫；半殖民地国家的统治阶级向它投降，二者结成同盟，共同压迫人民大众。这时候，人民大众往往采取国内战争的形式，去反对这个同盟。",
     "egs": ["辛亥革命战争", "一九二四年至一九二七年的革命战争", "一九二七年以后的十年土地革命战争", "军阀战争（原文归入这一类）"],
     "note": "第 62 段。注意原文点的是「十年土地革命战争」，从一九二七年算起，中间不再切刀——本卷的《中国社会各阶级的分析》《湖南农民运动考察报告》落在前一段，《中国的红色政权为什么能够存在？》以后各篇落在后一段。",
     "fn": "3"},
    {"key": "d", "name": "情形三 · 阵线分裂", "group": "中国 · 根本矛盾与三种情形",
     "phase": "《矛盾论》第 63 段",
     "main": "外国帝国主义和国内反动派　对　人民大众",
     "sides": ["外国帝国主义和国内反动派", "人民大众"], "aspectMain": "",
     "secondary": [],
     "secnote": "原文在这种情形下只说「其他矛盾」受它规定或影响，没有逐条列举。",
     "change": "国内革命战争发展到从根本上威胁帝国主义及其走狗国内反动派的存在时，帝国主义就换手法：或者分化革命阵线的内部，或者直接出兵援助国内反动派。两边于是完全公开地站成两极。",
     "egs": ["十月革命后各资本主义国家援助俄国反动派（武装干涉）", "一九二七年蒋介石的叛变（分化革命阵线）"],
     "note": "第 63 段。原文举的两个例子都在这里：一个讲武装干涉，一个讲分化阵线。",
     "fn": ""},
    {"key": "e", "name": "对照 · 资本主义社会", "group": "《矛盾论》原例（对照，不是中国的阶段）",
     "phase": "《矛盾论》第 59 段",
     "tag": "主要矛盾 · 原文拿来对照的一格",
     "main": "无产阶级　对　资产阶级",
     "sides": ["资产阶级", "无产阶级"], "aspectMain": "资产阶级",
     "secondary": ["残存的封建阶级和资产阶级", "农民小资产者和资产阶级", "无产阶级和农民小资产者", "自由资产阶级和垄断资产阶级", "资产阶级的民主主义和资产阶级的法西斯主义", "资本主义国家相互间", "帝国主义和殖民地"],
     "secnote": "这七对都是原文第 59 段自己列的，说它们「都为这个主要的矛盾力量所规定、所影响」。",
     "change": "换一套参照系。原文的顺序是：先指认无产阶级和资产阶级是主要矛盾，再说明社会性质由矛盾的主要方面规定——资产阶级占主要方面，所以是资本主义社会（第 66、69 段）。",
     "egs": [],
     "note": "原文只讲到这里：用资本主义社会作对照，说明主要矛盾规定其他矛盾；没有把中国的情形套进这个框子。",
     "fn": ""},
]

# 原文依据：篇名 + 段号 + 摘句关键词 + 对应哪一格（a–e 见 TOOL_SCENES 的 key）。
# 段号一律 1 起算，与阅读页 #pn 锚点同源，点进去就是这一句所在的那一段。
TOOL_QUOTES = [
    {"work": "矛盾论", "para": 45, "kw": "根本矛盾的性质", "for": ["a"], "note": "根本矛盾：二十多年不变"},
    {"work": "矛盾论", "para": 58, "kw": "必有一种是主要的矛盾", "for": ["a", "b", "c", "d", "e"], "note": "方法：多数矛盾里先找出主要的"},
    {"work": "矛盾论", "para": 64, "kw": "只有一种主要的矛盾", "for": ["a", "b", "c", "d", "e"], "note": "各阶段只有一种主要矛盾"},
    {"work": "矛盾论", "para": 61, "kw": "目前的中日战争", "for": ["b"], "note": "侵略战争：民族矛盾成主要"},
    {"work": "矛盾论", "para": 62, "kw": "帝国主义和封建阶级的同盟", "for": ["c"], "note": "温和压迫：反对帝国主义与封建阶级的同盟"},
    {"work": "矛盾论", "para": 63, "kw": "分化革命阵线", "for": ["d"], "note": "阵线公开分成两极"},
    {"work": "矛盾论", "para": 59, "kw": "无产阶级和资产阶级这两个矛盾着的力量是主要的矛盾", "for": ["e"], "note": "资本主义社会的主要矛盾与原例"},
    {"work": "矛盾论", "para": 66, "kw": "矛盾的主要方面", "for": ["e"], "note": "主要方面决定性质"},
    {"work": "矛盾论", "para": 69, "kw": "在资本主义社会中", "for": ["e"], "note": "性质随主要方面变化"},
    {"work": "中国共产党在抗日时期的任务", "para": 2, "kw": "中日矛盾成为主要的矛盾", "for": ["b"], "note": "1937：中日矛盾成主要"},
    {"work": "中国共产党在抗日时期的任务", "para": 9, "kw": "本身依然存在着", "for": ["b"], "note": "次要矛盾不等于消失"},
]

# ---------- 7.5 金字塔（先问，再答，三根柱子） ----------
def concept_chip(cid):
    c = CONCEPT_BY_ID[cid]
    return '<a class="chip" href="concepts/%s.html">%s</a>' % (cid, esc(c["name"]))

def branch_card(b, with_chips):
    chips = ('<div class="pyr-br-concepts"><div class="pyr-br-concepts-lb">%d 个概念</div><div class="pyr-chips">%s</div></div>'
             % (len(b["conceptIds"]), "".join(concept_chip(cid) for cid in b["conceptIds"]))) if with_chips else ""
    return """<div class="pyr-br" id="b-%s">
<div class="pyr-br-q">%s</div>
<div class="pyr-br-hd"><span class="pyr-key">%s</span><span class="pyr-br-nm">%s</span></div>
<div class="pyr-br-claim">%s</div>
<div class="pyr-br-logic">%s</div>
%s</div>""" % (b["slug"], esc(b["question"]), esc(b["key"]), esc(b["name"]),
                 esc(b["claim"]), esc(b["logic"]), chips)

def layer_block(level, q, inner, note, raw_note=False):
    q_html = '<div class="td-q">%s</div>' % esc(q) if q else ""
    n_html = '<div class="td-note">%s</div>' % (note if raw_note else esc(note)) if note else ""
    return """<div class="td-layer">
<div class="td-lv">%s</div>
%s
<div class="td-a">%s</div>
%s
</div>""" % (esc(level), q_html, inner, n_html)

def route_section():
    """页末：四篇读通全书。形态沿用最初那版独立页——编号、日期、问句、引文、
    读完带走，站与站之间一句过渡。数据在 pyramid.json 的 route 段；
    引文逐字，段号 1 基，cue 逐条核对。"""
    R = PYRAMID.get("route")
    if not R:
        return ""
    wmap = {w["id"]: w for w in WORKS}
    out = []
    for s in R["stations"]:
        w = wmap.get(s["wid"])
        if not w:
            raise SystemExit("导读站 %s 指向不存在的篇目 %s" % (s["no"], s["wid"]))
        paras = w["paragraphs"]
        qs = []
        for k, q in enumerate(s["quote"]):
            n = q["para"]
            if not (0 < n <= len(paras)):
                raise SystemExit("导读 %s 段号越界 p%d" % (s["no"], n))
            if q["text"] not in paras[n - 1]:
                raise SystemExit("导读 %s 引文不在第 %d 段原文里（段号可能位移）" % (s["no"], n))
            if q["cue"] not in paras[n - 1]:
                raise SystemExit("导读 %s 锚词失配 p%d（期望含「%s」）" % (s["no"], n, q["cue"]))
            # 分两段引就要交代中间省了多少：本站的底线是「省略也算改动」，
            # 所以不写含糊的省略号，直接告诉读者省了几个字。
            gap = ""
            if k:
                pv, p = s["quote"][k - 1], paras[n - 1]
                if pv["para"] == n:
                    a = p.find(pv["text"]) + len(pv["text"])
                    b = p.find(q["text"])
                    if b > a >= len(pv["text"]):
                        gap = '<p class="gap">（此处省略原文 %d 字）</p>' % (b - a)
                else:
                    gap = '<p class="gap">（原文另起一段，中间略去若干句）</p>'
            qs.append(gap + "<p>%s</p>" % esc(q["text"]))
        pn = s["quote"][0]["para"]
        out.append("""<div class="st" id="r-%s">
<div class="st-no">%s</div>
<div>
<div class="st-meta">%s · %s 字 · %s</div>
<h3>%s</h3>
<p class="st-q"><span class="qlab">问</span>%s</p>
<blockquote class="st-blk">%s<cite>《%s》 <a href="works/%s.html#p%d">第 %d 段 ↗</a> · <a href="works/%s.html">读全文 ↗</a></cite></blockquote>
<div class="st-take"><b>读完带走</b>%s</div>
</div></div>""" % (s["no"], s["no"], esc(s["date"]), "{:,}".format(s["chars"]), esc(s["mins"]),
                 esc(s["title"]), esc(s["q"]), "".join(qs), esc(s["title"]),
                 s["wid"], pn, pn, s["wid"], esc(s["take"])))
        if s.get("bridge"):
            out.append('<div class="st-link"><div></div><p>%s</p></div>' % esc(s["bridge"]))
    chars = sum(s["chars"] for s in R["stations"])
    mins = sum(int("".join(ch for ch in s["mins"] if ch.isdigit())) for s in R["stations"])
    return """<section class="rt-sec" id="route">
<div class="rt-kind">%s</div>
<h2>%s</h2>
<p class="rt-intro">%s</p>
<p class="rt-stat">%d 篇 · %s 字 · 占全卷 %.0f%% · 读完约 %d 小时</p>
<div class="rt">%s</div>
<p class="rt-foot">「问」与「读完带走」是本库的编辑概括，不是原文。引文一律逐字截取，标了段号，可点回原文核对——顶上那句总括里的「以弱胜强、农村包围城市」，是后来人对这段历史的概括，本卷原文里没有这样的提法。</p>
</section>""" % (esc(R["kicker"]), esc(R["title"]), esc(R["intro"]),
                 len(R["stations"]), "{:,}".format(chars), chars / TOTAL_CHARS * 100,
                 max(1, round(mins / 60)), "".join(out))


def build_pyramid():
    td = PYRAMID["topdown"]
    blocks = []
    for i, L in enumerate(td["layers"]):
        if L["a"] == "question":
            blocks.append("""<div class="td-layer">
<div class="td-lv">%s</div>
<div class="td-q">%s</div>
<div class="td-note">%s</div>
</div>""" % (esc(L["level"]), esc(PYRAMID["apex"]["question"]), esc(L["note"])))
        elif L["a"] == "answer":
            inner = """<div class="pyr-apex"><div class="pyr-apex-t">%s</div></div>""" % esc(PYRAMID["apex"]["answer"])
            # 这句是本库自己概括的，不是原文；页面必须把"可被指正"的口子开着，
            # 读者拿原文一对就能发现偏差，所以要留一个直接可点的信箱
            apex_note = esc(PYRAMID["apex"]["note"]) + \
                '概括如有不对，欢迎指正：%s。' % CONTACT
            blocks.append(layer_block(L["level"], "", inner, apex_note, raw_note=True))
        else:  # branches——不用大白卡罩住三张卡：层题与注释放页面上，三张卡独立并排
            # 不设层标题问句：三张卡各自的问句已经在回答上一层的「凭什么成立」，再来一行总问句是重复
            blocks.append("""<div class="td-layer-open">
<div class="td-lv">%s</div>
<div class="pyr-branches">%s</div>
<div class="td-note">%s</div>
</div>""" % (esc("第三层"), "".join(branch_card(b, True) for b in PYRAMID["branches"]), esc(L["note"])))
        if i < len(td["layers"]) - 1:
            blocks.append('<div class="td-conn"><span>%s</span></div>' % esc(L.get("conn", "拆开下一层")))
    body = """<div class="wrap" style="padding-top:40px">
<div class="crumb" style="font-size:12px;color:var(--ink-3)"><a href="index.html" style="color:var(--ink-3);text-decoration:none">首页</a> / 金字塔</div>
<h1 style="font-family:var(--display);font-size:30px;font-weight:700">金字塔 · %s篇，一个答案</h1>
<p style="font-size:13.5px;color:var(--ink-3);margin:10px 0 20px">从 1925 年《中国社会各阶级的分析》到 1937 年《矛盾论》，题目各异，问的是同一件事：<b>中国的路在哪</b>。%s</p>
<div id="top-down">%s</div>
%s
</div>""" % (cn_num(NW), esc(td["intro"]), "".join(blocks), route_section())
    write("pyramid.html", page("金字塔", body, 0, "pyramid"))

# ---------- 8. 经典语录 ----------
def build_quotes():
    """语录页：原文短句的呈现、溯源与本地收藏。
    每条的 text 由 scripts/gen_quotes.py 从 works.json 逐字截取并断言校验，这里只排版。
    para 是 1 基段号（与阅读页 div#pN 一致）；cue 是该段必含的原文片段，
    构建时逐条核对——段号会随数据清理位移，锚词不会，配不上就报错退出。"""
    wmap = {w["id"]: w for w in WORKS}
    cards = []
    for q in QUOTES["items"]:
        paras = wmap[q["wid"]]["paragraphs"]
        n = q["para"]
        if not (0 < n <= len(paras)) or q["cue"] not in paras[n - 1]:
            raise SystemExit("语录锚词失配 %s 第%d段：期望含「%s」，实际「%s」"
                             % (q["wid"], n, q["cue"], (paras[n - 1] if 0 < n <= len(paras) else "")[:40]))
        cards.append("""<figure class="qt" data-id="%s">
<button class="fav" type="button" data-id="%s" aria-pressed="false" aria-label="收藏这条语录"><svg viewBox="0 0 20 20" width="17" height="17" aria-hidden="true"><path d="M5.5 3.5h9v13l-4.5-3.2-4.5 3.2z"/></svg></button>
<div class="qt-tag">%s</div>
<blockquote class="qt-t">%s</blockquote>
<figcaption class="qt-src">《%s》 · <a href="works/%s.html#p%d">第 %d 段 ↗</a></figcaption>
</figure>""" % (q["id"], q["id"], esc(q["tag"]), esc(q["text"]), esc(q["work"]), q["wid"], n, n))
    body = """<div class="narrow" style="padding-top:40px">
<div class="crumb" style="font-size:12px;color:var(--ink-3)"><a href="index.html" style="color:var(--ink-3);text-decoration:none">首页</a> / 语录</div>
<h1 style="font-family:var(--display);font-size:30px;font-weight:700">经典语录</h1>
<p style="font-size:13.5px;color:var(--ink-2);margin:12px 0 6px;line-height:1.9">以下 %d 句，全部从《毛泽东选集》第一卷原文中<b>按句截取</b>，一字未改，也没有拼接不同段落。每条后面的「第 N 段」可以点回原文，看它前后在说什么——孤立的一句和放回上下文的同一句，常常不是一回事。</p>
<p style="font-size:12.5px;color:var(--ink-3);margin:0 0 22px;line-height:1.9">按卷内篇目顺序排列，不作高下之分。点右上角书签可留下你常想起的那几句。</p>
<div class="qt-bar">
<button class="qv on" type="button" data-v="all">全部 <span>%d</span></button>
<button class="qv" type="button" data-v="fav">收藏 <span id="favn">0</span></button>
<button class="qcopy" type="button" id="qcopy">复制收藏</button>
</div>
<div class="qt-list" id="qtlist">%s</div>
<div class="qt-empty" id="qtempty" hidden>还没有收藏。点每句话右上角的书签，这里就会留下它。</div>
<p class="qt-note">收藏只存在这台设备的浏览器里，不上传、不统计，换台设备就没了；要带走就点「复制收藏」。</p>
</div>""" % (len(QUOTES["items"]), len(QUOTES["items"]), "".join(cards))
    write("quotes.html", page("经典语录", body, 0, "quotes"))

# ---------- 9. 检索页 ----------
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
  // 窄屏导航常驻顶栏第二排，不再折叠，这里无需脚本开合
  // 顶栏检索 → 跳检索页（data-root 带出相对层级，深度 1 的页面才不会指到 works/search.html）
  var q = document.getElementById('q');
  if (q) {
    q.addEventListener('keydown', function(e){
      if (e.key === 'Enter' && q.value.trim()) {
        var root = q.getAttribute('data-root') || '';
        location.href = root + 'search.html?q=' + encodeURIComponent(q.value.trim());
      }
    });
  }
  // 今日一篇
  var today = document.getElementById('today');
  if (today && window.__TODAY__) {
    var ws = window.__TODAY__;
    var w = ws[Math.floor(Math.random() * ws.length)];
    today.innerHTML = '<div class="k">今日一篇</div><div><a class="t" href="' + w.u + '">' + w.t + '</a>' +
      '<div class="m">' + w.d + ' · ' + w.c + ' 字 · 约 ' + w.r + '</div></div>';
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
    function esc(s){ var d = document.createElement('div'); d.textContent = (s == null ? '' : s); return d.innerHTML; }
    // 阶段文案里要挂脚注时，scene.fn 给注号，跳页末「注 1 / 注 2」
    function fnRef(s) {
      if (!s.fn) return '';
      var n = esc(s.fn);
      return ' <a class="fn-ref" href="#fn' + n + '" title="见注 ' + n + '">注 ' + n + '</a>';
    }
    function render(i) {
      var s = scenes[i];
      // 按 group 分块：每块＝组名 + 该组按钮。之前把组名与按钮平铺在同一层，
      // flex 折行时组名会和上一组按钮混排（「《矛盾论》原例」飘到中国阶段按钮右边）
      var groups = [], idx = {}, tb = [];
      scenes.forEach(function(x, j){
        if (!(x.group in idx)) { idx[x.group] = groups.length; groups.push({ name: x.group, items: [] }); }
        groups[idx[x.group]].items.push({ scene: x, i: j });
      });
      tb = groups.map(function(g){
        return '<span class="tool-tab-group"><span class="tool-tab-grp">' + esc(g.name) + '</span>'
          + g.items.map(function(o){
              return '<button type="button" data-i="' + o.i + '" class="tool-tab' + (o.i === i ? ' on' : '') + '">' + esc(o.scene.name) + '</button>';
            }).join('') + '</span>';
      });
      tabs.innerHTML = tb.join('');
      Array.prototype.forEach.call(tabs.querySelectorAll('button'), function(b){
        b.addEventListener('click', function(){ render(+b.getAttribute('data-i')); });
      });
      var sideChips = s.sides.map(function(x){
        var m = s.aspectMain && x === s.aspectMain;
        return '<span class="md-chip' + (m ? ' md-chip-main' : '') + '">' + esc(x) + (m ? '<em>矛盾主要方面</em>' : '') + '</span>';
      }).join('<span class="md-vs">对</span>');
      // 原文举的例子单独成行，用原文的年份写法（「一八四○」），不换成通行纪年
      var egs = (s.egs && s.egs.length)
        ? '<div class="md-egs"><span class="lb">原文举的例子</span>' +
          s.egs.map(function(x){ return '<span class="eg">' + esc(x) + '</span>'; }).join('') + '</div>'
        : '';
      // 原文没逐条列次要矛盾的那几格，就空着并说明；不拿史学叙述来填空
      var secBox = s.secondary.length
        ? '<div class="md-sec">' + s.secondary.map(function(x){
            return '<div class="md-sec-card">' + esc(x) + '</div>';
          }).join('') + '</div>' +
          '<div class="md-sec-note">' + esc(s.secnote || '次要矛盾 · 被主要矛盾规定和影响，随阶段相互转化') + '</div>'
        : '<div class="md-sec md-sec-empty"><div class="md-sec-hd">次要矛盾 · 原文未逐条列出</div>' +
          '<div class="md-sec-tx">' + esc(s.secnote || '') + '</div></div>';
      stage.innerHTML =
        '<div class="md-phase">' + esc(s.phase) + '</div>' +
        '<div class="md-grid">' +
          '<div class="md-main">' +
            '<div class="md-tag">' + esc(s.tag || '主要矛盾 · 现阶段谁说话算数') + '</div>' +
            '<div class="md-title">' + esc(s.main) + '</div>' +
            '<div class="md-sides">矛盾双方　' + sideChips + '</div>' +
            egs +
          '</div>' +
          secBox +
        '</div>' +
        '<div class="tool-change"><b>变的是什么</b>' + esc(s.change) + fnRef(s) + '</div>';
      ex.innerHTML = '<b>读法</b>　' + esc(s.note);
      syncQuotes(s.key);
    }
    // 阶段 ↔ 原文依据联动：切到哪个阶段，就只把给这个阶段作证的段落点亮，其余压暗。
    // 不做滚动（读的人正在看上面那块，页面自己跳走最招人烦）
    function syncQuotes(key) {
      var box = document.getElementById('yuju');
      if (!box) return;
      var n = 0;
      Array.prototype.forEach.call(box.querySelectorAll('.yj-q'), function(q){
        var hit = (q.getAttribute('data-for') || '').split(',').indexOf(key) >= 0;
        q.classList.toggle('on', hit);
        q.classList.toggle('dim', !hit);
        if (hit) n++;
      });
      var cap = document.getElementById('yuju-cap');
      if (cap) cap.textContent = '当前这一格，给「' + scenes[
        (function(){ for (var j = 0; j < scenes.length; j++) { if (scenes[j].key === key) return j; } return 0; })()
      ].name + '」作证的原文有 ' + n + ' 段，已点亮；点段号回原文核对。';
    }
    var start = 0, hashKey = (location.hash || '').replace('#', '');
    if (hashKey) {
      scenes.forEach(function(x, j){ if (x.key === hashKey) start = j; });
    }
    render(start);
  }

  // 原版注释：点正文里的〔N〕就地展开那条注释，不跳页底。
  // 不用 href 的原因：注释区默认折叠，跳过去也可能是收着的；就地弹更好读。
  (function(){
    var pop = null;
    function close(){ if (pop) { pop.parentNode.removeChild(pop); pop = null; } }
    document.addEventListener('click', function(e){
      var a = e.target && e.target.closest ? e.target.closest('.nref a') : null;
      if (!a) { close(); return; }
      e.preventDefault();
      var src = document.getElementById(a.getAttribute('data-note') || '');
      if (!src) return;
      var tx = src.querySelector('.note-tx');
      if (!tx) return;
      close();
      var box = document.createElement('div');
      box.className = 'note-pop';
      var head = document.createElement('b');
      head.textContent = '注释 ' + a.textContent;
      var bodyT = document.createElement('div');
      bodyT.textContent = tx.textContent;
      box.appendChild(head);
      box.appendChild(bodyT);
      document.body.appendChild(box);
      pop = box;

      var r = a.getBoundingClientRect();
      var w = Math.min(380, window.innerWidth - 32);
      box.style.width = w + 'px';
      // fixed 定位，全部用视口坐标；滚动即关闭，不必换算 scrollY
      var left = r.left - 16;
      if (left + w > window.innerWidth - 16) left = window.innerWidth - w - 16;
      box.style.left = Math.max(12, left) + 'px';
      if (r.bottom + 240 > window.innerHeight) {
        box.style.top = 'auto';
        box.style.bottom = (window.innerHeight - r.top + 8) + 'px';
      } else {
        box.style.top = (r.bottom + 8) + 'px';
      }
    });
    document.addEventListener('keydown', function(e){ if (e.key === 'Escape') close(); });
    window.addEventListener('scroll', close, { passive: true });
  })();

  // 经典语录：本地收藏。只存 id，不存原文；localStorage 不可用时只在本次会话内有效。
  (function(){
    var list = document.getElementById('qtlist');
    if (!list) return;
    var KEY = 'maokb.fav.v1';
    var btns = [].slice.call(document.querySelectorAll('.fav'));
    var tabs = [].slice.call(document.querySelectorAll('.qv'));
    var countEl = document.getElementById('favn');
    var copyBtn = document.getElementById('qcopy');
    var emptyEl = document.getElementById('qtempty');
    var tab = 'all';

    var favs = (function(){
      try {
        var s = JSON.parse(localStorage.getItem(KEY) || '[]');
        return Array.isArray(s) ? s : [];
      } catch (e) { return []; }
    })();

    function save(){
      try { localStorage.setItem(KEY, JSON.stringify(favs)); } catch (e) {}
    }

    function paint(){
      btns.forEach(function(b){
        var on = favs.indexOf(b.getAttribute('data-id')) >= 0;
        b.setAttribute('aria-pressed', on ? 'true' : 'false');
        if (b.parentNode) b.parentNode.classList.toggle('on', on);
      });
      if (countEl) countEl.textContent = favs.length;
      if (copyBtn) copyBtn.disabled = favs.length === 0;
      list.classList.toggle('only-fav', tab === 'fav');
      if (emptyEl) emptyEl.hidden = !(tab === 'fav' && favs.length === 0);
    }

    tabs.forEach(function(t){
      t.addEventListener('click', function(){
        tab = t.getAttribute('data-v');
        tabs.forEach(function(x){ x.classList.toggle('on', x === t); });
        paint();
      });
    });

    list.addEventListener('click', function(e){
      var b = e.target && e.target.closest ? e.target.closest('.fav') : null;
      if (!b) return;
      var id = b.getAttribute('data-id');
      var i = favs.indexOf(id);
      if (i >= 0) favs.splice(i, 1); else favs.push(id);
      save();
      paint();
    });

    // 收藏要能带走：拼成纯文本，附上可点的原文链接
    if (copyBtn) copyBtn.addEventListener('click', function(){
      var out = [];
      favs.forEach(function(id){
        var fig = list.querySelector('.qt[data-id="' + id + '"]');
        if (!fig) return;
        var t = fig.querySelector('.qt-t');
        var src = fig.querySelector('.qt-src');
        var a = src ? src.querySelector('a') : null;
        var meta = src ? src.textContent.replace(/↗/g, '').replace(/\s+/g, ' ').trim() : '';
        out.push('「' + (t ? t.textContent.trim() : '') + '」\n——' + meta + (a ? '\n' + a.href : ''));
      });
      var text = out.join('\n\n');
      function fallback(){
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.top = '-1000px';
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); done(); } catch (e) {}
        document.body.removeChild(ta);
      }
      function done(){
        var old = copyBtn.textContent;
        copyBtn.textContent = '已复制 ' + favs.length + ' 句';
        setTimeout(function(){ copyBtn.textContent = old; }, 1800);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, fallback);
      } else { fallback(); }
    });

    paint();
  })();

})();
"""
os.makedirs(os.path.join(SITE, "assets"), exist_ok=True)
with open(os.path.join(SITE, "assets", "app.js"), "w", encoding="utf-8") as f:
    f.write(APP_JS)

# ---------- 生成 ----------
build_index()
build_pyramid()
build_works()
for w in WORKS:
    build_work(w)
build_concepts_index()
for c in CONCEPTS:
    build_concept(c)
build_redirects()
build_quotes()
build_search()

n = 0
for root, _, files in os.walk(SITE):
    for fn in files:
        n += 1
print("生成完毕：%d 个文件 -> %s" % (n, SITE))
