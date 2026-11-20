import { test } from "node:test";
import assert from "node:assert/strict";
import { labelFits, sectionCode, sectionViewport } from "./sectionStrip";
import type { TrackSection } from "../types/api";

const section = (label: string, cornerNumbers: number[]): TrackSection => ({
  label,
  distanceStart: 0,
  distanceEnd: 100,
  type: cornerNumbers.length > 0 ? "corner" : "straight",
  cornerNumbers,
});

test("sectionCode: turn numbers for corners, the label for straights", () => {
  assert.equal(sectionCode(section("Rettifilo", [1])), "T1");
  assert.equal(sectionCode(section("Variante", [1, 2])), "T1-2");
  assert.equal(sectionCode(section("Main straight", [])), "Main straight");
});

test("labelFits needs more room for longer text", () => {
  assert.equal(labelFits(3, "T1"), true);
  assert.equal(labelFits(2, "T1"), false);
  assert.equal(labelFits(3, "T11-13"), false);
  assert.equal(labelFits(6, "T11-13"), true);
});

test("sectionViewport pads 10% each side and clamps at zero", () => {
  assert.deepEqual(sectionViewport(1000, 1200), { distanceStart: 980, distanceEnd: 1220 });
  assert.deepEqual(sectionViewport(10, 110), { distanceStart: 0, distanceEnd: 120 });
});
