import QtQuick
import QtQuick.Controls.Basic
import "."

AbstractButton {
    id: n
    property string iconName
    property bool active: false
    readonly property color fg: active ? Theme.accentText : hovered ? Theme.text : Theme.textDim

    implicitHeight: 44
    hoverEnabled: true
    focusPolicy: Qt.NoFocus
    background: Item {}

    HoverHandler { cursorShape: Qt.PointingHandCursor }

    contentItem: Item {
        Rectangle {
            x: -24
            anchors.verticalCenter: parent.verticalCenter
            width: 3
            height: 22
            radius: 2
            color: Theme.accent
            opacity: n.active ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: 150 } }
        }
        Row {
            anchors.verticalCenter: parent.verticalCenter
            spacing: 14
            Rectangle {
                width: 30
                height: 30
                radius: 9
                color: n.active ? Theme.accentSoft : "transparent"
                Icon {
                    anchors.centerIn: parent
                    name: n.iconName
                    size: 17
                    color: n.fg
                }
            }
            Label {
                anchors.verticalCenter: parent.verticalCenter
                text: n.text
                color: n.fg
                font.pixelSize: 14
                font.weight: n.active ? Font.DemiBold : Font.Medium
            }
        }
    }
}
