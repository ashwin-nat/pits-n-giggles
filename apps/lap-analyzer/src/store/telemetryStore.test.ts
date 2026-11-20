import { beforeEach, test } from "node:test";
import assert from "node:assert/strict";
import { useTelemetryStore } from "./telemetryStore";

const store = useTelemetryStore;
const lapOf = (sessionId: string, driverIndex: number, lapNumber: number) => ({ sessionId, driverIndex, lapNumber });

beforeEach(() => store.getState().reset());

test("setLap appends comparison laps up to three and ignores a fifth lap", () => {
  const s = store.getState();
  s.setLap(0, lapOf("s1", 0, 1));
  for (let slot = 1; slot <= 4; slot++) {
    store.getState().setLap(slot, lapOf("s1", slot, 1));
  }
  assert.equal(store.getState().laps.length, 4);
});

test("setLap cannot skip a slot", () => {
  store.getState().setLap(0, lapOf("s1", 0, 1));
  store.getState().setLap(2, lapOf("s1", 2, 1));
  assert.equal(store.getState().laps.length, 1);
});

test("changing A's session drops comparison laps, sensors and the viewport", () => {
  const s = store.getState();
  s.setLap(0, lapOf("s1", 0, 1));
  s.setLap(1, lapOf("s1", 1, 2));
  s.setSensors(["speed"]);
  s.setViewport({ distanceStart: 0, distanceEnd: 100 });
  store.getState().setLap(0, { sessionId: "s2", driverIndex: 3 });
  const next = store.getState();
  assert.deepEqual(next.laps, [{ sessionId: "s2", driverIndex: 3, lapNumber: null }]);
  assert.deepEqual(next.sensors, []);
  assert.equal(next.viewport, null);
});

test("changing A's driver keeps comparison laps and sensors", () => {
  const s = store.getState();
  s.setLap(0, lapOf("s1", 0, 1));
  s.setLap(1, lapOf("s1", 1, 2));
  s.setSensors(["speed"]);
  store.getState().setLap(0, { driverIndex: 5, lapNumber: null });
  assert.equal(store.getState().laps.length, 2);
  assert.deepEqual(store.getState().sensors, ["speed"]);
});

test("changing a comparison lap's session clears its stale driver and lap", () => {
  const s = store.getState();
  s.setLap(0, lapOf("s1", 0, 1));
  s.setLap(1, lapOf("s1", 1, 2));
  store.getState().setLap(1, { sessionId: "s2" });
  assert.deepEqual(store.getState().laps[1], { sessionId: "s2", driverIndex: null, lapNumber: null });
});

test("removeLap on a comparison slot shifts later laps up; on A it clears everything", () => {
  const s = store.getState();
  s.setLap(0, lapOf("s1", 0, 1));
  s.setLap(1, lapOf("s1", 1, 1));
  s.setLap(2, lapOf("s1", 2, 1));
  store.getState().removeLap(1);
  assert.deepEqual(store.getState().laps.map((l) => l.driverIndex), [0, 2]);
  store.getState().removeLap(0);
  assert.deepEqual(store.getState().laps, []);
});

test("moveLap swaps two slots", () => {
  const s = store.getState();
  s.setLap(0, lapOf("s1", 0, 1));
  s.setLap(1, lapOf("s1", 1, 1));
  store.getState().moveLap(1, 0);
  assert.deepEqual(store.getState().laps.map((l) => l.driverIndex), [1, 0]);
});

test("the old primary / reference view follows laps and sensors", () => {
  const s = store.getState();
  s.setPrimary({ sessionId: "s1", driverIndex: 0, lapNumber: 1, sensors: ["speed"] });
  assert.equal(store.getState().reference, null);
  store.getState().setReference({ sessionId: "s1", driverIndex: 2, lapNumber: 3 });
  const next = store.getState();
  assert.deepEqual(next.primary, { sessionId: "s1", driverIndex: 0, lapNumber: 1, sensors: ["speed"] });
  assert.deepEqual(next.reference, { sessionId: "s1", driverIndex: 2, lapNumber: 3, sensors: ["speed"] });
  store.getState().setReference(null);
  assert.equal(store.getState().reference, null);
});
