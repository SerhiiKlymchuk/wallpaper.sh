import QtQuick
import QtQuick.Controls.Basic
import "."

AbstractButton {
    id: b
    property string iconName: ""
    property string variant: "primary"      // primary | ghost | glass | danger
    property bool compact: false
    readonly property color fg: variant === "danger" ? Theme.danger : variant === "ghost" ? Theme.text : "white"

    implicitHeight: compact ? 34 : 42
    implicitWidth: text ? row.implicitWidth + (compact ? 26 : 36) : implicitHeight
    hoverEnabled: true
    focusPolicy: Qt.NoFocus
    opacity: enabled ? 1 : 0.4
    scale: pressed ? 0.96 : 1
    font.family: Theme.font
    font.pixelSize: compact ? 13 : 14
    font.weight: Font.DemiBold
    Behavior on scale { NumberAnimation { duration: 90 } }

    HoverHandler { cursorShape: Qt.PointingHandCursor }

    background: Rectangle {
        radius: height / 2
        color: b.variant === "ghost" ? (b.hovered ? Theme.surfaceHover : Theme.surfaceHi)
             : b.variant === "glass" ? (b.hovered ? "#66000000" : "#40000000")
             : b.variant === "danger" ? (b.hovered ? "#33ff5a52" : "#1aff5a52")
             : "transparent"
        border.width: b.variant === "glass" ? 1 : 0
        border.color: "#2effffff"
        gradient: b.variant === "primary" ? primaryGradient : null

        Gradient {
            id: primaryGradient
            orientation: Gradient.Horizontal
            GradientStop { position: 0; color: b.hovered ? Theme.accentHi : Theme.accent }
            GradientStop { position: 1; color: Theme.red }
        }
    }

    contentItem: Item {
        Row {
            id: row
            anchors.centerIn: parent
            spacing: 8
            Icon {
                anchors.verticalCenter: parent.verticalCenter
                visible: b.iconName !== ""
                name: b.iconName
                size: b.compact ? 15 : 17
                color: b.fg
            }
            Label {
                anchors.verticalCenter: parent.verticalCenter
                visible: b.text !== ""
                text: b.text
                font: b.font
                color: b.fg
            }
        }
    }
}
