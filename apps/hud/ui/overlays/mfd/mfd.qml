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
        Log.debug("QML base URL:", Qt.resolvedUrl("."))
    }
    Loader {
        id: pageLoader
        anchors.fill: parent
        source: "pages/collapsed/collapsed_page.qml"

        onStatusChanged: {
            Log.debug("Loader status:", status)
            if (status === Loader.Ready) {
                Log.debug("Loader READY, item:", item)
                item.visible = true
            }
        }
    }
}
