import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "."

Rectangle {
    id: t
    property string iconName
    property string title
    property string subtitle
    property bool checked
    property bool available: true
    signal toggled(bool on)

    implicitHeight: 84
    radius: Theme.radiusSm
    color: area.containsMouse && available ? Theme.surfaceHi : Theme.surface
    border.width: 1
    border.color: checked && available ? "#59ff6b1f" : "transparent"
    Behavior on color { ColorAnimation { duration: 120 } }

    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        enabled: t.available
        cursorShape: Qt.PointingHandCursor
        onClicked: t.toggled(!t.checked)
    }
    RowLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 14
        Rectangle {
            Layout.preferredWidth: 44
            Layout.preferredHeight: 44
            radius: 12
            color: t.checked && t.available ? Theme.accentSoft : Theme.surfaceHi
            Icon {
                anchors.centerIn: parent
                name: t.iconName
                size: 20
                color: t.checked && t.available ? Theme.accent : Theme.textDim
            }
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 3
            Label { text: t.title; font.pixelSize: 15; font.weight: Font.DemiBold }
            Label {
                Layout.fillWidth: true
                text: t.subtitle
                elide: Text.ElideRight
                font.pixelSize: 12
                color: t.available ? Theme.textDim : Theme.danger
            }
        }
        AppSwitch {
            checked: t.checked && t.available
            enabled: t.available
            onClicked: t.toggled(checked)
        }
    }
}
