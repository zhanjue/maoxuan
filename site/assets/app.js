
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
    function esc(s){ var d = document.createElement('div'); d.textContent = (s == null ? '' : s); return d.innerHTML; }
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
      var sec = s.secondary.map(function(x){
        return '<div class="md-sec-card">' + esc(x) + '</div>';
      }).join('');
      var sideChips = s.sides.map(function(x){
        var m = s.aspectMain && x === s.aspectMain;
        return '<span class="md-chip' + (m ? ' md-chip-main' : '') + '">' + esc(x) + (m ? '<em>矛盾主要方面</em>' : '') + '</span>';
      }).join('<span class="md-vs">对</span>');
      stage.innerHTML =
        '<div class="md-phase">' + esc(s.phase) + '</div>' +
        '<div class="md-grid">' +
          '<div class="md-main">' +
            '<div class="md-tag">主要矛盾 · 现阶段谁说话算数</div>' +
            '<div class="md-title">' + esc(s.main) + '</div>' +
            '<div class="md-sides">矛盾双方　' + sideChips + '</div>' +
          '</div>' +
          '<div class="md-sec">' + sec + '</div>' +
        '</div>' +
        '<div class="md-sec-note">次要矛盾 · 被主要矛盾规定和影响，随阶段相互转化</div>' +
        '<div class="tool-change"><b>变的是什么</b>' + esc(s.change) + '</div>';
      ex.innerHTML = '<b>读法</b>　' + esc(s.note);
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
})();
