// ListModel driven by lib/table_differ.TableDiffer on the Python side.
//
// Python writes one property per table -- the payload returned by
// TableDiffer.update() -- and this model turns it into ListModel operations:
//   { kind: "reset", rows: [row, ...] }           -> clear() + append() each
//   { kind: "patch", rows: [{index, row}, ...] }  -> set(index, row) each
//
// One property means one write per tick however many rows moved, and a reset can
// never overtake patches produced before it. The "reset"/"patch" strings are
// TableDiffer.RESET / TableDiffer.PATCH.
//
// The point is that set() re-renders only the affected delegate, whereas
// re-assigning a view's model destroys and re-creates all of them. Views bind
// `model:` to this object and read row fields as delegate roles.
//
// Three constraints inherited from ListModel (dynamicRoles is off - it is slow):
//   - roles are fixed by the first append(), so every row must carry the same
//     key set with the same value types; pad optional fields rather than
//     omitting them, and don't mix e.g. a QML color with a Python "#rrggbb".
//   - keys must be valid property names, so no hyphens.
//   - rows must be flat. An array-valued field becomes a nested ListModel that
//     delegates bind to by object identity, and set() does not reliably reach
//     it - flatten such rows into one field per cell instead.
import QtQuick

ListModel {
    id: tableModel

    // Latest payload from TableDiffer.update(). Null until the first one lands.
    property var tableUpdate: null

    onTableUpdateChanged: {
        if (!tableUpdate || !tableUpdate.rows)
            return;

        if (tableUpdate.kind === "reset") {
            clear();
            for (let i = 0; i < tableUpdate.rows.length; ++i)
                append(tableUpdate.rows[i]);
            return;
        }

        // Patches only ever apply to the table they were diffed against. One
        // aimed at a stale or empty model is dropped; Python re-syncs by calling
        // TableDiffer.invalidate() whenever the QML target is re-created.
        for (let i = 0; i < tableUpdate.rows.length; ++i) {
            const patch = tableUpdate.rows[i];
            if (patch && patch.row !== undefined && patch.index >= 0 && patch.index < count)
                set(patch.index, patch.row);
        }
    }
}
