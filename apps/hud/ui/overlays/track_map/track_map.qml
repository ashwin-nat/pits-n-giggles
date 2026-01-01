import QtQuick
import QtQuick.Window

Window {
    id: root
    visible: false          // BaseOverlayQML will turn it visible

    // Base dimensions that will be scaled
    property real baseWidth: 400
    property real baseHeight: 400
    property real scaleFactor: 1.0 // will be updated/set in ctor

    width: baseWidth * scaleFactor
    height: baseHeight * scaleFactor
    color: "transparent"

    // Property to receive SVG path from Python
    property string svgPath: ""

    Rectangle {
        id: container
        anchors.fill: parent
        color: "transparent"

        Image {
            id: trackImage
            anchors.centerIn: parent
            width: Math.min(parent.width * 0.95, parent.height * 0.95)
            height: width
            fillMode: Image.PreserveAspectFit
            smooth: true
            antialiasing: true
            source: root.svgPath
            visible: root.svgPath !== ""
            antialiasing: true

            // Fallback if image fails to load
            onStatusChanged: {
                if (status === Image.Error) {
                    Log.debug("Failed to load track map: " + root.svgPath)
                }
            }
        }

        // Placeholder text when no track is loaded
        Text {
            anchors.centerIn: parent
            text: "No Track Loaded"
            color: "#666666"
            font.pixelSize: 16 * root.scaleFactor
            visible: root.svgPath === ""
        }
    }
}
