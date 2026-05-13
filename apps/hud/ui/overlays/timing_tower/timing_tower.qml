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

    // Column toggle properties - set by Python
    property bool showTeamLogos: true
    property bool showTyreInfo: true
    property bool showDeltas: true
    property bool showErsDrsInfo: true
    property bool showPens: true

    property bool showBestLap: false
    property bool showLastLap: false
    property bool showWingDmg: false
    property bool showSpeedTrap: false
    property bool showFuel: false
    property bool showDriverStatus: false
    property bool showColHeader: true

    // Dynamic width calculation based on enabled columns
    readonly property int baseWidth: {
        var width = cols.pos + cols.name;
        if (showTeamLogos) width += cols.team;
        if (showDeltas) width += cols.delta;
        if (showTyreInfo) width += cols.tyre;
        if (showErsDrsInfo) {
            // DRS bar needs extra space if pens are disabled
            // In the main layout, it spills into the pens column
            // this workaround is good enough
            width += showPens ? cols.ers : cols.ers + 10;
        }
        if (showPens) width += cols.pens;
        if (showBestLap) width += cols.bestLap;
        if (showLastLap) width += cols.lastLap;
        if (showWingDmg) width += cols.wingDmg;
        if (showSpeedTrap) width += cols.speedTrap;
        if (showFuel) width += cols.fuel;
        if (showDriverStatus) width += cols.driverStatus;
        return width + 10; // Add padding
    }

    readonly property int effectiveRows: Math.min(numRows, tableData.length)
    readonly property int baseHeight: headerHeight + (showColHeader ? colHeaderHeight : 0) + (rowHeight * effectiveRows) + margins

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

                    // Column widths
                    QtObject {
                        id: cols
                        readonly property int pos: 30
                        readonly property int team: 25
                        readonly property int name: 120
                        readonly property int delta: 72
                        readonly property int tyre: 58
                        readonly property int ers: 58
                        readonly property int pens: 56
                        readonly property int bestLap: 75
                        readonly property int lastLap: 72
                        readonly property int wingDmg: 50
                        readonly property int speedTrap: 55
                        readonly property int fuel: 55
                        readonly property int driverStatus: 95
                    }

                    // Column headers (race mode)
                    Item {
                        id: raceColHeader
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.margins: 2
                        height: (showColHeader && !showError && mode === "race") ? colHeaderHeight : 0
                        clip: true

                        Row {
                            anchors.left: parent.left
                            anchors.leftMargin: 4
                            anchors.verticalCenter: parent.verticalCenter
                            height: parent.height

                            Text {
                                width: cols.pos
                                height: parent.height
                                text: "P"
                                font.family: "Formula1"
                                font.pixelSize: 10
                                color: "#666666"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            Text {
                                width: showTeamLogos ? cols.team : 0
                                height: parent.height
                                text: ""
                                visible: showTeamLogos
                            }
                            Text {
                                width: cols.name
                                height: parent.height
                                text: "DRIVER"
                                font.family: "Formula1"
                                font.pixelSize: 10
                                color: "#666666"
                                horizontalAlignment: Text.AlignLeft
                                verticalAlignment: Text.AlignVCenter
                            }
                            Text {
                                width: showDeltas ? cols.delta : 0
                                height: parent.height
                                text: "DELTA"
                                font.family: "Formula1"
                                font.pixelSize: 10
                                color: "#666666"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                visible: showDeltas
                            }
                            Text {
                                width: showTyreInfo ? cols.tyre : 0
                                height: parent.height
                                text: "TYRE"
                                font.family: "Formula1"
                                font.pixelSize: 10
                                color: "#666666"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                visible: showTyreInfo
                            }
                            Text {
                                width: showErsDrsInfo ? cols.ers : 0
                                height: parent.height
                                text: "ERS/DRS"
                                font.family: "Formula1"
                                font.pixelSize: 10
                                color: "#666666"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                visible: showErsDrsInfo
                            }
                            Text {
                                width: showPens ? cols.pens : 0
                                height: parent.height
                                text: "PEN"
                                font.family: "Formula1"
                                font.pixelSize: 10
                                color: "#666666"
                                horizontalAlignment: Text.AlignLeft
                                verticalAlignment: Text.AlignVCenter
                                visible: showPens
                            }
                            Text {
                                width: showBestLap ? cols.bestLap : 0
                                height: parent.height
                                text: "BEST"
                                font.family: "Formula1"
                                font.pixelSize: 10
                                color: "#666666"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                visible: showBestLap
                            }
                            Text {
                                width: showLastLap ? cols.lastLap : 0
                                height: parent.height
                                text: "LAST"
                                font.family: "Formula1"
                                font.pixelSize: 10
                                color: "#666666"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                visible: showLastLap
                            }
                            Text {
                                width: showWingDmg ? cols.wingDmg : 0
                                height: parent.height
                                text: "DMG"
                                font.family: "Formula1"
                                font.pixelSize: 10
                                color: "#666666"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                visible: showWingDmg
                            }
                            Text {
                                width: showSpeedTrap ? cols.speedTrap : 0
                                height: parent.height
                                text: "TRAP"
                                font.family: "Formula1"
                                font.pixelSize: 10
                                color: "#666666"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                visible: showSpeedTrap
                            }
                            Text {
                                width: showFuel ? cols.fuel : 0
                                height: parent.height
                                text: "FUEL"
                                font.family: "Formula1"
                                font.pixelSize: 10
                                color: "#666666"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                visible: showFuel
                            }
                            Text {
                                width: showDriverStatus ? cols.driverStatus : 0
                                height: parent.height
                                text: "STATUS"
                                font.family: "Formula1"
                                font.pixelSize: 10
                                color: "#666666"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                visible: showDriverStatus
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
                        visible: !showError && mode === "race"

                        model: tableData

                        delegate: Item {
                            width: tableView.width
                            height: 28

                            // Row background
                            Rectangle {
                                anchors.fill: parent
                                color: modelData.isReference
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
                                color: modelData.isReference ? "#ffffff" : "transparent"
                                radius: 1
                            }

                            Row {
                                anchors.left: parent.left
                                anchors.leftMargin: 4
                                anchors.verticalCenter: parent.verticalCenter
                                height: parent.height
                                spacing: 0

                                // Position
                                Item {
                                    width: cols.pos
                                    height: parent.height

                                    Rectangle {
                                        anchors.fill: parent
                                        anchors.margins: 1
                                        color: modelData.isSb ? "#4a1d7a" : "transparent"
                                        radius: 2
                                    }

                                    Text {
                                        anchors.fill: parent
                                        text: modelData.position < 10 ? modelData.position + " " : modelData.position
                                        font.family: "Consolas"
                                        font.pixelSize: 12
                                        color: "#ddd"
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }

                                // Team icon
                                Item {
                                    width: showTeamLogos ? cols.team : 0
                                    height: parent.height
                                    visible: showTeamLogos

                                    Image {
                                        anchors.right: parent.right
                                        anchors.rightMargin: 4
                                        anchors.verticalCenter: parent.verticalCenter
                                        width: 20
                                        height: 20
                                        sourceSize.width: width * Screen.devicePixelRatio * 2
                                        sourceSize.height: height * Screen.devicePixelRatio * 2
                                        source: modelData.teamIcon || ""
                                        fillMode: Image.PreserveAspectFit
                                        smooth: true
                                        mipmap: true
                                        cache: true
                                        antialiasing: true
                                    }
                                }

                                // Driver name
                                Text {
                                    width: cols.name
                                    height: parent.height
                                    text: modelData.name
                                    font.family: "Formula1"
                                    font.pixelSize: 13
                                    color: "#ffffff"
                                    horizontalAlignment: Text.AlignLeft
                                    verticalAlignment: Text.AlignVCenter
                                    elide: Text.ElideRight
                                }

                                // Delta
                                Text {
                                    width: showDeltas ? cols.delta : 0
                                    height: parent.height
                                    text: modelData.delta
                                    font.family: "Consolas"
                                    font.pixelSize: 13
                                    color: "#ffffff"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    visible: showDeltas
                                }

                                // Tyre
                                Item {
                                    width: showTyreInfo ? cols.tyre : 0
                                    height: parent.height
                                    visible: showTyreInfo

                                    Row {
                                        anchors.centerIn: parent
                                        spacing: 4

                                        Image {
                                            width: 20
                                            height: 20
                                            sourceSize.width: width * Screen.devicePixelRatio
                                            sourceSize.height: height * Screen.devicePixelRatio
                                            source: modelData.tyreIcon || ""
                                            fillMode: Image.PreserveAspectFit
                                            smooth: true
                                            anchors.verticalCenter: parent.verticalCenter
                                            cache: true
                                            antialiasing: true
                                        }

                                        Text {
                                            text: modelData.tyreWear
                                            font.family: "Consolas"
                                            font.pixelSize: 13
                                            color: "#ffffff"
                                            anchors.verticalCenter: parent.verticalCenter
                                        }
                                    }
                                }

                                // ERS/DRS
                                Item {
                                    width: showErsDrsInfo ? cols.ers : 0
                                    height: parent.height
                                    visible: showErsDrsInfo

                                    // ERS mode strip (left)
                                    Rectangle {
                                        anchors.left: parent.left
                                        anchors.leftMargin: 1
                                        anchors.verticalCenter: parent.verticalCenter
                                        width: 6
                                        height: parent.height - 8
                                        radius: 2
                                        color: {
                                            switch(modelData.ersMode) {
                                                case "Medium": return "#e6d800"
                                                case "Hotlap": return "#00e676"
                                                case "Overtake": return "#ff1744"
                                                default: return "#444444"
                                            }
                                        }
                                    }

                                    // ERS text (center)
                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData.ers
                                        font.family: "Consolas"
                                        font.pixelSize: 13
                                        color: "#dddddd"
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }

                                    // DRS strip (right)
                                    Rectangle {
                                        anchors.right: parent.right
                                        anchors.rightMargin: 1
                                        anchors.verticalCenter: parent.verticalCenter
                                        width: 6
                                        height: parent.height - 8
                                        radius: 2
                                        color: modelData.drs ? "#00e676" : "#333333"
                                    }
                                }

                                // Penalties
                                Rectangle {
                                    width: showPens ? cols.pens : 0
                                    height: parent.height
                                    color: "transparent"
                                    visible: showPens

                                    Text {
                                        anchors.left: parent.left
                                        anchors.leftMargin: 4
                                        anchors.verticalCenter: parent.verticalCenter
                                        text: modelData.penalties
                                        font.family: "Formula1"
                                        font.pixelSize: 11
                                        color: "white"
                                        horizontalAlignment: Text.AlignLeft
                                        verticalAlignment: Text.AlignVCenter
                                        wrapMode: Text.NoWrap
                                        elide: Text.ElideRight
                                    }
                                }

                                // Best Lap
                                Text {
                                    width: showBestLap ? cols.bestLap : 0
                                    height: parent.height
                                    text: modelData.bestLap
                                    font.family: "Consolas"
                                    font.pixelSize: 12
                                    color: modelData.isSb ? "#c084fc" : "#dddddd"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    visible: showBestLap
                                }

                                // Last Lap
                                Text {
                                    width: showLastLap ? cols.lastLap : 0
                                    height: parent.height
                                    text: modelData.lastLap
                                    font.family: "Consolas"
                                    font.pixelSize: 12
                                    color: {
                                        if (!modelData.isPb) return "#dddddd";
                                        return modelData.isSb ? "#c084fc" : "#44dd88";
                                    }
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    visible: showLastLap
                                }

                                // Wing Damage
                                Text {
                                    width: showWingDmg ? cols.wingDmg : 0
                                    height: parent.height
                                    text: modelData.wingDmg
                                    font.family: "Consolas"
                                    font.pixelSize: 12
                                    color: modelData.wingDmg === "N/A" ? "#666666" : "#ff9944"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    visible: showWingDmg
                                }

                                // Speed Trap
                                Text {
                                    width: showSpeedTrap ? cols.speedTrap : 0
                                    height: parent.height
                                    text: modelData.speedTrap
                                    font.family: "Consolas"
                                    font.pixelSize: 12
                                    color: "#dddddd"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    visible: showSpeedTrap
                                }

                                // Fuel
                                Text {
                                    width: showFuel ? cols.fuel : 0
                                    height: parent.height
                                    text: modelData.fuel
                                    font.family: "Consolas"
                                    font.pixelSize: 12
                                    color: {
                                        var f = modelData.fuel;
                                        if (f === "N/A" || f === "---") return "#666666";
                                        return f.charAt(0) === "-" ? "#ff4444" : "#44dd88";
                                    }
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    visible: showFuel
                                }

                                // Driver Status
                                Text {
                                    width: showDriverStatus ? cols.driverStatus : 0
                                    height: parent.height
                                    text: modelData.driverStatus
                                    font.family: "Formula1"
                                    font.pixelSize: 10
                                    color: {
                                        switch(modelData.driverStatus) {
                                            case "Flying Lap": return "#00e676"
                                            case "On Track": return "#aaaaaa"
                                            case "Out Lap": return "#e6d800"
                                            case "In Lap": return "#e6d800"
                                            case "In Garage": return "#555555"
                                            case "Retired": return "#ff4444"
                                            default: return "#666666"
                                        }
                                    }
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    elide: Text.ElideRight
                                    visible: showDriverStatus
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
