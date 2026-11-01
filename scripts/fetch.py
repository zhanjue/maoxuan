# -*- coding: utf-8 -*-
"""抓取《毛泽东选集》第一卷全量语料（求是网，官方渠道）。
URL 规律：书籍 id + '_' + 篇目序号（第一篇为无后缀 URL）。
输出：data/raw/idxNN.html + report.json
"""
import requests, re, time, os, json

BASE = "https://www.qstheory.cn/books/2019-07/31/c_1119448591"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")
os.makedirs(OUT, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
urls = [BASE + ".htm"] + [BASE + "_%d.htm" % i for i in range(2, 26)]

report = []
for idx, url in enumerate(urls, 1):
    try:
        r = requests.get(url, headers=UA, timeout=25)
        if r.status_code != 200 or len(r.content) < 8000:
            print(idx, "skip", r.status_code, len(r.content))
            continue
        r.encoding = "utf-8"
        t = r.text
        with open(os.path.join(OUT, "idx%02d.html" % idx), "w", encoding="utf-8") as f:
            f.write(t)
        report.append({"idx": idx, "url": url, "bytes": len(r.content)})
        print(idx, "ok", len(r.content))
    except Exception as e:
        print(idx, "ERR", str(e)[:80])
    time.sleep(0.3)

with open(os.path.join(OUT, "report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("SAVED", len(report))
