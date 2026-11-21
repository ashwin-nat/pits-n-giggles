import { test } from "node:test";
import assert from "node:assert/strict";
import { formulaRules } from "./formulas";

test("F1 26 has active aero and overtake, no DRS", () => {
  const r = formulaRules("F1 26");
  assert.deepEqual([r.drs, r.activeAero, r.overtake, r.yearInName], [false, true, true, true]);
});

test("F2 and every other formula have DRS only", () => {
  for (const f of ["F2", "F2 2021", "F1 Modern", "F1 Classic", "F1", "Unknown (255)", ""]) {
    const r = formulaRules(f);
    assert.deepEqual([r.drs, r.activeAero, r.overtake], [true, false, false], f);
  }
  assert.equal(formulaRules("f2 2021").name, "F2");
  assert.equal(formulaRules("F1 Modern").name, "F1");
});

test("a formula that is not F1 or F2 keeps its own name and gets the F1 marks", () => {
  const r = formulaRules("Supercars");
  assert.equal(r.name, "Supercars");
  assert.deepEqual([r.drs, r.activeAero, r.overtake], [true, false, false]);
});
