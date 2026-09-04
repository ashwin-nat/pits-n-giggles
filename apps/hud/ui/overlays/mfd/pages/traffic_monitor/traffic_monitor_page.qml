pragma ComponentBehavior: Bound
import QtQuick 2.15
import QtQuick.Layouts 1.15
import "../../../base"

Rectangle {
    id: root
    property string title: "TRAFFIC MONITOR"
    color: "transparent"

    // States: "table" | "inGarage" | "empty"
    property string viewState: "empty"

    // Written by Python as one TableDiffer payload per tick; DiffedTableModel
    // applies it as a whole-table reset or a set of single-row patches.
    property var tableUpdate: null

    DiffedTableModel {
        id: tableModel
        tableUpdate: root.tableUpdate
    }

    property string iconSourcePrefixTeam: "../../../../../../../assets/team-logos/"
    readonly property var teamIcons: ({
        "Alpine":               iconSourcePrefixTeam + "alpine.svg",
        "Alpine '24":           iconSourcePrefixTeam + "alpine.svg",
        "Alpine '26":           iconSourcePrefixTeam + "alpine.svg",
        "Aston Martin":         iconSourcePrefixTeam + "aston_martin.svg",
        "Aston Martin '24":     iconSourcePrefixTeam + "aston_martin.svg",
        "Aston Martin '26":     iconSourcePrefixTeam + "aston_martin.svg",
        "Ferrari":              iconSourcePrefixTeam + "ferrari.svg",
        "Ferrari '24":          iconSourcePrefixTeam + "ferrari.svg",
        "Ferrari '26":          iconSourcePrefixTeam + "ferrari.svg",
        "Haas":                 iconSourcePrefixTeam + "haas.svg",
        "Haas '24":             iconSourcePrefixTeam + "haas.svg",
        "Haas '26":             iconSourcePrefixTeam + "haas.svg",
        "McLaren":              iconSourcePrefixTeam + "mclaren.svg",
        "Mclaren":              iconSourcePrefixTeam + "mclaren.svg",
        "Mclaren '24":          iconSourcePrefixTeam + "mclaren.svg",
        "Mclaren '26":          iconSourcePrefixTeam + "mclaren.svg",
        "Mercedes":             iconSourcePrefixTeam + "mercedes.svg",
        "Mercedes '24":         iconSourcePrefixTeam + "mercedes.svg",
        "Mercedes '26":         iconSourcePrefixTeam + "mercedes.svg",
        "RB":                   iconSourcePrefixTeam + "rb.svg",
        "Rb '24":               iconSourcePrefixTeam + "rb.svg",
        "RB '26":               iconSourcePrefixTeam + "rb.svg",
        "VCARB":                iconSourcePrefixTeam + "rb.svg",
        "Alpha Tauri":          iconSourcePrefixTeam + "rb.svg",
        "Red Bull":             iconSourcePrefixTeam + "red_bull.svg",
        "Red Bull Racing":      iconSourcePrefixTeam + "red_bull.svg",
        "Red Bull Racing '24":  iconSourcePrefixTeam + "red_bull.svg",
        "Red Bull Racing '26":  iconSourcePrefixTeam + "red_bull.svg",
        "Sauber":               iconSourcePrefixTeam + "sauber.svg",
        "Sauber '24":           iconSourcePrefixTeam + "sauber.svg",
        "Alfa Romeo":           iconSourcePrefixTeam + "sauber.svg",
        "Williams":             iconSourcePrefixTeam + "williams.svg",
        "Williams '24":         iconSourcePrefixTeam + "williams.svg",
        "Williams '26":         iconSourcePrefixTeam + "williams_26.svg",
        "Audi '26":             iconSourcePrefixTeam + "audi.svg",
        "Cadillac '26":         iconSourcePrefixTeam + "cadillac.svg"
    })
    readonly property string defaultTeamIcon: iconSourcePrefixTeam + "default.svg"

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Header
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            color: "#B3000000"
            border.color: "#444444"
            border.width: 1

            Text {
                anchors.centerIn: parent
                text: "CARS BEHIND"
                font.family: "Formula1"
                font.pixelSize: 11
                font.bold: true
                color: "white"
            }
        }

        // Body — switches between table, in-garage message, and empty
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            // Table view
            ListView {
                id: tableView
                anchors.fill: parent
                model: tableModel
                interactive: false
                clip: true
                visible: root.viewState === "table"

                delegate: Rectangle {
                    id: trafficRow
                    required property string team
                    required property string name
                    required property string ersColor
                    required property string ersPercent
                    required property bool drs
                    required property string relDist
                    required property string relDistColor
                    required property bool isRef
                    required property string location

                    width: tableView.width
                    height: 35
                    color: "#80000000"

                    border.color: trafficRow.isRef ? "white" : "transparent"
                    border.width: trafficRow.isRef ? 2 : 0

                    Rectangle {
                        anchors.top: parent.top
                        width: parent.width
                        height: 1
                        color: "#444444"
                    }

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 5
                        anchors.rightMargin: 5
                        spacing: 0

                        // Team logo
                        Item {
                            Layout.preferredWidth: 28
                            Layout.fillHeight: true

                            Image {
                                anchors.centerIn: parent
                                width: 20
                                height: 20
                                source: root.teamIcons[trafficRow.team] || root.defaultTeamIcon
                                fillMode: Image.PreserveAspectFit
                                smooth: true
                                mipmap: true
                            }
                        }

                        // Driver name
                        Text {
                            Layout.preferredWidth: 170
                            Layout.fillHeight: true
                            text: trafficRow.name
                            font.family: "Formula1"
                            font.pixelSize: 14
                            color: "white"
                            horizontalAlignment: Text.AlignLeft
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }

                        // ERS/DRS bar
                        Item {
                            Layout.preferredWidth: 65
                            Layout.fillHeight: true

                            Rectangle {
                                anchors.left: parent.left
                                anchors.leftMargin: 1
                                anchors.verticalCenter: parent.verticalCenter
                                width: 6
                                height: parent.height - 8
                                radius: 2
                                color: trafficRow.ersColor
                            }

                            Text {
                                anchors.centerIn: parent
                                text: trafficRow.ersPercent
                                font.family: "B612 Mono"
                                font.pixelSize: 12
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
                                color: trafficRow.drs ? "#00e676" : "#333333"
                            }
                        }

                        // Relative distance
                        Text {
                            Layout.preferredWidth: 55
                            Layout.fillHeight: true
                            text: trafficRow.relDist
                            font.family: "B612 Mono"
                            font.pixelSize: 12
                            color: trafficRow.relDistColor
                            horizontalAlignment: Text.AlignRight
                            verticalAlignment: Text.AlignVCenter
                        }

                        // Location
                        Text {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            text: trafficRow.location
                            font.family: "B612 Mono"
                            font.pixelSize: 12
                            color: "#aaaaaa"
                            horizontalAlignment: Text.AlignRight
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
            }

            // In-garage message
            Text {
                anchors.centerIn: parent
                visible: root.viewState === "inGarage"
                text: "IN GARAGE"
                font.family: "Formula1"
                font.pixelSize: 13
                color: "#888888"
            }

            // Waiting for data
            Text {
                anchors.centerIn: parent
                visible: root.viewState === "empty"
                text: "WAITING FOR DATA"
                font.family: "Formula1"
                font.pixelSize: 11
                color: "#666666"
            }
        }
    }

}
