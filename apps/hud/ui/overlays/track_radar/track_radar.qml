import QtQuick
import QtQuick.Window
import QtQuick.Shapes

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
    property real baseOpacity: 1.0
    property real idleOpacity: 0.3
    property bool lockedMode: true
    property bool carsNearby: false
    property bool carOnLeft: false
    property bool carOnRight: false

    // Set by Python post_setup to match _RADAR_AREA_RATIO — single source of truth
    property real radarAreaRatio: 0.85

    // Single property write per frame — flat array [x, y, heading, inRange, ...] stride 4
    property var carData: []

    onCarDataChanged:    radarCanvas.requestPaint()
    onCarOnLeftChanged:  radarCanvas.requestPaint()
    onCarOnRightChanged: radarCanvas.requestPaint()

    Item {
        id: scaledRoot
        anchors.centerIn: parent
        width: baseWidth
        height: baseHeight

        clip: true
        opacity: lockedMode ? (carsNearby ? baseOpacity : idleOpacity) : baseOpacity
        Behavior on opacity { NumberAnimation { duration: 500 } }

        transform: Scale {
            xScale: scaleFactor
            yScale: scaleFactor
            origin.x: baseWidth / 2
            origin.y: baseHeight / 2
        }

        // --- Static layer: grid circles (scene graph, paid once) ---
        readonly property real halfR: baseWidth * radarAreaRatio / 2

        Repeater {
            model: 4
            Shape {
                anchors.centerIn: parent
                width: baseWidth
                height: baseHeight
                ShapePath {
                    strokeColor: Qt.rgba(1, 1, 1, 0.22)
                    strokeWidth: 1
                    fillColor: "transparent"
                    strokeStyle: ShapePath.DashLine
                    dashPattern: [5, 5]
                    PathAngleArc {
                        centerX: baseWidth / 2
                        centerY: baseHeight / 2
                        radiusX: (index + 1) * scaledRoot.halfR / 2
                        radiusY: (index + 1) * scaledRoot.halfR / 2
                        startAngle: 0
                        sweepAngle: 360
                    }
                }
            }
        }

        // --- Static layer: crosshair (scene graph, paid once) ---
        Rectangle {
            anchors.centerIn: parent
            width: 1
            height: scaledRoot.halfR * 2
            color: Qt.rgba(1, 1, 1, 0.28)
        }
        Rectangle {
            anchors.centerIn: parent
            width: scaledRoot.halfR * 2
            height: 1
            color: Qt.rgba(1, 1, 1, 0.28)
        }

        Canvas {
            id: radarCanvas
            anchors.fill: parent
            renderStrategy: Canvas.Threaded

            function roundRect(ctx, x, y, w, h, r) {
                ctx.beginPath();
                ctx.moveTo(x + r, y);
                ctx.arcTo(x + w, y,     x + w, y + h, r);
                ctx.arcTo(x + w, y + h, x,     y + h, r);
                ctx.arcTo(x,     y + h, x,     y,     r);
                ctx.arcTo(x,     y,     x + w, y,     r);
                ctx.closePath();
            }

            onPaint: {
                const ctx = getContext("2d");
                const w = width;
                const h = height;
                const cx = w / 2;
                const cy = h / 2;
                const halfR = w * root.radarAreaRatio / 2;

                ctx.clearRect(0, 0, w, h);

                // --- Sector glows ---
                const halfW = root.carWidthPx / 2;
                const halfL = root.carLengthPx / 2;

                if (root.carOnLeft) {
                    const angleTopRight    = Math.atan2(-halfL,  halfW);
                    const angleBottomRight = Math.atan2( halfL,  halfW);
                    const gL = ctx.createRadialGradient(cx, cy, 0, cx, cy, halfR);
                    gL.addColorStop(0,   "rgba(255, 0, 0, 0.8)");
                    gL.addColorStop(0.3, "rgba(255, 0, 0, 0.4)");
                    gL.addColorStop(1,   "rgba(255, 0, 0, 0.0)");
                    ctx.fillStyle = gL;
                    ctx.beginPath();
                    ctx.moveTo(cx, cy);
                    ctx.arc(cx, cy, halfR, angleTopRight, angleBottomRight, false);
                    ctx.lineTo(cx, cy);
                    ctx.fill();
                }

                if (root.carOnRight) {
                    const angleTopLeft    = Math.atan2(-halfL, -halfW);
                    const angleBottomLeft = Math.atan2( halfL, -halfW);
                    const gR = ctx.createRadialGradient(cx, cy, 0, cx, cy, halfR);
                    gR.addColorStop(0,   "rgba(255, 0, 0, 0.8)");
                    gR.addColorStop(0.3, "rgba(255, 0, 0, 0.4)");
                    gR.addColorStop(1,   "rgba(255, 0, 0, 0.0)");
                    ctx.fillStyle = gR;
                    ctx.beginPath();
                    ctx.moveTo(cx, cy);
                    ctx.arc(cx, cy, halfR, angleBottomLeft, angleTopLeft, false);
                    ctx.lineTo(cx, cy);
                    ctx.fill();
                }

                // --- Other cars — stride 4: [x, y, heading, inRange] ---
                const cars = root.carData;
                const count = Math.floor(cars.length / 4);
                const cw = root.carWidthPx;
                const cl = root.carLengthPx;

                for (let i = 0; i < count; i++) {
                    const base = i * 4;
                    if (!cars[base + 3]) continue;

                    ctx.save();
                    ctx.translate(cars[base], cars[base + 1]);
                    ctx.rotate(cars[base + 2] * Math.PI / 180);
                    ctx.fillStyle = "#ffffff";
                    ctx.strokeStyle = "#888888";
                    ctx.lineWidth = 1;
                    radarCanvas.roundRect(ctx, -cw / 2, -cl / 2, cw, cl, 2);
                    ctx.fill();
                    ctx.stroke();
                    ctx.restore();
                }

                // --- Reference car ---
                ctx.save();
                ctx.translate(cx, cy);
                ctx.fillStyle = "#00ff00";
                ctx.strokeStyle = "#ffffff";
                ctx.lineWidth = 2;
                radarCanvas.roundRect(ctx, -halfW, -halfL, cw, cl, 2);
                ctx.fill();
                ctx.stroke();
                ctx.restore();
            }
        }
    }
}
