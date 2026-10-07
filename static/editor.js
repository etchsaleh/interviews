/* Editor + runner UI shared by the problem page and the playground. */
var PracticeEditor = (function () {
  "use strict";

  function store(key, value) {
    try {
      if (value === undefined) return localStorage.getItem(key);
      if (value === null) localStorage.removeItem(key);
      else localStorage.setItem(key, value);
    } catch (e) { /* storage unavailable: work without persistence */ }
    return null;
  }

  // Wraps CodeMirror if it loaded from the CDN, otherwise a plain textarea.
  function createEditor(textarea, onRun) {
    if (window.CodeMirror) {
      var cm = CodeMirror.fromTextArea(textarea, {
        mode: "python", lineNumbers: true, indentUnit: 4, tabSize: 4,
        matchBrackets: true, viewportMargin: Infinity,
        extraKeys: {
          "Tab": function (cm) {
            if (cm.somethingSelected()) cm.indentSelection("add");
            else cm.replaceSelection("    ", "end");
          },
          "Shift-Tab": function (cm) { cm.indentSelection("subtract"); },
          "Ctrl-Enter": onRun, "Cmd-Enter": onRun,
          "Ctrl-/": "toggleComment", "Cmd-/": "toggleComment"
        }
      });
      return {
        get: function () { return cm.getValue(); },
        set: function (v) { cm.setValue(v); },
        onChange: function (fn) { cm.on("change", fn); }
      };
    }
    textarea.classList.add("plain-editor");
    textarea.addEventListener("keydown", function (e) {
      if (e.key === "Tab") {
        e.preventDefault();
        var s = textarea.selectionStart;
        textarea.setRangeText("    ", s, textarea.selectionEnd, "end");
      } else if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        onRun();
      }
    });
    return {
      get: function () { return textarea.value; },
      set: function (v) { textarea.value = v; },
      onChange: function (fn) { textarea.addEventListener("input", fn); }
    };
  }

  // Render JSON values the way Python would print them (None/True/False, 'str').
  function pyRepr(v) {
    if (v === null || v === undefined) return "None";
    if (v === true) return "True";
    if (v === false) return "False";
    if (typeof v === "string") return JSON.stringify(v);
    if (typeof v === "number") return String(v);
    if (Array.isArray(v)) return "[" + v.map(pyRepr).join(", ") + "]";
    return "{" + Object.keys(v).map(function (k) { return JSON.stringify(k) + ": " + pyRepr(v[k]); }).join(", ") + "}";
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function block(label, text, cls) {
    var wrap = el("div", "kv");
    wrap.appendChild(el("span", "k", label));
    wrap.appendChild(el("pre", "v " + (cls || ""), text));
    return wrap;
  }

  function callText(entry, input, needsBaseUrl) {
    var args = input.map(pyRepr);
    if (needsBaseUrl) args.unshift("base_url");
    return entry + "(" + args.join(", ") + ")";
  }

  function post(url, body) {
    return fetch(url, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body)
    }).then(function (r) {
      if (!r.ok) throw new Error("Server returned " + r.status);
      return r.json();
    });
  }

  function setupTabs() {
    document.querySelectorAll(".tab").forEach(function (tab) {
      tab.addEventListener("click", function () {
        document.querySelectorAll(".tab").forEach(function (t) { t.classList.toggle("active", t === tab); });
        document.querySelectorAll(".tab-panel").forEach(function (p) {
          p.hidden = p.id !== "tab-" + tab.dataset.tab;
        });
      });
    });
  }

  function renderError(results, report) {
    results.innerHTML = "";
    results.appendChild(el("div", "summary fail", "Your code did not run"));
    results.appendChild(el("pre", "error", report.error));
    if (report.stdout) results.appendChild(block("stdout", report.stdout));
  }

  function initProblemPage(problem) {
    var results = document.getElementById("results");
    var runBtn = document.getElementById("btn-run");
    var key = "code:" + problem.id;
    var entry = (problem.starter.match(/^(?:def|class)\s+(\w+)/m) || [])[1] || "solve";
    var isClass = /^class\s/m.test(problem.starter);

    // Tests tab
    var preview = document.getElementById("test-preview");
    problem.tests.forEach(function (t) {
      var li = el("li");
      li.appendChild(el("code", "", isClass ? pyRepr(t.input[0]) + "\n" + pyRepr(t.input[1]) : callText(entry, t.input, problem.needs_base_url)));
      li.appendChild(el("div", "muted small", "expected → " + (t.expected_label || pyRepr(t.expected))));
      preview.appendChild(li);
    });
    setupTabs();

    var editor = createEditor(document.getElementById("code"), run);
    editor.set(store(key) || problem.starter);
    // Timer: starts on the first edit, stops when every test passes.
    var usedSolution = false;
    var bestKey = "best:" + problem.id;
    var bestEl = document.getElementById("timer-best");
    var timer = PracticeTimer.create({
      key: "timer:" + problem.id,
      clock: document.getElementById("timer-clock"),
      toggle: document.getElementById("timer-toggle"),
      reset: document.getElementById("timer-reset"),
      targetSeconds: problem.target_minutes * 60
    });
    function showBest() {
      var best = store(bestKey);
      bestEl.textContent = best ? "· best " + PracticeTimer.format(+best) : "";
    }
    showBest();
    editor.onChange(function () {
      store(key, editor.get());
      timer.start();
    });

    document.getElementById("btn-reset").addEventListener("click", function () {
      if (confirm("Start over? This restores the starter code and resets the timer.")) {
        editor.set(problem.starter);
        store(key, null);
        timer.reset();
        usedSolution = false;
      }
    });
    document.getElementById("btn-solution").addEventListener("click", function () {
      if (!confirm("Show the reference solution? It replaces your code in the editor (Ctrl/Cmd+Z undoes it).")) return;
      fetch("/api/solution/" + problem.id).then(function (r) { return r.json(); }).then(function (data) {
        usedSolution = true;
        editor.set(data.solution);
      });
    });

    function run() {
      runBtn.disabled = true;
      runBtn.textContent = "Running…";
      results.innerHTML = "<p class='muted'>Running…</p>";
      post("/api/run", { id: problem.id, code: editor.get() }).then(function (report) {
        if (!report.ok) return renderError(results, report);
        results.innerHTML = "";
        var allPassed = report.passed === report.total;
        var summary = el("div", "summary " + (allPassed ? "pass" : "fail"),
          (allPassed ? "All tests passed " : "Passed ") + report.passed + " / " + report.total);
        results.appendChild(summary);
        if (allPassed) {
          store("solved:" + problem.id, "1");
          timer.stop();
          var secs = Math.round(timer.elapsed());
          if (!usedSolution && secs > 0) {
            var best = store(bestKey);
            if (!best || secs < +best) store(bestKey, String(secs));
            showBest();
          }
          summary.textContent += usedSolution ? " (solution shown — time not recorded)"
            : " in " + PracticeTimer.format(secs) + (secs <= problem.target_minutes * 60 ? " — under target" : " — over target, redo it later");
        }
        if (report.stdout) results.appendChild(block("stdout (module level)", report.stdout));

        report.cases.forEach(function (c, i) {
          var d = el("details", "case " + (c.passed ? "pass" : "fail"));
          if (!c.passed) d.open = true;
          d.appendChild(el("summary", "", (c.passed ? "✓ " : "✗ ") + "Test " + (i + 1) + "  ·  " + c.ms + " ms"));
          var input = isClass ? pyRepr(c.input[0]) + "\n" + pyRepr(c.input[1]) : callText(entry, c.input, problem.needs_base_url);
          d.appendChild(block("call", input));
          d.appendChild(block("expected", c.expected_label || pyRepr(c.expected)));
          if (c.error) d.appendChild(block("error", c.error, "error"));
          else d.appendChild(block("returned", pyRepr(c.actual)));
          if (c.stdout) d.appendChild(block("stdout", c.stdout));
          results.appendChild(d);
        });
        if (report.stderr) results.appendChild(block("stderr", report.stderr, "error"));
      }).catch(function (err) {
        results.innerHTML = "";
        results.appendChild(el("pre", "error", String(err)));
      }).finally(function () {
        runBtn.disabled = false;
        runBtn.textContent = "Run tests";
      });
    }
    runBtn.addEventListener("click", run);
  }

  function initPlayground(baseUrl) {
    var starter = [
      "import requests",
      "",
      "BASE_URL = " + JSON.stringify(baseUrl),
      "",
      "nums = [5, 3, 8, 1]",
      "print(sorted(nums), sum(nums), max(nums))",
      "",
      "resp = requests.get(f\"{BASE_URL}/users\", params={\"team\": \"platform\"}, timeout=5)",
      "print(resp.status_code)",
      "for user in resp.json():",
      "    print(user[\"name\"], user[\"email\"])",
      ""
    ].join("\n");
    var key = "code:playground";
    var results = document.getElementById("results");
    var runBtn = document.getElementById("btn-run");
    var editor = createEditor(document.getElementById("code"), run);
    editor.set(store(key) || starter);
    editor.onChange(function () { store(key, editor.get()); });
    document.getElementById("btn-reset").addEventListener("click", function () {
      if (confirm("Reset the playground?")) { editor.set(starter); store(key, null); }
    });

    function run() {
      runBtn.disabled = true;
      results.innerHTML = "<p class='muted'>Running…</p>";
      post("/api/run", { id: "playground", code: editor.get() }).then(function (report) {
        if (!report.ok) return renderError(results, report);
        results.innerHTML = "";
        results.appendChild(block("output", report.stdout || "(no output — use print())"));
        if (report.stderr) results.appendChild(block("stderr", report.stderr, "error"));
      }).catch(function (err) {
        results.innerHTML = "";
        results.appendChild(el("pre", "error", String(err)));
      }).finally(function () { runBtn.disabled = false; });
    }
    runBtn.addEventListener("click", run);
  }

  return { initProblemPage: initProblemPage, initPlayground: initPlayground };
})();
