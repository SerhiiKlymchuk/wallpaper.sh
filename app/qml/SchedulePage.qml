import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "."

ScrollView {
    id: page
    contentWidth: availableWidth
    rightPadding: 14
    clip: true

    // editable copy of backend.schedule, saved explicitly
    property string mode
    property int every
    property string time
    property string day
    readonly property var s: backend.schedule
    readonly property bool timeValid: /^([01]\d|2[0-3]):[0-5]\d$/.test(time)
    readonly property bool dirty: mode !== s.mode || (mode === "hours" && every !== s.every)
                                  || ((mode === "daily" || mode === "weekly") && time !== s.time)
                                  || (mode === "weekly" && day !== s.day)
    readonly property string summary: mode === "off" ? "No automatic changes - only when you press “New image”"
                                    : mode === "hours" ? (every === 1 ? "A new wallpaper every hour" : "A new wallpaper every " + every + " hours")
                                    : mode === "daily" ? "A new wallpaper every day at " + time
                                    : "A new wallpaper every " + day + " at " + time

    function load() {
        mode = s.mode; every = s.every; time = s.time; day = s.day
    }
    Component.onCompleted: load()
    Connections { target: backend; function onScheduleChanged() { if (!page.dirty) page.load() } }

    ColumnLayout {
        width: page.availableWidth
        spacing: 20

        PageHeader {
            Layout.fillWidth: true
            title: "Schedule"
            subtitle: "How often the wallpaper changes on its own. Runs from a systemd user timer, so it works with this app closed, and catches up after sleep or shutdown."
        }

        Card {
            Layout.fillWidth: true
            title: "How often"

            RowLayout {
                Layout.fillWidth: true
                spacing: 14
                Repeater {
                    model: [["off", "pause", "Off", "Manual only"],
                            ["hours", "clock", "Every few hours", "1 – 12 hours"],
                            ["daily", "sun", "Daily", "At a set time"],
                            ["weekly", "calendar", "Weekly", "Day and time"]]
                    delegate: Rectangle {
                        id: tile
                        required property var modelData
                        readonly property bool selected: page.mode === modelData[0]
                        Layout.fillWidth: true
                        implicitHeight: 92
                        radius: Theme.radiusSm
                        color: selected ? Theme.accentSoft : tileArea.containsMouse ? Theme.surfaceHover : Theme.surfaceHi
                        border.width: 1
                        border.color: selected ? Theme.accent : "transparent"
                        Behavior on color { ColorAnimation { duration: 120 } }
                        MouseArea {
                            id: tileArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: page.mode = tile.modelData[0]
                        }
                        Column {
                            anchors { left: parent.left; verticalCenter: parent.verticalCenter; leftMargin: 18 }
                            spacing: 8
                            Icon { name: tile.modelData[1]; size: 20; color: tile.selected ? Theme.accent : Theme.textDim }
                            Column {
                                spacing: 2
                                Label { text: tile.modelData[2]; font.pixelSize: 14; font.weight: Font.DemiBold }
                                Label { text: tile.modelData[3]; font.pixelSize: 12; color: Theme.textDim }
                            }
                        }
                    }
                }
            }

            RowLayout {
                visible: page.mode === "hours"
                spacing: 8
                Label { text: "Every"; color: Theme.textDim; Layout.preferredWidth: 56 }
                Repeater {
                    model: [1, 2, 3, 4, 6, 12]
                    delegate: Chip {
                        required property int modelData
                        text: modelData + " h"
                        active: page.every === modelData
                        onClicked: page.every = modelData
                    }
                }
            }

            RowLayout {
                visible: page.mode === "weekly"
                spacing: 8
                Label { text: "On"; color: Theme.textDim; Layout.preferredWidth: 56 }
                Repeater {
                    model: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                    delegate: Chip {
                        required property string modelData
                        text: modelData
                        active: page.day === modelData
                        onClicked: page.day = modelData
                    }
                }
            }

            RowLayout {
                visible: page.mode === "daily" || page.mode === "weekly"
                spacing: 8
                Label { text: "At"; color: Theme.textDim; Layout.preferredWidth: 56 }
                TextField {
                    id: timeField
                    implicitWidth: 92
                    implicitHeight: 36
                    text: page.time
                    inputMask: "99:99"
                    horizontalAlignment: TextInput.AlignHCenter
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                    font.features: { "tnum": 1 }
                    color: Theme.text
                    selectByMouse: true
                    selectionColor: Theme.accent
                    background: Rectangle {
                        radius: 10
                        color: Theme.surfaceHi
                        border.width: 1
                        border.color: !page.timeValid ? Theme.danger : timeField.activeFocus ? Theme.accent : "transparent"
                    }
                    onTextEdited: page.time = text
                }
                Repeater {
                    model: ["07:00", "08:30", "12:00", "18:00"]
                    delegate: Chip {
                        required property string modelData
                        text: modelData
                        active: page.time === modelData
                        onClicked: page.time = modelData
                    }
                }
            }

            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.stroke }

            RowLayout {
                Layout.fillWidth: true
                Label {
                    Layout.fillWidth: true
                    text: page.summary
                    wrapMode: Text.WordWrap
                    font.pixelSize: 14
                    font.weight: Font.Medium
                }
                PillButton {
                    variant: "ghost"
                    text: "Discard"
                    visible: page.dirty
                    onClicked: page.load()
                }
                PillButton {
                    text: "Save schedule"
                    iconName: "check"
                    enabled: page.dirty && (page.timeValid || page.mode === "off" || page.mode === "hours")
                    onClicked: backend.saveSchedule(page.mode, page.every, page.time, page.day)
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 20

            Card {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignTop
                title: "Status"

                GridLayout {
                    columns: 2
                    columnSpacing: 24
                    rowSpacing: 12
                    Label { text: "Timer"; color: Theme.textDim }
                    Label {
                        text: page.s.active ? "Active" : "Off"
                        font.weight: Font.DemiBold
                        color: page.s.active ? Theme.ok : Theme.textFaint
                    }
                    Label { text: "Next change"; color: Theme.textDim }
                    Label {
                        text: page.s.nextLabel + (page.s.nextRelative ? "  ·  " + page.s.nextRelative : "")
                        font.weight: Font.DemiBold
                    }
                    Label { text: "Last change"; color: Theme.textDim }
                    Label { text: backend.current.appliedLabel || "-"; font.weight: Font.DemiBold }
                }
            }

            Card {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignTop
                title: "Storage & display"

                RowLayout {
                    spacing: 8
                    Label { text: "Keep newest"; color: Theme.textDim; Layout.preferredWidth: 110 }
                    Repeater {
                        model: [20, 40, 80, 150]
                        delegate: Chip {
                            required property int modelData
                            text: modelData
                            active: backend.keepFiles === modelData
                            onClicked: backend.setKeepFiles(modelData)
                        }
                    }
                }
                RowLayout {
                    spacing: 8
                    Label { text: "All monitors"; color: Theme.textDim; Layout.preferredWidth: 110 }
                    AppSwitch {
                        checked: backend.targets.allMonitors
                        onClicked: backend.setAllMonitors(checked)
                    }
                }
            }
        }
    }
}
