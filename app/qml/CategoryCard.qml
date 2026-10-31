import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "."

Rectangle {
    id: card
    property var cat
    property int idx
    property int total: 1

    implicitHeight: col.implicitHeight + 44
    radius: Theme.radius
    color: Theme.surface

    ColumnLayout {
        id: col
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 22 }
        spacing: 16

        RowLayout {
            spacing: 12
            TextField {
                id: nameField
                Layout.preferredWidth: 230
                text: card.cat.name
                font.pixelSize: 17
                font.weight: Font.DemiBold
                color: Theme.text
                selectByMouse: true
                selectionColor: Theme.accent
                leftPadding: 10
                background: Rectangle {
                    radius: 10
                    color: nameField.activeFocus ? Theme.surfaceHi : nameField.hovered ? Theme.hoverTint : "transparent"
                }
                onEditingFinished: if (text !== card.cat.name) backend.renameCategory(card.idx, text)
            }
            Rectangle {
                implicitWidth: share.implicitWidth + 20
                implicitHeight: 26
                radius: 13
                color: card.cat.weight > 0 ? Theme.accentSoft : Theme.surfaceHi
                Label {
                    id: share
                    anchors.centerIn: parent
                    text: card.cat.weight > 0 ? Math.round(card.cat.weight / card.total * 100) + "% of picks" : "Never picked"
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                    color: card.cat.weight > 0 ? Theme.accentText : Theme.textFaint
                }
            }
            Item { Layout.fillWidth: true }
            Label { text: "Sort by"; font.pixelSize: 12; color: Theme.textFaint }
            Repeater {
                model: [["relevance", "Best match"], ["date_added", "Newest"], ["toplist", "Top rated"]]
                delegate: Chip {
                    required property var modelData
                    text: modelData[1]
                    active: card.cat.sorting === modelData[0]
                    onClicked: backend.setCategorySorting(card.idx, modelData[0])
                }
            }
            PillButton {
                compact: true
                variant: "danger"
                iconName: "trash"
                ToolTip.visible: hovered
                ToolTip.text: "Delete category"
                onClicked: backend.removeCategory(card.idx)
            }
        }

        RowLayout {
            spacing: 14
            Label { text: "Weight"; font.pixelSize: 13; color: Theme.textDim; Layout.preferredWidth: 52 }
            AppSlider {
                id: weight
                Layout.fillWidth: true
                from: 0
                to: 100
                stepSize: 1
                value: card.cat.weight
                onPressedChanged: if (!pressed && Math.round(value) !== card.cat.weight) backend.setCategoryWeight(card.idx, Math.round(value))
            }
            Label {
                text: Math.round(weight.value)
                font.pixelSize: 13
                font.weight: Font.DemiBold
                horizontalAlignment: Text.AlignRight
                Layout.preferredWidth: 30
            }
        }

        Flow {
            Layout.fillWidth: true
            spacing: 8
            Repeater {
                model: card.cat.queries
                delegate: Chip {
                    required property string modelData
                    required property int index
                    text: modelData
                    iconName: "play"
                    closable: true
                    enabled: !backend.busy
                    ToolTip.visible: hovered
                    ToolTip.delay: 500
                    ToolTip.text: "Find a wallpaper for “" + modelData + "” now"
                    onClicked: backend.tryQuery(modelData)
                    onCloseClicked: backend.removeQuery(card.idx, index)
                }
            }
            TextField {
                id: addField
                width: 190
                height: 30
                placeholderText: "+ add query"
                placeholderTextColor: Theme.textFaint
                font.pixelSize: 12
                color: Theme.text
                leftPadding: 14
                topPadding: 0
                bottomPadding: 0
                verticalAlignment: TextInput.AlignVCenter
                selectByMouse: true
                selectionColor: Theme.accent
                background: Rectangle {
                    radius: 15
                    color: "transparent"
                    border.width: 1
                    border.color: addField.activeFocus ? Theme.accent : Theme.stroke
                }
                onAccepted: {
                    if (text.trim()) backend.addQuery(card.idx, text)
                    text = ""
                }
            }
        }
        Label {
            visible: card.cat.queries.length === 0
            text: "Add at least one query - categories without queries are skipped"
            font.pixelSize: 12
            color: Theme.danger
        }
    }
}
