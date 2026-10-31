import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page
    signal previewRequested(var list, int index)

    property string filter: ""
    readonly property var categories: [...new Set(backend.images.map(i => i.category))]
    readonly property var shown: filter ? backend.images.filter(i => i.category === filter) : backend.images

    spacing: 20

    PageHeader {
        Layout.fillWidth: true
        title: "Gallery"
        subtitle: backend.images.length + " images in " + backend.about.folder + "  ·  the newest " + backend.keepFiles + " are kept  ·  hover an image for quick actions"
        PillButton { variant: "ghost"; text: "Open folder"; iconName: "folder"; onClicked: backend.openFolder() }
    }

    Flow {
        Layout.fillWidth: true
        spacing: 8
        Chip { text: "All"; active: page.filter === ""; onClicked: page.filter = "" }
        Repeater {
            model: page.categories
            delegate: Chip {
                required property string modelData
                text: backend.images.find(i => i.category === modelData).categoryLabel
                active: page.filter === modelData
                onClicked: page.filter = modelData
            }
        }
    }

    GridView {
        id: grid
        readonly property int columns: Math.max(2, Math.floor(width / 300))
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.leftMargin: -8
        Layout.rightMargin: -8
        clip: true
        cellWidth: width / columns
        cellHeight: cellWidth * 0.64
        model: page.shown
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {}

        delegate: Item {
            required property var modelData
            required property int index
            width: grid.cellWidth
            height: grid.cellHeight
            GalleryCard {
                anchors.fill: parent
                anchors.margins: 8
                actions: true
                img: parent.modelData
                onClicked: page.previewRequested(page.shown, parent.index)
            }
        }

        Label {
            anchors.centerIn: parent
            visible: grid.count === 0
            text: "No wallpapers yet - hit “New image” to get the first one"
            color: Theme.textDim
        }
    }
}
