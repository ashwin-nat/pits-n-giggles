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

    // A hosted page may declare a preferred standalone height via `standaloneHeight`
    // to hug its content instead of the full baseHeight. Pages that don't fall back.
    // qmllint disable missing-property
    readonly property int pageHeight: {
        const it = pageContentLoader.item
        if (it && it.standaloneHeight !== undefined && it.standaloneHeight > 0)
            return it.standaloneHeight
        return baseHeight
    }
    // qmllint enable missing-property

    width:  Math.round(baseWidth * scaleFactor)
    height: Math.round((pageHeight + (showTitleBar ? titleBarHeight : 0)) * scaleFactor)

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
            id:     pageContentLoader
            objectName: "pageContent"
            y:      root.showTitleBar ? root.titleBarHeight : 0
            width:  root.baseWidth
            height: root.pageHeight
            source: root.pageSource
        }
    }
}
