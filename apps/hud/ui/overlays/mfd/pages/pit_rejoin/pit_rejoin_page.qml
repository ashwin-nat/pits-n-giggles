import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    property string title: "PIT REJOIN PREDICTION"
    color: "transparent"

    property string pitTimeLossText: "Pit Time Loss: --"
    property var tableData: []
    property int refIndex: -1

    // Icon mappings
    property string iconSourcePrefix: "../../../../../../../assets/tyre-icons/"
    readonly property var tyreIcons: ({
        "Super Soft": iconSourcePrefix + "super_soft_tyre.svg",
        "Soft":       iconSourcePrefix + "soft_tyre.svg",
        "Medium":     iconSourcePrefix + "medium_tyre.svg",
        "Hard":       iconSourcePrefix + "hard_tyre.svg",
        "Inters":     iconSourcePrefix + "intermediate_tyre.svg",
        "Wet":        iconSourcePrefix + "wet_tyre.svg"
    })

    property string iconSourcePrefixTeam: "../../../../../../../assets/team-logos/"
    readonly property var teamIcons: ({
        "Alpine": iconSourcePrefixTeam + "alpine.svg",
        "Alpine '24": iconSourcePrefixTeam + "alpine.svg",
        "Aston Martin": iconSourcePrefixTeam + "aston_martin.svg",
        "Aston Martin '24": iconSourcePrefixTeam + "aston_martin.svg",
        "Ferrari": iconSourcePrefixTeam + "ferrari.svg",
        "Ferrari '24": iconSourcePrefixTeam + "ferrari.svg",
        "Haas": iconSourcePrefixTeam + "haas.svg",
        "Haas '24": iconSourcePrefixTeam + "haas.svg",
        "McLaren": iconSourcePrefixTeam + "mclaren.svg",
        "Mclaren": iconSourcePrefixTeam + "mclaren.svg",
        "Mclaren '24": iconSourcePrefixTeam + "mclaren.svg",
        "Mercedes": iconSourcePrefixTeam + "mercedes.svg",
        "Mercedes '24": iconSourcePrefixTeam + "mercedes.svg",
        "RB": iconSourcePrefixTeam + "rb.svg",
        "Rb '24": iconSourcePrefixTeam + "rb.svg",
        "VCARB": iconSourcePrefixTeam + "rb.svg",
        "Alpha Tauri": iconSourcePrefixTeam + "rb.svg",
        "Red Bull": iconSourcePrefixTeam + "red_bull.svg",
        "Red Bull Racing": iconSourcePrefixTeam + "red_bull.svg",
        "Red Bull Racing '24": iconSourcePrefixTeam + "red_bull.svg",
        "Sauber": iconSourcePrefixTeam + "sauber.svg",
        "Sauber '24": iconSourcePrefixTeam + "sauber.svg",
        "Alfa Romeo": iconSourcePrefixTeam + "sauber.svg",
        "Williams": iconSourcePrefixTeam + "williams.svg",
        "Williams '24": iconSourcePrefixTeam + "williams.svg"
    })
    readonly property string defaultTeamIcon: iconSourcePrefixTeam + "default.svg"

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Header - Pit Time Loss
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            color: "#B3000000"
            border.color: "#444444"
            border.width: 1

            Text {
                anchors.centerIn: parent
                text: root.pitTimeLossText
                font.family: "Formula1"
                font.pixelSize: 11
                font.bold: true
                color: "white"
            }
        }

        // Table
        ListView {
            id: tableView
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: root.tableData
            interactive: false
            clip: true

            delegate: Rectangle {
                width: tableView.width
                height: 35
                color: "#80000000"

                // Border for reference driver
                border.color: modelData.isRef ? "white" : "transparent"
                border.width: modelData.isRef ? 2 : 0

                // Top border for all rows
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

                    // Position
                    Text {
                        Layout.preferredWidth: 32
                        Layout.fillHeight: true
                        text: modelData.position
                        font.family: "Formula1"
                        font.pixelSize: 10
                        font.bold: true
                        color: "white"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    // Team Icon
                    Item {
                        Layout.preferredWidth: 32
                        Layout.fillHeight: true

                        Image {
                            anchors.centerIn: parent
                            width: 20
                            height: 20
                            source: root.teamIcons[modelData.team] || root.defaultTeamIcon
                            fillMode: Image.PreserveAspectFit
                            smooth: true
                            mipmap: true
                        }
                    }

                    // Driver Name
                    Text {
                        Layout.preferredWidth: 220
                        Layout.fillHeight: true
                        text: modelData.name
                        font.family: "Formula1"
                        font.pixelSize: 10
                        color: "white"
                        horizontalAlignment: Text.AlignLeft
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }

                    // Tyre Icon
                    Item {
                        Layout.preferredWidth: 26
                        Layout.fillHeight: true

                        Image {
                            anchors.centerIn: parent
                            width: 18
                            height: 18
                            source: root.tyreIcons[modelData.compound] || ""
                            fillMode: Image.PreserveAspectFit
                            smooth: true
                            mipmap: true
                            visible: source !== ""
                        }
                    }

                    // Tyre Age
                    Text {
                        Layout.preferredWidth: 30
                        Layout.fillHeight: true
                        text: modelData.tyreAge
                        font.family: "B612 Mono"
                        font.pixelSize: 9
                        color: "white"
                        horizontalAlignment: Text.AlignCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    // Delta
                    Text {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        text: modelData.delta
                        font.family: "B612 Mono"
                        font.pixelSize: 9
                        color: "white"
                        horizontalAlignment: Text.AlignRight
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideNone
                    }
                }
            }
        }
    }

    // Python hooks
    function updateData(pitTimeLoss, rows, refIdx) {
        root.pitTimeLossText = pitTimeLoss;
        root.refIndex = refIdx;
        root.tableData = rows;
    }

    function showEmptyTable() {
        root.pitTimeLossText = "Pit Time Loss: --";
        root.tableData = [];
    }
}
