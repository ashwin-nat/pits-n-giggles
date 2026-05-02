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
    property real carWidthPx: 10.2
    property real carLengthPx: 28.7
    property real radarRange: 25.0  // meters - zoomed in for side awareness
    property real baseOpacity: 1.0
    property real idleOpacity: 0.3
    property bool lockedMode: true
    property bool carsNearby: false
    property bool carOnLeft: false
    property bool carOnRight: false

    // Fixed-pool car slot update — called by Python once per visible car per frame.
    // slot:    index into the carPool Repeater (0-based)
    // radarX:  screen x in radarArea coordinates
    // radarY:  screen y in radarArea coordinates
    // heading: rotation angle in degrees
    // inRange: whether the car is within radar range
    // name:    driver name string (for hover tooltip)
    function updateCarSlot(slot, radarX, radarY, heading, inRange, name) {
        if (slot < 0 || slot >= carPool.count) return;
        const item = carPool.itemAt(slot);
        if (!item) return;
        item.slotX       = radarX;
        item.slotY       = radarY;
        item.slotHeading = heading;
        item.slotInRange = inRange;
        item.slotName    = name;
        item.slotActive  = true;
    }

    // Hide all slots that Python didn't populate this frame.
    // Called once after all updateCarSlot calls are done.
    function commitFrame(activeCount) {
        for (let i = 0; i < carPool.count; i++) {
            const item = carPool.itemAt(i);
            if (!item) continue;
            if (i >= activeCount) {
                item.slotActive = false;
            }
        }
    }

    // ==========================================================
    // GLOBAL SCALING ROOT
    // ==========================================================
    Item {
        id: scaledRoot
        anchors.centerIn: parent
        width: baseWidth
        height: baseHeight

        opacity: lockedMode ? (carsNearby ? baseOpacity : idleOpacity) : baseOpacity
        Behavior on opacity { NumberAnimation { duration: 500 } }

        transform: Scale {
            xScale: scaleFactor
            yScale: scaleFactor
            origin.x: baseWidth / 2
            origin.y: baseHeight / 2
        }

        Rectangle { anchors.fill: parent; color: "transparent" }

        // Radar display area
        Item {
            id: radarArea
            anchors.centerIn: parent
            width: parent.width * 0.85
            height: parent.height * 0.85

            readonly property real centerX: width / 2
            readonly property real centerY: height / 2

            // Grid circles — static, paint once
            Repeater {
                model: 4
                delegate: Canvas {
                    property real circleRadius: (index + 1) * (radarArea.width / 8)
                    x: radarArea.centerX - circleRadius
                    y: radarArea.centerY - circleRadius
                    width: circleRadius * 2
                    height: circleRadius * 2

                    onPaint: {
                        const ctx = getContext("2d");
                        ctx.clearRect(0, 0, width, height);
                        ctx.strokeStyle = Qt.rgba(1, 1, 1, 0.22);
                        ctx.lineWidth = 1;
                        ctx.setLineDash([5, 5]);
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

            // Reference car with side-awareness indicators
            Item {
                x: radarArea.centerX
                y: radarArea.centerY

                Canvas {
                    id: leftSector
                    anchors.centerIn: parent
                    width: radarArea.width
                    height: radarArea.height
                    opacity: root.carOnLeft ? 1.0 : 0.0
                    Behavior on opacity { NumberAnimation { duration: 150 } }

                    onPaint: {
                        const ctx = getContext("2d");
                        ctx.clearRect(0, 0, width, height);
                        if (opacity > 0) {
                            const cx = width / 2, cy = height / 2;
                            const angleTopRight    = Math.atan2(-root.carLengthPx / 2,  root.carWidthPx / 2);
                            const angleBottomRight = Math.atan2( root.carLengthPx / 2,  root.carWidthPx / 2);
                            const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.min(width, height) / 2);
                            gradient.addColorStop(0,   "rgba(255, 0, 0, 0.8)");
                            gradient.addColorStop(0.3, "rgba(255, 0, 0, 0.4)");
                            gradient.addColorStop(1,   "rgba(255, 0, 0, 0.0)");
                            ctx.fillStyle = gradient;
                            ctx.beginPath();
                            ctx.moveTo(cx, cy);
                            ctx.arc(cx, cy, Math.min(width, height) / 2, angleTopRight, angleBottomRight, false);
                            ctx.lineTo(cx, cy);
                            ctx.fill();
                        }
                    }

                    onOpacityChanged: { if (opacity >= 0.99 || opacity <= 0.01) requestPaint() }
                }

                Canvas {
                    id: rightSector
                    anchors.centerIn: parent
                    width: radarArea.width
                    height: radarArea.height
                    opacity: root.carOnRight ? 1.0 : 0.0
                    Behavior on opacity { NumberAnimation { duration: 150 } }

                    onPaint: {
                        const ctx = getContext("2d");
                        ctx.clearRect(0, 0, width, height);
                        if (opacity > 0) {
                            const cx = width / 2, cy = height / 2;
                            const angleTopLeft    = Math.atan2(-root.carLengthPx / 2, -root.carWidthPx / 2);
                            const angleBottomLeft = Math.atan2( root.carLengthPx / 2, -root.carWidthPx / 2);
                            const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.min(width, height) / 2);
                            gradient.addColorStop(0,   "rgba(255, 0, 0, 0.8)");
                            gradient.addColorStop(0.3, "rgba(255, 0, 0, 0.4)");
                            gradient.addColorStop(1,   "rgba(255, 0, 0, 0.0)");
                            ctx.fillStyle = gradient;
                            ctx.beginPath();
                            ctx.moveTo(cx, cy);
                            ctx.arc(cx, cy, Math.min(width, height) / 2, angleBottomLeft, angleTopLeft, false);
                            ctx.lineTo(cx, cy);
                            ctx.fill();
                        }
                    }

                    onOpacityChanged: { if (opacity >= 0.99 || opacity <= 0.01) requestPaint() }
                }

                Rectangle {
                    id: refCar
                    anchors.centerIn: parent
                    width: root.carWidthPx
                    height: root.carLengthPx
                    color: "#00ff00"
                    border.color: "#ffffff"
                    border.width: 2
                    radius: 2
                }
            }

            // Fixed pool of 20 car marker slots — no create/destroy on data change
            Repeater {
                id: carPool
                model: 22

                delegate: Item {
                    id: carSlot

                    // Slot state — written by updateCarSlot() / commitFrame()
                    property real slotX:       0
                    property real slotY:       0
                    property real slotHeading: 0
                    property bool slotInRange: false
                    property string slotName:  ""
                    property bool slotActive:  false

                    visible: slotActive && slotInRange
                    x: slotX
                    y: slotY

                    Rectangle {
                        anchors.centerIn: parent
                        width: root.carWidthPx
                        height: root.carLengthPx
                        color: "#ffffff"
                        border.color: "#888888"
                        border.width: 1
                        radius: 2
                        rotation: -slotHeading
                    }

                    Rectangle {
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.bottom: parent.top
                        anchors.bottomMargin: 5
                        width: nameLabel.width + 8
                        height: nameLabel.height + 4
                        color: "#000000"
                        opacity: 0.8
                        radius: 3
                        visible: hoverArea.containsMouse

                        Text {
                            id: nameLabel
                            anchors.centerIn: parent
                            text: slotName
                            color: "#ffffff"
                            font.pixelSize: 10
                            font.bold: true
                        }
                    }

                    MouseArea {
                        id: hoverArea
                        anchors.fill: parent
                        anchors.margins: -10
                        hoverEnabled: true
                    }
                }
            }
        }
    }
}
