pragma ComponentBehavior: Bound
import QtQuick 2.15
import QtQuick.Layouts 1.15

// Cell styling mirrors the timing tower (fonts, sizes, ERS/DRS bars, row backgrounds).
Rectangle {
    id: root
    property string title: "RIVALS STATUS"
    color: "transparent"

    property var tableData: []

    readonly property int rowHeight: 28
    readonly property int colHeaderHeight: 20

    QtObject {
        id: cols
        readonly property int pos: 30
        readonly property int teamLogo: 25
        readonly property int ersDrs: 58
        readonly property int tyre: 58
        readonly property int wingDmg: 50
    }

    // Same container as the timing tower, so the row tints composite identically
    Rectangle {
        anchors.fill: parent
        anchors.margins: 4
        color: Qt.rgba(0.04, 0.04, 0.06, 0.90)
        radius: 8
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 6
        spacing: 0

        // Column headers
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: false
            Layout.preferredHeight: root.colHeaderHeight
            Layout.leftMargin: 4
            spacing: 0
            visible: root.tableData.length > 0

            Text {
                Layout.preferredWidth: cols.pos
                Layout.fillHeight: true
                text: "P"
                font.family: "Formula1"
                font.pixelSize: 10
                color: "#666666"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            Item { Layout.preferredWidth: cols.teamLogo }
            Text {
                Layout.fillWidth: true
                Layout.fillHeight: true
                text: "DRIVER"
                font.family: "Formula1"
                font.pixelSize: 10
                color: "#666666"
                verticalAlignment: Text.AlignVCenter
            }
            Text {
                Layout.preferredWidth: cols.ersDrs
                Layout.fillHeight: true
                text: "ERS/DRS"
                font.family: "Formula1"
                font.pixelSize: 10
                color: "#666666"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            Text {
                Layout.preferredWidth: cols.tyre
                Layout.fillHeight: true
                text: "TYRE"
                font.family: "Formula1"
                font.pixelSize: 10
                color: "#666666"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            Text {
                Layout.preferredWidth: cols.wingDmg
                Layout.fillHeight: true
                text: "DMG"
                font.family: "Formula1"
                font.pixelSize: 10
                color: "#666666"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        // Waiting for data
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: root.tableData.length === 0

            Text {
                anchors.centerIn: parent
                text: "WAITING FOR DATA"
                font.family: "Formula1"
                font.pixelSize: 11
                color: "#666666"
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
            visible: root.tableData.length > 0

            delegate: Item {
                id: rivalRow
                required property var modelData

                width: tableView.width
                height: root.rowHeight

                Rectangle {
                    anchors.fill: parent
                    color: rivalRow.modelData.isRef
                        ? Qt.rgba(1, 1, 1, 0.07)
                        : Qt.rgba(0.08, 0.08, 0.10, 0.6)
                    radius: 3
                }

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
                    color: rivalRow.modelData.isRef ? "#ffffff" : "transparent"
                    radius: 1
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 4
                    spacing: 0

                    // Position
                    Text {
                        Layout.preferredWidth: cols.pos
                        Layout.fillHeight: true
                        text: rivalRow.modelData.position < 10
                            ? rivalRow.modelData.position + " "
                            : rivalRow.modelData.position
                        font.family: "Consolas"
                        font.pixelSize: 12
                        color: "#dddddd"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    // Team logo
                    Item {
                        Layout.preferredWidth: cols.teamLogo
                        Layout.fillHeight: true

                        Image {
                            anchors.right: parent.right
                            anchors.rightMargin: 4
                            anchors.verticalCenter: parent.verticalCenter
                            width: 20
                            height: 20
                            sourceSize.width: width * Screen.devicePixelRatio * 2
                            sourceSize.height: height * Screen.devicePixelRatio * 2
                            source: rivalRow.modelData.teamIcon || ""
                            fillMode: Image.PreserveAspectFit
                            smooth: true
                            mipmap: true
                            cache: true
                            antialiasing: true
                        }
                    }

                    // Driver name
                    Text {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        text: rivalRow.modelData.name
                        font.family: "Formula1"
                        font.pixelSize: 13
                        color: "#ffffff"
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }

                    // ERS bar | ERS % | DRS / overtake bar
                    Item {
                        Layout.preferredWidth: cols.ersDrs
                        Layout.fillHeight: true

                        Rectangle {
                            anchors.left: parent.left
                            anchors.leftMargin: 1
                            anchors.verticalCenter: parent.verticalCenter
                            width: 6
                            height: parent.height - 8
                            radius: 2
                            color: rivalRow.modelData.ersColor || "#444444"
                        }
                        Text {
                            anchors.centerIn: parent
                            text: rivalRow.modelData.ers
                            font.family: "Consolas"
                            font.pixelSize: 13
                            color: "#dddddd"
                        }
                        Rectangle {
                            anchors.right: parent.right
                            anchors.rightMargin: 1
                            anchors.verticalCenter: parent.verticalCenter
                            width: 6
                            height: parent.height - 8
                            radius: 2
                            color: rivalRow.modelData.overtakeBarColor || "#333333"
                        }
                    }

                    // Tyre icon + wear/age
                    Item {
                        Layout.preferredWidth: cols.tyre
                        Layout.fillHeight: true

                        Row {
                            anchors.centerIn: parent
                            spacing: 4

                            Image {
                                width: 20
                                height: 20
                                sourceSize.width: width * Screen.devicePixelRatio
                                sourceSize.height: height * Screen.devicePixelRatio
                                source: rivalRow.modelData.tyreIcon || ""
                                fillMode: Image.PreserveAspectFit
                                smooth: true
                                anchors.verticalCenter: parent.verticalCenter
                                cache: true
                                antialiasing: true
                            }
                            Text {
                                text: rivalRow.modelData.tyreWear
                                font.family: "Consolas"
                                font.pixelSize: 13
                                color: "#ffffff"
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }
                    }

                    // Wing damage
                    Text {
                        Layout.preferredWidth: cols.wingDmg
                        Layout.fillHeight: true
                        text: rivalRow.modelData.wingDmg
                        font.family: "Consolas"
                        font.pixelSize: 12
                        color: rivalRow.modelData.wingDmgColor
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }
    }
}
