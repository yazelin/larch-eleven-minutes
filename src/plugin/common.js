/* 插件卡共用：跟 Larch 溝通、點擊與按鍵。卡片用 L.onInit / L.set / L.get / L.done / L.press。 */
var L = (function () {
  var initFns = [], vars = {}, values = {};
  addEventListener('message', function (e) {
    var d = e.data; if (!d || d.type !== 'larch:init') return;
    vars = d.variables || {}; values = d.values || {};
    initFns.forEach(function (f) { f(values, vars, d.assets || []); });
  });
  parent.postMessage({ type: 'larch:ready' }, '*');
  var pressFns = [];
  addEventListener('keydown', function (e) {
    if (e.target && e.target.closest && e.target.closest('button,input,textarea,select')) return;  /* 表單元素保留原生行為 */
    if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); pressFns.forEach(function (f) { f(); }); }
  });
  var finished = false;
  return {
    onInit: function (f) { initFns.push(f); },
    set: function (n, v) { vars[n] = v; parent.postMessage({ type: 'larch:set', name: n, value: v }, '*'); },
    get: function (n, dflt) { return (n in vars && vars[n] !== '' && vars[n] != null) ? vars[n] : dflt; },
    script: function () { try { return JSON.parse(values.script || '{}'); } catch (e) { return {}; } },
    done: function () { if (finished) return; finished = true; parent.postMessage({ type: 'larch:complete' }, '*'); },
    /* 點畫面（#tap）、空白鍵、Enter 都算一次「按」；按鈕自己的點擊不算 */
    press: function (fn) {
      pressFns.push(fn);
      var tap = document.getElementById('tap');
      if (tap) tap.addEventListener('pointerdown', function () { fn(); });
    }
  };
})();
