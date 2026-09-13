// Throwaway manual smoke-test for LocalFileProvider -- no UI exists yet at
// this phase. Loads a Phase 1 fixture, exercises every interface method,
// logs the results for eyeballing. Run via `pnpm dev:manual-test`.
// Delete or leave in place once Phase 4/5 UI exists to exercise this code
// visually/interactively instead.
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { LocalFileProvider } from "../providers/LocalFileProvider";
import { PngtError } from "../lib/pngtErrors";

const moduleDir = dirname(fileURLToPath(import.meta.url));
const FIXTURE_PATH = join(moduleDir, "..", "..", "test-fixtures", "sample-session.pngt");

async function main(): Promise<void> {
  const bytes = readFileSync(FIXTURE_PATH);
  const file = new File([bytes], "sample-session.pngt");
  const provider = new LocalFileProvider(file);

  console.log("capabilities:", provider.capabilities);

  const sessions = await provider.getSessions();
  console.log("\ngetSessions():", JSON.stringify(sessions, null, 2));

  const session = sessions[0];
  const drivers = await provider.getDrivers(session.id);
  console.log(`\ngetDrivers(): ${drivers.length} driver(s)`);
  console.log(JSON.stringify(drivers, null, 2));

  for (const driver of drivers) {
    const laps = await provider.getLaps(session.id, driver.index);
    console.log(`\ngetLaps(driver ${driver.index} / ${driver.name}): ${laps.length} lap(s)`);

    const completedLap = laps.find((l) => l.lapTime !== null);
    if (completedLap === undefined) {
      continue;
    }

    const sensorKeys = session.sensorManifest.slice(0, 3).map((s) => s.key);
    const telemetry = await provider.getTelemetry(session.id, driver.index, completedLap.lapNumber, sensorKeys);
    console.log(
      `  getTelemetry(lap ${completedLap.lapNumber}, sensors [${sensorKeys.join(", ")}]): ${telemetry.length} point(s)`
    );
    console.log("  first point:", telemetry[0]);
    console.log("  last point:", telemetry[telemetry.length - 1]);
  }

  const sections = await provider.getTrackSections(session.trackId);
  console.log(`\ngetTrackSections(trackId ${session.trackId}): ${sections.length} section(s)`);
  console.log(JSON.stringify(sections.slice(0, 3), null, 2));
}

main().catch((err) => {
  if (err instanceof PngtError) {
    console.error(`PngtError: ${err.message}`);
  } else {
    console.error(err);
  }
  process.exitCode = 1;
});
