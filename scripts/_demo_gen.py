# -*- coding: utf-8 -*-
"""三个 demo 页生成器：注释里的另一本书 / 四篇读通全书 / 词频演变
输出到 site/_demo-*.html（临时页，确认后再并入 build.py）"""
import json, os, re, html, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'site')
W = json.load(open(os.path.join(ROOT, 'data/works.json'), encoding='utf-8'))
esc = lambda s: html.escape(s, quote=False)
CN = str.maketrans('〇一二三四五六七八九', '0123456789')

def cn2num(s):
    s = s.translate(CN)
    return int(s) if s.isdigit() else None

NAV = [('index.html', '首页'), ('works.html', '篇目'), ('pyramid.html', '金字塔'),
       ('concepts.html', '概念'), ('timeline.html', '时期'), ('quotes.html', '语录')]

def page(title, body, extra_css=''):
    nav = ''.join('<a href="%s">%s</a>' % (h, l) for h, l in NAV)
    return """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%s · 知行录</title>
<link rel="stylesheet" href="assets/style.css?v=30">
<style>%s</style></head><body>
<header class="topbar"><div class="topbar-in">
<a class="brand" href="index.html">知行录<small>MAO WORKS · VOL.1</small></a>
<nav class="nav">%s</nav>
<div class="searchbox"><input type="search" placeholder="检索全文…" autocomplete="off"></div>
</div></header>
%s
<footer class="footer"><div class="wrap"><div class="bd">
<p><b>知行录</b>——文献检索与阅读工具。文本依据人民出版社《毛泽东选集》第一卷，逐字收录，未作改写。</p>
<p>示例页 · 用于确认版式与信息组织，尚未接入正式构建。</p>
</div></div></footer>
</body></html>""" % (title, extra_css, nav, body)

def write(name, content):
    open(os.path.join(SITE, name), 'w', encoding='utf-8').write(content)
    print('  ->', name, len(content), 'bytes')

# ================= 数据 =================
class N:
    def __init__(self, w, num, text):
        self.w, self.num, self.text = w, num, text
        self.para = None
        for i, p in enumerate(w['paragraphs'], 1):
            if '〔%s〕' % num in p:
                self.para = i
                break

NOTES = []
for w in W:
    for n in (w.get('notes') or []):
        m = re.match(r'〔(\d+)〕(.*)', n, re.S)
        if m:
            NOTES.append(N(w, m.group(1), m.group(2).strip()))

# 人物小传
DOC = re.compile(r'^([\u4e00-\u9fa5·]{2,6})[（(]([〇一二三四五六七八九]{4})[—―－\-─]+([〇一二三四五六七八九]{4})[）)](.*)$', re.S)
people = {}
for n in NOTES:
    m = DOC.match(n.text)
    if m:
        people.setdefault(m.group(1), {'born': cn2num(m.group(2)), 'died': cn2num(m.group(3)),
                                       'tail': m.group(4).lstrip('，,'), 'items': []})['items'].append(n)

# 事件条目（以年份开头）
events = []
for n in NOTES:
    m = re.match(r'^([〇一二三四五六七八九]{4})年', n.text)
    if m:
        events.append({'year': cn2num(m.group(1)), 'brief': n.text.split('。')[0], 'n': n})

# 名词释义（以“指”开头）
terms = [n for n in NOTES if re.match(r'^(这里|这|那时)?(是)?指', n.text)]

# 年份分布
yearh = collections.Counter()
for n in NOTES:
    for y in re.findall(r'([〇一二三四五六七八九]{4})', n.text):
        v = cn2num(y)
        if v and 1900 <= v <= 1949:
            yearh[v] += 1
years_sorted = sorted(yearh.items())

print('注释 %d | 人物 %d 人 / %d 条 | 事件 %d | 名词 %d' % (
    len(NOTES), len(people), sum(len(p['items']) for p in people.values()), len(events), len(terms)))

