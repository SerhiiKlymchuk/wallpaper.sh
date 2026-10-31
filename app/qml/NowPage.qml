import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "."

ScrollView {
    id: page
    signal previewRequested(var list, int index)
    signal galleryRequested()

    readonly property var cur: backend.current
    readonly property var imgs: backend.images
    readonly property var targets: backend.targets

    contentWidth: availableWidth
    rightPadding: 14
    clip: true

    ColumnLayout {
        width: page.availableWidth
        spacing: 22

        // --- current wallpaper ---------------------------------------------
        Item {
            id: hero
            Layout.fillWidth: true
            Layout.preferredHeight: Math.max(320, Math.min(width * 0.56, page.height - 250))

            RoundImage {
                anchors.fill: parent
                source: page.cur.url || ""
                sourceSize.width: 2000
            }
            Rectangle {
                anchors.fill: parent
                radius: Theme.radius
                gradient: Gradient {
                    GradientStop { position: 0.6; color: "#00000000" }
                    GradientStop { position: 1.0; color: "#bf000000" }
                }
            }
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: page.previewRequested(page.imgs, Math.max(0, page.imgs.findIndex(i => i.path === page.cur.path)))
            }

            RowLayout {
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 24 }
                spacing: 10

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    Label {
                        Layout.fillWidth: true
                        text: page.cur.categoryLabel || "No wallpaper yet"
                        elide: Text.ElideRight
                        font.family: Theme.display
                        font.pixelSize: 26
                        font.weight: Font.Bold
                        color: "white"
                    }
                    Label {
                        Layout.fillWidth: true
                        text: [page.cur.appliedLabel ? "Applied " + page.cur.appliedLabel.toLowerCase() : "",
                               page.cur.width ? page.cur.width + " × " + page.cur.height : "",
                               page.cur.query ? "“" + page.cur.query + "”" : ""].filter(Boolean).join("  ·  ")
                        elide: Text.ElideRight
                        font.pixelSize: 13
                        color: "#ccffffff"
                    }
                }
                PillButton {
                    variant: "glass"
                    iconName: "external"
                    visible: !!page.cur.id
                    ToolTip.visible: hovered
                    ToolTip.text: "Open on wallhaven"
                    onClicked: backend.openWallhaven(page.cur.id)
                }
                PillButton {
                    text: "New image"
                    iconName: "refresh"
                    enabled: !backend.busy
                    onClicked: backend.newImage()
                }
            }
        }

        // --- where it shows + next change ---------------------------------
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Label { text: "Shows on"; font.pixelSize: 13; color: Theme.textDim; rightPadding: 4 }
            Repeater {
                model: [["desktop", "monitor", "Desktop"], ["lock", "lock", "Lock screen"], ["login", "user", "Login screen"]]
                delegate: Chip {
                    required property var modelData
                    readonly property bool available: modelData[0] !== "login" || page.targets.loginAvailable
                    implicitHeight: 32
                    soft: true
                    iconName: modelData[1]
                    text: modelData[2]
                    active: page.targets[modelData[0]] && available
                    enabled: available
                    ToolTip.visible: hovered
                    ToolTip.delay: 400
                    ToolTip.text: !available ? "Run ~/.config/wallpaper-sh/setup-login-screen.sh once"
                                : active ? "Click to stop changing the " + modelData[2].toLowerCase()
                                : "Click to also change the " + modelData[2].toLowerCase()
                    onClicked: backend.setTarget(modelData[0], !page.targets[modelData[0]])
                }
            }
            PillButton {
                compact: true
                variant: "ghost"
                text: "Re-apply"
                enabled: !!page.cur.path && !backend.busy
                ToolTip.visible: hovered
                ToolTip.text: "Apply the current wallpaper again, e.g. after changing where it shows"
                onClicked: backend.applyImage(page.cur.path)
            }

            Item { Layout.fillWidth: true }
        }

        // --- recent --------------------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            Layout.topMargin: 6
            spacing: 12
            RowLayout {
                Label { Layout.fillWidth: true; text: "Recent"; font.pixelSize: 15; font.weight: Font.DemiBold }
                Label {
                    text: "Gallery →"
                    font.pixelSize: 13
                    color: seeAll.containsMouse ? Theme.accentText : Theme.textDim
                    MouseArea {
                        id: seeAll
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: page.galleryRequested()
                    }
                }
            }
            Row {
                id: recent
                readonly property real cell: (width - spacing * 5) / 6
                Layout.fillWidth: true
                Layout.preferredHeight: cell * 0.62
                spacing: 14
                Repeater {
                    model: page.imgs.slice(0, 6)
                    delegate: GalleryCard {
                        required property var modelData
                        required property int index
                        width: recent.cell
                        height: recent.height
                        minimal: true
                        img: modelData
                        onClicked: page.previewRequested(page.imgs, index)
                    }
                }
            }
            Item { Layout.preferredHeight: 6 }
        }
    }
}
