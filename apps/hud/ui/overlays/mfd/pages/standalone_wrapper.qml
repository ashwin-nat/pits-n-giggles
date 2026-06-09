import QtQuick
import QtQuick.Window

Window {
    id: root
    visible: true
    color: "black"
    property real scaleFactor: 1.0
    property url  pageSource:  ""
    property bool showTitleBar: false
    property string titleText:  ""

    readonly property int baseWidth:      400
    readonly property int baseHeight:     220
    readonly property int titleBarHeight: 20

    width:  Math.round(baseWidth * scaleFactor)
    height: Math.round((baseHeight + (showTitleBar ? titleBarHeight : 0)) * scaleFactor)

    Item {
        anchors.fill: parent
        scale: root.scaleFactor
        transformOrigin: Item.TopLeft

        Rectangle {
            visible: root.showTitleBar
            width:   root.baseWidth
            height:  root.titleBarHeight
            color:   Qt.rgba(0, 0, 0, 0.3)

            Rectangle {
                anchors.left:   parent.left
                anchors.right:  parent.right
                anchors.bottom: parent.bottom
                height: 2
                color:  "#FF0000"
            }

            Text {
                width:  root.baseWidth
                height: root.titleBarHeight
                text:   root.titleText
                color:              "#FF0000"
                font.family:        "Formula1"
                font.pixelSize:     13
                font.bold:          true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment:   Text.AlignVCenter
            }
        }

        Loader {
            objectName: "pageContent"
            y:      root.showTitleBar ? root.titleBarHeight : 0
            width:  baseWidth
            height: baseHeight
            source: root.pageSource
        }
    }
}
