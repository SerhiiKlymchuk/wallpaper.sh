import QtQuick
import "."

Icon {
    name: "loader"
    color: Theme.accent
    RotationAnimator on rotation {
        from: 0; to: 360; duration: 800
        loops: Animation.Infinite
        running: visible
    }
}
