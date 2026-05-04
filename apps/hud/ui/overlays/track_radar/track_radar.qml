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

    onCarDataChanged: {
        const cars = carData;
        for (let i = 0; i < 22; i++) {
            const slot = carPool.children[i];
            const base = i * 4;
            const inRange = base + 3 < cars.length && cars[base + 3];
            slot.visible = inRange;
            if (inRange) {
                slot.x        = cars[base]     - carWidthPx  / 2;
                slot.y        = cars[base + 1] - carLengthPx / 2;
                slot.rotation = cars[base + 2];
            }
        }
    }

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

        // --- Sector glows — pre-baked images, GPU opacity fade (scene graph) ---
        Image {
            anchors.fill: parent
            source: "image://radar/glow-left"
            opacity: root.carOnLeft ? 1.0 : 0.0
            Behavior on opacity { NumberAnimation { duration: 150 } }
        }
        Image {
            anchors.fill: parent
            source: "image://radar/glow-right"
            opacity: root.carOnRight ? 1.0 : 0.0
            Behavior on opacity { NumberAnimation { duration: 150 } }
        }

        // --- Other cars — fixed 22-slot Rectangle pool (scene graph) ---
        // carData is a flat array [cx, cy, heading, inRange, ...] stride 4.
        // cx/cy are radar centre-relative; QML Rectangle origin is top-left,
        // so x = cx - width/2, y = cy - height/2. rotation is around item centre (default transformOrigin).
        Item {
            id: carPool
            anchors.fill: parent

            // Slot 0
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 1
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 2
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 3
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 4
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 5
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 6
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 7
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 8
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 9
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 10
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 11
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 12
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 13
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 14
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 15
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 16
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 17
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 18
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 19
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 20
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
            // Slot 21
            Rectangle { width: root.carWidthPx; height: root.carLengthPx; color: "#ffffff"; border.color: "#888888"; border.width: 1; radius: 2; visible: false }
        }

        // --- Reference car — always visible, centred (scene graph) ---
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
}
