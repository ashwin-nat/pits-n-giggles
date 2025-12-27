import QtQuick
import QtQuick.Window
import QtQuick.Layouts

Window {
    id: root
    visible: true
    color: "black"

    width: 400
    height: 60

    property real scaleFactor: 1.0
    property int currentPage: 0

    // pushed from python
    property string collapsedTitle: "MFD"
    property string fuelSurplus: ""

    Component.onCompleted: {
        console.log("QML base URL:", Qt.resolvedUrl("."))
    }
    Loader {
        id: pageLoader
        anchors.fill: parent
        source: "pages/collapsed/collapsed_page.qml"

        onStatusChanged: {
            console.log("Loader status:", status)
            if (status === Loader.Ready) {
                console.log("Loader READY, item:", item)
                item.visible = true
            }
        }
    }
}
