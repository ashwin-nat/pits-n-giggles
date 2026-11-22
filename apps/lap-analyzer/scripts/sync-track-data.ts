// Copies the main repo's track data into src/assets/track-data/ so Vite bundles it:
// assets/track-segments/*.json -> track-data/segments/, assets/track-data/c<n>.npz -> track-data/.
// Track data is static reference data that ships with the app and is read from the bundle, not
// through the provider (see README, "Track data"). Run via `pnpm sync-track-data` whenever it changes.
import { readdirSync, readFileSync, copyFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

export function syncSegments(sourceDir: string, destDir: string): number {
  const jsonFiles = readdirSync(sourceDir).filter((file) => file.endsWith(".json"));
  if (jsonFiles.length === 0) {
    throw new Error(`No .json files found in source dir: ${sourceDir}`);
  }

  mkdirSync(destDir, { recursive: true });
  for (const file of jsonFiles) {
    copyFileSync(join(sourceDir, file), join(destDir, file));
  }
  return jsonFiles.length;
}

// Copies assets/track-data/c<n>.npz. Strict (release build): every circuit in the segment files must have
// a geometry file, else the build fails. Not strict (pnpm dev): a missing folder or file is skipped.
export function syncGeometry(
  sourceDir: string,
  destDir: string,
  segmentsDir: string,
  strict: boolean
): number {
  const files = existsSync(sourceDir) ? readdirSync(sourceDir).filter((f) => /^c\d+\.npz$/.test(f)) : [];
  if (strict) {
    const missing = readdirSync(segmentsDir)
      .filter((f) => f.endsWith(".json"))
      .map((f) => Number(JSON.parse(readFileSync(join(segmentsDir, f), "utf-8")).circuit_number))
      .filter((n) => !files.includes(`c${n}.npz`));
    if (missing.length > 0) {
      throw new Error(`No track geometry file in ${sourceDir} for circuit(s): ${missing.join(", ")}`);
    }
  }
  if (files.length === 0) {
    return 0;
  }
  mkdirSync(destDir, { recursive: true });
  for (const file of files) {
    copyFileSync(join(sourceDir, file), join(destDir, file));
  }
  return files.length;
}

function main(): void {
  const moduleDir = dirname(fileURLToPath(import.meta.url));
  const sourceDir = join(moduleDir, "..", "..", "..", "assets", "track-segments");
  const destDir = join(moduleDir, "..", "src", "assets", "track-data", "segments");

  const count = syncSegments(sourceDir, destDir);
  console.log(`Synced ${count} track segment file(s) from ${sourceDir} to ${destDir}`);

  const geometrySrc = join(moduleDir, "..", "..", "..", "assets", "track-data");
  const geometryDest = join(moduleDir, "..", "src", "assets", "track-data");
  const strict = process.argv.includes("--strict");
  const geometryCount = syncGeometry(geometrySrc, geometryDest, sourceDir, strict);
  console.log(`Synced ${geometryCount} track geometry file(s) from ${geometrySrc} to ${geometryDest}`);
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  main();
}
