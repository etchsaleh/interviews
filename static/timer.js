/* A small stopwatch that survives page reloads (state kept in localStorage). */
var PracticeTimer = (function () {
  "use strict";

  function format(totalSeconds) {
    var s = Math.max(0, Math.floor(totalSeconds));
    var m = Math.floor(s / 60);
    return (m < 10 ? "0" : "") + m + ":" + (s % 60 < 10 ? "0" : "") + (s % 60);
  }

  function load(key) {
    try { return JSON.parse(localStorage.getItem(key)) || null; } catch (e) { return null; }
  }

  function save(key, value) {
    try {
      if (value === null) localStorage.removeItem(key);
      else localStorage.setItem(key, JSON.stringify(value));
    } catch (e) { /* no persistence available */ }
  }

  // opts: {key, clock, toggle, reset, targetSeconds, onChange}
  function create(opts) {
    var state = load(opts.key) || { elapsed: 0, startedAt: null };
    var interval = null;

    function elapsed() {
      return state.elapsed + (state.startedAt ? (Date.now() - state.startedAt) / 1000 : 0);
    }
    function running() { return state.startedAt !== null; }

    function render() {
      var e = elapsed();
      opts.clock.textContent = format(e);
      opts.clock.classList.toggle("over", e > opts.targetSeconds);
      opts.clock.classList.toggle("paused", !running() && e > 0);
      if (opts.toggle) opts.toggle.textContent = running() ? "❚❚" : "▶";
    }

    function start() {
      if (running()) return;
      state.startedAt = Date.now();
      save(opts.key, state);
      interval = setInterval(render, 500);
      render();
      if (opts.onChange) opts.onChange("start");
    }
    function stop() {
      if (!running()) return;
      state.elapsed = elapsed();
      state.startedAt = null;
      save(opts.key, state);
      clearInterval(interval);
      render();
    }
    function reset() {
      clearInterval(interval);
      state = { elapsed: 0, startedAt: null };
      save(opts.key, null);
      render();
      if (opts.onChange) opts.onChange("reset");
    }

    if (opts.toggle) opts.toggle.addEventListener("click", function () { running() ? stop() : start(); });
    if (opts.reset) opts.reset.addEventListener("click", reset);
    if (running()) interval = setInterval(render, 500);
    render();

    return { start: start, stop: stop, reset: reset, elapsed: elapsed, running: running };
  }

  return { create: create, format: format };
})();
