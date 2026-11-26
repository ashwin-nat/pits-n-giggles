// Injected at runtime by BaseOverlay when the overlay is in unlocked mode.
// Parented to the root window's contentItem.
// Shows a dashed border + four corner drag handles, and the overlay's name on hover.
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
    property string overlayName: ""

    property bool nameShown: false

    HoverHandler {
        id: hover
        onHoveredChanged: {
            if (hovered) {
                nameDelay.restart()
            } else {
                nameDelay.stop()
                unlockOverlay.nameShown = false
            }
        }
    }

    Timer {
        id: nameDelay
        interval: 700
        onTriggered: {
            nameLabel.placeAt(hover.point.position)
            unlockOverlay.nameShown = true
        }
    }

    // Takes no input, so covering a corner handle does not block a resize
    Rectangle {
        id: nameLabel
        readonly property int margin: 4
        readonly property int cursorGap: 16

        // Below-right of the cursor, flipped above or left where it would leave the window
        function placeAt(p) {
            const maxX = unlockOverlay.width - width - margin
            const maxY = unlockOverlay.height - height - margin
            const nx = p.x + cursorGap <= maxX ? p.x + cursorGap : p.x - cursorGap - width
            const ny = p.y + cursorGap <= maxY ? p.y + cursorGap : p.y - cursorGap - height
            x = Math.max(margin, Math.min(nx, maxX))
            y = Math.max(margin, Math.min(ny, maxY))
        }

        width: Math.min(nameText.implicitWidth + 20, parent.width - 2 * margin)
        height: nameText.implicitHeight + 10
        radius: 4
        color: "#CC000000"
        border.color: unlockOverlay.accentColor
        border.width: 1
        visible: unlockOverlay.nameShown && unlockOverlay.overlayName !== "" && width > 0

        Text {
            id: nameText
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 10
            verticalAlignment: Text.AlignVCenter
            text: unlockOverlay.overlayName
            color: "white"
            font.family: "Formula1"
            font.pixelSize: 18
            elide: Text.ElideRight
        }
    }

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
