import { test } from "node:test";
import assert from "node:assert/strict";
import { saveViewerSessionUrl } from "./saveViewerLink";

test("builds the lap telemetry url from the slug", () => {
  assert.equal(saveViewerSessionUrl({ sessionSlug: "abc-123" }), "/save-viewer/sessions/abc-123?tab=lap-telemetry");
});

test("escapes the slug", () => {
  assert.equal(saveViewerSessionUrl({ sessionSlug: "a/b c" }), "/save-viewer/sessions/a%2Fb%20c?tab=lap-telemetry");
});

test("is null without a slug", () => {
  for (const session of [undefined, {}, { sessionSlug: null }, { sessionSlug: "" }]) {
    assert.equal(saveViewerSessionUrl(session), null);
  }
});
