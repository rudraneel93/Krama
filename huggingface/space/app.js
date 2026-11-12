"use strict";
(function () {
  const API = "https://getkrama.vercel.app/api/v1/demo/check";
  const NS = "http://www.w3.org/2000/svg";
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (s) => document.querySelector(s);
  const el = (t, c, x) => { const n = document.createElement(t); if (c) n.className = c; if (x != null) n.textContent = x; return n; };
  const svg = (t, a, p) => { const n = document.createElementNS(NS, t); for (const k in a) n.setAttribute(k, a[k]); if (p) p.append(n); return n; };
  const sleep = (ms) => new Promise((r) => setTimeout(r, reduce ? 0 : ms));
  const fmt = (n) => Number(n).toLocaleString("en-US");
  function toast(m) { const t = $("#toast"); t.textContent = m; t.classList.add("show"); clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove("show"), 3500); }

  async function check(values) {
    let r;
    try {
      r = await fetch(API, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ values }) });
    } catch (e) { throw new Error("Couldn't reach Krama. Please try again in a moment."); }
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error((d.error && d.error.message) || "Something went wrong.");
    return d;
  }

  const PLAIN = [
    [/^a\[n\] = a\[n-1\] \+ (.+)$/, (m) => `Each number = the one before + ${m[1]}`],
    [/^a\[n\] = a\[n-1\] - (.+)$/, (m) => `Each number = the one before − ${m[1]}`],
    [/^a\[n\] = (\S+)\*a\[n-1\]$/, (m) => `Each number = the one before × ${m[1]}`],
    [/^a\[n\] = (\S+)\*a\[n-1\] ([+-]) (.+)$/, (m) => `Each number = the one before × ${m[1]} ${m[2] === "+" ? "+" : "−"} ${m[3]}`],
    [/^a\[n\] = a\[n-(\d)\]$/, (m) => `The pattern repeats every ${m[1]} numbers`],
    [/^a\[n\] = a\[n-1\] \+ a\[n-2\]$/, () => "Each number = the two before it added together"],
  ];
  const plain = (rule, ex) => { if (!rule) return ""; for (const [re, f] of PLAIN) { const m = rule.match(re); if (m) return f(m); } return ex || rule; };
  const asNum = (x) => (typeof x === "string" && x.includes("/") ? x.split("/").reduce((a, b) => +a / +b) : +x);

  // ---------------- tabs ----------------
  function moveInk() {
    const a = $(".tab.active"), ink = $(".tab-ink");
    ink.style.left = a.offsetLeft + "px"; ink.style.width = a.offsetWidth + "px";
  }
  function showTab(name) {
    document.querySelectorAll(".tab").forEach((t) => { const on = t.dataset.tab === name; t.classList.toggle("active", on); t.setAttribute("aria-selected", on); });
    document.querySelectorAll(".panel").forEach((p) => { p.hidden = p.dataset.panel !== name; });
    moveInk();
    if (name === "board") drawBoard();
    if (name === "game" && !game.started) startGame();
  }

  // ---------------- try it ----------------
  const EX = {
    invoices: Array.from({ length: 24 }, (_, i) => 24001 + i).filter((v) => v !== 24013),
    fees: [500, 575, 650, 725, 800, 875, 950, 1025, 1100, 1175, 1250, 1352, 1400, 1475, 1550, 1625],
    double: (() => { const a = [3]; for (let i = 1; i < 14; i++) a.push(a[i - 1] * 2); a[8] = 769; return a; })(),
    cycle: Array.from({ length: 21 }, (_, i) => [12, 7, 30, 18, 22, 9, 15][i % 7]),
    random: [83, 12, 57, 91, 4, 66, 38, 75, 20, 49, 97, 31, 8, 62, 44, 15],
  };
  function drawChart(vals, res) {
    const c = $("#chart"); c.replaceChildren();
    const L = 14, R = 586, T = 18, B = 222;
    const defs = svg("defs", {}, c);
    const lg = svg("linearGradient", { id: "cg", x1: 0, x2: 1 }, defs);
    svg("stop", { offset: 0, "stop-color": "#2ef2c8" }, lg); svg("stop", { offset: 1, "stop-color": "#8b7cff" }, lg);
    const ag = svg("linearGradient", { id: "ca", x1: 0, x2: 0, y1: 0, y2: 1 }, defs);
    svg("stop", { offset: 0, "stop-color": "#2ef2c8", "stop-opacity": ".35" }, ag); svg("stop", { offset: 1, "stop-color": "#2ef2c8", "stop-opacity": "0" }, ag);
    for (let k = 0; k < 4; k++) svg("line", { x1: L, x2: R, y1: T + (k * (B - T)) / 3, y2: T + (k * (B - T)) / 3, class: "gl" }, c);
    const exp = vals.slice(), bad = new Set();
    if (res) res.breaks.forEach((b) => { exp[b.index] = asNum(b.expected); bad.add(b.index); });
    const all = vals.concat(exp), lo = Math.min(...all), hi = Math.max(...all), pad = (hi - lo) * 0.1 || 1;
    const x = (i) => L + (i * (R - L)) / Math.max(1, vals.length - 1), y = (v) => B - ((v - lo + pad) * (B - T)) / (hi - lo + 2 * pad);
    if (res && res.rule) {
      const d = "M" + exp.map((v, i) => `${x(i)},${y(v)}`).join(" L");
      svg("path", { d: d + ` L${x(vals.length - 1)},${B} L${x(0)},${B} Z`, class: "area" }, c);
      const p = svg("path", { d, class: "rl" }, c);
      if (!reduce) { const len = p.getTotalLength(); p.style.strokeDasharray = len; p.animate([{ strokeDashoffset: len }, { strokeDashoffset: 0 }], { duration: 1000, easing: "cubic-bezier(.6,0,.2,1)", fill: "forwards" }); }
    }
    vals.forEach((v, i) => {
      const dot = svg("circle", { cx: x(i), cy: y(v), r: 4.2, class: !res ? "pt" : !res.rule ? "pt" : bad.has(i) ? "pt bad" : "pt ok" }, c);
      if (!reduce) dot.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 300, delay: i * 14, fill: "both" });
      if (bad.has(i)) svg("circle", { cx: x(i), cy: y(v), r: 11, class: "ring" }, c);
    });
  }
  async function run() {
    const parts = $("#nums").value.split(/[\s,;]+/).filter(Boolean);
    const vals = parts.map((p) => Number(p.replace(/[_₹,]/g, "")));
    const bad = parts.find((p, i) => !Number.isFinite(vals[i]));
    if (bad) return toast(`“${bad}” isn't a number`);
    if (vals.length < 4) return toast("Enter at least 4 numbers");
    if (vals.length > 200) return toast("Up to 200 numbers here — the full app checks 1,000 at a time");
    const go = $("#go"); go.disabled = true; $("#meta").textContent = "Thinking…";
    drawChart(vals, null);
    const t0 = performance.now();
    try {
      const r = await check(vals);
      await sleep(Math.max(0, 420 - (performance.now() - t0)));
      drawChart(vals, r);
      const out = $("#out"); const nodes = [];
      if (r.status === "follows_rule") nodes.push(el("span", "badge ok", "Every number follows the rule"));
      else if (r.status === "rule_with_breaks") nodes.push(el("span", "badge bad", `${r.breaks.length} number${r.breaks.length > 1 ? "s break" : " breaks"} the rule`));
      else nodes.push(el("span", "badge none", "No rule found"));
      if (r.rule) { nodes.push(el("div", "plain", plain(r.rule, r.explanation))); nodes.push(el("div", "formula", r.rule)); }
      else nodes.push(el("p", "muted", "No common pattern fits these numbers — so Krama says so instead of inventing one."));
      if (r.breaks.length) {
        const ul = el("ul", "breaks");
        r.breaks.forEach((b, j) => {
          const li = el("li"); li.style.animationDelay = `${j * 90}ms`;
          li.append(document.createTextNode(`Number ${b.index + 1} is `), el("b", null, fmt(b.actual)), document.createTextNode(` — it should be ${fmt(asNum(b.expected))}` + (b.kind === "jump" ? " (something is missing or repeated here)" : "")));
          ul.append(li);
        });
        nodes.push(ul);
      }
      out.replaceChildren(...nodes);
      $("#meta").textContent = `${vals.length} numbers · ${Math.round(performance.now() - t0)} ms`;
    } catch (e) { toast(e.message); $("#meta").textContent = ""; }
    finally { go.disabled = false; }
  }

  // ---------------- game ----------------
  const game = { started: false, list: [], i: 0, score: 0, streak: 0, best: 0, locked: false };
  const ROUNDS = 10;
  async function startGame() {
    if (!game.all) game.all = await fetch("game.json").then((r) => r.json());
    const pool = game.all.slice().sort(() => Math.random() - 0.5);
    game.list = pool.slice(0, ROUNDS); game.i = 0; game.score = 0; game.streak = 0; game.started = true;
    $("#done").hidden = true; document.querySelector(".game-card").hidden = false;
    setScores(); showPuzzle();
  }
  function setScores(anim) {
    $("#score").textContent = game.score; $("#streak").textContent = game.streak; $("#round").textContent = Math.min(game.i + 1, ROUNDS);
    if (anim) ["#score", "#streak"].forEach((s) => { const n = $(s); n.classList.remove("bump"); void n.offsetWidth; n.classList.add("bump"); });
  }
  function showPuzzle() {
    const p = game.list[game.i]; game.locked = false;
    $("#reveal").replaceChildren(); $("#next").hidden = true;
    ["#allOk", "#noPat"].forEach((s) => { $(s).disabled = false; $(s).classList.remove("picked"); });
    $("#tiles").replaceChildren(...p.v.map((v, k) => {
      const t = el("button", "tile", fmt(v)); t.style.animationDelay = `${k * 35}ms`;
      t.addEventListener("click", () => answer({ type: "tile", index: k }, t)); return t;
    }));
  }
  async function answer(choice, node) {
    if (game.locked) return; game.locked = true;
    const p = game.list[game.i];
    if (node) node.classList.add("picked");
    document.querySelectorAll(".tile, .choice").forEach((b) => { b.disabled = true; });
    const right = choice.type === "tile" ? p.b.includes(choice.index)
      : choice.type === "ok" ? p.s === "follows_rule" : p.s === "no_rule";
    game.score += right ? 1 : 0; game.streak = right ? game.streak + 1 : 0; game.best = Math.max(game.best, game.streak);
    setScores(true);
    if (right && game.streak >= 3) confetti(18);
    // show the answer on the tiles
    const tiles = [...document.querySelectorAll(".tile")];
    tiles.forEach((t, k) => t.classList.add(p.b.includes(k) ? "ans" : p.s === "no_rule" ? "x" : "fine"));
    const rev = $("#reveal");
    const head = el("p", `verdict ${right ? "win" : "lose"}`, right ? pickOne(["Nailed it!", "Sharp eye!", "Exactly right!", "You beat the noise!"]) : "Not quite.");
    rev.replaceChildren(head, el("p", "why", "Krama is explaining…"));
    let why;
    try {
      const r = await check(p.v);
      const b = r.breaks[0];
      if (b) {
        tiles[b.index].append(el("span", "exp", `→ ${fmt(asNum(b.expected))}`));
        why = `Krama: ${plain(r.rule, r.explanation)}. Number ${b.index + 1} is ${fmt(b.actual)} but should be ${fmt(asNum(b.expected))}` + (b.kind === "jump" ? " — a value is missing or repeated there." : ".");
      } else if (r.rule) why = `Krama: ${plain(r.rule, r.explanation)} — every number fits.`;
      else why = p.c === "beyond"
        ? `This one follows a real rule (${familyName(p.f)}) — outside Krama's six rule families, so Krama itself says “no rule”. Rare cases like this are where people and some AI models can beat it.`
        : "Krama: no common pattern fits — these numbers are random. Many AI models invent a rule here anyway.";
    } catch (e) {
      why = p.s === "no_rule" ? "These numbers are random — there's no rule." : p.b.length ? `The broken number is #${p.b[0] + 1}.` : "Every number fits the rule.";
    }
    const w = el("p", "why"); w.textContent = why; rev.replaceChild(w, rev.lastChild);
    $("#next").hidden = false; $("#next").focus({ preventScroll: true });
  }
  const pickOne = (a) => a[Math.floor(Math.random() * a.length)];
  const familyName = (f) => ({ primes: "consecutive prime numbers", factorial: "factorial growth", catalan: "Catalan numbers", prime_squares: "squares of primes" }[f] || f);
  function nextPuzzle() {
    game.i += 1;
    if (game.i >= ROUNDS) return finish();
    setScores(); showPuzzle();
  }
  function finish() {
    document.querySelector(".game-card").hidden = true;
    const d = $("#done"); d.hidden = false;
    const s = game.score;
    $("#doneTitle").textContent = s >= 9 ? `🏆 ${s}/10 — pattern master!` : s >= 7 ? `🎯 ${s}/10 — great eye!` : s >= 4 ? `👀 ${s}/10 — not bad!` : `🤔 ${s}/10 — tricky, right?`;
    $("#doneText").textContent = `Best streak: ${game.best}. Krama checks thousands of numbers like these in a second — and never invents a pattern in random data.`;
    if (s >= 7) confetti(60);
  }
  function confetti(n) {
    if (reduce) return;
    const colors = ["#2ef2c8", "#5aa9ff", "#8b7cff", "#ff9f1c"];
    for (let i = 0; i < n; i++) {
      const c = el("i", "confetti"); c.style.left = Math.random() * 100 + "vw"; c.style.background = colors[i % 4];
      c.style.animationDuration = 1.6 + Math.random() * 1.6 + "s"; c.style.animationDelay = Math.random() * 0.3 + "s";
      document.body.append(c); setTimeout(() => c.remove(), 3800);
    }
  }

  // ---------------- leaderboard ----------------
  let board = null;
  async function drawBoard() {
    if (!board) board = await fetch("leaderboard.json").then((r) => r.json());
    const rows = board.results.slice().sort((a, b) => b.exact_accuracy - a.exact_accuracy);
    const pct = (x) => (x == null ? "—" : (x * 100).toFixed(1).replace(/\.0$/, "") + "%");
    const short = (n) => n.replace(" (PIM engine)", "").replace("Constant-step check (spreadsheet-style)", "Spreadsheet step check").replace("Always says 'follows a rule'", "Always “follows a rule”");
    const bars = (id, key, warm) => {
      $(id).replaceChildren(...rows.map((r) => {
        const row = el("div", "bar-row" + (r.system.startsWith("Krama") ? " kr" : ""));
        const tr = el("div", "track"), f = el("div", "fill" + (warm ? " warm" : ""));
        tr.append(f); row.append(el("span", "name", short(r.system)), tr, el("span", "val", pct(r[key])));
        requestAnimationFrame(() => requestAnimationFrame(() => { f.style.width = Math.max(1.5, r[key] * 100) + "%"; }));
        return row;
      }));
    };
    bars("#barsPhantom", "phantom_pattern_rate", true);
    bars("#barsExact", "exact_accuracy", false);
    $("#lb tbody").replaceChildren(...rows.map((r) => {
      const tr = el("tr", r.system.startsWith("Krama") ? "kr" : null);
      tr.append(el("td", null, short(r.system)), el("td", "num", pct(r.exact_accuracy)), el("td", "num", pct(r.phantom_pattern_rate)),
        el("td", "num", r.break_f1.toFixed(2)), el("td", "num", pct(r.clean_false_alarm_rate)), el("td", "num", pct(r.by_category.beyond)));
      return tr;
    }), (() => { const tr = el("tr"); const td = el("td", "muted", "Your model? Submit on the dataset page →"); td.colSpan = 6; tr.append(td); return tr; })());
  }

  // ---------------- wire up ----------------
  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => showTab(t.dataset.tab)));
    addEventListener("resize", moveInk); moveInk(); setTimeout(moveInk, 300);
    const setEx = (n) => { $("#nums").value = EX[n].join(", "); document.querySelectorAll(".chip").forEach((c) => c.classList.toggle("active", c.dataset.ex === n)); };
    setEx("invoices"); drawChart(EX.invoices, null);
    document.querySelectorAll(".chip").forEach((c) => c.addEventListener("click", () => { setEx(c.dataset.ex); run(); }));
    $("#go").addEventListener("click", run);
    $("#nums").addEventListener("keydown", (e) => { if ((e.metaKey || e.ctrlKey) && e.key === "Enter") run(); });
    $("#allOk").addEventListener("click", (e) => answer({ type: "ok" }, e.currentTarget));
    $("#noPat").addEventListener("click", (e) => answer({ type: "none" }, e.currentTarget));
    $("#next").addEventListener("click", nextPuzzle);
    $("#again").addEventListener("click", startGame);
    const h = location.hash.replace("#", ""); if (["try", "game", "board"].includes(h)) showTab(h);
  });
})();
