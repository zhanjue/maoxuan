# -*- coding: utf-8 -*-
"""把 data/works.json 导出成 Markdown。

产物（默认写到 export/）：
  毛选第一卷-全文.md        —— 18 篇合订，带目录
  分篇/01 篇名.md           —— 每篇一个文件

只做文本搬运，不改一个字：正文沿用原文（含〔N〕注号），
脚注原样附在篇末。标题识别靠「短且无句末标点」，与站内渲染一致。
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "works.json")
OUT = os.path.join(ROOT, "export")

END_PUNCT = "。？！：；"


def is_heading(p):
    s = p.strip()
    if not s:
        return False
    if s[0] in "一二三四五六七八九十" and "　" in s[:4]:
        return True
    if s.startswith("第") and ("章" in s[:6] or "节" in s[:6]):
        return True
    return len(s) <= 28 and not any(ch in s for ch in END_PUNCT)


def safe_name(s):
    return re.sub(r'[\\/:*?"<>|]', "＿", s).strip()


def note_lines(notes):
    out = []
    for n in notes:
        n = n.strip()
        if not n:
            continue
        # 〔1〕正文 → 1. 正文，便于 Markdown 渲染
        m = re.match(r"^〔(\d+)〕\s*(.*)$", n, re.S)
        if m:
            out.append("%s. %s" % (m.group(1), m.group(2).strip()))
        else:
            out.append("- " + n)
    return out


def render_work(w, level=1, with_toc=False):
    h = "#" * level
    lines = ["%s %02d %s" % (h, w["order"], w["title"]), ""]
    lines.append("- 时期：%s" % w.get("period", ""))
    lines.append("- 写作日期：%s" % w.get("date", "").strip("（）"))
    lines.append("- 字数：%s" % "{:,}".format(w.get("charCount", 0)))
    if w.get("source"):
        lines.append("- 来源：%s" % w["source"])
    lines.append("")

    for p in w["paragraphs"]:
        s = p.strip()
        if not s:
            continue
        if s == w.get("period"):
            continue  # 时期名已在头部元信息里
        if is_heading(s):
            lines.append("%s %s" % ("#" * (level + 1), s))
            lines.append("")
        else:
            lines.append(s)
            lines.append("")

    nl = note_lines(w.get("notes") or [])
    if nl:
        lines.append("%s 注释" % ("#" * (level + 1)))
        lines.append("")
        lines.extend(nl)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main():
    works = json.load(io.open(DATA, encoding="utf-8"))
    works.sort(key=lambda x: x["order"])
    os.makedirs(os.path.join(OUT, "分篇"), exist_ok=True)

    total_chars = sum(w.get("charCount", 0) for w in works)
    total_notes = sum(len(w.get("notes") or []) for w in works)

    # 合订本
    head = [
        "# 《毛泽东选集》第一卷 · 全文",
        "",
        "> 共 %d 篇，%s 字，原注 %d 条。正文与脚注均按原文照录，未作改写。"
        % (len(works), "{:,}".format(total_chars), total_notes),
        "",
        "## 目录",
        "",
    ]
    for w in works:
        head.append("%d. [%s](#%02d-%s)" % (w["order"], w["title"], w["order"], w["order"]))
    parts = ["\n".join(head)]
    for w in works:
        parts.append("\n---\n\n" + render_work(w, level=1))
    combo = "\n".join(parts)
    with io.open(os.path.join(OUT, "毛选第一卷-全文.md"), "w", encoding="utf-8") as f:
        f.write(combo)

    # 分篇
    for w in works:
        fn = "%02d %s.md" % (w["order"], safe_name(w["title"]))
        with io.open(os.path.join(OUT, "分篇", fn), "w", encoding="utf-8") as f:
            f.write(render_work(w, level=1))

    print("导出完成：%s" % OUT)
    print("  合订本 1 个（%s 字）" % "{:,}".format(total_chars))
    print("  分篇 %d 个" % len(works))


if __name__ == "__main__":
    sys.exit(main())
