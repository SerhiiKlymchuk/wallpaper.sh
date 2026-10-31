import QtQuick
import QtQuick.Controls.Basic
import "."

Slider {
    id: sl
    implicitHeight: 24
    focusPolicy: Qt.NoFocus

    HoverHandler { cursorShape: Qt.PointingHandCursor }

    background: Rectangle {
        x: sl.leftPadding
        y: sl.topPadding + sl.availableHeight / 2 - height / 2
        width: sl.availableWidth
        height: 4
        radius: 2
        color: Theme.surfaceHover

        Rectangle {
            width: sl.visualPosition * parent.width
            height: parent.height
            radius: 2
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: Theme.amber }
                GradientStop { position: 1; color: Theme.accent }
            }
        }
    }
    handle: Rectangle {
        x: sl.leftPadding + sl.visualPosition * (sl.availableWidth - width)
        y: sl.topPadding + sl.availableHeight / 2 - height / 2
        width: 18
        height: 18
        radius: 9
        color: "white"
        border.color: Theme.accent
        border.width: 4
        scale: sl.pressed ? 1.15 : 1
        Behavior on scale { NumberAnimation { duration: 100 } }
    }
}
