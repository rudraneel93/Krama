/* global Office, Excel, extractColumn, breakCells, summarize */
"use strict";

// Same origin as the add-in: the site serves the add-in and proxies /api to the PIM API.
const DEFAULT_URL = window.location.origin + "/api";
const HIGHLIGHT = "#FFD8A8"; // Krama saffron
let lastHighlights = []; // { sheet, address, previousColor }

function store(k, v) {
  try {
    if (v === undefined) return localStorage.getItem(k);
    localStorage.setItem(k, v);
  } catch (e) {
    return null;
  }
  return null;
}

function el(id) { return document.getElementById(id); }

function show(nodes) {
  const r = el("result");
  r.replaceChildren(...nodes);
}

function text(tag, s, cls) {
  const n = document.createElement(tag);
  n.textContent = s;
  if (cls) n.className = cls;
  return n;
}

async function callCheck(numbers) {
  const key = store("pim_key");
  if (!key) throw new Error("Add your API key under Settings.");
  const url = (store("pim_url") || DEFAULT_URL).replace(/\/+$/, "");
  const resp = await fetch(`${url}/v1/check`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-API-Key": key },
    body: JSON.stringify({ values: numbers }),
  });
  const body = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const e = (body && body.error) || {};
    throw new Error(e.message ? `${e.message} (${resp.status})` : `Request failed (${resp.status})`);
  }
  return body;
}

async function clearHighlights() {
  if (!lastHighlights.length) return;
  await Excel.run(async (ctx) => {
    for (const h of lastHighlights) {
      const cell = ctx.workbook.worksheets.getItem(h.sheet).getRange(h.address);
      if (h.previousColor && h.previousColor !== "#FFFFFF") cell.format.fill.color = h.previousColor;
      else cell.format.fill.clear();
    }
    await ctx.sync();
  });
  lastHighlights = [];
  el("clear").disabled = true;
}

async function runCheck() {
  el("check").disabled = true;
  show([text("p", "Checking…")]);
  try {
    await clearHighlights();
    await Excel.run(async (ctx) => {
      const range = ctx.workbook.getSelectedRange();
      range.load("values,rowIndex,columnIndex");
      const sheet = range.worksheet;
      sheet.load("name");
      await ctx.sync();
      const col = extractColumn(range.values, range.rowIndex);
      if (col.error) {
        show([text("p", col.error, "error")]);
        return;
      }
      const result = await callCheck(col.numbers);
      const cells = breakCells(result.breaks, col.rows, range.columnIndex);
      const fills = cells.map((c) => {
        const cell = sheet.getRange(c.address);
        cell.format.fill.load("color");
        return { cell, c };
      });
      await ctx.sync();
      for (const { cell, c } of fills) {
        lastHighlights.push({ sheet: sheet.name, address: c.address, previousColor: cell.format.fill.color });
        cell.format.fill.color = HIGHLIGHT;
      }
      await ctx.sync();

      const nodes = [text("p", summarize(result))];
      if (result.rule) {
        nodes.push(text("p", result.rule, "rule"));
        if (result.explanation) nodes.push(text("p", result.explanation, "hint"));
      }
      if (cells.length) {
        const ul = document.createElement("ul");
        for (const c of cells) {
          const li = document.createElement("li");
          const a = text("a", c.address);
          a.addEventListener("click", () => Excel.run(async (x) => {
            x.workbook.worksheets.getItem(sheet.name).getRange(c.address).select();
            await x.sync();
          }));
          li.append(a, document.createTextNode(`: ${c.message}`));
          ul.append(li);
        }
        nodes.push(ul);
      }
      if (col.blanks.length) nodes.push(text("p", `${col.blanks.length} blank cell(s) skipped.`, "hint"));
      show(nodes);
      el("clear").disabled = lastHighlights.length === 0;
    });
  } catch (e) {
    show([text("p", e.message || String(e), "error")]);
  } finally {
    el("check").disabled = false;
  }
}

Office.onReady((info) => {
  if (info.host !== Office.HostType.Excel) return;
  el("key").value = store("pim_key") || "";
  el("url").value = store("pim_url") || DEFAULT_URL;
  el("check").disabled = false;
  el("check").addEventListener("click", runCheck);
  el("clear").addEventListener("click", () => clearHighlights().catch((e) => show([text("p", e.message, "error")])));
  el("save").addEventListener("click", () => {
    store("pim_key", el("key").value.trim());
    store("pim_url", el("url").value.trim());
    show([text("p", "Saved.")]);
  });
});
