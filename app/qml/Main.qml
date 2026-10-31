import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "."

ApplicationWindow {
    id: win
    width: 1340
    height: 880
    minimumWidth: 1080
    minimumHeight: 720
    visible: true
    title: backend.about.name
    color: Theme.bg
    font.family: Theme.font

    palette {
        window: Theme.bg
        windowText: Theme.text
        text: Theme.text
        base: Theme.surface
        button: Theme.surfaceHi
        buttonText: Theme.text
        highlight: Theme.accent
        highlightedText: "white"
        placeholderText: Theme.textFaint
        toolTipBase: Theme.surfaceHi
        toolTipText: Theme.text
        mid: Theme.stroke
        dark: Theme.surfaceHover
    }

    readonly property var pages: [["Now", "flag"], ["Gallery", "grid"], ["Themes", "sparkles"], ["Schedule", "clock"]]
    readonly property int aboutPage: 4
    property int page: 0

    Binding { target: Theme; property: "mode"; value: backend.appearance }

    // warm glow in the top-left corner, like light bleeding off the hero image
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: Theme.glow }
            GradientStop { position: 0.4; color: Theme.bg }
        }
    }

    Connections {
        target: backend
        function onToast(message, ok) { toast.show(message, ok) }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // --- sidebar ---------------------------------------------------------
        ColumnLayout {
            Layout.preferredWidth: 240
            Layout.minimumWidth: 240
            Layout.maximumWidth: 240
            Layout.fillHeight: true
            Layout.margins: 28
            Layout.rightMargin: 12
            spacing: 6

            RowLayout {
                spacing: 12
                Layout.bottomMargin: 36
                Image {
                    Layout.preferredWidth: 32          // 1:1 with the 32 px pixel art
                    Layout.preferredHeight: 32
                    source: Qt.resolvedUrl("../icon-32.png")
                    sourceSize: Qt.size(32, 32)
                    smooth: false
                }
                Column {
                    Label { text: "wallpaper.sh"; font.pixelSize: 17; font.weight: Font.Black }
                    Label { text: "wallpaper of the day"; font.pixelSize: 12; color: Theme.textDim }
                }
            }

            Repeater {
                model: win.pages
                delegate: NavItem {
                    required property var modelData
                    required property int index
                    Layout.fillWidth: true
                    text: modelData[0]
                    iconName: modelData[1]
                    active: win.page === index
                    onClicked: win.page = index
                }
            }

            Item { Layout.fillHeight: true }

            NavItem {
                Layout.fillWidth: true
                Layout.bottomMargin: 12
                text: "About"
                iconName: "info"
                active: win.page === win.aboutPage
                onClicked: win.page = win.aboutPage
            }

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: side.implicitHeight + 32
                radius: Theme.radiusSm
                color: "transparent"
                border.width: 1
                border.color: Theme.stroke
                ColumnLayout {
                    id: side
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 16 }
                    spacing: 4
                    Label { text: "Next change"; font.pixelSize: 12; color: Theme.textDim }
                    RowLayout {
                        Label {
                            Layout.fillWidth: true
                            text: backend.schedule.active ? backend.schedule.nextRelative || backend.schedule.nextLabel : "Off"
                            elide: Text.ElideRight
                            font.pixelSize: 15
                            font.weight: Font.DemiBold
                        }
                        PillButton {
                            compact: true
                            variant: "ghost"
                            iconName: "refresh"
                            enabled: !backend.busy
                            ToolTip.visible: hovered
                            ToolTip.text: "New image now"
                            onClicked: backend.newImage()
                        }
                    }
                }
            }
        }

        // --- content ---------------------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 28
            Layout.rightMargin: 32
            Layout.bottomMargin: 24
            spacing: 26

            RowLayout {
                Layout.fillWidth: true
                spacing: 14

                Rectangle {
                    Layout.fillWidth: true
                    Layout.maximumWidth: 600
                    Layout.preferredHeight: 46
                    radius: 14
                    color: Theme.surface
                    border.width: 1
                    border.color: prompt.activeFocus ? "#80ff6b1f" : "transparent"

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 16
                        anchors.rightMargin: 6
                        spacing: 10
                        Icon { name: "search"; size: 17; color: Theme.textDim }
                        TextField {
                            id: prompt
                            Layout.fillWidth: true
                            placeholderText: "Try a prompt - e.g. " + backend.activeTheme.examples
                            placeholderTextColor: Theme.textFaint
                            color: Theme.text
                            font.pixelSize: 14
                            selectByMouse: true
                            selectionColor: Theme.accent
                            background: null
                            onAccepted: if (text.trim() && !backend.busy) backend.tryQuery(text)
                        }
                        PillButton {
                            compact: true
                            text: "Find"
                            iconName: "sparkles"
                            enabled: prompt.text.trim() !== "" && !backend.busy
                            onClicked: backend.tryQuery(prompt.text)
                        }
                    }
                }

                Item { Layout.fillWidth: true }

                Rectangle {
                    visible: backend.busy
                    Layout.preferredHeight: 38
                    Layout.preferredWidth: Math.min(busyRow.implicitWidth + 30, 420)
                    radius: 19
                    color: Theme.surface
                    Row {
                        id: busyRow
                        anchors.centerIn: parent
                        spacing: 10
                        Spinner { anchors.verticalCenter: parent.verticalCenter; size: 16 }
                        Label {
                            anchors.verticalCenter: parent.verticalCenter
                            width: Math.min(implicitWidth, 360)
                            text: backend.status
                            elide: Text.ElideRight
                            font.pixelSize: 12
                            color: Theme.textDim
                        }
                    }
                }

                PillButton {
                    variant: "ghost"
                    iconName: "folder"
                    ToolTip.visible: hovered
                    ToolTip.text: "Open wallpaper folder"
                    onClicked: backend.openFolder()
                }

                PillButton {
                    variant: "ghost"
                    iconName: Theme.dark ? "sun" : "moon"
                    ToolTip.visible: hovered
                    ToolTip.text: Theme.dark ? "Switch to light mode" : "Switch to dark mode"
                    onClicked: backend.setAppearance(Theme.dark ? "light" : "dark")
                }
            }

            StackLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: win.page

                NowPage {
                    onPreviewRequested: (list, index) => preview.show(list, index)
                    onGalleryRequested: win.page = 1
                }
                GalleryPage {
                    onPreviewRequested: (list, index) => preview.show(list, index)
                }
                PromptsPage {}
                SchedulePage {}
                AboutPage {}
            }
        }
    }

    PreviewPopup { id: preview; objectName: "preview" }
    Toast { id: toast }
}