# ================= Demo 1 注释 =================
CSS1 = """
.dm-hero { padding: 46px 0 26px; }
.dm-hero h1 { font-family: var(--display); font-size: 34px; font-weight: 700; letter-spacing: .02em; }
.dm-lede { font-size: 14px; color: var(--ink-2); max-width: 620px; margin-top: 14px; line-height: 2.05; }
.dm-nums { display: flex; gap: 40px; margin: 26px 0 8px; }
.dm-nums div b { display: block; font-family: var(--display); font-size: 24px; font-weight: 700; }
.dm-nums div span { font-size: 12px; color: var(--ink-3); letter-spacing: .04em; }
.dm-sec { margin: 54px 0 0; }
.dm-sec > h2 { font-family: var(--display); font-size: 21px; font-weight: 700; padding-bottom: 10px; border-bottom: 1px solid var(--line); }
.dm-sec > .hint { font-size: 12.5px; color: var(--ink-3); margin: 10px 0 22px; line-height: 1.95; }
.ppl { display: grid; grid-template-columns: 1fr 1fr; gap: 0 34px; }
.pp { padding: 18px 0; border-bottom: 1px solid var(--line); }
.pp-hd { display: flex; align-items: baseline; gap: 10px; }
.pp-nm { font-family: var(--display); font-size: 16.5px; font-weight: 700; }
.pp-yr { font-size: 11.5px; color: var(--ink-3); font-variant-numeric: tabular-nums; }
.pp-tx { font-size: 12.5px; color: var(--ink-2); line-height: 1.95; margin-top: 7px; cursor: pointer;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.pp-tx.open { display: block; -webkit-line-clamp: unset; }
.pp-ft { font-size: 11.5px; color: var(--ink-3); margin-top: 6px; }
.pp-ft a { color: var(--teal); text-decoration: none; }
.pp[data-multi] .pp-nm::after { content: " ×" attr(data-multi); font-size: 10.5px; color: var(--teal); font-family: var(--text); }
.ev { border-left: 2px solid var(--line-2); padding-left: 18px; }
.ev details { padding: 6px 0; }
.ev summary { cursor: pointer; font-size: 13px; color: var(--ink-2); list-style: none; }
.ev summary::-webkit-details-marker { display: none; }
.ev summary b { font-family: var(--mono); font-size: 12.5px; color: var(--teal); margin-right: 10px; }
.ev details[open] summary { color: var(--ink); }
.ev .ev-b { font-size: 12px; color: var(--ink-2); line-height: 1.9; margin: 8px 0 4px 42px; padding-left: 12px; border-left: 1px solid var(--line-2); }
.tm { display: grid; grid-template-columns: 1fr 1fr; gap: 0 34px; }
.tm div { padding: 12px 0; border-bottom: 1px solid var(--line); font-size: 12.5px; color: var(--ink-2); line-height: 1.85; }
.tm div span { color: var(--ink-3); font-size: 11.5px; display: block; margin-top: 3px; }
.tm-h { font-family: var(--display); font-size: 13px; font-weight: 700; color: var(--ink); display: block; margin-bottom: 3px; }
@media (max-width: 760px) { .ppl, .tm { grid-template-columns: 1fr; } .dm-hero h1 { font-size: 26px; } .dm-nums { gap: 22px; } }
"""

def hist_svg():
    items = [(y, c) for y, c in years_sorted if 1921 <= y <= 1939 and c >= 2]
    mx = max(c for _, c in items)
    H = len(items) * 21 + 4
    g = ['<svg viewBox="0 0 640 %d" style="width:100%%;max-width:640px;height:auto" role="img" aria-label="注释年份分布">' % H]
    for i, (y, c) in enumerate(items):
        yy = i * 21
        g.append('<text x="42" y="%d" font-size="11" fill="#8A8A82" text-anchor="end">%d</text>' % (yy + 11, y))
        g.append('<rect x="52" y="%d" width="%.1f" height="10" fill="#0F766E" opacity="%.2f"/>'
                 % (yy + 2, c / mx * 490, 0.38 if c < 8 else 0.8))
        g.append('<text x="%.1f" y="%d" font-size="10.5" fill="#8A8A82">%d</text>' % (56 + c / mx * 490, yy + 11, c))
    g.append('</svg>')
    return ''.join(g)

