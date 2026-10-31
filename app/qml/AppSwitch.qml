import QtQuick
import QtQuick.Controls.Basic
import "."

AbstractButton {
    id: s
    checkable: true
    focusPolicy: Qt.NoFocus
    implicitWidth: 42
    implicitHeight: 24
    opacity: enabled ? 1 : 0.4

    HoverHandler { cursorShape: Qt.PointingHandCursor }

    background: Rectangle {
        radius: height / 2
        color: s.checked ? Theme.accent : Theme.surfaceHover
        Behavior on color { ColorAnimation { duration: 150 } }

        Rectangle {
            y: 3
            x: s.checked ? parent.width - width - 3 : 3
            width: 18
            height: 18
            radius: 9
            color: "white"
            Behavior on x { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
        }
    }
    contentItem: Item {}
}
