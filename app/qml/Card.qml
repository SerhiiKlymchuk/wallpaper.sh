import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic
import "."

// Surface panel with a title; children go into a padded column.
Rectangle {
    id: card
    property string title
    property string subtitle
    default property alias content: body.data

    implicitHeight: col.implicitHeight + 48
    radius: Theme.radius
    color: Theme.surface

    ColumnLayout {
        id: col
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
        spacing: 18
        ColumnLayout {
            spacing: 4
            visible: card.title !== ""
            Label { text: card.title; font.pixelSize: 17; font.weight: Font.DemiBold }
            Label {
                Layout.fillWidth: true
                visible: card.subtitle !== ""
                text: card.subtitle
                wrapMode: Text.WordWrap
                font.pixelSize: 13
                color: Theme.textDim
            }
        }
        ColumnLayout {
            id: body
            Layout.fillWidth: true
            spacing: 16
        }
    }
}