ppl_html = []
for name, p in sorted(people.items(), key=lambda kv: (-len(kv[1]['items']), kv[1]['born'])):
    multi = ' data-multi="%d"' % len(p['items']) if len(p['items']) > 1 else ''
    srcs = '、'.join('《%s》<a href="works/%s.html#p%d">p%d</a>' % (esc(x.w['title']), x.w['id'], x.para, x.para)
                    for x in p['items'] if x.para)
    ppl_html.append("""<div class="pp"%s>
<div class="pp-hd"><span class="pp-nm">%s</span><span class="pp-yr">%d—%d</span></div>
<div class="pp-tx" onclick="this.classList.toggle('open')">%s</div>
<div class="pp-ft">%s</div></div>""" % (multi, esc(name), p['born'], p['died'], esc(p['tail']), srcs))

ev_by_year = collections.OrderedDict()
_seen = {}
for e in sorted(events, key=lambda x: x['year']):
    key = re.sub(r'\s+', '', e['brief'])[:26]
    if key in _seen:
        _seen[key]['dups'] += 1
        continue
    e['dups'] = 0
    _seen[key] = e
    if e['year'] >= 1921:
        ev_by_year.setdefault(e['year'], []).append(e)

top_open = set(sorted(ev_by_year, key=lambda v: -len(ev_by_year[v]))[:3])
ev_html = []
for y in sorted(ev_by_year)[:8]:
    rows = ev_by_year[y]
    inner = ''.join('<div class="ev-b">%s%s <a href="works/%s.html#p%d" style="color:var(--teal)">p%d ↗</a></div>'
                    % (esc(r['brief']), ('（另 %d 处同注）' % r['dups']) if r['dups'] else '',
                       r['n'].w['id'], r['n'].para or 0, r['n'].para or 0) for r in rows[:4])
    if len(rows) > 4:
        inner += '<div class="ev-b" style="border-left:0;color:var(--ink-3)">另有 %d 条同年的注释未列出</div>' % (len(rows) - 4)
    ev_html.append('<details%s><summary><b>%d</b>%d 条注释解释这一年</summary>%s</details>'
                   % (' open' if (y in top_open or len(rows) <= 2) else '', y, len(rows), inner))

def term_head(n):
    """取正文上标前那几个字当词头；清理「如自耕农」「们从…的五卅运动」这类上下文"""
    if not n.para:
        return ''
    ppr = n.w['paragraphs'][n.para - 1]
    i = ppr.find('〔%s〕' % n.num)
    if i <= 0:
        return ''
    m = re.search(r'([\u4e00-\u9fa5A-Za-z0-9“”"]{2,12})$', ppr[max(0, i - 16):i])
    if not m:
        return ''
    h = m.group(1)
    if '的' in h:
        h = h.rsplit('的', 1)[1] or h
    h = re.sub(r'^(例如|比如|所谓|这些|那些|这个|一个|如|即|是|和|与|及|其)', '', h)
    if re.match(r'^[〇一二三四五六七八九十]+年$', h) or h.startswith(('那', '这')):
        return ''
    return h if 2 <= len(h) <= 7 else ''

named = [(term_head(t), t) for t in terms]
named = [(h, t) for h, t in named if h]
term_html = ''.join('<div><b class="tm-h">%s</b>%s<span>《%s》<a href="works/%s.html#p%d" style="color:var(--teal);text-decoration:none">p%d ↗</a></span></div>'
                    % (esc(h), esc(t.text.split('。')[0] + '。'), esc(t.w['title']), t.w['id'], t.para or 0, t.para or 0)
                    for h, t in named[:20])

