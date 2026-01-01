import QtQuick

Item {
    id: page
    width: parent ? parent.width : 400
    height: parent ? parent.height : 36

    property string title: "Pits n' Giggles MFD"
    property url iconSource: "../../../../../../../assets/logo.png"

    Rectangle {
        id: background
        anchors.fill: parent
        color: "#000000"
        opacity: 0.35
    }

    Row {
        id: contentRow
        anchors.centerIn: parent
        spacing: 6

        // Icon wrapper to control vertical alignment
        Item {
            id: iconContainer
            width: 24
            height: 24

            Image {
                id: icon
                anchors.centerIn: parent
                source: page.iconSource
                width: 24
                height: 24
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
            }
        }

        Item {
            id: textContainer
            height: 24
            width: titleText.implicitWidth
            anchors.verticalCenter: iconContainer.verticalCenter

            Text {
                id: titleText
                anchors.centerIn: parent
                text: page.title
                font.pixelSize: 13
                font.family: "Formula1"
                color: "white"
                verticalAlignment: Text.AlignVCenter
            }
        }
    }
}
