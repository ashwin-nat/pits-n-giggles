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
    readonly property int titleBarHeight: 40

    /* ---------- PAGE CONTROL ---------- */
    property url currentPageQml: ""
    property bool collapsed: false   // SET FROM PYTHON

    // Get title from loaded page
    readonly property string pageTitle: pageLoader.item && pageLoader.item.title !== undefined ? pageLoader.item.title : ""
    readonly property bool showTitleBar: pageTitle.length > 0 && !collapsed

    width: baseWidth * scaleFactor
    height: (collapsed ? baseHeightCollapsed : (baseHeightExpanded + (showTitleBar ? titleBarHeight : 0))) * scaleFactor

    Item {
        id: scaledRoot
        anchors.fill: parent

        // Scale the entire content
        scale: root.scaleFactor
        transformOrigin: Item.TopLeft

        // Title Bar
        Rectangle {
            id: titleBar
            x: 0
            y: 0
            width: baseWidth
            height: titleBarHeight
            color: Qt.rgba(0, 0, 0, 0.3)
            visible: showTitleBar

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 2
                color: "#FF0000"
            }

            Text {
                x: 0
                y: 0
                width: baseWidth
                height: titleBarHeight
                text: pageTitle
                color: "#FF0000"
                font.family: "Formula1"
                font.pixelSize: 13
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        Loader {
            id: pageLoader
            objectName: "pageLoader"
            width: baseWidth
            height: collapsed ? baseHeightCollapsed : baseHeightExpanded
            anchors.top: showTitleBar ? titleBar.bottom : parent.top
            source: root.currentPageQml
        }
    }
}