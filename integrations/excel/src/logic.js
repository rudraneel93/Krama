// Pure helpers for the PIM Excel add-in (no Office.js dependency; unit-tested with node).
"use strict";

const MAX_VALUES = 1000;

// Column letters for a 0-based column index: 0 -> A, 25 -> Z, 26 -> AA.
function columnLetter(index) {
  let s = "";
  let n = index + 1;
  while (n > 0) {
    const r = (n - 1) % 26;
    s = String.fromCharCode(65 + r) + s;
    n = Math.floor((n - 1) / 26);
  }
  return s;
}

function toNumber(v) {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string") {
    const t = v.trim().replace(/,/g, "");
    if (t !== "" && /^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$/.test(t)) return Number(t);
  }
  return null;
}

// Turn a selected single-column range into the values to check.
// values: 2-D array from Range.values; firstRow: 0-based sheet row of values[0].
// A non-numeric first cell is treated as a header. Blank cells are skipped (reported).
// Any other non-numeric cell is an error, because skipping it would hide a problem.
function extractColumn(values, firstRow) {
  if (!Array.isArray(values) || values.length === 0) return { error: "Select a column of numbers." };
  if (values.some((row) => row.length !== 1)) return { error: "Select a single column." };
  let start = 0;
  let header = null;
  if (toNumber(values[0][0]) === null && String(values[0][0]).trim() !== "") {
    header = String(values[0][0]);
    start = 1;
  }
  const numbers = [];
  const rows = [];
  const blanks = [];
  for (let i = start; i < values.length; i++) {
    const raw = values[i][0];
    if (raw === "" || raw === null) {
      blanks.push(firstRow + i);
      continue;
    }
    const v = toNumber(raw);
    if (v === null) return { error: `Row ${firstRow + i + 1} is not a number: ${JSON.stringify(raw)}` };
    numbers.push(v);
    rows.push(firstRow + i);
  }
  if (numbers.length < 4) return { error: "Select at least 4 numbers." };
  if (numbers.length > MAX_VALUES) return { error: `At most ${MAX_VALUES} numbers per check.` };
  return { header, numbers, rows, blanks };
}

// Map API breaks (indices into numbers) to sheet cells.
function breakCells(breaks, rows, columnIndex) {
  const col = columnLetter(columnIndex);
  return breaks.map((b) => ({
    address: `${col}${rows[b.index] + 1}`,
    row: rows[b.index],
    kind: b.kind,
    actual: b.actual,
    expected: b.expected,
    message: b.kind === "jump"
      ? `Sequence jumps here: ${b.actual}, rule expects ${b.expected}`
      : `Wrong value: ${b.actual}, rule expects ${b.expected}`,
  }));
}

function summarize(result) {
  if (result.status === "follows_rule") return `Every row follows the rule ${result.rule}.`;
  if (result.status === "no_rule") return "No rule found. PIM checks rules such as constant steps, " +
    "constant ratios, polynomials, recurrences and repeating cycles.";
  const n = result.breaks.length;
  return `${n} row${n === 1 ? "" : "s"} break${n === 1 ? "s" : ""} the rule ${result.rule}.`;
}

if (typeof module !== "undefined") {
  module.exports = { columnLetter, toNumber, extractColumn, breakCells, summarize, MAX_VALUES };
}
