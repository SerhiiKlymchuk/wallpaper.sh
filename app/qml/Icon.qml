import QtQuick
import "."

// Stroke icon from the Python icon provider, tinted to any color.
Item {
    property string name
    property color color: Theme.text
    property int size: 18

    implicitWidth: size
    implicitHeight: size

    Image {
        anchors.fill: parent
        sourceSize: Qt.size(parent.size * 2, parent.size * 2)
        source: parent.name ? "image://icon/" + parent.name + "/" + String(parent.color).replace("#", "") : ""
        smooth: true
        mipmap: true
    }
}
