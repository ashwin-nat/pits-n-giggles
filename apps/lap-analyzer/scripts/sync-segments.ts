// Copies assets/track-segments/*.json from the main repo into
// src/assets/segments/, so LocalFileProvider.getTrackSections() can read a
// local asset with no network call and no runtime dependency on the main
// app's directory layout. Run via `pnpm sync-segments` whenever the main
// repo's track-segment data changes. See lap-analyzer-provider-spec.md's
// "Bundled Segments Asset" section.
import { readdirSync, copyFileSync, mkdirSync } from "node:fs";
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

function main(): void {
  const moduleDir = dirname(fileURLToPath(import.meta.url));
  const sourceDir = join(moduleDir, "..", "..", "..", "assets", "track-segments");
  const destDir = join(moduleDir, "..", "src", "assets", "segments");

  const count = syncSegments(sourceDir, destDir);
  console.log(`Synced ${count} track segment file(s) from ${sourceDir} to ${destDir}`);
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  main();
}
