// ListModel driven by lib/table_differ.TableDiffer on the Python side.
//
// Python writes two root properties per table and this model turns them into
// the matching ListModel operations:
//   tableRows -> clear() + append() of every row  (whole-table reset)
//   rowPatch  -> set(index, row)                  (one row changed)
//
// The point is that set() re-renders only the one affected delegate, whereas
// re-assigning a view's model destroys and re-creates all of them. Views bind
// `model:` to this object and read row fields as delegate roles.
//
// Two constraints inherited from ListModel (dynamicRoles is off — it is slow):
//   - roles are fixed by the first append(), so every row must carry the same
//     key set; pad optional fields rather than omitting them.
//   - keys must be valid property names, so no hyphens.
import QtQuick

ListModel {
    id: tableModel

    // Whole table, as pushed by the differ's reset hook.
    property var tableRows: []

    // Latest single-row update: { index: int, row: object }.
    property var rowPatch: ({})

    onTableRowsChanged: {
        clear();
        if (!tableRows)
            return;
        for (let i = 0; i < tableRows.length; ++i)
            append(tableRows[i]);
    }

    // Patches only ever apply to the table they were diffed against. A patch
    // arriving against a stale/empty model is dropped; Python re-syncs by
    // calling TableDiffer.invalidate() whenever the QML target is re-created.
    onRowPatchChanged: {
        if (!rowPatch || rowPatch.row === undefined)
            return;
        if (rowPatch.index >= 0 && rowPatch.index < count)
            set(rowPatch.index, rowPatch.row);
    }
}
