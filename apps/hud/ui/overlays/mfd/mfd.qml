import QtQuick
import QtQuick.Window
import QtQuick.Layouts

Window {
    id: root
    property real scaleFactor: 1.0
    property int currentPage: 0

    // pushed from python
    property string collapsedTitle: ""
    property string fuelSurplus: ""

    StackLayout {
        id: stack
        currentIndex: root.currentPage

        Loader { source: "pages/collapsed/collapsed_page.qml" }
        Loader { source: "pages/fuel/fuel_page.qml" }
    }

    height: stack.currentItem.implicitHeight
}
