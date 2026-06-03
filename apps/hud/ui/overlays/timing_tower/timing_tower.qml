import QtQuick
import QtQuick.Window
import QtQuick.Layouts

Window {
    id: root
    visible: true

    property real scaleFactor: 1.0
    property int numRows: 5  // Set by Python
    readonly property int rowHeight: 28
    readonly property int headerHeight: 34
    readonly property int colHeaderHeight: 20
    readonly property int margins: 20

    property bool showColHeader: true

    // Dynamic column order - set by Python as list of column ID strings
    // Does not include team_logo (fixed position between pos and name)
    property var columnOrder: []

    // Column widths keyed by TimingTowerColId enum values
    QtObject {
        id: cols
        readonly property int pos: 30
        readonly property int team_logo: 25
        readonly property int name: 120
        readonly property int delta: 72
        readonly property int tyre: 58
        readonly property int ers_drs: 58
        readonly property int pens: 44
        readonly property int tl_warns: 32
        readonly property int best_lap: 75
        readonly property int last_lap: 72
        readonly property int wing_dmg: 50
        readonly property int speed_trap: 75
        readonly property int fuel: 55
        readonly property int driver_status: 95
    }

    // Dynamic width: fixed structural cols + optional team_logo + sum of enabled dynamic cols
    readonly property int baseWidth: {
        var w = cols.pos + cols.name;
        w += cols.team_logo;
        for (var i = 0; i < columnOrder.length; ++i) {
            w += cols[columnOrder[i]];
        }
        return w + 24;
    }

    function colHeaderLabel(colId) {
        switch(colId) {
            case "delta":         return "DELTA"
            case "tyre":          return "TYRE"
            case "ers_drs":       return "ERS/DRS"
            case "pens":          return "PEN"
            case "tl_warns":      return "TL"
            case "best_lap":      return "BEST"
            case "last_lap":      return "LAST"
            case "wing_dmg":      return "DMG"
            case "speed_trap":    return "TRAP"
            case "fuel":          return "FUEL"
            case "driver_status": return "STATUS"
            default:              return colId
        }
    }

    // Column cell components — defined once at root level so they are not
    // re-instantiated for every delegate. Each declares property var rowData
    // which the Loader sets via onLoaded after instantiation.
    Component {
        id: deltaColComp
        Text {
            property var rowData
            anchors.fill: parent
            text: rowData ? rowData.delta : ""
            font.family: "Consolas"
            font.pixelSize: 13
            color: "#ffffff"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }
    Component {
        id: tyreColComp
        Item {
            property var rowData
            anchors.fill: parent
            Row {
                anchors.centerIn: parent
                spacing: 4
                Image {
                    width: 20
                    height: 20
                    sourceSize.width: width * Screen.devicePixelRatio
                    sourceSize.height: height * Screen.devicePixelRatio
                    source: rowData ? (rowData.tyreIcon || "") : ""
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    anchors.verticalCenter: parent.verticalCenter
                    cache: true
                    antialiasing: true
                }
                Text {
                    text: rowData ? rowData.tyreWear : ""
                    font.family: "Consolas"
                    font.pixelSize: 13
                    color: "#ffffff"
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }
    Component {
        id: ersDrsColComp
        Item {
            property var rowData
            anchors.fill: parent
            Rectangle {
                anchors.left: parent.left
                anchors.leftMargin: 1
                anchors.verticalCenter: parent.verticalCenter
                width: 6
                height: parent.height - 8
                radius: 2
                color: rowData ? rowData.ersColor : "#444444"
            }
            Text {
                anchors.centerIn: parent
                text: rowData ? rowData.ers : ""
                font.family: "Consolas"
                font.pixelSize: 13
                color: "#dddddd"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            Rectangle {
                anchors.right: parent.right
                anchors.rightMargin: 1
                anchors.verticalCenter: parent.verticalCenter
                width: 6
                height: parent.height - 8
                radius: 2
                color: (rowData && rowData.overtakeBarColor) ? rowData.overtakeBarColor : "#333333"
            }
        }
    }
    Component {
        id: pensColComp
        Item {
            property var rowData
            anchors.fill: parent
            Text {
                anchors.left: parent.left
                anchors.leftMargin: 4
                anchors.verticalCenter: parent.verticalCenter
                text: rowData ? rowData.penalties : ""
                font.family: "Formula1"
                font.pixelSize: 11
                color: "white"
                horizontalAlignment: Text.AlignLeft
                verticalAlignment: Text.AlignVCenter
                wrapMode: Text.NoWrap
                elide: Text.ElideRight
            }
        }
    }
    Component {
        id: tlWarnsColComp
        Text {
            property var rowData
            anchors.fill: parent
            text: (rowData && rowData.tlWarns !== undefined) ? rowData.tlWarns : "---"
            font.family: "Consolas"
            font.pixelSize: 13
            color: "#dddddd"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }
    Component {
        id: bestLapColComp
        Text {
            property var rowData
            anchors.fill: parent
            text: rowData ? rowData.bestLap : ""
            font.family: "Consolas"
            font.pixelSize: 12
            color: rowData ? rowData.bestLapColor : "#dddddd"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }
    Component {
        id: lastLapColComp
        Text {
            property var rowData
            anchors.fill: parent
            text: rowData ? rowData.lastLap : ""
            font.family: "Consolas"
            font.pixelSize: 12
            color: rowData ? rowData.lastLapColor : "#dddddd"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }
    Component {
        id: wingDmgColComp
        Text {
            property var rowData
            anchors.fill: parent
            text: rowData ? rowData.wingDmg : ""
            font.family: "Consolas"
            font.pixelSize: 12
            color: rowData ? rowData.wingDmgColor : "#dddddd"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }
    Component {
        id: speedTrapColComp
        Text {
            property var rowData
            anchors.fill: parent
            text: rowData ? rowData.speedTrap : ""
            font.family: "Consolas"
            font.pixelSize: 12
            color: "#dddddd"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }
    Component {
        id: fuelColComp
        Text {
            property var rowData
            anchors.fill: parent
            text: rowData ? rowData.fuel : ""
            font.family: "Consolas"
            font.pixelSize: 12
            color: rowData ? rowData.fuelColor : "#dddddd"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }
    Component {
        id: driverStatusColComp
        Text {
            property var rowData
            anchors.fill: parent
            text: rowData ? rowData.driverStatus : ""
            font.family: "Formula1"
            font.pixelSize: 10
            color: "#dddddd"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
    }

    readonly property int effectiveRows: Math.min(numRows, tableData.length)
    readonly property bool colHeaderVisible: showColHeader && !showError && mode === "race"
    readonly property int baseHeight: headerHeight + (colHeaderVisible ? colHeaderHeight : 0) + (rowHeight * effectiveRows) + margins

    width: (mode === "tt" ? ttBaseWidth : baseWidth) * scaleFactor
    height: (mode === "tt" ? ttBaseHeight : baseHeight) * scaleFactor
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    // Exposed properties for Python to set
    property string sessionInfo: "-- / --"
    property var tableData: []
    property int referenceRow: -1
    property string errorMessage: ""
    property bool showError: false
    property string mode: "race"  // "race" or "tt"
    property var ttTableData: []

    // TT mode column widths and dimensions
    readonly property int ttColLabel: 52
    readonly property int ttColLapTime: 85
    readonly property int ttColSector: 62
    // +34: accounts for nested margins (outer rect 8, layout 8, col 4) + 4 left margin + 10 right padding
    readonly property int ttBaseWidth: ttColLabel + ttColLapTime + ttColSector * 3 + 34
    readonly property int ttColHeaderHeight: 22
    readonly property int ttBaseHeight: headerHeight + ttColHeaderHeight + (rowHeight * 4) + margins

    // Global scaling root
    Item {
        id: scaledRoot
        anchors.centerIn: parent
        width: mode === "tt" ? ttBaseWidth : baseWidth
        height: mode === "tt" ? ttBaseHeight : baseHeight

        transform: Scale {
            xScale: scaleFactor
            yScale: scaleFactor
            origin.x: scaledRoot.width / 2
            origin.y: scaledRoot.height / 2
        }

        // Main container
        Rectangle {
            anchors.fill: parent
            anchors.margins: 4
            color: Qt.rgba(0.04, 0.04, 0.06, 0.90)
            radius: 8

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 4
                spacing: 3

                // Header section
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 28
                    color: Qt.rgba(0.12, 0.12, 0.14, 0.95)
                    radius: 5

                    Text {
                        anchors.centerIn: parent
                        text: sessionInfo
                        font.family: "Formula1"
                        font.pixelSize: 13
                        color: "#cccccc"
                    }
                }

                // Timing table section
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "transparent"
                    radius: 6

                    // Error message display (race mode only)
                    Text {
                        anchors.centerIn: parent
                        text: errorMessage
                        font.pixelSize: 12
                        font.bold: true
                        color: "#ffb86b"
                        visible: showError && mode === "race"
                    }

                    // Column headers (race mode)
                    Item {
                        id: raceColHeader
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.margins: 2
                        height: colHeaderVisible ? colHeaderHeight : 0

                        Row {
                            anchors.left: parent.left
                            anchors.leftMargin: 4
                            anchors.verticalCenter: parent.verticalCenter
                            height: parent.height

                            Item {
                                width: cols.pos
                                height: parent.height
                                Text {
                                    anchors.fill: parent
                                    text: "P"
                                    font.family: "Formula1"
                                    font.pixelSize: 10
                                    color: "#666666"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                Rectangle {
                                    anchors.right: parent.right
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: 1
                                    height: parent.height - 4
                                    color: Qt.rgba(1, 1, 1, 0.15)
                                }
                            }
                            // team_logo header: fixed, empty label
                            Item {
                                width: cols.team_logo
                                height: parent.height
                                Rectangle {
                                    anchors.right: parent.right
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: 1
                                    height: parent.height - 4
                                    color: Qt.rgba(1, 1, 1, 0.15)
                                }
                            }
                            Item {
                                width: cols.name
                                height: parent.height
                                Text {
                                    anchors.fill: parent
                                    text: "DRIVER"
                                    font.family: "Formula1"
                                    font.pixelSize: 10
                                    color: "#666666"
                                    horizontalAlignment: Text.AlignLeft
                                    verticalAlignment: Text.AlignVCenter
                                }
                                Rectangle {
                                    anchors.right: parent.right
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: 1
                                    height: parent.height - 4
                                    color: Qt.rgba(1, 1, 1, 0.15)
                                }
                            }
                            Repeater {
                                model: columnOrder
                                delegate: Item {
                                    width: cols[modelData]
                                    height: parent.height
                                    Text {
                                        anchors.fill: parent
                                        text: colHeaderLabel(modelData)
                                        font.family: "Formula1"
                                        font.pixelSize: 10
                                        color: "#666666"
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                    Rectangle {
                                        anchors.right: parent.right
                                        anchors.verticalCenter: parent.verticalCenter
                                        width: 1
                                        height: parent.height - 4
                                        color: Qt.rgba(1, 1, 1, 0.15)
                                    }
                                }
                            }
                        }
                    }

                    // Table content (race mode)
                    ListView {
                        id: tableView
                        anchors.top: raceColHeader.bottom
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        anchors.margins: 2
                        anchors.topMargin: 0
                        clip: true
                        interactive: false
                        reuseItems: true
                        visible: !showError && mode === "race"

                        model: tableData

                        delegate: Item {
                            property var rowData: modelData
                            width: tableView.width
                            height: 28

                            // Row background
                            Rectangle {
                                anchors.fill: parent
                                color: rowData.isReference
                                    ? Qt.rgba(1, 1, 1, 0.07)
                                    : Qt.rgba(0.08, 0.08, 0.10, 0.6)
                                radius: 3
                            }

                            // Bottom separator
                            Rectangle {
                                anchors.bottom: parent.bottom
                                width: parent.width
                                height: 1
                                color: Qt.rgba(1, 1, 1, 0.05)
                            }

                            // Reference row left accent
                            Rectangle {
                                anchors.left: parent.left
                                anchors.verticalCenter: parent.verticalCenter
                                width: 2
                                height: parent.height - 6
                                color: rowData.isReference ? "#ffffff" : "transparent"
                                radius: 1
                            }

                            Row {
                                anchors.left: parent.left
                                anchors.leftMargin: 4
                                anchors.verticalCenter: parent.verticalCenter
                                height: parent.height
                                spacing: 0

                                // Position (fixed)
                                Item {
                                    width: cols.pos
                                    height: parent.height

                                    Rectangle {
                                        anchors.fill: parent
                                        anchors.margins: 1
                                        color: rowData.isSb ? "#4a1d7a" : "transparent"
                                        radius: 2
                                    }

                                    Text {
                                        anchors.fill: parent
                                        text: rowData.position < 10 ? rowData.position + " " : rowData.position
                                        font.family: "Consolas"
                                        font.pixelSize: 12
                                        color: "#ddd"
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }

                                // Team logo (fixed)
                                Item {
                                    width: cols.team_logo
                                    height: parent.height

                                    Image {
                                        anchors.right: parent.right
                                        anchors.rightMargin: 4
                                        anchors.verticalCenter: parent.verticalCenter
                                        width: 20
                                        height: 20
                                        sourceSize.width: width * Screen.devicePixelRatio * 2
                                        sourceSize.height: height * Screen.devicePixelRatio * 2
                                        source: rowData.teamIcon || ""
                                        fillMode: Image.PreserveAspectFit
                                        smooth: true
                                        mipmap: true
                                        cache: true
                                        antialiasing: true
                                    }
                                }

                                // Driver name (fixed)
                                Text {
                                    width: cols.name
                                    height: parent.height
                                    text: rowData.name
                                    font.family: "Formula1"
                                    font.pixelSize: 13
                                    color: "#ffffff"
                                    horizontalAlignment: Text.AlignLeft
                                    verticalAlignment: Text.AlignVCenter
                                    elide: Text.ElideRight
                                }

                                // Dynamic columns — Loader instantiates one component per slot.
                                // Components live at root level (not per-delegate), so onLoaded
                                // wires rowData from the enclosing delegate into each cell.
                                Repeater {
                                    model: columnOrder
                                    delegate: Loader {
                                        property string colId: modelData
                                        width: cols[colId]
                                        height: parent.height
                                        sourceComponent: {
                                            switch(colId) {
                                                case "delta":         return deltaColComp
                                                case "tyre":          return tyreColComp
                                                case "ers_drs":       return ersDrsColComp
                                                case "pens":          return pensColComp
                                                case "tl_warns":      return tlWarnsColComp
                                                case "best_lap":      return bestLapColComp
                                                case "last_lap":      return lastLapColComp
                                                case "wing_dmg":      return wingDmgColComp
                                                case "speed_trap":    return speedTrapColComp
                                                case "fuel":          return fuelColComp
                                                case "driver_status": return driverStatusColComp
                                                default:              return null
                                            }
                                        }
                                        onLoaded: item.rowData = Qt.binding(function() { return rowData })
                                    }
                                }
                            }
                        }
                    }

                    // TT table (time trial mode)
                    Column {
                        anchors.fill: parent
                        anchors.margins: 2
                        spacing: 0
                        visible: mode === "tt"

                        // Column headers
                        Row {
                            width: parent.width
                            height: ttColHeaderHeight

                            Text {
                                width: ttColLabel
                                height: parent.height
                                text: ""
                            }
                            Text {
                                width: ttColLapTime
                                height: parent.height
                                text: "LAP"
                                font.family: "Formula1"
                                font.pixelSize: 10
                                color: "#888888"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            Text {
                                width: ttColSector
                                height: parent.height
                                text: "S1"
                                font.family: "Formula1"
                                font.pixelSize: 10
                                color: "#888888"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            Text {
                                width: ttColSector
                                height: parent.height
                                text: "S2"
                                font.family: "Formula1"
                                font.pixelSize: 10
                                color: "#888888"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            Text {
                                width: ttColSector
                                height: parent.height
                                text: "S3"
                                font.family: "Formula1"
                                font.pixelSize: 10
                                color: "#888888"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }

                        Repeater {
                            model: ttTableData

                            delegate: Item {
                                width: parent.width
                                height: 28

                                Rectangle {
                                    anchors.fill: parent
                                    color: index % 2 === 0
                                        ? Qt.rgba(0.10, 0.10, 0.12, 0.7)
                                        : Qt.rgba(0.06, 0.06, 0.08, 0.5)
                                    radius: 3
                                }

                                Rectangle {
                                    anchors.bottom: parent.bottom
                                    width: parent.width
                                    height: 1
                                    color: Qt.rgba(1, 1, 1, 0.05)
                                }

                                Row {
                                    anchors.left: parent.left
                                    anchors.leftMargin: 4
                                    anchors.verticalCenter: parent.verticalCenter
                                    height: parent.height

                                    Text {
                                        width: ttColLabel
                                        height: parent.height
                                        text: modelData.label
                                        font.family: "Formula1"
                                        font.pixelSize: 12
                                        color: "#aaaaaa"
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                    Text {
                                        width: ttColLapTime
                                        height: parent.height
                                        text: modelData["lap-time-str"]
                                        font.family: "Consolas"
                                        font.pixelSize: 13
                                        color: "#ffffff"
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                    Text {
                                        width: ttColSector
                                        height: parent.height
                                        text: modelData["s1-time-str"]
                                        font.family: "Consolas"
                                        font.pixelSize: 12
                                        color: "#cccccc"
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                    Text {
                                        width: ttColSector
                                        height: parent.height
                                        text: modelData["s2-time-str"]
                                        font.family: "Consolas"
                                        font.pixelSize: 12
                                        color: "#cccccc"
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                    Text {
                                        width: ttColSector
                                        height: parent.height
                                        text: modelData["s3-time-str"]
                                        font.family: "Consolas"
                                        font.pixelSize: 12
                                        color: "#cccccc"
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
