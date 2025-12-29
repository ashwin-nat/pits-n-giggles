import QtQuick
import QtQuick.Layouts

Item {
    id: page
    width: parent ? parent.width : 600
    height: parent ? parent.height : 220
    clip: true

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

    // Calculate card width dynamically based on available space
    readonly property int maxCards: 5
    readonly property int separatorWidth: 1
    readonly property int cardSpacing: 6
    readonly property int totalMargin: 16
    readonly property int cardCount: Math.min(forecastData.length, maxCards)
    readonly property int availableWidth: width - totalMargin
    readonly property int totalSpacing: (cardCount - 1) * (separatorWidth + cardSpacing * 2)
    readonly property int cardWidth: cardCount > 0 ? Math.floor((availableWidth - totalSpacing) / cardCount) : 80

    Rectangle {
        anchors.fill: parent
        color: "transparent"

        Row {
            anchors.centerIn: parent
            spacing: cardSpacing

            Repeater {
                model: forecastData.length

                Row {
                    spacing: cardSpacing

                    WeatherCard {
                        width: cardWidth
                        height: page.height - 20
                        cardData: forecastData[index]
                    }

                    // Separator
                    Rectangle {
                        visible: index < forecastData.length - 1
                        width: separatorWidth
                        height: Math.min(page.height * 0.6, 120)
                        color: separatorColor
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
        }
    }

    component WeatherCard: Item {
        id: card
        required property var cardData

        Column {
            anchors.centerIn: parent
            width: parent.width - 4
            spacing: 3

            // Time offset
            Text {
                text: {
                    const offset = cardData["time-offset"] || 0
                    return offset > 0 ? `+${offset}m` : "Now"
                }
                font.family: "Consolas"
                font.pixelSize: 13
                font.weight: Font.DemiBold
                color: primaryTextColor
                horizontalAlignment: Text.AlignHCenter
                width: parent.width
            }

            // Weather emoji
            Text {
                text: weatherEmojis[cardData.weather] || "☀️"
                font.pixelSize: 20
                horizontalAlignment: Text.AlignHCenter
                width: parent.width
                textFormat: Text.PlainText
                renderType: Text.NativeRendering
                smooth: true
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
                font.pixelSize: 11
                font.weight: Font.Bold
                color: rainColor
                horizontalAlignment: Text.AlignHCenter
                width: parent.width
                textFormat: Text.PlainText
                renderType: Text.NativeRendering
                smooth: true
            }
        }
    }

    component TemperatureRow: Item {
        required property string iconSource
        required property var temperature
        required property string temperatureChange

        height: 18

        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 2

            // Icon
            Image {
                width: 12
                height: 12
                source: iconSource
                sourceSize.width: 48
                sourceSize.height: 48
                fillMode: Image.PreserveAspectFit
                smooth: true
                antialiasing: true
                mipmap: true
                anchors.verticalCenter: parent.verticalCenter
            }

            // Temperature value
            Text {
                text: temperature !== undefined ? `${temperature}°C` : "N/A"
                font.family: "Consolas"
                font.pixelSize: 11
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
                font.pixelSize: 11
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
}
