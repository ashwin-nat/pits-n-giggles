import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync, readFileSync, readdirSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { syncSegments } from "./sync-segments";

function makeTempDir(): string {
  return mkdtempSync(join(tmpdir(), "sync-segments-test-"));
}

test("copies every .json file from source to dest and returns the count", () => {
  const sourceDir = makeTempDir();
  const destDir = join(makeTempDir(), "nested", "dest");
  try {
    writeFileSync(join(sourceDir, "Monaco.json"), JSON.stringify({ circuit_number: 5 }));
    writeFileSync(join(sourceDir, "Monza.json"), JSON.stringify({ circuit_number: 6 }));

    const count = syncSegments(sourceDir, destDir);

    assert.equal(count, 2);
    assert.deepEqual(readdirSync(destDir).sort(), ["Monaco.json", "Monza.json"]);
    assert.equal(
      readFileSync(join(destDir, "Monaco.json"), "utf-8"),
      JSON.stringify({ circuit_number: 5 })
    );
  } finally {
    rmSync(sourceDir, { recursive: true, force: true });
    rmSync(destDir, { recursive: true, force: true });
  }
});

test("creates the destination directory when it does not exist", () => {
  const sourceDir = makeTempDir();
  const destDir = join(makeTempDir(), "does", "not", "exist", "yet");
  try {
    writeFileSync(join(sourceDir, "Baku.json"), "{}");

    assert.equal(existsSync(destDir), false);
    syncSegments(sourceDir, destDir);
    assert.equal(existsSync(destDir), true);
  } finally {
    rmSync(sourceDir, { recursive: true, force: true });
    rmSync(destDir, { recursive: true, force: true });
  }
});

test("skips non-.json files", () => {
  const sourceDir = makeTempDir();
  const destDir = makeTempDir();
  try {
    writeFileSync(join(sourceDir, "Baku.json"), "{}");
    writeFileSync(join(sourceDir, "README.md"), "not a segment file");

    const count = syncSegments(sourceDir, destDir);

    assert.equal(count, 1);
    assert.deepEqual(readdirSync(destDir), ["Baku.json"]);
  } finally {
    rmSync(sourceDir, { recursive: true, force: true });
    rmSync(destDir, { recursive: true, force: true });
  }
});

test("throws on an empty source directory instead of silently syncing nothing", () => {
  const sourceDir = makeTempDir();
  const destDir = makeTempDir();
  try {
    assert.throws(() => syncSegments(sourceDir, destDir), /No \.json files found/);
  } finally {
    rmSync(sourceDir, { recursive: true, force: true });
    rmSync(destDir, { recursive: true, force: true });
  }
});

test("throws when the source directory has files but none are .json", () => {
  const sourceDir = makeTempDir();
  const destDir = makeTempDir();
  try {
    writeFileSync(join(sourceDir, "README.md"), "not a segment file");
    assert.throws(() => syncSegments(sourceDir, destDir), /No \.json files found/);
  } finally {
    rmSync(sourceDir, { recursive: true, force: true });
    rmSync(destDir, { recursive: true, force: true });
  }
});

test("throws when the source directory does not exist", () => {
  const sourceDir = join(makeTempDir(), "does-not-exist");
  const destDir = makeTempDir();
  try {
    assert.throws(() => syncSegments(sourceDir, destDir));
  } finally {
    rmSync(destDir, { recursive: true, force: true });
  }
});
