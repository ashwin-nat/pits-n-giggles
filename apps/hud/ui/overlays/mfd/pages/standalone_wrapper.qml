import QtQuick
import QtQuick.Window

Window {
    id: root
    visible: true
    color: "black"
    property real scaleFactor: 1.0
    property url pageSource: ""

    readonly property int baseWidth:  400
    readonly property int baseHeight: 220

    width:  Math.round(baseWidth  * scaleFactor)
    height: Math.round(baseHeight * scaleFactor)

    Item {
        anchors.fill: parent
        scale: root.scaleFactor
        transformOrigin: Item.TopLeft

        Loader {
            objectName: "pageContent"
            width:  baseWidth
            height: baseHeight
            source: root.pageSource
        }
    }
}
