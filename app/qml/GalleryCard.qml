import QtQuick
import QtQuick.Controls.Basic
import "."

Item {
    id: card
    property var img
    property bool actions: false        // hover buttons: set as wallpaper / delete
    property bool minimal: false        // image only - no caption or badge
    readonly property bool isCurrent: !!img && backend.current.path === img.path
    signal clicked()

    scale: hover.hovered ? 1.025 : 1
    Behavior on scale { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }

    HoverHandler { id: hover; onHoveredChanged: if (!hovered) deleteBtn.armed = false }

    RoundImage {
        anchors.fill: parent
        radius: Theme.radiusSm
        source: card.img ? card.img.url : ""
        sourceSize.width: 720
    }
    Rectangle {
        anchors.fill: parent
        visible: !card.minimal
        radius: Theme.radiusSm
        gradient: Gradient {
            GradientStop { position: 0.45; color: "#00000000" }
            GradientStop { position: 1.0; color: "#d9000000" }
        }
    }
    Rectangle {
        anchors.fill: parent
        radius: Theme.radiusSm
        color: "transparent"
        border.width: 2
        border.color: Theme.accent
        visible: card.isCurrent
    }
    Chip {
        anchors { left: parent.left; top: parent.top; margins: 12 }
        visible: card.isCurrent && !card.minimal
        active: true
        enabled: false
        text: "Current"
        iconName: "check"
    }
    Column {
        visible: !card.minimal
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 14 }
        spacing: 2
        Label {
            width: parent.width
            text: card.img ? card.img.categoryLabel : ""
            elide: Text.ElideRight
            font.pixelSize: 14
            font.weight: Font.DemiBold
            color: "white"
        }
        Label {
            width: parent.width
            text: card.img ? card.img.dateLabel : ""
            elide: Text.ElideRight
            font.pixelSize: 12
            color: "#ccffffff"
        }
    }
    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: card.clicked()
    }

    Row {
        anchors { right: parent.right; top: parent.top; margins: 12 }
        spacing: 8
        visible: card.actions
        opacity: hover.hovered ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 140 } }

        CardAction {
            iconName: "check"
            tip: card.isCurrent ? "Already the wallpaper" : "Set as wallpaper"
            enabled: !card.isCurrent && !backend.busy && hover.hovered
            onClicked: backend.applyImage(card.img.path)
        }
        CardAction {
            id: deleteBtn
            danger: true
            iconName: "trash"
            tip: card.isCurrent ? "Can't delete the current wallpaper"
               : armed ? "Click again to delete" : "Delete"
            enabled: !card.isCurrent && hover.hovered
            onClicked: {
                if (armed) {
                    armed = false
                    backend.deleteImage(card.img.path)
                } else {
                    armed = true
                    disarm.restart()
                }
            }
            Timer { id: disarm; interval: 3000; onTriggered: deleteBtn.armed = false }
        }
    }
}
