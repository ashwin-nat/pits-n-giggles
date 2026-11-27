// Root window for every overlay. Children declared in an OverlayWindow go into contentLayer.
// BaseOverlay writes the overlay's opacity to contentOpacity and uses window opacity only to fade,
// so the unlock border (a sibling of contentLayer) always draws at full alpha.
import QtQuick
import QtQuick.Window

Window {
    id: win
    color: "transparent"

    property real contentOpacity: 1.0
    // Use this instead of the window color, which content opacity does not reach
    property color backgroundColor: "transparent"
    default property alias content: contentLayer.data

    Item {
        id: contentLayer
        anchors.fill: parent
        opacity: win.contentOpacity
        // Group opacity, as window opacity was; off at 100% so the render path is unchanged
        layer.enabled: win.contentOpacity < 1.0

        Rectangle {
            anchors.fill: parent
            color: win.backgroundColor
            z: -1
        }
    }
}
