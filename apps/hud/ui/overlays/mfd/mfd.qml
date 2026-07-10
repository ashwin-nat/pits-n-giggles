pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Window

Window {
    id: root
    visible: true
    color: "black"

    signal pageLoaded(string pageKey, var item)

    /* ---------- SCALING ---------- */
    property real scaleFactor: 1.0
    readonly property int baseWidth: 400
    readonly property int baseHeightExpanded: 220
    readonly property int baseHeightCollapsed: 36
    readonly property int titleBarHeight: 40
    readonly property int footerHeight: 45

    /* ---------- PAGE CONTROL ---------- */
    property url currentPageQml: ""
    property string activePageKey: ""
    property bool collapsed: false   // SET FROM PYTHON
    property int totalPages: 0       // SET FROM PYTHON
    property int currentPageIndex: 0 // SET FROM PYTHON

    // Animation control
    property int animationDuration: 100
    property int collapseDuration: 75
    property bool isAnimating: false
    property url pendingPageQml: ""

    // Track the actual display state (delayed from collapsed property)
    property bool displayCollapsed: collapsed
    property bool useCollapseAnimation: false

    // Get title from loaded page
    // qmllint disable missing-property
    readonly property string pageTitle: pageLoader.item && pageLoader.item.title !== undefined ? pageLoader.item.title : ""
    // qmllint enable missing-property
    readonly property bool showTitleBar: pageTitle.length > 0 && !displayCollapsed
    readonly property bool showFooter: totalPages > 0 && !displayCollapsed

    width: baseWidth * scaleFactor
    height: {
        let h = displayCollapsed ? baseHeightCollapsed : baseHeightExpanded;
        if (showTitleBar) h += titleBarHeight;
        if (showFooter) h += footerHeight;
        return h * scaleFactor;
    }

    // Smooth height animation when collapsing/expanding
    Behavior on height {
        enabled: root.useCollapseAnimation
        NumberAnimation {
            duration: root.collapseDuration
            easing.type: Easing.InOutCubic
        }
    }

    // Watch for page changes and animate
    onCurrentPageQmlChanged: {
        if (currentPageQml.toString() === "") return;

        if (isAnimating) {
            // Queue the next transition
            pendingPageQml = currentPageQml;
            return;
        }

        if (pageLoader.source == currentPageQml) return;

        startPageTransition();
    }

    function startPageTransition() {
        if (pageLoader.source.toString() === "") {
            // First load, no animation
            pageLoader.source = currentPageQml;
            displayCollapsed = collapsed;
            return;
        }

        // Determine if we need collapse/expand animation
        let wasCollapsed = displayCollapsed;
        let willBeCollapsed = collapsed;
        useCollapseAnimation = (wasCollapsed !== willBeCollapsed);

        isAnimating = true;

        if (useCollapseAnimation) {
            if (willBeCollapsed) {
                // Going TO collapsed: fade out content, then collapse height
                fadeOutAnimation.start();
            } else {
                // Going FROM collapsed: expand height first, then fade in new content
                displayCollapsed = false; // Expand immediately
                pageLoader.opacity = 0.0; // Start hidden
                pageLoader.source = currentPageQml; // Load new page
                // Fade in will be triggered by onLoaded
                Qt.callLater(function() {
                    fadeInAnimation.start();
                });
            }
        } else {
            // Normal page-to-page transition (no collapse involved)
            fadeOutAnimation.start();
        }
    }

    function onAnimationFinished() {
        isAnimating = false;

        // Update display state now that animation is complete
        displayCollapsed = collapsed;

        // Process any pending transition
        if (pendingPageQml.toString() !== "") {
            let pending = pendingPageQml;
            pendingPageQml = "";
            currentPageQml = pending;
        }
    }

    Item {
        id: scaledRoot
        anchors.fill: parent

        // Scale the entire content
        scale: root.scaleFactor
        transformOrigin: Item.TopLeft

        // Title Bar
        Rectangle {
            id: titleBar
            x: 0
            y: 0
            width: root.baseWidth
            height: root.titleBarHeight
            color: Qt.rgba(0, 0, 0, 0.3)
            visible: root.showTitleBar
            opacity: root.showTitleBar ? 1.0 : 0.0

            Behavior on opacity {
                NumberAnimation {
                    duration: root.animationDuration
                    easing.type: Easing.InOutCubic
                }
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 2
                color: "#FF0000"
            }

            Text {
                x: 0
                y: 0
                width: root.baseWidth
                height: root.titleBarHeight
                text: root.pageTitle
                color: "#FF0000"
                font.family: "Formula1"
                font.pixelSize: 13
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        Loader {
            id: pageLoader
            objectName: "pageLoader"
            width: root.baseWidth
            height: root.displayCollapsed ? root.baseHeightCollapsed : root.baseHeightExpanded
            anchors.top: root.showTitleBar ? titleBar.bottom : parent.top
            opacity: 1.0

            onLoaded: {
                root.pageLoaded(root.activePageKey, item)
            }

            // Fade out animation
            NumberAnimation on opacity {
                id: fadeOutAnimation
                running: false
                from: 1.0
                to: 0.0
                duration: root.useCollapseAnimation ? root.collapseDuration : root.animationDuration
                easing.type: Easing.OutCubic

                onFinished: {
                    if (root.useCollapseAnimation && root.collapsed) {
                        // Going TO collapsed: now collapse the height
                        root.displayCollapsed = true;
                        // Give a brief moment for height to collapse, then switch page
                        Qt.callLater(function() {
                            pageLoader.source = root.currentPageQml;
                            fadeInAnimation.start();
                        });
                    } else {
                        // Normal transition: switch page immediately
                        pageLoader.source = root.currentPageQml;
                        fadeInAnimation.start();
                    }
                }
            }

            // Fade in animation
            NumberAnimation on opacity {
                id: fadeInAnimation
                running: false
                from: 0.0
                to: 1.0
                duration: root.useCollapseAnimation ? root.collapseDuration : root.animationDuration
                easing.type: Easing.InCubic

                onFinished: {
                    root.onAnimationFinished();
                }
            }
        }

        // Page Indicator Footer
        Rectangle {
            id: footer
            width: root.baseWidth
            height: root.footerHeight
            anchors.top: pageLoader.bottom
            color: Qt.rgba(0, 0, 0, 0.3)
            visible: root.showFooter

            // Top border
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 1
                color: Qt.rgba(255, 255, 255, 0.4)
            }

            // Page indicator circles
            Row {
                id: indicatorRow
                anchors.centerIn: parent
                spacing: 18 // Space between circles (30 - 12 diameter)

                Repeater {
                    model: root.totalPages

                    Rectangle {
                        id: indicatorDot
                        required property int index

                        width: 12
                        height: 12
                        radius: 6
                        color: indicatorDot.index === root.currentPageIndex ?
                               Qt.rgba(245/255, 236/255, 235/255, 1.0) :
                               "transparent"
                        border.color: Qt.rgba(245/255, 236/255, 235/255, 1.0)
                        border.width: 1
                        antialiasing: true

                        // Smooth transition for indicator changes
                        Behavior on color {
                            ColorAnimation { duration: 150 }
                        }
                    }
                }
            }
        }
    }
}
