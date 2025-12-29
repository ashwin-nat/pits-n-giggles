import QtQuick
import QtQuick.Layouts

Item {
    id: page
    width: parent ? parent.width : 600
    height: parent ? parent.height : 220

    /* ---------- WEATHER EMOJIS ---------- */
    readonly property var weatherEmojis: ({
        "Clear": "☀️",
        "Light Cloud": "🌤️",
        "Overcast": "☁️",
        "Light Rain": "🌦️",
        "Heavy Rain": "🌧️",
        "Storm": "⛈️",
        "Thunderstorm": "⛈️"
    })

    /* ---------- COLORS ---------- */
    readonly property color separatorColor: "#444444"
    readonly property color primaryTextColor: "#EEE"
    readonly property color dimTextColor: "#999999"
    readonly property color rainColor: "#7dafff"
    readonly property color tempUpColor: "#ff6666"
    readonly property color tempDownColor: "#6699ff"

    /* ---------- DATA PROPERTIES ---------- */
    property var forecastData: []

    RowLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 8

        Item { Layout.fillWidth: true }

        Repeater {
            id: cardRepeater
            model: forecastData.length

            delegate: Item {
                Layout.fillHeight: true
                Layout.preferredWidth: 100
                Layout.maximumWidth: 100

                WeatherCard {
                    anchors.fill: parent
                    anchors.margins: 4
                    cardData: forecastData[index]
                }

                // Separator after each card except the last
                Rectangle {
                    visible: index < forecastData.length - 1
                    width: 1
                    height: Math.min(parent.height * 0.6, 120)
                    color: separatorColor
                    anchors.left: parent.right
                    anchors.leftMargin: 4
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }

        Item { Layout.fillWidth: true }
    }

    component WeatherCard: Item {
        id: card
        required property var cardData

        Column {
            anchors.fill: parent
            anchors.margins: 4
            spacing: 6

            // Time offset
            Text {
                text: {
                    const offset = cardData["time-offset"] || 0
                    return offset > 0 ? `+${offset}m` : "Now"
                }
                font.family: "Consolas"
                font.pixelSize: 15
                font.weight: Font.DemiBold
                color: primaryTextColor
                anchors.horizontalCenter: parent.horizontalCenter
            }

            // Weather emoji
            Text {
                text: weatherEmojis[cardData.weather] || "☀️"
                font.pixelSize: 24
                anchors.horizontalCenter: parent.horizontalCenter
            }

            // Track temperature row
            TemperatureRow {
                width: parent.width
                iconSource: "../../../../../../../assets/overlays/road.svg"
                temperature: cardData["track-temperature"]
                temperatureChange: cardData["track-temperature-change"]
            }

            // Air temperature row
            TemperatureRow {
                width: parent.width
                iconSource: "../../../../../../../assets/overlays/thermometer-half.svg"
                temperature: cardData["air-temperature"]
                temperatureChange: cardData["air-temperature-change"]
            }

            // Rain percentage
            Text {
                text: `💧 ${cardData["rain-percentage"] || 0}%`
                font.family: "Consolas"
                font.pixelSize: 13
                font.weight: Font.Bold
                color: rainColor
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }
    }

    component TemperatureRow: Row {
        required property string iconSource
        required property var temperature
        required property string temperatureChange

        spacing: 4

        // Icon
        Image {
            width: 16
            height: 16
            source: iconSource
            sourceSize.width: 16
            sourceSize.height: 16
            fillMode: Image.PreserveAspectFit
            anchors.verticalCenter: parent.verticalCenter
        }

        // Temperature value
        Text {
            text: temperature !== undefined ? `${temperature}°C` : "N/A"
            font.family: "Consolas"
            font.pixelSize: 13
            font.weight: Font.Bold
            color: primaryTextColor
            anchors.verticalCenter: parent.verticalCenter
        }

        // Temperature change arrow
        Text {
            text: {
                if (temperatureChange === "Temperature Up") return "▲"
                if (temperatureChange === "Temperature Down") return "▼"
                return "─"
            }
            font.family: "Consolas"
            font.pixelSize: 14
            font.weight: Font.Bold
            color: {
                if (temperatureChange === "Temperature Up") return tempUpColor
                if (temperatureChange === "Temperature Down") return tempDownColor
                return dimTextColor
            }
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}