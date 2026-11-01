
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
      }).join('') || '<div class="result-empty">没有命中。换个词试试，或去<a href="concepts.html" style="color:var(--color-accent)">概念图谱</a>按主题浏览。</div>';
    }
  }
  // 矛盾论工具
  if (window.__TOOL__) {
    var scenes = window.__TOOL__, tabs = document.getElementById('tabs'), stage = document.getElementById('scene'), ex = document.getElementById('explain');
    function render(i) {
      var s = scenes[i];
      tabs.innerHTML = scenes.map(function(x, j){
        return '<button data-i="' + j + '" style="font-family:var(--font-body);font-size:13px;padding:6px 14px;border-radius:var(--radius-pill);border:1px solid ' + (j===i?'var(--color-accent)':'var(--color-rule-2)') + ';background:' + (j===i?'var(--color-paper-2)':'#fff') + ';color:' + (j===i?'var(--color-accent)':'var(--color-ink-2)') + ';cursor:pointer">' + x.name + '</button>';
      }).join('');
      tabs.querySelectorAll('button').forEach(function(b){
        b.addEventListener('click', function(){ render(+b.dataset.i); });
      });
      var sec = s.secondary.map(function(x){
        return '<div style="padding:12px 16px;background:var(--color-paper-2);border:1px solid var(--color-rule);border-radius:var(--radius-pill);font-size:14px;color:var(--color-ink-2)">' + x + '</div>';
      }).join('');
      stage.innerHTML =
        '<div style="font-size:11px;color:var(--color-muted);letter-spacing:0;margin-bottom:10px">' + s.phase + '</div>' +
        '<div style="display:flex;flex-wrap:wrap;gap:14px;align-items:stretch">' +
          '<div style="flex:1 1 300px;padding:18px 20px;background:var(--color-paper-2);border:2px solid var(--color-accent);border-radius:var(--radius-pill)">' +
            '<div style="font-size:11px;color:var(--color-accent);letter-spacing:0">主要矛盾</div>' +
            '<div style="font-family:var(--font-display);font-size:20px;font-weight:700;margin-top:6px;color:var(--color-accent)">' + s.main + '</div>' +
            '<div style="font-size:12.5px;color:var(--color-ink-2);margin-top:8px">' + s.mainAspect + '</div>' +
          '</div>' +
          '<div style="flex:2 1 340px;display:grid;grid-template-columns:1fr 1fr;gap:10px">' + sec + '</div>' +
        '</div>' +
        '<div style="font-size:12px;color:var(--color-muted);margin-top:14px">次要矛盾 · 受主要矛盾规定和影响，随阶段相互转化</div>';
      ex.innerHTML = '<b>读法</b>　' + s.note;
    }
    render(0);
  }
})();
