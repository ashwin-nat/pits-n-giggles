import { useEffect, useMemo, useRef, useState } from "react";
import { useSessions } from "../../hooks/useSessions";
import { LAP_SLOT_LETTERS } from "../../lib/chartConstants";
import {
  buildSensorTree,
  checkState,
  collectKeys,
  DEFAULT_PRESET,
  filterTree,
  missingSlots,
  presetKeys,
  SENSOR_PRESETS,
  toggleKeys,
  unionManifest,
  type TreeNode,
} from "../../lib/sensorTree";
import { useTelemetryStore } from "../../store/telemetryStore";
import { isCompleteLap } from "../../types/store";
import { Popover } from "../ui/Popover";
import { listItemClass } from "../ui/surfaces";

interface TreeRowProps {
  node: TreeNode;
  depth: number;
  selected: ReadonlySet<string>;
  missing: ReadonlyMap<string, number[]>;
  onToggle: (keys: string[], select: boolean) => void;
}

function TreeRow({ node, depth, selected, missing, onToggle }: TreeRowProps) {
  const keys = useMemo(() => collectKeys(node), [node]);
  const state = checkState(keys, selected);
  const checkbox = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (checkbox.current !== null) {
      checkbox.current.indeterminate = state === "partial";
    }
  }, [state]);

  const label = node.kind === "leaf" ? node.sensor.label : node.displayName;
  const lacking = node.kind === "leaf" ? (missing.get(node.sensor.key) ?? []) : [];

  return (
    <div>
      <label className={`${listItemClass} cursor-pointer py-1 text-xs`} style={{ paddingLeft: 10 + depth * 14 }}>
        <input
          ref={checkbox}
          type="checkbox"
          checked={state === "checked"}
          onChange={(e) => onToggle(keys, e.target.checked)}
          className="accent-sky-500"
        />
        <span className={node.kind === "group" ? "font-medium text-tone-100" : "text-tone-200"}>{label}</span>
        {lacking.length > 0 && (
          <span className="ml-auto text-2xs text-tone-500">missing on {lacking.map((s) => LAP_SLOT_LETTERS[s]).join(", ")}</span>
        )}
      </label>
      {node.kind === "group" &&
        node.children.map((child) => (
          <TreeRow
            key={child.kind === "leaf" ? child.sensor.key : child.segment}
            node={child}
            depth={depth + 1}
            selected={selected}
            missing={missing}
            onToggle={onToggle}
          />
        ))}
    </div>
  );
}

// Header button with the lane count; opens the sensor tree. The tree lists
// every sensor any selected lap has, and notes the laps missing each one.
export function SensorsPopover() {
  const laps = useTelemetryStore((s) => s.laps);
  const sensors = useTelemetryStore((s) => s.sensors);
  const setSensors = useTelemetryStore((s) => s.setSensors);
  const { data: sessions } = useSessions();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  const manifests = laps.map((lap) =>
    isCompleteLap(lap) ? sessions?.find((s) => s.id === lap.sessionId)?.sensorManifest : undefined
  );
  const manifestKey = manifests.map((m) => m?.length ?? -1).join(",") + laps.map((l) => l.sessionId).join(",");
  const union = useMemo(() => unionManifest(manifests), [manifestKey, sessions]); // eslint-disable-line react-hooks/exhaustive-deps
  const missing = useMemo(() => missingSlots(manifests), [manifestKey, sessions]); // eslint-disable-line react-hooks/exhaustive-deps
  const tree = useMemo(() => filterTree(buildSensorTree(union), query), [union, query]);
  const selected = useMemo(() => new Set(sensors), [sensors]);

  const disabled = !isCompleteLap(laps[0]);

  return (
    <div className="relative">
      <button
        type="button"
        disabled={disabled}
        onClick={() => setOpen((o) => !o)}
        className="rounded-lg bg-tone-800 px-3 py-1.5 text-xs text-tone-100 hover:bg-tone-700 disabled:cursor-not-allowed disabled:opacity-40"
      >
        Sensors <span className="ml-1 rounded bg-tone-700 px-1.5 text-tone-300">{sensors.length}</span>
      </button>
      {open && !disabled && (
        <Popover onClose={() => setOpen(false)} className="right-0 top-full mt-2 w-[360px]">
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Find a sensor"
            className="mb-2 w-full rounded-lg bg-tone-800 px-3 py-1.5 text-xs text-tone-100 outline-none placeholder:text-tone-500"
          />
          <div className="mb-2 flex gap-1">
            {Object.entries(SENSOR_PRESETS).map(([name, groups]) => (
              <button
                key={name}
                type="button"
                onClick={() => setSensors(presetKeys(union, groups))}
                className="rounded-md bg-tone-800 px-2.5 py-1 text-2xs text-tone-200 hover:bg-tone-700"
              >
                {name}
              </button>
            ))}
            <button
              type="button"
              onClick={() => setSensors([])}
              className="ml-auto rounded-md px-2.5 py-1 text-2xs text-tone-400 hover:bg-tone-800"
            >
              Clear
            </button>
          </div>
          <div className="max-h-[55vh] overflow-y-auto">
            {tree.length === 0 ? (
              <p className="px-2.5 py-3 text-xs text-tone-500">No sensors match</p>
            ) : (
              tree.map((node) => (
                <TreeRow
                  key={node.kind === "leaf" ? node.sensor.key : node.segment}
                  node={node}
                  depth={0}
                  selected={selected}
                  missing={missing}
                  onToggle={(keys, select) => setSensors(toggleKeys(sensors, keys, select))}
                />
              ))
            )}
          </div>
        </Popover>
      )}
    </div>
  );
}

// Picks the default preset's sensors when a reference lap's session is first
// chosen and nothing is selected yet. Only on a session change, so clearing
// every sensor on purpose sticks.
export function useDefaultSensors() {
  const laps = useTelemetryStore((s) => s.laps);
  const sensors = useTelemetryStore((s) => s.sensors);
  const setSensors = useTelemetryStore((s) => s.setSensors);
  const { data: sessions } = useSessions();
  const handled = useRef<string | null>(null);

  const sessionId = isCompleteLap(laps[0]) ? laps[0].sessionId : null;
  useEffect(() => {
    if (sessionId === null) {
      handled.current = null;
      return;
    }
    const manifest = sessions?.find((s) => s.id === sessionId)?.sensorManifest;
    if (manifest === undefined || handled.current === sessionId) {
      return;
    }
    handled.current = sessionId;
    if (sensors.length === 0) {
      setSensors(presetKeys(manifest, SENSOR_PRESETS[DEFAULT_PRESET]));
    }
  }, [sessionId, sessions, sensors.length, setSensors]);
}
