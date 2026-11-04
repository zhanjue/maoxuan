# -*- coding: utf-8 -*-
"""补录第 18 篇《为争取千百万群众进入抗日民族统一战线而斗争》，并修正两处数据。

为什么要单独写：求是网这一篇的篇名在 <strong> 里、开篇第一段没包 <p>，
parse2.py 只认 <p>，于是整篇被当成《中国共产党在抗日时期的任务》的续页丢掉，
它的 14 条注释又被算进上一篇（编号回退即换篇）。补篇之后：

1) works.json 从 17 篇变 18 篇，「第一卷全量」才成立；
2) 《中国共产党在抗日时期的任务》的注释回到它自己的 22 条；
3) 全站「另有 14 条注释属于未收录篇目」的提示自然消失；
4) id / order 按写作时间重排，concepts / pyramid / quotes / reading 里的
   work id 引用同步改写（按篇名映射，不按序号硬猜）。

另修正：《中国共产党在抗日时期的任务》日期由「五月八日」改为「五月三日」。
求是网该页标的是五月八日，与同页另一篇结论日期相同，属源站标注错误；
《毛泽东选集》第 1 卷（人民出版社 1991 年版，第 263 页）记为一八三七年五月三日，
人民网党史频道引用同版同页。
"""
import io, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
D = os.path.join(ROOT, "data")

DATE_RE = re.compile(r"^（([一二三四五六七八九〇零]{4})年([一二三四五六七八九十]{1,3})月"
                     r"(?:([一二三四五六七八九十]{1,3})日)?）$")
CN = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
      "〇": 0, "零": 0, "○": 0, "十": "十"}


def cn_num(s):
    """一九三七 → 1937；十 → 10；十三 → 13；二十三 → 23"""
    if "十" in s:
        a, _, b = s.partition("十")
        return (CN.get(a, 1) if a else 1) * 10 + (CN.get(b, 0) if b else 0)
    n = 0
    for ch in s:
        n = n * 10 + CN[ch]
    return n


# ---------- 1. 从 raw/idx20.html 抽这一篇 ----------
t = io.open(os.path.join(RAW, "idx20.html"), encoding="utf-8").read()
m = re.search(r"<strong>\s*(.{4,60}?)\s*</strong>", t, re.S)
TITLE = re.sub(r"<[^>]+>", "", m.group(1)).strip()
seg = t[m.end():]

items = []
for mm in re.finditer(r"<p[^>]*>(.*?)</p>|>([^<>]{40,}?)<", seg, re.S):
    raw = mm.group(1) if mm.group(1) is not None else mm.group(2)
    txt = re.sub(r"<[^>]+>", "", raw)
    txt = (txt.replace("&nbsp;", " ").replace("&quot;", '"').replace("&amp;", "&")
              .replace("　", "").strip())
    if txt:
        items.append(txt)

# 截到「注释」为止
ni = items.index("注释")
head, tail = items[:ni], items[ni + 1:]

date_norm = date_key = None
body = []
for p in head:
    dm = DATE_RE.match(p)
    if dm:
        date_key = "%d-%02d" % (cn_num(dm.group(1)), cn_num(dm.group(2)))
        if dm.group(3):
            date_key += "-%02d" % cn_num(dm.group(3))
        date_norm = p
        continue
    # 求是网把末节小标题折成两段（「…进入抗日」/「民族统一战线而斗争」）
    if body and body[-1] == "为争取千百万群众进入抗日" and p == "民族统一战线而斗争":
        body[-1] = "为争取千百万群众进入抗日民族统一战线而斗争"
        continue
    body.append(p)

notes = [p for p in tail if p.startswith("〔")]
# tail 里还有一条题解「（这是毛泽东在一九三七年…所作的结论。）」，其他篇也都不收题解，这里同样跳过

print("篇名：", TITLE)
print("日期：", date_norm, "->", date_key)
print("正文 %d 段 / %d 字 | 注释 %d 条" % (len(body), sum(len(p) for p in body), len(notes)))
for p in body[:3]:
    print("   首段：", p[:40])

# ---------- 2. 装载并修补 works ----------
works = json.load(io.open(os.path.join(D, "works.json"), encoding="utf-8"))
old_id_title = {w["id"]: w["title"] for w in works}

TASK = "中国共产党在抗日时期的任务"
for w in works:
    if w["title"] == TASK:
        if w["dateKey"] != "1937-05-03":
            print("修正《%s》日期：%s -> 1937-05-03" % (TASK, w["dateKey"]))
            w["dateKey"] = "1937-05-03"
            w["date"] = "（一九三七年五月三日）"
        # 注释只留本篇的：编号一旦回退，后面的都属于另一篇
        own, seen = [], set()
        for n in w["notes"]:
            mm = re.match(r"〔(\d+)〕", n.strip())
            if mm:
                num = int(mm.group(1))
                if num in seen:
                    break
                seen.add(num)
            own.append(n)
        print("《%s》注释 %d -> %d" % (TASK, len(w["notes"]), len(own)))
        w["notes"] = own

new = {
    "id": "v1-XXX",
    "vol": 1,
    "order": 0,
    "period": "第二次国内革命战争时期",
    "title": TITLE,
    "date": date_norm,
    "dateKey": date_key,
    "paragraphs": body,
    "notes": notes,
    "charCount": sum(len(p) for p in body),
    "source": "求是网 qstheory.cn",
}
if not any(w["title"] == TITLE for w in works):
    works.append(new)

# ---------- 3. 按写作时间重排，重编 id / order ----------
works.sort(key=lambda w: (w["dateKey"] or "9999", w["title"]))
for i, w in enumerate(works, 1):
    w["order"] = i
    w["id"] = "v1-%03d" % i

new_id_by_title = {w["title"]: w["id"] for w in works}
remap = {old: new_id_by_title[title] for old, title in old_id_title.items()}
remap = {k: v for k, v in remap.items() if k != v}
print("id 重映射：", remap or "无变化", "| 篇数 %d" % len(works))

with io.open(os.path.join(D, "works.json"), "w", encoding="utf-8") as f:
    json.dump(works, f, ensure_ascii=False, indent=1)


# ---------- 4. 其余数据里的 work id 引用同步改写 ----------
def walk(o):
    if isinstance(o, dict):
        return {k: walk(v) for k, v in o.items()}
    if isinstance(o, list):
        return [walk(v) for v in o]
    if isinstance(o, str) and o in remap:
        return remap[o]
    return o


for name in ("concepts.json", "pyramid.json", "quotes.json", "reading.json"):
    p = os.path.join(D, name)
    if not os.path.exists(p):
        continue
    data = json.load(io.open(p, encoding="utf-8"))
    fixed = walk(data)
    if fixed != data:
        with io.open(p, "w", encoding="utf-8") as f:
            json.dump(fixed, f, ensure_ascii=False, indent=1)
        print("改写引用：", name)

print("\n合计 %d 篇 / %d 字 / %d 条注释" % (
    len(works), sum(w["charCount"] for w in works), sum(len(w["notes"]) for w in works)))
