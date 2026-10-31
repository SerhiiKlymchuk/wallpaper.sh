import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "."

// Full-window preview of one image, with arrows to step through a list.
Popup {
    id: pop
    property var list: []
    property int index: 0
    readonly property var img: list.length ? list[Math.min(index, list.length - 1)] : null
    readonly property bool isCurrent: !!img && backend.current.path === img.path

    function show(images, i) {
        list = images
        index = i
        open()
    }
    function step(delta) {
        if (list.length)
            index = (index + delta + list.length) % list.length
    }

    parent: Overlay.overlay
    x: 0
    y: 0
    width: parent ? parent.width : 0
    height: parent ? parent.height : 0
    modal: true
    padding: 0
    closePolicy: Popup.CloseOnEscape
    onOpened: keys.forceActiveFocus()

    Overlay.modal: Rectangle { color: "#e60a0a0d" }
    background: Item {}
    enter: Transition { NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 160 } }
    exit: Transition { NumberAnimation { property: "opacity"; from: 1; to: 0; duration: 120 } }

    contentItem: Item {
        id: keys
        focus: true
        Keys.onLeftPressed: pop.step(-1)
        Keys.onRightPressed: pop.step(1)

        MouseArea { anchors.fill: parent; onClicked: pop.close() }

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 20

            Item {
                id: frame
                readonly property real ratio: pop.img && pop.img.height ? pop.img.width / pop.img.height : 16 / 9
                readonly property real maxW: pop.width - 220
                readonly property real maxH: pop.height - 200
                Layout.preferredWidth: Math.max(200, Math.min(maxW, maxH * ratio))
                Layout.preferredHeight: Layout.preferredWidth / ratio

                RoundImage {
                    anchors.fill: parent
                    source: pop.img ? pop.img.url : ""
                    sourceSize.width: 2560
                }
                MouseArea { anchors.fill: parent }
            }

            RowLayout {
                Layout.preferredWidth: frame.Layout.preferredWidth
                spacing: 10
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3
                    RowLayout {
                        spacing: 10
                        Label {
                            text: pop.img ? pop.img.categoryLabel : ""
                            color: "white"
                            font.pixelSize: 20
                            font.weight: Font.DemiBold
                        }
                        Chip { visible: pop.isCurrent; active: true; enabled: false; text: "Current"; iconName: "check" }
                    }
                    Label {
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                        text: pop.img ? [pop.img.dateLabel, pop.img.width + " × " + pop.img.height, pop.img.sizeLabel,
                                         (pop.index + 1) + " of " + pop.list.length].join("  ·  ") : ""
                        font.pixelSize: 13
                        color: "#b3ffffff"
                    }
                }
                PillButton {
                    text: "Set as wallpaper"
                    iconName: "check"
                    enabled: !!pop.img && !pop.isCurrent && !backend.busy
                    onClicked: backend.applyImage(pop.img.path)
                }
                PillButton {
                    variant: "ghost"
                    text: "wallhaven"
                    iconName: "external"
                    visible: !!pop.img && pop.img.id !== ""
                    onClicked: backend.openWallhaven(pop.img.id)
                }
                PillButton {
                    variant: "danger"
                    iconName: "trash"
                    enabled: !!pop.img && !pop.isCurrent
                    ToolTip.visible: hovered
                    ToolTip.text: "Delete this image"
                    onClicked: {
                        const path = pop.img.path
                        backend.deleteImage(path)
                        pop.list = pop.list.filter(i => i.path !== path)
                        if (!pop.list.length)
                            pop.close()
                        else
                            pop.index = Math.min(pop.index, pop.list.length - 1)
                    }
                }
            }
        }

        PillButton {
            anchors { left: parent.left; leftMargin: 32; verticalCenter: parent.verticalCenter }
            variant: "ghost"
            iconName: "left"
            visible: pop.list.length > 1
            onClicked: pop.step(-1)
        }
        PillButton {
            anchors { right: parent.right; rightMargin: 32; verticalCenter: parent.verticalCenter }
            variant: "ghost"
            iconName: "right"
            visible: pop.list.length > 1
            onClicked: pop.step(1)
        }
        PillButton {
            anchors { right: parent.right; top: parent.top; margins: 28 }
            variant: "ghost"
            iconName: "x"
            onClicked: pop.close()
        }
    }
}
