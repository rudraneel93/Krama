"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const L = require("../src/logic.js");

test("column letters", () => {
  assert.deepEqual([0, 1, 25, 26, 27, 51, 52, 701, 702].map(L.columnLetter),
    ["A", "B", "Z", "AA", "AB", "AZ", "BA", "ZZ", "AAA"]);
});

test("numbers from cells", () => {
  assert.equal(L.toNumber(5), 5);
  assert.equal(L.toNumber("1,250.50"), 1250.5);
  assert.equal(L.toNumber(" -3e2 "), -300);
  assert.equal(L.toNumber("12abc"), null);
  assert.equal(L.toNumber(NaN), null);
  assert.equal(L.toNumber(true), null);
});

test("header, blanks and row mapping", () => {
  const vals = [["Invoice"], [1001], [1002], [""], [1004], [1005], ["1006"]];
  const c = L.extractColumn(vals, 4); // selection starts on sheet row 5
  assert.equal(c.header, "Invoice");
  assert.deepEqual(c.numbers, [1001, 1002, 1004, 1005, 1006]);
  assert.deepEqual(c.rows, [5, 6, 8, 9, 10]);
  assert.deepEqual(c.blanks, [7]);
  const cells = L.breakCells([{ index: 2, kind: "jump", actual: 1004, expected: 1003 }], c.rows, 2);
  assert.equal(cells[0].address, "C9");
  assert.match(cells[0].message, /jumps/);
});

test("errors instead of silently skipping", () => {
  assert.match(L.extractColumn([[1, 2], [3, 4]], 0).error, /single column/);
  assert.match(L.extractColumn([[1], ["n/a"], [3], [4], [5]], 0).error, /Row 2 is not a number/);
  assert.match(L.extractColumn([[1], [2]], 0).error, /at least 4/);
  assert.match(L.extractColumn(Array.from({ length: 1001 }, (_, i) => [i]), 0).error, /At most/);
});

test("summaries", () => {
  assert.match(L.summarize({ status: "follows_rule", rule: "a[n] = a[n-1] + 1", breaks: [] }), /Every row/);
  assert.match(L.summarize({ status: "rule_with_breaks", rule: "r", breaks: [{}, {}] }), /2 rows break/);
  assert.match(L.summarize({ status: "no_rule", breaks: [] }), /No rule found/);
});
