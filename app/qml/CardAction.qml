import QtQuick
import QtQuick.Controls.Basic
import "."

// Small round icon button shown over an image, with a tooltip.
AbstractButton {
    id: a
    property string iconName
    property string tip
    property bool danger: false
    property bool armed: false          // danger action waiting for its confirming click

    implicitWidth: 34
    implicitHeight: 34
    hoverEnabled: true
    focusPolicy: Qt.NoFocus
    opacity: enabled ? 1 : 0.45
    scale: pressed ? 0.92 : 1
    Behavior on scale { NumberAnimation { duration: 90 } }
    HoverHandler { cursorShape: Qt.PointingHandCursor }

    ToolTip.visible: hovered && tip !== ""
    ToolTip.delay: 300
    ToolTip.text: tip

    background: Rectangle {
        radius: width / 2
        color: a.armed ? Theme.danger
             : a.hovered ? (a.danger ? "#e6c62d25" : Theme.accent)
             : "#bf151519"
        border.width: 1
        border.color: "#2effffff"
        Behavior on color { ColorAnimation { duration: 120 } }
    }
    contentItem: Item {
        Icon {
            anchors.centerIn: parent
            name: a.iconName
            size: 16
            color: "white"
        }
    }
}
