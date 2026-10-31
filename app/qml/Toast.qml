import QtQuick
import QtQuick.Controls.Basic
import "."

Rectangle {
    id: toast
    property bool success: true

    function show(message, ok) {
        label.text = message
        success = ok
        state = "shown"
        hideTimer.restart()
    }

    width: Math.min(row.implicitWidth + 36, parent.width - 48)
    height: 48
    radius: 24
    color: Theme.surfaceHi
    border.width: 1
    border.color: success ? "#4041d392" : "#66ff5a52"
    opacity: 0
    y: parent.height
    anchors.horizontalCenter: parent.horizontalCenter

    states: State {
        name: "shown"
        PropertyChanges { toast.opacity: 1; toast.y: toast.parent.height - toast.height - 28 }
    }
    transitions: Transition {
        NumberAnimation { properties: "opacity,y"; duration: 220; easing.type: Easing.OutCubic }
    }
    Timer { id: hideTimer; interval: 4200; onTriggered: toast.state = "" }

    Row {
        id: row
        anchors.centerIn: parent
        spacing: 10
        Icon {
            anchors.verticalCenter: parent.verticalCenter
            name: toast.success ? "check" : "x"
            size: 16
            color: toast.success ? Theme.ok : Theme.danger
        }
        Label {
            id: label
            anchors.verticalCenter: parent.verticalCenter
            width: Math.min(implicitWidth, toast.parent.width - 120)
            elide: Text.ElideRight
            font.pixelSize: 13
            font.weight: Font.Medium
        }
    }
}
