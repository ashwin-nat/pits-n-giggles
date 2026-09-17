import { useMemo } from "react";
import { useSessions } from "../hooks/useSessions";
import { useTelemetryStore } from "../store/telemetryStore";
import type { SensorDefinition } from "../types/api";
import type { SelectionState } from "../types/store";

interface SensorSelectorProps {
  selection: SelectionState;
  onChange: (patch: Partial<SelectionState>) => void;
  disabled: boolean;
}

interface GroupNode {
  kind: "group";
  segment: string;
  displayName: string;
  children: TreeNode[];
}
interface LeafNode {
  kind: "leaf";
  sensor: SensorDefinition;
}
type TreeNode = GroupNode | LeafNode;

const POSITION_SEGMENTS = new Set(["fl", "fr", "rl", "rr"]);

function segmentDisplayName(segment: string): string {
  if (POSITION_SEGMENTS.has(segment.toLowerCase())) {
    return segment.toUpperCase();
  }
  return segment
    .split("_")
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

// Splits each dotted manifest key on "." -- first segment is the group,
// subsequent segments are subgroups/leaf, per the frontend spec's tree mock.
function buildSensorTree(manifest: SensorDefinition[]): TreeNode[] {
  const root: TreeNode[] = [];
  for (const sensor of manifest) {
    const segments = sensor.key.split(".");
    let siblings = root;
    for (let i = 0; i < segments.length - 1; i++) {
      const segment = segments[i];
      let group = siblings.find((n): n is GroupNode => n.kind === "group" && n.segment === segment);
      if (group === undefined) {
        group = { kind: "group", segment, displayName: segmentDisplayName(segment), children: [] };
        siblings.push(group);
      }
      siblings = group.children;
    }
    siblings.push({ kind: "leaf", sensor });
  }
  return root;
}

function collectKeys(node: TreeNode): string[] {
  if (node.kind === "leaf") {
    return [node.sensor.key];
  }
  return node.children.flatMap(collectKeys);
}

// Frontend-owned grouping of manifest top-level groups into the spec's four
// preset buttons -- the real dotted sensor keys are still being settled by
// Phase 7's F1SensorMapper, so update this list once that lands. "All" needs
// no entry; it always means every sensor in the manifest.
// TODO: evaluate if we really want these presets here
// TODO: if so, review this
const PRESET_GROUPS: Record<"Basics" | "Tyres" | "Engine", string[]> = {
  Basics: ["speed", "throttle", "brake", "gear", "drs", "steering", "clutch"],
  Tyres: ["tyre_temp", "tyre_wear", "tyre_pressure", "tyre_damage"],
  Engine: ["engine_rpm", "engine_temperature", "ers", "fuel", "front_brake_bias"],
};

function keysForPreset(manifest: SensorDefinition[], groups: string[]): string[] {
  return manifest.filter((s) => groups.includes(s.key.split(".")[0])).map((s) => s.key);
}

interface TreeRowProps {
  node: TreeNode;
  depth: number;
  selected: Set<string>;
  unavailableInReference: Set<string>;
  onToggle: (keys: string[], select: boolean) => void;
}

function TreeRow({ node, depth, selected, unavailableInReference, onToggle }: TreeRowProps) {
  const keys = useMemo(() => collectKeys(node), [node]);
  const checkedCount = keys.filter((k) => selected.has(k)).length;
  const allChecked = checkedCount === keys.length;
  const someChecked = checkedCount > 0 && !allChecked;
  const label = node.kind === "leaf" ? node.sensor.label : node.displayName;
  const warn = node.kind === "leaf" && unavailableInReference.has(node.sensor.key);

  return (
    <div style={{ paddingLeft: depth * 12 }}>
      <label className="flex items-center gap-1 text-xs text-slate-200">
        <input
          type="checkbox"
          checked={allChecked}
          ref={(el) => {
            if (el !== null) {
              el.indeterminate = someChecked;
            }
          }}
          onChange={(e) => onToggle(keys, e.target.checked)}
        />
        {label}
        {warn && <span title="Not available in the reference session">⚠ not in reference session</span>}
      </label>
      {node.kind === "group" &&
        node.children.map((child) => (
          <TreeRow
            key={child.kind === "leaf" ? child.sensor.key : child.segment}
            node={child}
            depth={depth + 1}
            selected={selected}
            unavailableInReference={unavailableInReference}
            onToggle={onToggle}
          />
        ))}
    </div>
  );
}

// Only rendered for variant="primary" -- both laps share the primary
// session's sensor selection (see SelectionPanel).
export function SensorSelector({ selection, onChange, disabled }: SensorSelectorProps) {
  const { data: sessions } = useSessions();
  const referenceSessionId = useTelemetryStore((state) => state.reference?.sessionId ?? null);

  const session = sessions?.find((s) => s.id === selection.sessionId);
  const referenceSession = sessions?.find((s) => s.id === referenceSessionId);
  const manifest = session?.sensorManifest ?? [];

  const unavailableInReference = useMemo(() => {
    if (referenceSession === undefined) {
      return new Set<string>();
    }
    const referenceKeys = new Set(referenceSession.sensorManifest.map((s) => s.key));
    return new Set(manifest.filter((s) => !referenceKeys.has(s.key)).map((s) => s.key));
  }, [manifest, referenceSession]);

  const tree = useMemo(() => buildSensorTree(manifest), [manifest]);
  const selected = useMemo(() => new Set(selection.sensors), [selection.sensors]);

  function toggle(keys: string[], select: boolean) {
    const next = select
      ? Array.from(new Set([...selection.sensors, ...keys]))
      : selection.sensors.filter((k) => !keys.includes(k));
    onChange({ sensors: next });
  }

  function applyPreset(name: "Basics" | "Tyres" | "Engine" | "All") {
    const keys = name === "All" ? manifest.map((s) => s.key) : keysForPreset(manifest, PRESET_GROUPS[name]);
    onChange({ sensors: keys });
  }

  if (disabled) {
    return (
      <div className="rounded border border-dashed border-slate-800 p-2 text-xs text-slate-600 opacity-40">
        Select a lap first
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2 rounded border border-slate-700 bg-slate-800/40 p-2">
      <div className="flex gap-1">
        {(["Basics", "Tyres", "Engine", "All"] as const).map((name) => (
          <button
            key={name}
            type="button"
            onClick={() => applyPreset(name)}
            className="rounded bg-slate-700 px-2 py-0.5 text-xs text-slate-100 hover:bg-slate-600"
          >
            {name}
          </button>
        ))}
      </div>
      <div className="flex flex-col gap-1">
        {tree.map((node) => (
          <TreeRow
            key={node.kind === "leaf" ? node.sensor.key : node.segment}
            node={node}
            depth={0}
            selected={selected}
            unavailableInReference={unavailableInReference}
            onToggle={toggle}
          />
        ))}
      </div>
    </div>
  );
}