body1 = """<div class="wrap"><div class="dm-hero">
<div class="crumb" style="font-size:12px;color:var(--ink-3)"><a href="index.html" style="color:var(--ink-3);text-decoration:none">首页</a> / 另一本书</div>
<h1>注释里的另一本书</h1>
<p class="dm-lede">正文十六万字讲道理，脚注里三百多条讲人事。把注释单独抽出来按年代排，就是一张 1925—1937 年的中国政治地图：谁掌权、谁叛变、哪个组织成立、哪一年打什么仗。这一页不读正文，只读注。</p>
<div class="dm-nums">
<div><b>%d</b><span>条原版注释</span></div>
<div><b>%d</b><span>条人物小传</span></div>
<div><b>%d</b><span>条事件编年</span></div>
<div><b>%d</b><span>条名词释义</span></div>
</div>
<p style="font-size:11.5px;color:var(--ink-3)">数字由脚本从 works.json 统计，未作人工挑选。</p>
</div>

<section class="dm-sec"><h2>一 · 谁是谁</h2>
<p class="hint">注释里带生卒年的条目，本身就是一篇小传：原名、籍贯、做过什么、怎么死的。点姓名旁的段号可回到正文，看他在哪一句被提到；点正文可展开全文。</p>
<div class="ppl">%s</div></section>

<section class="dm-sec"><h2>二 · 哪一年被解释得最多</h2>
<p class="hint">统计 314 条注释里出现的年份（1921 年以前与 1939 年以后的零散条目未画）。1927 年出现 50 次，是整卷注释里被解释得最多的一年——大革命失败那一年，几乎每篇文章都要交代一次。</p>
<div style="max-width:640px">%s</div></section>

<section class="dm-sec"><h2>三 · 注出来的年表</h2>
<p class="hint">以年份开头的注释本身就是记事条目。按年份归拢，不用读正文，也能排出一条时间线。</p>
<div class="ev">%s</div></section>

<section class="dm-sec"><h2>四 · 词与物</h2>
<p class="hint">正文里带〔N〕的地方，多数就是被解释的那个词。把词头抽出来排成一页索引：自耕农、挨户团、五卅运动——今天听着陌生的，注释里一句讲清。</p>
<div class="tm">%s</div></section>
</div>""" % (len(NOTES), sum(len(p['items']) for p in people.values()), len(events), len(terms),
             ''.join(ppl_html), hist_svg(), ''.join(ev_html), term_html)

# 这一页已并入正式站：概念图谱页末的附录（build.py 里的 note_book()）。
# 这里不再重复生成，否则会出现两份内容不一致的同一页——上面这段代码留作历史参考。
# write('_demo-notes.html', page('另一本书', body1, CSS1))

# Demo 2「四篇读通全书」已放进正式站：金字塔页末那一节（build.py 的 route_section）。
# 这里不再重复生成，否则同一页会有两份内容不一致的副本。

# ================= Demo 3 词频 =================
CSS3 = """
.fq-hero { padding: 46px 0 8px; }
.fq-hero h1 { font-family: var(--display); font-size: 32px; font-weight: 700; }
.fq-hero .lede { font-size: 14px; color: var(--ink-2); max-width: 640px; margin-top: 14px; line-height: 2.05; }
.sms { display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px 26px; margin: 28px 0 0; }
.sm { border-top: 2px solid var(--line-2); padding-top: 9px; }
.sm-hd { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 2px; }
.sm-w { font-family: var(--display); font-size: 15px; font-weight: 700; }
.sm-pk { font-size: 10px; color: var(--ink-3); }
.fq-note { font-size: 11.5px; color: var(--ink-3); line-height: 1.95; margin-top: 16px; }
.fq-two { display: grid; grid-template-columns: 1fr 1fr; gap: 28px; margin: 40px 0 40px; }
.fq-box { border-top: 1px solid var(--line-2); padding-top: 16px; }
.fq-box h3 { font-family: var(--display); font-size: 15px; font-weight: 700; margin-bottom: 10px; }
.fq-box li { font-size: 12.5px; color: var(--ink-2); line-height: 1.95; margin-left: 16px; margin-bottom: 8px; }
.fq-box.bad h3 { color: #B4552D; }
@media (max-width: 820px) { .sms { grid-template-columns: repeat(2, 1fr); } .fq-two { grid-template-columns: 1fr; gap: 18px; } .fq-hero h1 { font-size: 25px; } }
"""

words = [('革命', '#0F766E'), ('农民', '#B4552D'), ('战争', '#6B7A8F'),
         ('群众', '#8A6D3B'), ('矛盾', '#4A6B57'), ('实践', '#7A5C8F')]
years = list(range(1925, 1938))
by = {}
for y in years:
    ws = [w for w in W if int(w['dateKey'][:4]) == y]
    by[y] = {'chars': sum(w['charCount'] for w in ws),
             'text': ''.join(''.join(w['paragraphs']) for w in ws)}

def freq(word, y):
    d = by[y]
    return None if not d['chars'] else d['text'].count(word) / d['chars'] * 10000

