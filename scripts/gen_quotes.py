# -*- coding: utf-8 -*-
"""从 data/works.json 抽取「经典语录」页所需的短句。

原则（重要，不要为了好看去改字）：
1. 每条语录都是原文的子串，**逐字不改**，脚本里用 assert 硬校验。
2. 只做「按句截取」，不拼接不同段落，不改标点。
3. 每条都带篇目 id 与段号，页面上要能点回原文核对。

抽取方式：给定 (篇目id, 段号, 起始锚, 结束锚)，取 [起始锚, 结束锚] 之间的子串
（含结束锚）。锚点都是原文里现成的句子边界，避免手写整句时抄错一个字。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def load_works():
    with open(os.path.join(DATA, "works.json"), encoding="utf-8") as f:
        raw = json.load(f)
    works = raw if isinstance(raw, list) else raw.get("works") or raw.get("items")
    return {w["id"]: w for w in works}


def cut(works, wid, pidx, start, end):
    """从 works[wid].paragraphs[pidx] 里截出 start..end（含两端），并校验是原文子串。"""
    para = works[wid]["paragraphs"][pidx]
    i = para.find(start)
    assert i >= 0, "起始锚不在原文里：%s / %s p%d / %r" % (wid, works[wid]["title"], pidx, start)
    j = para.find(end, i)
    assert j >= 0, "结束锚不在原文里：%s / %s p%d / %r" % (wid, works[wid]["title"], pidx, end)
    s = para[i:j + len(end)]
    assert s in para, "截取结果不是原文子串"
    return s


# (篇目 id, 段号, 起始锚, 结束锚, 主题标签)
# 标签只用原作标题或原文中的概念，不自造评价性词。
SPEC = [
    ("v1-001", 1, "谁是我们的敌人", "这个问题是革命的首要问题。", "阶级分析"),
    ("v1-007", 1, "你对于某个问题没有调查", "就停止你对于某个问题的发言权。", "调查研究"),
    # 原本取第 36 段那行小标题「中国革命斗争的胜利要靠中国同志了解中国情况」，
    # 但它是标题、不带句号，和其他条目排在一起像半句话。改用第 37 段正文的完整句：
    # 结论一样（策略只能从实际经验里来），且有句末标点、可独立成立。
    ("v1-007", 37, "共产党的正确而不动摇的斗争策略", "要在实际经验中才能产生。", "调查研究"),
    ("v1-016", 7, "你要知道梨子的滋味", "亲口吃一吃。", "实践论"),
    ("v1-016", 24, "通过实践而发现真理", "这就是辩证唯物论的知行统一观。", "实践论"),
    ("v1-017", 42, "研究问题", "忌带主观性、片面性和表面性。", "矛盾论"),
    # 原取 p6「就得关心群众的痛痒…」，起点是「就得」，脱离上文不成句。改取 p2 末尾整句。
    ("v1-011", 2, "因为革命战争是群众的战争", "只有依靠群众才能进行战争。", "群众工作"),
    ("v1-006", 17, "它是站在海岸遥望海中", "快要成熟了的一个婴儿。", "形势判断"),
]


def main():
    works = load_works()
    items = []
    for wid, pidx, start, end, tag in SPEC:
        w = works[wid]
        text = cut(works, wid, pidx, start, end)
        items.append({
            "id": "%s-p%d" % (wid, pidx),
            "work": w["title"],
            "wid": wid,
            "period": w["period"],
            "date": w["date"],
            "para": pidx,
            "tag": tag,
            "text": text,
        })
    out = {
        "note": "每条均为原文子串，按句截取，未改字。点出处可核对完整段落。",
        "items": items,
    }
    path = os.path.join(DATA, "quotes.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("写出 %d 条 -> %s" % (len(items), path))
    for it in items:
        print(" -", it["wid"], "p%d" % it["para"], "|", it["text"][:28] + ("…" if len(it["text"]) > 28 else ""))


if __name__ == "__main__":
    main()
