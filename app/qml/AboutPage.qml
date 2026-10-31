import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "."

ScrollView {
    id: page
    readonly property var info: backend.about

    contentWidth: availableWidth
    rightPadding: 14
    clip: true

    ColumnLayout {
        width: page.availableWidth
        spacing: 20

        // --- hero ----------------------------------------------------------
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 200
            radius: Theme.radius
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: Theme.amber }
                GradientStop { position: 0.5; color: "#e5541f" }
                GradientStop { position: 1.0; color: Theme.red }
            }
            Rectangle {
                anchors.fill: parent
                radius: parent.radius
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#00000000" }
                    GradientStop { position: 1.0; color: "#59000000" }
                }
            }
            RowLayout {
                anchors.fill: parent
                anchors.margins: 32
                spacing: 28
                Image {
                    Layout.preferredWidth: 128
                    Layout.preferredHeight: 128
                    source: Qt.resolvedUrl("../icon-32.png")
                    smooth: false               // keep the pixel art crisp
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Label {
                        text: page.info.name
                        font.family: Theme.display
                        font.pixelSize: 38
                        font.weight: Font.Black
                        color: "white"
                    }
                    Label {
                        text: "Version " + page.info.version
                        font.pixelSize: 15
                        font.weight: Font.DemiBold
                        color: "#ebffffff"
                    }
                    Label {
                        Layout.topMargin: 8
                        text: "Created by " + page.info.author + "  ·  " + page.info.role
                        font.pixelSize: 14
                        color: "white"
                    }
                    Label {
                        Layout.fillWidth: true
                        text: "A fresh wallpaper every day for your desktop, lock screen and login screen - on any theme you like. Happy little wallpapers."
                        wrapMode: Text.WordWrap
                        font.pixelSize: 13
                        color: "#d9ffffff"
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 20

            Card {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignTop
                title: "Compatibility"
                subtitle: "Live check of what this system supports"

                Repeater {
                    model: page.info.checks
                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 12
                        Rectangle {
                            Layout.preferredWidth: 26
                            Layout.preferredHeight: 26
                            radius: 13
                            readonly property color tone: parent.modelData.ok ? Theme.ok : Theme.danger
                            color: Qt.rgba(tone.r, tone.g, tone.b, 0.16)
                            Icon {
                                anchors.centerIn: parent
                                name: parent.parent.modelData.ok ? "check" : "x"
                                size: 14
                                color: parent.parent.modelData.ok ? Theme.ok : Theme.danger
                            }
                        }
                        Label { text: modelData.label; font.pixelSize: 14; font.weight: Font.DemiBold; Layout.preferredWidth: 170 }
                        Label {
                            Layout.fillWidth: true
                            text: modelData.detail
                            elide: Text.ElideRight
                            font.pixelSize: 13
                            color: Theme.textDim
                        }
                    }
                }
            }

            Card {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignTop
                title: "System"

                GridLayout {
                    columns: 2
                    columnSpacing: 24
                    rowSpacing: 12
                    Repeater {
                        model: ["OS", "Session", "Plasma", "Python", "PySide6", "Images", "Settings"]
                        delegate: Label {
                            required property string modelData
                            required property int index
                            Layout.row: index
                            Layout.column: 0
                            text: modelData
                            color: Theme.textDim
                        }
                    }
                    Repeater {
                        model: [page.info.os, page.info.session, page.info.plasma, page.info.python,
                                page.info.pyside, page.info.folder, page.info.config]
                        delegate: Label {
                            required property var modelData
                            required property int index
                            Layout.row: index
                            Layout.column: 1
                            Layout.fillWidth: true
                            text: modelData || "-"
                            elide: Text.ElideMiddle
                            font.weight: Font.DemiBold
                        }
                    }
                }
                Flow {
                    Layout.fillWidth: true
                    spacing: 10
                    PillButton { compact: true; variant: "ghost"; text: "Images folder"; iconName: "folder"; onClicked: backend.openFolder() }
                    PillButton { compact: true; variant: "ghost"; text: "Settings folder"; iconName: "folder"; onClicked: backend.openConfigFolder() }
                    PillButton { compact: true; variant: "ghost"; text: "wallhaven.cc"; iconName: "external"; onClicked: Qt.openUrlExternally("https://wallhaven.cc") }
                    PillButton { compact: true; variant: "ghost"; text: "GitHub"; iconName: "external"; onClicked: Qt.openUrlExternally("https://github.com/SerhiiKlymchuk/wallpaper.sh") }
                }
            }
        }
    }
}
