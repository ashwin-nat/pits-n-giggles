// The hierarchical sensor tree behind the Sensors popover: dotted manifest
// keys become groups, every level toggles, partial groups read as indeterminate.
// Pure, for sensorTree.test.ts.
import type { SensorDefinition } from "../types/api";

export interface GroupNode {
  kind: "group";
  segment: string;
  displayName: string;
  children: TreeNode[];
}
export interface LeafNode {
  kind: "leaf";
  sensor: SensorDefinition;
}
export type TreeNode = GroupNode | LeafNode;

const POSITION_SEGMENTS = new Set(["fl", "fr", "rl", "rr"]);

export function segmentDisplayName(segment: string): string {
  if (POSITION_SEGMENTS.has(segment.toLowerCase())) {
    return segment.toUpperCase();
  }
  return segment
    .split("_")
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

// Splits each dotted key on "." -- the first segment is the group, later
// segments are subgroups, the last is the leaf.
export function buildSensorTree(manifest: readonly SensorDefinition[]): TreeNode[] {
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

export function collectKeys(node: TreeNode): string[] {
  return node.kind === "leaf" ? [node.sensor.key] : node.children.flatMap(collectKeys);
}

// Keeps the leaves whose label or key contains `query`, and the groups on the way to them.
export function filterTree(nodes: readonly TreeNode[], query: string): TreeNode[] {
  const q = query.trim().toLowerCase();
  if (q === "") {
    return [...nodes];
  }
  const out: TreeNode[] = [];
  for (const node of nodes) {
    if (node.kind === "leaf") {
      if (node.sensor.label.toLowerCase().includes(q) || node.sensor.key.toLowerCase().includes(q)) {
        out.push(node);
      }
    } else if (node.displayName.toLowerCase().includes(q)) {
      out.push(node);
    } else {
      const children = filterTree(node.children, query);
      if (children.length > 0) {
        out.push({ ...node, children });
      }
    }
  }
  return out;
}

export function toggleKeys(selected: readonly string[], keys: readonly string[], select: boolean): string[] {
  return select ? Array.from(new Set([...selected, ...keys])) : selected.filter((k) => !keys.includes(k));
}

export type CheckState = "checked" | "unchecked" | "partial";

export function checkState(keys: readonly string[], selected: ReadonlySet<string>): CheckState {
  const count = keys.filter((k) => selected.has(k)).length;
  return count === 0 ? "unchecked" : count === keys.length ? "checked" : "partial";
}

// Sensor presets by top-level group, in the popover's preset buttons.
export const SENSOR_PRESETS: Record<string, string[]> = {
  Driving: ["speed", "throttle", "brake", "gear", "steering"],
  Braking: ["speed", "brake", "gear", "front_brake_bias"],
  Minimal: ["speed", "throttle", "brake"],
};

export const DEFAULT_PRESET = "Driving";

export function presetKeys(manifest: readonly SensorDefinition[], groups: readonly string[]): string[] {
  // In the preset's own order, so the lanes open as listed.
  return groups.flatMap((group) => manifest.filter((s) => s.key.split(".")[0] === group).map((s) => s.key));
}

// The union of every lap's manifest, first definition wins.
export function unionManifest(manifests: readonly (readonly SensorDefinition[] | undefined)[]): SensorDefinition[] {
  const seen = new Map<string, SensorDefinition>();
  for (const manifest of manifests) {
    for (const sensor of manifest ?? []) {
      if (!seen.has(sensor.key)) {
        seen.set(sensor.key, sensor);
      }
    }
  }
  return [...seen.values()];
}

// For each sensor in the union: the slots whose lap lacks it. A slot with no
// manifest (not picked yet) is left out of the count.
export function missingSlots(manifests: readonly (readonly SensorDefinition[] | undefined)[]): Map<string, number[]> {
  const missing = new Map<string, number[]>();
  for (const sensor of unionManifest(manifests)) {
    missing.set(
      sensor.key,
      manifests.flatMap((m, slot) => (m !== undefined && !m.some((s) => s.key === sensor.key) ? [slot] : []))
    );
  }
  return missing;
}
