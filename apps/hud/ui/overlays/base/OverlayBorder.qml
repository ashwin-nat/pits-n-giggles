// Injected at runtime by BaseOverlay when the overlay is in unlocked mode.
// Parented to the root window's contentItem.
// Shows a dashed border + four corner drag handles.
import QtQuick

Item {
    id: unlockOverlay
    anchors.fill: parent

    // Corner handle size in logical pixels.
    // NOTE: This is the single source of truth for the handle size; the Python
    // side reads this property from the unlockOverlay item instead of
    // hard-coding a constant, so visuals and hit-testing stay in sync.
    readonly property int handleSize: 18
    readonly property color accentColor: "#E10600"
    readonly property color borderColor: "#E10600"
    readonly property real borderOpacity: 0.85

    // Dashed border drawn as four thin rectangles
    Rectangle {
        id: topEdge
        x: 0; y: 0
        width: parent.width; height: 2
        color: unlockOverlay.borderColor
        opacity: unlockOverlay.borderOpacity
    }
    Rectangle {
        id: bottomEdge
        x: 0; y: parent.height - 2
        width: parent.width; height: 2
        color: unlockOverlay.borderColor
        opacity: unlockOverlay.borderOpacity
    }
    Rectangle {
        id: leftEdge
        x: 0; y: 0
        width: 2; height: parent.height
        color: unlockOverlay.borderColor
        opacity: unlockOverlay.borderOpacity
    }
    Rectangle {
        id: rightEdge
        x: parent.width - 2; y: 0
        width: 2; height: parent.height
        color: unlockOverlay.borderColor
        opacity: unlockOverlay.borderOpacity
    }

    // Corner handles - solid filled squares to make grab zones obvious
    Rectangle {
        id: tlHandle
        x: 0; y: 0
        width: unlockOverlay.handleSize; height: unlockOverlay.handleSize
        color: unlockOverlay.accentColor
        opacity: 0.9
        radius: 2
    }
    Rectangle {
        id: trHandle
        x: parent.width - unlockOverlay.handleSize; y: 0
        width: unlockOverlay.handleSize; height: unlockOverlay.handleSize
        color: unlockOverlay.accentColor
        opacity: 0.9
        radius: 2
    }
    Rectangle {
        id: blHandle
        x: 0; y: parent.height - unlockOverlay.handleSize
        width: unlockOverlay.handleSize; height: unlockOverlay.handleSize
        color: unlockOverlay.accentColor
        opacity: 0.9
        radius: 2
    }
    Rectangle {
        id: brHandle
        x: parent.width - unlockOverlay.handleSize; y: parent.height - unlockOverlay.handleSize
        width: unlockOverlay.handleSize; height: unlockOverlay.handleSize
        color: unlockOverlay.accentColor
        opacity: 0.9
        radius: 2
    }
}
