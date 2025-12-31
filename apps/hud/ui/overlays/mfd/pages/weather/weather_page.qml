import QtQuick
import QtQuick.Layouts

Item {
    id: page
    width: parent ? parent.width : 600
    height: parent ? parent.height : 220
    clip: true
    property string title: "WEATHER FORECAST"

    /* ---------- WEATHER ICONS (SVG) ---------- */
    readonly property var weatherIcons: ({
        "Clear": "../../../../../../../assets/weather/clear.svg",
        "Light Cloud": "../../../../../../../assets/weather/light-cloud.svg",
        "Overcast": "../../../../../../../assets/weather/overcast.svg",
        "Light Rain": "../../../../../../../assets/weather/light-rain.svg",
        "Heavy Rain": "../../../../../../../assets/weather/heavy-rain.svg",
        "Storm": "../../../../../../../assets/weather/storm.svg",
        "Thunderstorm": "../../../../../../../assets/weather/thunderstorm.svg"
    })

    readonly property string rainIcon: "../../../../../../../assets/weather/rain-drop.svg"
    readonly property string arrowUpIcon: "../../../../../../../assets/weather/arrow-up.svg"
    readonly property string arrowDownIcon: "../../../../../../../assets/weather/arrow-down.svg"
    readonly property string dashIcon: "../../../../../../../assets/weather/dash.svg"

    /* ---------- COLORS ---------- */
    readonly property color separatorColor: "#444444"
    readonly property color primaryTextColor: "#EEE"
    readonly property color dimTextColor: "#999999"
    readonly property color rainColor: "#7dafff"
    readonly property color tempUpColor: "#ff6666"
    readonly property color tempDownColor: "#6699ff"

    /* ---------- DATA ---------- */
    property var forecastData: []

    readonly property int maxCards: 5
    readonly property int separatorWidth: 1
    readonly property int cardSpacing: 6
    readonly property int totalMargin: 16
    readonly property int cardCount: Math.min(forecastData.length, maxCards)
    readonly property int availableWidth: width - totalMargin
    readonly property int totalSpacing: (cardCount - 1) * (separatorWidth + cardSpacing * 2)
    readonly property int cardWidth: cardCount > 0
        ? Math.floor((availableWidth - totalSpacing) / cardCount)
        : 80

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

            // Weather icon (SVG)
            Image {
                width: 20
                height: 20
                anchors.horizontalCenter: parent.horizontalCenter
                source: weatherIcons[cardData.weather] || weatherIcons["Clear"]
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
            }

            // Track temperature
            TemperatureRow {
                width: parent.width
                iconSource: "../../../../../../../assets/overlays/road.svg"
                temperature: cardData["track-temperature"]
                temperatureChange: cardData["track-temperature-change"]
            }

            // Air temperature
            TemperatureRow {
                width: parent.width
                iconSource: "../../../../../../../assets/overlays/thermometer-half.svg"
                temperature: cardData["air-temperature"]
                temperatureChange: cardData["air-temperature-change"]
            }

            // Rain percentage
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 3

                Image {
                    width: 11
                    height: 11
                    source: rainIcon
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                }

                Text {
                    text: `${cardData["rain-percentage"] || 0}%`
                    font.family: "Consolas"
                    font.pixelSize: 11
                    font.weight: Font.Bold
                    color: rainColor
                }
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

            Image {
                width: 12
                height: 12
                source: iconSource
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
                anchors.verticalCenter: parent.verticalCenter
            }

            Text {
                text: temperature !== undefined ? `${temperature}°C` : "N/A"
                font.family: "Consolas"
                font.pixelSize: 11
                font.weight: Font.Bold
                color: primaryTextColor
                anchors.verticalCenter: parent.verticalCenter
            }

            Image {
                width: 10
                height: 10
                anchors.verticalCenter: parent.verticalCenter
                source: {
                    if (temperatureChange === "Temperature Up") return arrowUpIcon
                    if (temperatureChange === "Temperature Down") return arrowDownIcon
                    return dashIcon
                }
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
            }
        }
    }
}
