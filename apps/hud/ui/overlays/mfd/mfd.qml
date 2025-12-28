import QtQuick
import QtQuick.Window

Window {
    id: root
    visible: true
    color: "black"

    /* ---------- SCALING ---------- */
    property real scaleFactor: 1.0
    readonly property int baseWidth: 400
    readonly property int baseHeightExpanded: 220
    readonly property int baseHeightCollapsed: 36

    /* ---------- PAGE CONTROL ---------- */
    property url currentPageQml: ""
    property bool collapsed: false   // SET FROM PYTHON

    width: baseWidth * scaleFactor
    height: (collapsed ? baseHeightCollapsed : baseHeightExpanded) * scaleFactor

    Item {
        id: scaledRoot
        anchors.fill: parent

        // Scale the entire content
        scale: root.scaleFactor
        transformOrigin: Item.TopLeft

        Loader {
            id: pageLoader
            objectName: "pageLoader"
            width: baseWidth
            height: collapsed ? baseHeightCollapsed : baseHeightExpanded
            source: root.currentPageQml
        }
    }
}
