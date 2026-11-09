pragma ComponentBehavior: Bound
import QtQuick 2.15

// Layout B: one compound icon in the centre, a cell per tyre in its car position.
// Every data point is its own property so the Python side can skip unchanged writes.
// A value of -Infinity means "no data" (check isFinite()).
Rectangle {
    id: root
    property string title: "TYRES STATUS"
    color: "transparent"
    width: parent ? parent.width : 400
    height: parent ? parent.height : 220

    readonly property real noData: -Infinity
    property string compoundIcon: ""
    property int tyreAge: -1
    property bool telemetryDisabled: false

    property real flWear: root.noData
    property real flCoreTemp: root.noData
    property real flSurfaceTemp: root.noData
    property real frWear: root.noData
    property real frCoreTemp: root.noData
    property real frSurfaceTemp: root.noData
    property real rlWear: root.noData
    property real rlCoreTemp: root.noData
    property real rlSurfaceTemp: root.noData
    property real rrWear: root.noData
    property real rrCoreTemp: root.noData
    property real rrSurfaceTemp: root.noData

    /* ---------- COLORS ---------- */
    readonly property color bgCard:      "#1b1b1b"
    readonly property color bgBar:       "#2a2a2a"
    readonly property color borderColor: "#333333"
    readonly property color dimColor:    "#808080"
    readonly property color brightColor: "#ffffff"
    readonly property color okColor:     "#00ff88"
    readonly property color warnColor:   "#ffaa00"
    readonly property color dangerColor: "#ff4444"
    readonly property color coldColor:   "#4da6ff"

    // Temperature bands (C); same bands for core and surface
    readonly property real tempColdBelow: 75
    readonly property real tempHotAbove:  110

    /* ---------- HELPERS ---------- */
    function isValid(v) { return v !== undefined && v !== null && isFinite(v) }
    function wearText(v) { return isValid(v) ? v.toFixed(1) + "%" : "—" }
    function tempText(v) { return isValid(v) ? Math.round(v) + "°C" : "—" }
    function wearColor(v) {
        if (!isValid(v)) return dimColor
        if (v < 50)      return okColor
        if (v < 75)      return warnColor
        return dangerColor
    }
    function tempColor(v) {
        if (!isValid(v))       return dimColor
        if (v < tempColdBelow) return coldColor
        if (v > tempHotAbove)  return dangerColor
        return okColor
    }

    /* ---------- COMPONENTS ---------- */

    // "LABEL ........ value" with the label on the outer edge; flipped when mirrored
    component LabelValueRow: Item {
        id: lvRow
        required property string label
        required property string valueText
        required property color valueColor
        required property int labelSize
        required property int valueSize
        required property bool mirrored
        required property string valueFamily

        width: parent ? parent.width : 0
        height: 22

        Text {
            anchors.left: lvRow.mirrored ? undefined : parent.left
            anchors.right: lvRow.mirrored ? parent.right : undefined
            anchors.verticalCenter: parent.verticalCenter
            text: lvRow.label
            color: root.dimColor
            font.pixelSize: lvRow.labelSize
            font.bold: true
        }
        Text {
            anchors.right: lvRow.mirrored ? undefined : parent.right
            anchors.left: lvRow.mirrored ? parent.left : undefined
            anchors.verticalCenter: parent.verticalCenter
            text: lvRow.valueText
            color: lvRow.valueColor
            font.family: lvRow.valueFamily
            font.pixelSize: lvRow.valueSize
            font.bold: true
        }
    }

    component TyreCell: Rectangle {
        id: cell
        required property bool mirrored
        required property real wear
        required property real coreTemp
        required property real surfaceTemp

        width: 150
        height: 96
        color: root.bgCard
        radius: 8
        border.color: root.borderColor
        border.width: 1

        Column {
            anchors.fill: parent
            anchors.margins: 8
            spacing: 3

            LabelValueRow {
                label: "WEAR"
                valueText: root.wearText(cell.wear)
                valueColor: root.wearColor(cell.wear)
                labelSize: 10
                valueSize: 15
                valueFamily: "Consolas"
                mirrored: cell.mirrored
            }

            // Wear bar, filling from the outer edge
            Rectangle {
                width: parent.width
                height: 4
                radius: 2
                color: root.bgBar
                Rectangle {
                    anchors.left: cell.mirrored ? undefined : parent.left
                    anchors.right: cell.mirrored ? parent.right : undefined
                    height: parent.height
                    radius: 2
                    width: root.isValid(cell.wear) ? parent.width * Math.min(Math.max(cell.wear, 0), 100) / 100 : 0
                    color: root.wearColor(cell.wear)
                }
            }

            LabelValueRow {
                label: "CORE"
                valueText: root.tempText(cell.coreTemp)
                valueColor: root.tempColor(cell.coreTemp)
                labelSize: 10
                valueSize: 15
                valueFamily: "Consolas"
                mirrored: cell.mirrored
            }

            LabelValueRow {
                label: "SURF"
                valueText: root.tempText(cell.surfaceTemp)
                valueColor: root.tempColor(cell.surfaceTemp)
                labelSize: 10
                valueSize: 15
                valueFamily: "Consolas"
                mirrored: cell.mirrored
            }
        }
    }

    /* ---------- LAYOUT ---------- */
    TyreCell {
        anchors.left: parent.left
        anchors.leftMargin: 8
        anchors.top: parent.top
        anchors.topMargin: 8
        mirrored: false
        wear: root.flWear
        coreTemp: root.flCoreTemp
        surfaceTemp: root.flSurfaceTemp
    }
    TyreCell {
        anchors.right: parent.right
        anchors.rightMargin: 8
        anchors.top: parent.top
        anchors.topMargin: 8
        mirrored: true
        wear: root.frWear
        coreTemp: root.frCoreTemp
        surfaceTemp: root.frSurfaceTemp
    }
    TyreCell {
        anchors.left: parent.left
        anchors.leftMargin: 8
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 8
        mirrored: false
        wear: root.rlWear
        coreTemp: root.rlCoreTemp
        surfaceTemp: root.rlSurfaceTemp
    }
    TyreCell {
        anchors.right: parent.right
        anchors.rightMargin: 8
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 8
        mirrored: true
        wear: root.rrWear
        coreTemp: root.rrCoreTemp
        surfaceTemp: root.rrSurfaceTemp
    }

    // Centre: compound icon (same on all four tyres)
    Image {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset: -8
        width: 56
        height: 56
        visible: !root.telemetryDisabled
        sourceSize.width: width * Screen.devicePixelRatio
        sourceSize.height: height * Screen.devicePixelRatio
        source: root.compoundIcon
        fillMode: Image.PreserveAspectFit
        smooth: true
        mipmap: true
        cache: true
        antialiasing: true
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.verticalCenter
        anchors.topMargin: 24
        visible: !root.telemetryDisabled && root.tyreAge >= 0
        text: root.tyreAge + "L"
        color: root.brightColor
        font.pixelSize: 18
        font.bold: true
    }

    Text {
        anchors.centerIn: parent
        visible: root.telemetryDisabled
        text: "Telemetry\ndisabled"
        horizontalAlignment: Text.AlignHCenter
        color: root.dimColor
        font.pixelSize: 13
    }
}
