import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic
import "."

RowLayout {
    property string title
    property string subtitle
    default property alias actions: actionRow.data

    spacing: 16
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6
        Label { text: title; font.family: Theme.display; font.pixelSize: 28; font.weight: Font.Bold }
        Label {
            Layout.fillWidth: true
            Layout.maximumWidth: 680
            visible: subtitle !== ""
            text: subtitle
            wrapMode: Text.WordWrap
            font.pixelSize: 13
            lineHeight: 1.2
            color: Theme.textDim
        }
    }
    RowLayout {
        id: actionRow
        Layout.alignment: Qt.AlignBottom
        spacing: 10
    }
}
