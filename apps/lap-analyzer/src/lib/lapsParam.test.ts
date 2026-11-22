import { test } from "node:test";
import assert from "node:assert/strict";
import { parseLapsParam } from "./lapsParam";

test("parses refs in order, A first", () => {
  assert.deepEqual(parseLapsParam("race-a~21~2,race-a~16~2"), [
    { sessionId: "race-a", driverIndex: 21, lapNumber: 2 },
    { sessionId: "race-a", driverIndex: 16, lapNumber: 2 },
  ]);
});

test("drops junk and duplicates", () => {
  assert.deepEqual(parseLapsParam("race-a~21~2,race-a~21~2,../x~1~1,race-b~3~x,race-b~~,a~1~2~3,solo,"), [
    { sessionId: "race-a", driverIndex: 21, lapNumber: 2 },
  ]);
});

test("empty without a param, and capped at A plus three comparison laps", () => {
  assert.deepEqual(parseLapsParam(null), []);
  assert.equal(parseLapsParam("s~1~1,s~1~2,s~1~3,s~1~4,s~1~5").length, 4);
});
