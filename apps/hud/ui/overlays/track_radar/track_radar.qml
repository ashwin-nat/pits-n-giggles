import QtQuick
import QtQuick.Window
import QtQuick.Layouts

Window {
    id: root
    visible: true

    property real scaleFactor: 1.0
    readonly property int baseWidth: 300
    readonly property int baseHeight: 300

    width: baseWidth * scaleFactor
    height: baseHeight * scaleFactor
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    // Radar properties
    property var driverData: []
    property real radarRange: 25.0  // meters - zoomed in for side awareness
    property real baseOpacity: 1.0  // Externally controlled opacity
    property real idleOpacity: 0.3  // Opacity when no cars nearby (0.0 - 1.0)
    property bool lockedMode: true  // Enable/disable fade behavior
    property bool carsNearby: false  // Track if cars are in vicinity
    // Default value is false so that the radar stays faded in menu when the app is launched
    // When actual data starts coming, the correct computed value will be set

    function updateTelemetry(drivers) {
        driverData = drivers || [];
        carsNearby = hasCarInVicinity();
    }

    // Helper functions for side detection
    function hasCarOnLeft() {
        for (var i = 0; i < driverData.length; i++) {
            var driver = driverData[i];
            if (driver.is_ref) continue;

            var relX = driver.relX || 0;
            var relZ = driver.relZ || 0;

            // Check if car is on left side and within alongside range
            // Left is negative X, alongside is similar Z position
            if (relX < -1.5 && relX > -4.0 && Math.abs(relZ) < 8.0) {
                return true;
            }
        }
        return false;
    }

    function hasCarOnRight() {
        for (var i = 0; i < driverData.length; i++) {
            var driver = driverData[i];
            if (driver.is_ref) continue;

            var relX = driver.relX || 0;
            var relZ = driver.relZ || 0;

            // Check if car is on right side and within alongside range
            // Right is positive X, alongside is similar Z position
            if (relX > 1.5 && relX < 4.0 && Math.abs(relZ) < 8.0) {
                return true;
            }
        }
        return false;
    }

    // Check if any car is in vicinity (within radar range)
    function hasCarInVicinity() {
        var count = 0;
        for (var i = 0; i < driverData.length; i++) {
            var driver = driverData[i];
            if (driver.is_ref) continue;

            var relX = driver.relX || 0;
            var relZ = driver.relZ || 0;
            var distance = Math.sqrt(relX * relX + relZ * relZ);

            if (distance <= radarRange) {
                count++;
            }
        }
        return count > 0;
    }

    // ==========================================================
    // GLOBAL SCALING ROOT
    // ==========================================================
    Item {
        id: scaledRoot
        anchors.centerIn: parent
        width: baseWidth
        height: baseHeight

        // Fade in/out based on car vicinity (only if lockedMode is true)
        opacity: {
            let targetOpacity = lockedMode ? (carsNearby ? baseOpacity : idleOpacity) : baseOpacity;
            return targetOpacity;
        }

        Behavior on opacity {
            NumberAnimation { duration: 500 }
        }

        transform: Scale {
            xScale: scaleFactor
            yScale: scaleFactor
            origin.x: baseWidth / 2
            origin.y: baseHeight / 2
        }

        // Background (fully transparent)
        Rectangle {
            anchors.fill: parent
            color: "transparent"
        }

        // Radar display area
        Item {
            id: radarArea
            anchors.centerIn: parent
            width: parent.width * 0.85
            height: parent.height * 0.85

            readonly property real centerX: width / 2
            readonly property real centerY: height / 2

            // Grid lines
            Repeater {
                model: 4
                delegate: Canvas {
                    property real circleRadius: (index + 1) * (radarArea.width / 8)
                    x: radarArea.centerX - circleRadius
                    y: radarArea.centerY - circleRadius
                    width: circleRadius * 2
                    height: circleRadius * 2

                    onPaint: {
                        var ctx = getContext("2d");
                        ctx.clearRect(0, 0, width, height);

                        ctx.strokeStyle = Qt.rgba(1, 1, 1, 0.22);
                        ctx.lineWidth = 1;
                        ctx.setLineDash([5, 5]); // Dashed pattern: 5px dash, 5px gap

                        ctx.beginPath();
                        ctx.arc(width / 2, height / 2, circleRadius, 0, 2 * Math.PI);
                        ctx.stroke();
                    }

                    Component.onCompleted: requestPaint()
                }
            }

            // Crosshair
            Rectangle {
                x: radarArea.centerX - width / 2
                y: 0
                width: 1
                height: radarArea.height
                color: Qt.rgba(1, 1, 1, 0.28)
            }
            Rectangle {
                x: 0
                y: radarArea.centerY - height / 2
                width: radarArea.width
                height: 1
                color: Qt.rgba(1, 1, 1, 0.28)
            }

            // Reference car (center) with side indicators
            Item {
                x: radarArea.centerX
                y: radarArea.centerY

                // Left side radial gradient sector
                Canvas {
                    id: leftSector
                    anchors.centerIn: parent
                    width: radarArea.width
                    height: radarArea.height
                    opacity: hasCarOnLeft() ? 1.0 : 0.0

                    Behavior on opacity {
                        NumberAnimation { duration: 150 }
                    }

                    onPaint: {
                        var ctx = getContext("2d");
                        ctx.clearRect(0, 0, width, height);

                        if (opacity > 0) {
                            var centerX = width / 2;
                            var centerY = height / 2;
                            var carWidth = 12;
                            var carHeight = 34;

                            // Calculate angles for left side sector (USING RIGHT CORNERS)
                            // Top-right corner
                            var topRightX = carWidth / 2;
                            var topRightY = -carHeight / 2;
                            var angleTopRight = Math.atan2(topRightY, topRightX);

                            // Bottom-right corner
                            var bottomRightX = carWidth / 2;
                            var bottomRightY = carHeight / 2;
                            var angleBottomRight = Math.atan2(bottomRightY, bottomRightX);

                            // Create radial gradient
                            var gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, Math.min(width, height) / 2);
                            gradient.addColorStop(0, "rgba(255, 0, 0, 0.8)");
                            gradient.addColorStop(0.3, "rgba(255, 0, 0, 0.4)");
                            gradient.addColorStop(1, "rgba(255, 0, 0, 0.0)");

                            ctx.fillStyle = gradient;
                            ctx.beginPath();
                            ctx.moveTo(centerX, centerY);
                            ctx.arc(centerX, centerY, Math.min(width, height) / 2, angleTopRight, angleBottomRight, false);  // clockwise
                            ctx.lineTo(centerX, centerY);
                            ctx.fill();
                        }
                    }

                    onOpacityChanged: requestPaint()
                }

                // Right side radial gradient sector
                Canvas {
                    id: rightSector
                    anchors.centerIn: parent
                    width: radarArea.width
                    height: radarArea.height
                    opacity: hasCarOnRight() ? 1.0 : 0.0

                    Behavior on opacity {
                        NumberAnimation { duration: 150 }
                    }

                    onPaint: {
                        var ctx = getContext("2d");
                        ctx.clearRect(0, 0, width, height);

                        if (opacity > 0) {
                            var centerX = width / 2;
                            var centerY = height / 2;
                            var carWidth = 12;
                            var carHeight = 34;

                            // Calculate angles for right side sector (USING LEFT CORNERS)
                            // Top-left corner
                            var topLeftX = -carWidth / 2;
                            var topLeftY = -carHeight / 2;
                            var angleTopLeft = Math.atan2(topLeftY, topLeftX);

                            // Bottom-left corner
                            var bottomLeftX = -carWidth / 2;
                            var bottomLeftY = carHeight / 2;
                            var angleBottomLeft = Math.atan2(bottomLeftY, bottomLeftX);

                            // Create radial gradient
                            var gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, Math.min(width, height) / 2);
                            gradient.addColorStop(0, "rgba(255, 0, 0, 0.8)");
                            gradient.addColorStop(0.3, "rgba(255, 0, 0, 0.4)");
                            gradient.addColorStop(1, "rgba(255, 0, 0, 0.0)");

                            ctx.fillStyle = gradient;
                            ctx.beginPath();
                            ctx.moveTo(centerX, centerY);
                            ctx.arc(centerX, centerY, Math.min(width, height) / 2, angleBottomLeft, angleTopLeft, false);  // clockwise
                            ctx.lineTo(centerX, centerY);
                            ctx.fill();
                        }
                    }

                    onOpacityChanged: requestPaint()
                }

                Rectangle {
                    id: refCar
                    anchors.centerIn: parent
                    width: 12  // Width: 2m scaled
                    height: 34 // Length: 5.63m scaled (ratio ~2.8:1)
                    color: "#00ff00"
                    border.color: "#ffffff"
                    border.width: 2
                    radius: 2
                }
            }

            // Other cars
            Repeater {
                model: driverData
                delegate: Item {
                    id: carMarker

                    property var driver: modelData
                    property bool isRef: driver.is_ref || false

                    visible: !isRef && driver.relX !== undefined && driver.relZ !== undefined

                    // Convert world position to radar coordinates (flip X axis)
                    // relX: world-space lateral offset from player.
                    // Convention: +relX = car is to the right of the player.
                    //
                    // NOTE:
                    // Radar screen space intentionally mirrors world X so that the radar
                    // matches the driver's perspective. As a result:
                    //   - +relX (world right) is drawn to the LEFT on screen
                    //   - -relX (world left)  is drawn to the RIGHT on screen
                    //
                    // Side-awareness logic (hasCarOnLeft/Right) always uses world-space relX.
                    property real radarX: radarArea.centerX - (driver.relX / root.radarRange) * (radarArea.width / 2)
                    property real radarY: radarArea.centerY - (driver.relZ / root.radarRange) * (radarArea.height / 2)

                    // Check if within radar range
                    property real distance: Math.sqrt(driver.relX * driver.relX + driver.relZ * driver.relZ)
                    property bool inRange: distance <= root.radarRange

                    x: radarX
                    y: radarY

                    opacity: inRange ? 1.0 : 0.0

                    Rectangle {
                        anchors.centerIn: parent
                        width: 12  // Width: 2m scaled
                        height: 34 // Length: 5.63m scaled (ratio ~2.8:1)
                        color: "#ffffff"
                        border.color: "#888888"
                        border.width: 1
                        radius: 2
                        rotation: -(driver.heading || 0)  // Invert rotation
                    }

                    // Driver name on hover
                    Rectangle {
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.bottom: parent.top
                        anchors.bottomMargin: 5
                        width: nameText.width + 8
                        height: nameText.height + 4
                        color: "#000000"
                        opacity: 0.8
                        radius: 3
                        visible: mouseArea.containsMouse

                        Text {
                            id: nameText
                            anchors.centerIn: parent
                            text: driver.name || ""
                            color: "#ffffff"
                            font.pixelSize: 10
                            font.bold: true
                        }
                    }

                    MouseArea {
                        id: mouseArea
                        anchors.fill: parent
                        anchors.margins: -10
                        hoverEnabled: true
                    }
                }
            }
        }
    }
}
