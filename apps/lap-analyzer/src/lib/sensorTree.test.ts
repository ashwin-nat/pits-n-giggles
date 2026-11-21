import { test } from "node:test";
import assert from "node:assert/strict";
import {
  buildSensorTree,
  checkState,
  collectKeys,
  filterTree,
  missingSlots,
  presetKeys,
  SENSOR_PRESETS,
  toggleKeys,
  unionManifest,
} from "./sensorTree";
import type { SensorDefinition } from "../types/api";

const s = (key: string, label: string = key): SensorDefinition => ({ key, label, unit: "", type: "continuous" });
const manifest = [s("speed", "Speed"), s("tyre_temp.fl.inner", "Inner"), s("tyre_temp.fl.outer", "Outer"), s("tyre_temp.fr.inner", "Inner")];

test("buildSensorTree: dotted keys nest, wheel segments upper-case, plain keys are top-level leaves", () => {
  const tree = buildSensorTree(manifest);
  assert.equal(tree.length, 2);
  assert.equal(tree[0].kind, "leaf");
  const group = tree[1];
  assert.equal(group.kind, "group");
  if (group.kind === "group") {
    assert.equal(group.displayName, "Tyre Temp");
    assert.deepEqual(group.children.map((c) => (c.kind === "group" ? c.displayName : "leaf")), ["FL", "FR"]);
  }
});

test("collectKeys gathers every leaf under a group", () => {
  const tree = buildSensorTree(manifest);
  assert.deepEqual(collectKeys(tree[1]), ["tyre_temp.fl.inner", "tyre_temp.fl.outer", "tyre_temp.fr.inner"]);
});

test("toggleKeys selects and clears a whole group without duplicates", () => {
  const keys = ["tyre_temp.fl.inner", "tyre_temp.fl.outer"];
  assert.deepEqual(toggleKeys(["speed", "tyre_temp.fl.inner"], keys, true), ["speed", "tyre_temp.fl.inner", "tyre_temp.fl.outer"]);
  assert.deepEqual(toggleKeys(["speed", ...keys], keys, false), ["speed"]);
});

test("checkState: checked, partial (indeterminate) and unchecked", () => {
  const keys = ["a", "b"];
  assert.equal(checkState(keys, new Set(["a", "b"])), "checked");
  assert.equal(checkState(keys, new Set(["a"])), "partial");
  assert.equal(checkState(keys, new Set()), "unchecked");
});

test("filterTree keeps matching leaves with their groups, and a whole group on a group-name match", () => {
  const tree = buildSensorTree(manifest);
  const byLeaf = filterTree(tree, "outer");
  assert.deepEqual(byLeaf.flatMap(collectKeys), ["tyre_temp.fl.outer"]);
  const byGroup = filterTree(tree, "tyre");
  assert.equal(byGroup.flatMap(collectKeys).length, 3);
  assert.equal(filterTree(tree, "").length, 2);
});

test("presetKeys picks every sensor under the listed top-level groups", () => {
  assert.deepEqual(presetKeys(manifest, SENSOR_PRESETS.Driving), ["speed"]);
  assert.equal(presetKeys(manifest, ["tyre_temp"]).length, 3);
});

test("unionManifest and missingSlots name the laps that lack each sensor", () => {
  const a = [s("speed"), s("gear")];
  const b = [s("speed")];
  assert.deepEqual(unionManifest([a, undefined, b]).map((x) => x.key), ["speed", "gear"]);
  const missing = missingSlots([a, undefined, b]);
  assert.deepEqual(missing.get("gear"), [2]);
  assert.deepEqual(missing.get("speed"), []);
});
