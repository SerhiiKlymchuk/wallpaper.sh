import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "."

ScrollView {
    id: page
    readonly property var theme: backend.activeTheme

    contentWidth: availableWidth
    rightPadding: 14
    clip: true

    ColumnLayout {
        width: page.availableWidth
        spacing: 16

        PageHeader {
            Layout.fillWidth: true
            title: "Themes"
            subtitle: "A theme is what your wallpapers are about. Each run picks one of its categories by weight, then searches wallhaven.cc with a few of that category's queries. Short, tag-like words work best. Click a query to try it right now."
        }

        // --- theme switcher ------------------------------------------------
        Flow {
            Layout.fillWidth: true
            spacing: 8
            Repeater {
                model: backend.themes
                delegate: Chip {
                    required property var modelData
                    implicitHeight: 34
                    text: modelData.label
                    active: modelData.active
                    onClicked: if (!modelData.active) backend.setActiveTheme(modelData.id)
                }
            }
            TextField {
                id: newTheme
                width: 170
                height: 34
                placeholderText: "+ new theme"
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
                    radius: 17
                    color: "transparent"
                    border.width: 1
                    border.color: newTheme.activeFocus ? Theme.accent : Theme.stroke
                }
                onAccepted: {
                    if (text.trim()) backend.addTheme(text)
                    text = ""
                }
            }
        }

        // --- active theme settings ---------------------------------------
        Rectangle {
            Layout.fillWidth: true
            Layout.topMargin: 4
            implicitHeight: themeCol.implicitHeight + 44
            radius: Theme.radius
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: Theme.accentSoft }
                GradientStop { position: 1; color: Theme.surface }
            }
            border.width: 1
            border.color: Theme.accentSoft

            ColumnLayout {
                id: themeCol
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 22 }
                spacing: 14

                RowLayout {
                    spacing: 12
                    TextField {
                        id: themeName
                        Layout.preferredWidth: 340
                        text: page.theme.label
                        font.family: Theme.display
                        font.pixelSize: 22
                        font.weight: Font.Bold
                        color: Theme.text
                        selectByMouse: true
                        selectionColor: Theme.accent
                        leftPadding: 10
                        background: Rectangle {
                            radius: 10
                            color: themeName.activeFocus ? Theme.surfaceHi : themeName.hovered ? Theme.hoverTint : "transparent"
                        }
                        onEditingFinished: if (text.trim() && text !== page.theme.label) backend.renameTheme(text)
                    }
                    Item { Layout.fillWidth: true }
                    PillButton {
                        variant: "ghost"
                        compact: true
                        text: "Reset to defaults"
                        iconName: "refresh"
                        visible: page.theme.preset
                        onClicked: backend.resetCategories()
                    }
                    PillButton {
                        variant: "danger"
                        compact: true
                        text: "Delete theme"
                        iconName: "trash"
                        enabled: backend.themes.length > 1
                        onClicked: backend.deleteTheme()
                    }
                }

                RowLayout {
                    spacing: 8
                    Label { text: "Content"; font.pixelSize: 13; color: Theme.textDim; Layout.preferredWidth: 70 }
                    Repeater {
                        model: [["general", "General"], ["anime", "Anime"], ["people", "People"]]
                        delegate: Chip {
                            required property var modelData
                            readonly property bool on: page.theme.content.indexOf(modelData[0]) >= 0
                            text: modelData[1]
                            iconName: on ? "check" : ""
                            active: on
                            onClicked: backend.setThemeContent(modelData[0], !on)
                        }
                    }
                    Label {
                        Layout.leftMargin: 8
                        text: "wallhaven content types to search · always safe-for-work"
                        font.pixelSize: 12
                        color: Theme.textFaint
                    }
                }
            }
        }

        RowLayout {
            Layout.topMargin: 6
            Label {
                Layout.fillWidth: true
                text: "Categories"
                font.pixelSize: 18
                font.weight: Font.DemiBold
            }
            PillButton { compact: true; text: "Add category"; iconName: "plus"; onClicked: backend.addCategory() }
        }

        Repeater {
            model: backend.categories
            delegate: CategoryCard {
                required property var modelData
                required property int index
                Layout.fillWidth: true
                cat: modelData
                idx: index
                total: backend.totalWeight
            }
        }
        Item { Layout.preferredHeight: 8 }
    }
}
