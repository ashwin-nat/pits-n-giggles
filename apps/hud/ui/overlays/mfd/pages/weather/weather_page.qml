pragma ComponentBehavior: Bound
import QtQuick

Item {
    id: page
    width: parent ? parent.width : 600
    height: parent ? parent.height : 220
    clip: true
    property string title: "WEATHER FORECAST"

    /* ---------- UI MODE ---------- */
    property bool graphBasedUI: true

    /* ---------- STANDALONE SIZING ---------- */
    // Preferred window height when hosted standalone (StandalonePageHost reads this).
    // The card layout only needs ~130px of content; the graph benefits from the full
    // height. Ignored inside the MFD, which forces its own fixed page height.
    readonly property int standaloneHeight: graphBasedUI ? 220 : 140

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
    readonly property color primaryTextColor: "#EEEEEE"
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
                visible: page.sessionTitle !== ""
                text: page.sessionTitle
                font.family: "Formula1"
                font.pixelSize: 14
                font.weight: Font.Bold
                color: page.primaryTextColor
                horizontalAlignment: Text.AlignHCenter
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Item {
                width: parent.width
                height: parent.height - (page.sessionTitle !== "" ? 30 : 0)

                // No data message
                Text {
                    visible: page.forecastData.length === 0
                    anchors.centerIn: parent
                    text: "WAITING FOR DATA ..."
                    font.family: "Formula1"
                    font.pixelSize: 14
                    font.weight: Font.Bold
                    color: page.dimTextColor
                    horizontalAlignment: Text.AlignHCenter
                }

                // CARD-BASED UI
                Row {
                    visible: page.forecastData.length > 0 && !page.graphBasedUI
                    anchors.centerIn: parent
                    spacing: page.cardSpacing

                    Repeater {
                        model: page.forecastData.length

                        Row {
                            id: cardRow
                            required property int index
                            spacing: page.cardSpacing

                            WeatherCard {
                                width: page.cardWidth
                                height: page.height - 20
                                cardData: page.forecastData[cardRow.index]
                            }

                            Rectangle {
                                visible: cardRow.index < page.forecastData.length - 1
                                width: page.separatorWidth
                                height: Math.min(page.height * 0.6, 120)
                                color: page.separatorColor
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }
                    }
                }

                // GRAPH-BASED UI
                WeatherGraph {
                    visible: page.forecastData.length > 0 && page.graphBasedUI
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
                    const offset = card.cardData["time-offset"] || 0
                    return offset > 0 ? `+${offset}m` : "Now"
                }
                font.family: "Consolas"
                font.pixelSize: 13
                font.weight: Font.DemiBold
                color: page.primaryTextColor
                horizontalAlignment: Text.AlignHCenter
                width: parent.width
            }

            // Weather icon (SVG)
            Image {
                width: 20
                height: 20
                anchors.horizontalCenter: parent.horizontalCenter
                source: page.weatherIcons[card.cardData.weather] || page.weatherIcons["Clear"]
                fillMode: Image.PreserveAspectFit
                antialiasing: true
                smooth: true
                mipmap: true
            }

            // Track temperature
            TemperatureRow {
                width: parent.width
                iconSource: "../../../../../../../assets/overlays/track-temperature.svg"
                temperature: card.cardData["track-temperature"]
                temperatureChange: card.cardData["track-temperature-change"]
            }

            // Air temperature
            TemperatureRow {
                width: parent.width
                iconSource: "../../../../../../../assets/overlays/air-temperature.svg"
                temperature: card.cardData["air-temperature"]
                temperatureChange: card.cardData["air-temperature-change"]
            }

            // Rain percentage
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 3

                Image {
                    width: 11
                    height: 11
                    source: page.rainIcon
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                    antialiasing: true
                }

                Text {
                    text: `${card.cardData["rain-percentage"] || 0}%`
                    font.family: "Consolas"
                    font.pixelSize: 11
                    font.weight: Font.Bold
                    color: page.rainColor
                }
            }
        }
    }

    component TemperatureRow: Item {
        id: tempRow
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
                source: tempRow.iconSource
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
                anchors.verticalCenter: parent.verticalCenter
                antialiasing: true
            }

            Text {
                text: tempRow.temperature !== undefined ? `${tempRow.temperature}°C` : "N/A"
                font.family: "Consolas"
                font.pixelSize: 11
                font.weight: Font.Bold
                color: page.primaryTextColor
                anchors.verticalCenter: parent.verticalCenter
            }

            Image {
                width: 10
                height: 10
                anchors.verticalCenter: parent.verticalCenter
                source: {
                    if (tempRow.temperatureChange === "Temperature Up") return page.arrowUpIcon
                    if (tempRow.temperatureChange === "Temperature Down") return page.arrowDownIcon
                    return page.dashIcon
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
            if (graphRoot.forecastData.length === 0) return { minTemp: 0, maxTemp: 100, maxRain: 100 }

            let minTemp = 999
            let maxTemp = -999
            let maxRain = 0

            for (let i = 0; i < graphRoot.forecastData.length; i++) {
                const item = graphRoot.forecastData[i]
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
            if (range === 0) return graphRoot.graphMarginTop + graphRoot.graphHeight / 2
            const normalized = (value - minVal) / range
            return graphRoot.graphMarginTop + graphRoot.graphHeight * (1 - normalized)
        }

        // Convert index to X coordinate
        function indexToX(index) {
            const count = Math.max(1, graphRoot.forecastData.length - 1)
            return graphRoot.graphMarginLeft + (graphRoot.graphWidth * index / count)
        }

        // Background grid
        Canvas {
            id: gridCanvas
            anchors.fill: parent
            onPaint: {
                const ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)

                // Horizontal grid lines (5 lines)
                ctx.strokeStyle = page.gridColor
                ctx.lineWidth = 1
                ctx.setLineDash([3, 3])

                for (let i = 0; i <= 4; i++) {
                    const y = graphRoot.graphMarginTop + (graphRoot.graphHeight * i / 4)
                    ctx.beginPath()
                    ctx.moveTo(graphRoot.graphMarginLeft, y)
                    ctx.lineTo(graphRoot.graphMarginLeft + graphRoot.graphWidth, y)
                    ctx.stroke()
                }

                // Vertical grid lines (one per data point)
                for (let i = 0; i < graphRoot.forecastData.length; i++) {
                    const x = graphRoot.indexToX(i)
                    ctx.beginPath()
                    ctx.moveTo(x, graphRoot.graphMarginTop)
                    ctx.lineTo(x, graphRoot.graphMarginTop + graphRoot.graphHeight)
                    ctx.stroke()
                }
            }
        }

        // Y-axis labels (temperature)
        Item {
            x: 0
            y: graphRoot.graphMarginTop
            width: graphRoot.graphMarginLeft - 5
            height: graphRoot.graphHeight

            Repeater {
                model: 5
                Item {
                    id: yAxisTick
                    required property int index

                    width: parent ? parent.width : 0
                    height: 12
                    y: parent ? (parent.height * yAxisTick.index / 4) - 6 : 0

                    Text {
                        text: {
                            const ratio = (4 - yAxisTick.index) / 4
                            const temp = graphRoot.dataStats.minTemp + ratio * (graphRoot.dataStats.maxTemp - graphRoot.dataStats.minTemp)
                            return Math.round(temp) + "°"
                        }
                        font.family: "Consolas"
                        font.pixelSize: page.yAxisLabelFontSize
                        color: page.dimTextColor
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.rightMargin: 5
                    }
                }
            }
        }

        // Rain percentage scale (right side)
        Item {
            x: graphRoot.graphMarginLeft + graphRoot.graphWidth + 5
            y: graphRoot.graphMarginTop
            width: graphRoot.graphMarginRight - 10
            height: graphRoot.graphHeight

            Repeater {
                model: 5
                Item {
                    id: rainAxisTick
                    required property int index

                    width: parent ? parent.width : 0
                    height: 12
                    y: parent ? (parent.height * rainAxisTick.index / 4) - 6 : 0

                    Text {
                        text: {
                            const ratio = (4 - rainAxisTick.index) / 4
                            const rain = ratio * 100
                            return Math.round(rain) + "%"
                        }
                        font.family: "Consolas"
                        font.pixelSize: page.yAxisLabelFontSize
                        color: page.rainColor
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

                if (graphRoot.forecastData.length === 0) return

                // Draw rain percentage line
                ctx.strokeStyle = page.rainColor
                ctx.lineWidth = 2
                ctx.setLineDash([])
                ctx.beginPath()
                for (let i = 0; i < graphRoot.forecastData.length; i++) {
                    const x = graphRoot.indexToX(i)
                    const rain = graphRoot.forecastData[i]["rain-percentage"] || 0
                    const y = graphRoot.valueToY(rain, 0, 100)
                    if (i === 0) ctx.moveTo(x, y)
                    else ctx.lineTo(x, y)
                }
                ctx.stroke()

                // Draw track temperature line
                ctx.strokeStyle = page.trackTempColor
                ctx.lineWidth = 2
                ctx.beginPath()
                let started = false
                for (let i = 0; i < graphRoot.forecastData.length; i++) {
                    const temp = graphRoot.forecastData[i]["track-temperature"]
                    if (temp !== undefined) {
                        const x = graphRoot.indexToX(i)
                        const y = graphRoot.valueToY(temp, graphRoot.dataStats.minTemp, graphRoot.dataStats.maxTemp)
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
                ctx.strokeStyle = page.airTempColor
                ctx.lineWidth = 2
                ctx.beginPath()
                started = false
                for (let i = 0; i < graphRoot.forecastData.length; i++) {
                    const temp = graphRoot.forecastData[i]["air-temperature"]
                    if (temp !== undefined) {
                        const x = graphRoot.indexToX(i)
                        const y = graphRoot.valueToY(temp, graphRoot.dataStats.minTemp, graphRoot.dataStats.maxTemp)
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
                for (let i = 0; i < graphRoot.forecastData.length; i++) {
                    const x = graphRoot.indexToX(i)

                    // Rain point
                    const rain = graphRoot.forecastData[i]["rain-percentage"] || 0
                    const rainY = graphRoot.valueToY(rain, 0, 100)
                    ctx.fillStyle = page.rainColor
                    ctx.beginPath()
                    ctx.arc(x, rainY, 3, 0, Math.PI * 2)
                    ctx.fill()

                    // Track temp point
                    const trackTemp = graphRoot.forecastData[i]["track-temperature"]
                    if (trackTemp !== undefined) {
                        const trackY = graphRoot.valueToY(trackTemp, graphRoot.dataStats.minTemp, graphRoot.dataStats.maxTemp)
                        ctx.fillStyle = page.trackTempColor
                        ctx.beginPath()
                        ctx.arc(x, trackY, 3, 0, Math.PI * 2)
                        ctx.fill()
                    }

                    // Air temp point
                    const airTemp = graphRoot.forecastData[i]["air-temperature"]
                    if (airTemp !== undefined) {
                        const airY = graphRoot.valueToY(airTemp, graphRoot.dataStats.minTemp, graphRoot.dataStats.maxTemp)
                        ctx.fillStyle = page.airTempColor
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
            x: graphRoot.graphMarginLeft
            y: graphRoot.graphMarginTop + graphRoot.graphHeight + 3
            width: graphRoot.graphWidth
            height: 35

            Repeater {
                model: graphRoot.forecastData.length

                Item {
                    id: xAxisTick
                    required property int index

                    x: xAxisTick.index === 0 ? 0 : (graphRoot.graphWidth * xAxisTick.index / Math.max(1, graphRoot.forecastData.length - 1))
                    width: 1
                    height: 35

                    Column {
                        anchors.horizontalCenter: parent.horizontalCenter
                        spacing: 2

                        // Time label
                        Text {
                            text: {
                                const offset = graphRoot.forecastData[xAxisTick.index]["time-offset"] || 0
                                return offset > 0 ? `+${offset}m` : "Now"
                            }
                            font.family: "Consolas"
                            font.pixelSize: page.timeOffsetFontSize
                            font.weight: Font.Bold
                            color: page.primaryTextColor
                            anchors.horizontalCenter: parent.horizontalCenter
                        }

                        // Weather icon
                        Image {
                            width: 16
                            height: 16
                            anchors.horizontalCenter: parent.horizontalCenter
                            source: page.weatherIcons[graphRoot.forecastData[xAxisTick.index].weather] || page.weatherIcons["Clear"]
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
                    color: page.rainColor
                    anchors.verticalCenter: parent.verticalCenter
                }
                Text {
                    text: "Rain %"
                    font.family: "Consolas"
                    font.pixelSize: page.legendFontSize
                    color: page.rainColor
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            Row {
                spacing: 4
                Rectangle {
                    width: 16
                    height: 3
                    color: page.trackTempColor
                    anchors.verticalCenter: parent.verticalCenter
                }
                Text {
                    text: "Track °C"
                    font.family: "Consolas"
                    font.pixelSize: page.legendFontSize
                    color: page.trackTempColor
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            Row {
                spacing: 4
                Rectangle {
                    width: 16
                    height: 3
                    color: page.airTempColor
                    anchors.verticalCenter: parent.verticalCenter
                }
                Text {
                    text: "Air °C"
                    font.family: "Consolas"
                    font.pixelSize: page.legendFontSize
                    color: page.airTempColor
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