SM_W, SM_H = 268, 132
def sm_svg(word, color):
    pts = [(y, freq(word, y)) for y in years if freq(word, y) is not None]
    vmax = (max(v for _, v in pts) or 1) * 1.15
    L2, R2, T2, B2 = 26, 10, 12, 20
    fx = lambda y: L2 + (y - 1925) / 12.0 * (SM_W - L2 - R2)
    fy = lambda v: T2 + (1 - v / vmax) * (SM_H - T2 - B2)
    g = ['<svg viewBox="0 0 %d %d" style="width:100%%;height:auto" role="img" aria-label="%s 词频">' % (SM_W, SM_H, word)]
    g.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#E4E1D9" stroke-width="1"/>' % (L2, fy(0), SM_W - R2, fy(0)))
    for (ya, va), (yb, vb) in zip(pts, pts[1:]):
        dash = ' stroke-dasharray="2.5 2.5"' if yb - ya > 1 else ''
        g.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.5" stroke-linecap="round"%s/>'
                 % (fx(ya), fy(va), fx(yb), fy(vb), color, dash))
    for yy, vv in pts:
        g.append('<circle cx="%.1f" cy="%.1f" r="2.6" fill="%s"><title>%d 年 · 每万字 %.1f 次</title></circle>'
                 % (fx(yy), fy(vv), color, yy, vv))
    for ty in (1925, 1930, 1937):
        g.append('<text x="%.1f" y="%d" font-size="9.5" fill="#8A8A82" text-anchor="middle">%d</text>' % (fx(ty), SM_H - 5, ty))
    g.append('</svg>')
    return ''.join(g)

sms = []
for word, color in words:
    pts = [(y, freq(word, y)) for y in years if freq(word, y) is not None]
    pk_y, pk_v = max(pts, key=lambda t: t[1])
    sms.append('<div class="sm" style="border-top-color:%s"><div class="sm-hd"><span class="sm-w">%s</span>'
               '<span class="sm-pk">峰值 %d 年 · 每万字 %.1f 次</span></div>%s</div>'
               % (color, word, pk_y, pk_v, sm_svg(word, color)))

body3 = """<div class="wrap"><div class="fq-hero">
<div class="crumb" style="font-size:12px;color:var(--ink-3)"><a href="index.html" style="color:var(--ink-3);text-decoration:none">首页</a> / 词频</div>
<h1>词频演变 · 一张容易被误读的图</h1>
<p class="lede">按年统计六个词在正文里的密度（每万字出现次数），再按字数归一，让长短不同的文章能放在一起比。图很好看，但先看每一格右上角那行峰值——很多「趋势」其实是某一篇文章造成的。</p>
</div>
<div class="sms">%s</div>
<p class="fq-note">六格的纵轴各自刻度（按该词的峰值定高），只能看形状，不能横向比高低。跨年没有文章的区间画成虚线，表示中间没有观测点，不是连续变化；1925 年只有一篇 3,780 字的文章，那一点的起伏最不可信。</p>
<div class="fq-two">
<div class="fq-box"><h3>这张图能读出来的</h3><ul>
<li>「农民」的高点全在 1927 年，此后一路走低——那一年他专门做了一次农村调查，之后转去谈战争和组织。</li>
<li>「矛盾」「实践」在 1937 年之前几乎为零，因为这两个词成为系统术语，是 1937 年那两篇讲哲学的文章之后的事。</li>
<li>「群众」在 1933—1934 年最密，正好是关心群众生活、经济政策那几篇；1935 年之后骤降。</li>
</ul></div>
<div class="fq-box bad"><h3>这张图读不出来的</h3><ul>
<li>读不出「思想在变化」。一年的数据往往只由一两篇文章构成，尖峰是题材，不是时代。</li>
<li>读不出重视程度。他在 1930 年几乎不提「矛盾」，不等于不重视矛盾，只是那几篇不谈哲学。</li>
<li>读不出因果关系。词多了或少了，与局势、与写作对象、与文章体裁都有关，单看频次分不清。</li>
</ul></div>
</div>
</div>""" % ''.join(sms)

write('_demo-freq.html', page('词频演变', body3, CSS3))
print('done')
