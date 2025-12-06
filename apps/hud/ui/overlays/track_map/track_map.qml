import QtQuick
import QtQuick.Window

Window {
    id: root
    visible: false          // BaseOverlayQML will turn it visible
    width: 400
    height: 400
    color: "transparent"        // Dark background for track visibility

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

            // Fallback if image fails to load
            onStatusChanged: {
                if (status === Image.Error) {
                    console.log("Failed to load track map: " + root.svgPath)
                }
            }
        }

        // Placeholder text when no track is loaded
        Text {
            anchors.centerIn: parent
            text: "Waiting for session"
            color: "#666666"
            font.pixelSize: 16
            visible: root.svgPath === ""
        }
    }
}
