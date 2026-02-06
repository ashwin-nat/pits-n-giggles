import QtQuick
import QtQuick.Layouts

Item {
    id: page
    width: parent ? parent.width : 600
    height: parent ? parent.height : 220
    clip: true
    property string title: "WEATHER FORECAST"

    /* ---------- UI MODE ---------- */
    property bool graphBasedUI: true

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
    readonly property color trackTempColor: "#ff6666"
    readonly property color airTempColor: "#66ff66"
    readonly property color tempUpColor: "#ff6666"
    readonly property color tempDownColor: "#6699ff"
    readonly property color gridColor: "#333333"

    /* ---------- FONT SIZES ---------- */
    readonly property int yAxisLabelFontSize: 11
    readonly property int timeOffsetFontSize: 11
    readonly property int legendFontSize: 11

    /* ---------- DATA ---------- */
    property var forecastData: []
    property string sessionTitle: ""

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

        Column {
            anchors.fill: parent
            spacing: 8

            // Session title
            Text {
                visible: sessionTitle !== ""
                text: sessionTitle
                font.family: "Formula1"
                font.pixelSize: 14
                font.weight: Font.Bold
                color: primaryTextColor
                horizontalAlignment: Text.AlignHCenter
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Item {
                width: parent.width
                height: parent.height - (sessionTitle !== "" ? 30 : 0)

                // No data message
                Text {
                    visible: forecastData.length === 0
                    anchors.centerIn: parent
                    text: "WAITING FOR DATA ..."
                    font.family: "Formula1"
                    font.pixelSize: 14
                    font.weight: Font.Bold
                    color: dimTextColor
                    horizontalAlignment: Text.AlignHCenter
                }

                // CARD-BASED UI
                Row {
                    visible: forecastData.length > 0 && !graphBasedUI
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

                // GRAPH-BASED UI
                WeatherGraph {
                    visible: forecastData.length > 0 && graphBasedUI
                    anchors.fill: parent
                    anchors.margins: 4
                    forecastData: page.forecastData
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
                antialiasing: true
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
                    antialiasing: true
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
                antialiasing: true
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
                antialiasing: true
            }
        }
    }

    component WeatherGraph: Item {
        id: graphRoot
        required property var forecastData

        readonly property int graphMarginLeft: 45
        readonly property int graphMarginRight: 45
        readonly property int graphMarginTop: 18
        readonly property int graphMarginBottom: 42
        readonly property int graphWidth: width - graphMarginLeft - graphMarginRight
        readonly property int graphHeight: height - graphMarginTop - graphMarginBottom

        // Calculate min/max values for scaling
        readonly property var dataStats: {
            if (forecastData.length === 0) return { minTemp: 0, maxTemp: 100, maxRain: 100 }

            let minTemp = 999
            let maxTemp = -999
            let maxRain = 0

            for (let i = 0; i < forecastData.length; i++) {
                const item = forecastData[i]
                const trackTemp = item["track-temperature"]
                const airTemp = item["air-temperature"]
                const rain = item["rain-percentage"] || 0

                if (trackTemp !== undefined) {
                    minTemp = Math.min(minTemp, trackTemp)
                    maxTemp = Math.max(maxTemp, trackTemp)
                }
                if (airTemp !== undefined) {
                    minTemp = Math.min(minTemp, airTemp)
                    maxTemp = Math.max(maxTemp, airTemp)
                }
                maxRain = Math.max(maxRain, rain)
            }

            // Add padding to temperature range
            const tempRange = maxTemp - minTemp
            const padding = Math.max(5, tempRange * 0.1)

            return {
                minTemp: Math.floor(minTemp - padding),
                maxTemp: Math.ceil(maxTemp + padding),
                maxRain: Math.max(100, maxRain)
            }
        }

        // Convert data value to Y coordinate
        function valueToY(value, minVal, maxVal) {
            const range = maxVal - minVal
            if (range === 0) return graphMarginTop + graphHeight / 2
            const normalized = (value - minVal) / range
            return graphMarginTop + graphHeight * (1 - normalized)
        }

        // Convert index to X coordinate
        function indexToX(index) {
            const count = Math.max(1, forecastData.length - 1)
            return graphMarginLeft + (graphWidth * index / count)
        }

        // Background grid
        Canvas {
            id: gridCanvas
            anchors.fill: parent
            onPaint: {
                const ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)

                // Horizontal grid lines (5 lines)
                ctx.strokeStyle = gridColor
                ctx.lineWidth = 1
                ctx.setLineDash([3, 3])

                for (let i = 0; i <= 4; i++) {
                    const y = graphMarginTop + (graphHeight * i / 4)
                    ctx.beginPath()
                    ctx.moveTo(graphMarginLeft, y)
                    ctx.lineTo(graphMarginLeft + graphWidth, y)
                    ctx.stroke()
                }

                // Vertical grid lines (one per data point)
                for (let i = 0; i < forecastData.length; i++) {
                    const x = indexToX(i)
                    ctx.beginPath()
                    ctx.moveTo(x, graphMarginTop)
                    ctx.lineTo(x, graphMarginTop + graphHeight)
                    ctx.stroke()
                }
            }
        }

        // Y-axis labels (temperature)
        Item {
            x: 0
            y: graphMarginTop
            width: graphMarginLeft - 5
            height: graphHeight

            Repeater {
                model: 5
                Item {
                    width: parent.width
                    height: 12
                    y: (parent.height * index / 4) - 6

                    Text {
                        text: {
                            const ratio = (4 - index) / 4
                            const temp = dataStats.minTemp + ratio * (dataStats.maxTemp - dataStats.minTemp)
                            return Math.round(temp) + "°"
                        }
                        font.family: "Consolas"
                        font.pixelSize: yAxisLabelFontSize
                        color: dimTextColor
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.rightMargin: 5
                    }
                }
            }
        }

        // Rain percentage scale (right side)
        Item {
            x: graphMarginLeft + graphWidth + 5
            y: graphMarginTop
            width: graphMarginRight - 10
            height: graphHeight

            Repeater {
                model: 5
                Item {
                    width: parent.width
                    height: 12
                    y: (parent.height * index / 4) - 6

                    Text {
                        text: {
                            const ratio = (4 - index) / 4
                            const rain = ratio * 100
                            return Math.round(rain) + "%"
                        }
                        font.family: "Consolas"
                        font.pixelSize: yAxisLabelFontSize
                        color: rainColor
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
        }

        // Graph lines
        Canvas {
            id: graphCanvas
            anchors.fill: parent
            onPaint: {
                const ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)

                if (forecastData.length === 0) return

                // Draw rain percentage line
                ctx.strokeStyle = rainColor
                ctx.lineWidth = 2
                ctx.setLineDash([])
                ctx.beginPath()
                for (let i = 0; i < forecastData.length; i++) {
                    const x = indexToX(i)
                    const rain = forecastData[i]["rain-percentage"] || 0
                    const y = valueToY(rain, 0, 100)
                    if (i === 0) ctx.moveTo(x, y)
                    else ctx.lineTo(x, y)
                }
                ctx.stroke()

                // Draw track temperature line
                ctx.strokeStyle = trackTempColor
                ctx.lineWidth = 2
                ctx.beginPath()
                let started = false
                for (let i = 0; i < forecastData.length; i++) {
                    const temp = forecastData[i]["track-temperature"]
                    if (temp !== undefined) {
                        const x = indexToX(i)
                        const y = valueToY(temp, dataStats.minTemp, dataStats.maxTemp)
                        if (!started) {
                            ctx.moveTo(x, y)
                            started = true
                        } else {
                            ctx.lineTo(x, y)
                        }
                    }
                }
                ctx.stroke()

                // Draw air temperature line
                ctx.strokeStyle = airTempColor
                ctx.lineWidth = 2
                ctx.beginPath()
                started = false
                for (let i = 0; i < forecastData.length; i++) {
                    const temp = forecastData[i]["air-temperature"]
                    if (temp !== undefined) {
                        const x = indexToX(i)
                        const y = valueToY(temp, dataStats.minTemp, dataStats.maxTemp)
                        if (!started) {
                            ctx.moveTo(x, y)
                            started = true
                        } else {
                            ctx.lineTo(x, y)
                        }
                    }
                }
                ctx.stroke()

                // Draw data points
                for (let i = 0; i < forecastData.length; i++) {
                    const x = indexToX(i)

                    // Rain point
                    const rain = forecastData[i]["rain-percentage"] || 0
                    const rainY = valueToY(rain, 0, 100)
                    ctx.fillStyle = rainColor
                    ctx.beginPath()
                    ctx.arc(x, rainY, 3, 0, Math.PI * 2)
                    ctx.fill()

                    // Track temp point
                    const trackTemp = forecastData[i]["track-temperature"]
                    if (trackTemp !== undefined) {
                        const trackY = valueToY(trackTemp, dataStats.minTemp, dataStats.maxTemp)
                        ctx.fillStyle = trackTempColor
                        ctx.beginPath()
                        ctx.arc(x, trackY, 3, 0, Math.PI * 2)
                        ctx.fill()
                    }

                    // Air temp point
                    const airTemp = forecastData[i]["air-temperature"]
                    if (airTemp !== undefined) {
                        const airY = valueToY(airTemp, dataStats.minTemp, dataStats.maxTemp)
                        ctx.fillStyle = airTempColor
                        ctx.beginPath()
                        ctx.arc(x, airY, 3, 0, Math.PI * 2)
                        ctx.fill()
                    }
                }
            }

            Connections {
                target: graphRoot
                function onForecastDataChanged() { graphCanvas.requestPaint() }
            }
        }

        // X-axis labels (time) and weather icons
        Item {
            x: graphMarginLeft
            y: graphMarginTop + graphHeight + 3
            width: graphWidth
            height: 35

            Repeater {
                model: forecastData.length

                Item {
                    x: index === 0 ? 0 : (graphWidth * index / Math.max(1, forecastData.length - 1))
                    width: 1
                    height: 35

                    Column {
                        anchors.horizontalCenter: parent.horizontalCenter
                        spacing: 2

                        // Time label
                        Text {
                            text: {
                                const offset = forecastData[index]["time-offset"] || 0
                                return offset > 0 ? `+${offset}m` : "Now"
                            }
                            font.family: "Consolas"
                            font.pixelSize: timeOffsetFontSize
                            font.weight: Font.Bold
                            color: primaryTextColor
                            anchors.horizontalCenter: parent.horizontalCenter
                        }

                        // Weather icon
                        Image {
                            width: 16
                            height: 16
                            anchors.horizontalCenter: parent.horizontalCenter
                            source: weatherIcons[forecastData[index].weather] || weatherIcons["Clear"]
                            fillMode: Image.PreserveAspectFit
                            antialiasing: true
                            smooth: true
                            mipmap: true
                        }
                    }
                }
            }
        }

        // Legend (moved above X-axis area)
        Row {
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.rightMargin: 10
            anchors.topMargin: -2
            spacing: 15

            Row {
                spacing: 4
                Rectangle {
                    width: 16
                    height: 3
                    color: rainColor
                    anchors.verticalCenter: parent.verticalCenter
                }
                Text {
                    text: "Rain %"
                    font.family: "Consolas"
                    font.pixelSize: legendFontSize
                    color: rainColor
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            Row {
                spacing: 4
                Rectangle {
                    width: 16
                    height: 3
                    color: trackTempColor
                    anchors.verticalCenter: parent.verticalCenter
                }
                Text {
                    text: "Track °C"
                    font.family: "Consolas"
                    font.pixelSize: legendFontSize
                    color: trackTempColor
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            Row {
                spacing: 4
                Rectangle {
                    width: 16
                    height: 3
                    color: airTempColor
                    anchors.verticalCenter: parent.verticalCenter
                }
                Text {
                    text: "Air °C"
                    font.family: "Consolas"
                    font.pixelSize: legendFontSize
                    color: airTempColor
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }

        // Redraw graph when data changes
        Connections {
            target: graphRoot
            function onForecastDataChanged() {
                gridCanvas.requestPaint()
                graphCanvas.requestPaint()
            }
        }
    }
}
