import QtQuick
import QtQuick.Window

Window {
    id: root
    visible: true
    color: "black"

    width: 400
    height: pageLoader.item ? pageLoader.item.implicitHeight : 40

    property real scaleFactor: 1.0

    // driven from python
    property int currentPage: 0
    property url currentPageQml: ""

    Loader {
        id: pageLoader
        anchors.fill: parent
        source: root.currentPageQml
    }
}
