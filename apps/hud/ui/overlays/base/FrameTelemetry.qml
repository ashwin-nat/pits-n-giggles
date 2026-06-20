import QtQuick

Item {
    id: root
    property real fps:               0
    property real frameTimeMs:       0
    property real smoothFrameTimeMs: 0
    property int  frameCount:        0

    FrameAnimation {
        id: frameAnim
        running: root.visible
        onTriggered: {
            root.frameTimeMs       = (frameAnim.frameTime       || 0) * 1000
            root.smoothFrameTimeMs = (frameAnim.smoothFrameTime || 0) * 1000
            root.fps               = frameAnim.frameTime > 0 ? 1.0 / frameAnim.frameTime : 0
            root.frameCount        += 1
        }
    }
}
