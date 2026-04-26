---
description: Scaffold a new MCP tool in apps/mcp_server/ with full wiring
allowed-tools: Read, Glob, Grep, Edit, Write
---

Add a new MCP tool to the Pits n' Giggles MCP server: create the tool module, wire it into the server, and validate the design against the existing patterns.

**You are expected to ask clarifying questions before writing any code.** Read the relevant parts of the codebase first, then ask. Do not guess at ambiguous design decisions.

---

## Input

The user must provide:
- **Tool name** in `snake_case` (becomes the MCP tool name, e.g. `get_fuel_info`)
- **What data the tool should return** — at minimum a description; ideally field names
- **Arguments** — names, types, whether optional or mandatory
- **Data source** — which IPC topic feeds the data (usually `race-table-update`; check with the user if unclear)

If the tool name or data description are missing, ask before proceeding.

---

## Questions to ask before coding

Stop and ask the user about any of the following that are unclear or ambiguous. One consolidated message is fine.

1. **Data source**: Is the data available in the cached `race-table-update` IPC snapshot, or does it require an HTTP call to the backend's `/driver-info` endpoint (or another endpoint)? Look at the relevant backend serialisation code and HUD overlay code to find out before asking — only ask if genuinely ambiguous.

2. **Index / reference driver**: If the tool is driver-specific:
   - Should `driver_index` be mandatory, or optional with a fallback to the player/reference driver?
   - If there should be a no-arg variant (always player/reference), consider splitting into two tools: one with a mandatory index and one (`get_player_<x>`) with no args. Ask the user whether they want this split.
   - In spectator mode, `get_ref_row` resolves to the spectated driver — confirm this is the right behaviour for the no-arg variant.

3. **Session-type sensitivity**: Do any fields only make sense in race sessions (e.g. surplus laps from a rolling burn model)? If so, how should they behave in practice/qualifying — return `null`, a different field, or a flag?

4. **Data sufficiency**: If computed fields require a minimum number of data points (e.g. ≥2 racing laps for a burn average), how should the tool signal that the data is not yet reliable? Options: `null` fields + a `data_sufficient: bool`, a top-level error, or an `available: false` response.

5. **Sentinel zeros**: The backend serialises missing recommender data as `0.0`, not `null`. Confirm whether `0.0` should be surfaced as-is or converted to `null` in the MCP response.

6. **Field names and units**: Confirm units for numeric fields (kg, %, ms, etc.) and whether the user wants them in the field name or only in the schema description.

7. **Schema strictness**: Should `additionalProperties` be `false` (strict) or `true` (allows forward-compatible extension)? Existing tools use `true` at the top level.

---

## Steps

Work through these in order. Read each target file before editing it.

### 1. Understand the data shape

Before writing anything:

- Read the backend serialisation method that produces the data (e.g. `getFuelStatsJSON`, `getCarDamageJSON`).
- Read the HUD overlay that consumes the same IPC topic to see which keys it reads and how it handles missing data.
- Read `apps/mcp_server/mcp_server/tools/common.py` to understand `_get_race_table_context` and `fetch_driver_info`.
- Read an existing similar tool (e.g. `get_race_table.py` for race-table-derived tools, `get_car_damage.py` for HTTP-derived tools) to confirm the pattern.

This reading phase informs the questions above. Do it first.

### 2. Decide: race-table snapshot vs HTTP fetch

**Race-table snapshot** (preferred when the data is present in `race-table-update`):
- Call `_get_race_table_context(logger)` to get `telemetry_update` and `base_rsp`.
- Walk `telemetry_update["table-entries"]` to find the target row, or call `get_ref_row(telemetry_update)` for the player/reference driver.
- No network call, no `async` required — the function can be a plain `def`.

**HTTP fetch** (when the data is only available via the backend REST API):
- Use `fetch_driver_info(core_server_port, logger, driver_index)` from `common.py`.
- The tool handler must be `async def` and receives `core_server_port` from `MCPBridge`.

### 3. Create the tool module — `apps/mcp_server/mcp_server/tools/get_<tool_name>.py`

Structure the file as:
1. MIT licence header (copy from any existing tool)
2. Imports
3. `<TOOL_NAME>_OUTPUT_SCHEMA` — JSON Schema dict describing the response
4. Public function `get_<tool_name>(logger, ...)` that returns `Dict[str, Any]`
5. Private helpers (`_find_row_by_index`, `_build_payload`, etc.) below the public function

**Output schema conventions:**
- Always include `"available"`, `"connected"`, `"ok"` in `properties` and `required`.
- Use `["type", "null"]` for any field that may be absent.
- Add a `"description"` string to numeric fields that need unit clarification.
- Set `"additionalProperties": True` at the top level.

**Response conventions:**
- Start from `base_rsp` returned by `_get_race_table_context` (or build an equivalent base dict for HTTP tools).
- Return early with `base_rsp` (unenriched) whenever data is unavailable.
- Set `"ok": True` only when the payload is fully populated.
- Use a clear `"error"` string on failure (e.g. `"No driver found with index 5."`).

**Shared logic**: If two tools (e.g. `get_fuel_info` and `get_player_fuel_info`) return the same shape, extract the payload builder into a private `_build_<x>_payload(base_rsp, row)` function in the indexed tool's module and import it from the no-arg sibling.

### 4. Register the tool — `apps/mcp_server/mcp_server/mcp_server.py`

Read the file. Make three edits:

**a) Import** — add to the import block, keeping it alphabetically ordered with the other tool imports:
```python
from .tools.get_<tool_name> import <TOOL_NAME>_OUTPUT_SCHEMA, get_<tool_name>
```

**b) Register** — inside `_register_tools`, add a `@self._tool(...)` block following the pattern of existing tools:
```python
@self._tool(
    name="get_<tool_name>",
    description="...",
    title="...",
    tags={...},
    output_schema=<TOOL_NAME>_OUTPUT_SCHEMA,
    annotations=ToolAnnotations(
        title="...",
        readOnlyHint=True,
        openWorldHint=False,
    ),
)
async def handle_get_<tool_name>(<args>) -> Dict[str, Any]:
    self.logger.debug("get_<tool_name> called: ...")
    return get_<tool_name>(...)
```

For race-table tools (plain `def`), the handler is still `async def` — just call the sync function directly without `await`.

**c) Typing imports** — if the handler signature introduces a new type (e.g. `Optional`), add it to the `from typing import ...` line. Remove any imports that are no longer used.

### 5. Verify

- Check that all imports resolve (no unused imports, no missing names).
- Confirm the output schema covers every field the function can return.
- Confirm `data_sufficient` or equivalent gating is consistent between the schema description and the actual logic.

---

## Summary

After completing all steps, report:
- Files created, with a one-line description of purpose
- Files modified, with a one-line description of what changed in each
