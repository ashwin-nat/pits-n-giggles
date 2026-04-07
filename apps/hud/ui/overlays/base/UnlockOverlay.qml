// Injected at runtime by BaseOverlayQML when the overlay is in unlocked mode.
// Parented to the root window's contentItem.
// Shows a dashed border + four corner drag handles.
import QtQuick

Item {
    id: unlockOverlay
    anchors.fill: parent

    // Corner handle size in logical pixels
    readonly property int handleSize: 18
    readonly property color accentColor: "#E10600"
    readonly property color borderColor: "#E10600"
    readonly property real borderOpacity: 0.85

    // Dashed border drawn as four thin rectangles
    Rectangle {
        id: topEdge
        x: 0; y: 0
        width: parent.width; height: 2
        color: borderColor
        opacity: borderOpacity
    }
    Rectangle {
        id: bottomEdge
        x: 0; y: parent.height - 2
        width: parent.width; height: 2
        color: borderColor
        opacity: borderOpacity
    }
    Rectangle {
        id: leftEdge
        x: 0; y: 0
        width: 2; height: parent.height
        color: borderColor
        opacity: borderOpacity
    }
    Rectangle {
        id: rightEdge
        x: parent.width - 2; y: 0
        width: 2; height: parent.height
        color: borderColor
        opacity: borderOpacity
    }

    // Corner handles - solid filled squares to make grab zones obvious
    Rectangle {
        id: tlHandle
        x: 0; y: 0
        width: handleSize; height: handleSize
        color: accentColor
        opacity: 0.9
        radius: 2
    }
    Rectangle {
        id: trHandle
        x: parent.width - handleSize; y: 0
        width: handleSize; height: handleSize
        color: accentColor
        opacity: 0.9
        radius: 2
    }
    Rectangle {
        id: blHandle
        x: 0; y: parent.height - handleSize
        width: handleSize; height: handleSize
        color: accentColor
        opacity: 0.9
        radius: 2
    }
    Rectangle {
        id: brHandle
        x: parent.width - handleSize; y: parent.height - handleSize
        width: handleSize; height: handleSize
        color: accentColor
        opacity: 0.9
        radius: 2
    }
}
