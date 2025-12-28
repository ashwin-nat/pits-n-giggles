import QtQuick

Item {
    id: page
    width: parent ? parent.width : 0
    implicitHeight: 36

    Component.onCompleted: {
        console.log("Collapsed page base URL:", Qt.resolvedUrl("."))
        console.log("Icon resolved to:", Qt.resolvedUrl(iconSource))
    }

    property string title: "Pits n' Giggles MFD"
    property url iconSource: "../../../../../../../assets/logo.png"

    Rectangle {
        anchors.fill: parent
        color: "#000000"
        opacity: 0.35
    }

    Row {
        id: content
        anchors.centerIn: parent
        spacing: 6

        // Icon wrapper to control vertical alignment
        Item {
            width: 24
            height: textItem.implicitHeight

            Image {
                anchors.centerIn: parent
                source: page.iconSource
                width: 24
                height: 24
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
            }
        }

        Text {
            id: textItem
            text: page.title
            font.pixelSize: 13
            font.family: "Formula1"
            color: "white"
            verticalAlignment: Text.AlignVCenter
        }
    }
}
