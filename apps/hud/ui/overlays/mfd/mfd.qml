import QtQuick
import QtQuick.Window

Window {
    id: root
    visible: true
    color: "black"

    width: 400
    height: pageLoader.item ? pageLoader.item.implicitHeight : 40

    /* ---------- FUEL DATA (SET FROM PYTHON) ---------- */
    property string currValue: "---"
    property string lastValue: "---"
    property string tgtAvgValue: "---"
    property string tgtNextValue: "---"

    property string surplusText: "Surplus: ---"
    property real surplusValue: 0.0
    property bool surplusValid: false

    /* ---------- PAGE CONTROL ---------- */
    property url currentPageQml: ""

    Loader {
        id: pageLoader
        objectName: "pageLoader"
        anchors.fill: parent
        source: root.currentPageQml
    }
}
