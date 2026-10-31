import QtQuick
import QtQuick.Controls.Basic
import "."

AbstractButton {
    id: c
    property string iconName: ""
    property bool active: false
    property bool onImage: false
    property bool closable: false
    property bool soft: false           // active state as a tint instead of solid accent
    signal closeClicked()

    implicitHeight: 30
    implicitWidth: row.implicitWidth + 24
    hoverEnabled: true
    focusPolicy: Qt.NoFocus

    HoverHandler { cursorShape: Qt.PointingHandCursor }

    background: Rectangle {
        radius: height / 2
        color: c.active ? (c.soft ? Theme.accentSoft : Theme.accent)
             : c.onImage ? "#99151519"
             : c.hovered && c.enabled ? Theme.surfaceHover : Theme.surfaceHi
        border.width: c.onImage ? 1 : 0
        border.color: "#1fffffff"
        Behavior on color { ColorAnimation { duration: 120 } }
    }

    contentItem: Item {
        Row {
            id: row
            anchors.centerIn: parent
            spacing: 6
            Icon {
                anchors.verticalCenter: parent.verticalCenter
                visible: c.iconName !== ""
                name: c.iconName
                size: 13
                color: c.active ? (c.soft ? Theme.accentText : "white") : c.onImage ? "#ccffffff" : (c.hovered && c.enabled ? Theme.accent : Theme.textDim)
            }
            Label {
                anchors.verticalCenter: parent.verticalCenter
                text: c.text
                font.pixelSize: 12
                font.weight: Font.Medium
                color: c.active && c.soft ? Theme.accentText : c.active || c.onImage ? "white" : Theme.text
            }
            Item {
                anchors.verticalCenter: parent.verticalCenter
                visible: c.closable
                width: 14
                height: 14
                Icon {
                    anchors.centerIn: parent
                    name: "x"
                    size: 12
                    color: closeArea.containsMouse ? Theme.danger : Theme.textFaint
                }
                MouseArea {
                    id: closeArea
                    anchors.fill: parent
                    anchors.margins: -5
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: c.closeClicked()
                }
            }
        }
    }
}
