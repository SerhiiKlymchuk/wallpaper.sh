pragma Singleton
import QtQuick

QtObject {
    // "dark" | "light" - bound to backend.appearance in Main.qml
    property string mode: "dark"
    readonly property bool dark: mode !== "light"

    // surfaces
    readonly property color bg: dark ? "#121216" : "#f3f2f6"
    readonly property color glow: dark ? "#201517" : "#fde9de"
    readonly property color surface: dark ? "#1c1c22" : "#ffffff"
    readonly property color surfaceHi: dark ? "#25252d" : "#efeef3"
    readonly property color surfaceHover: dark ? "#2e2e38" : "#e4e3ea"
    readonly property color stroke: dark ? "#2c2c36" : "#e1e0e7"
    readonly property color hoverTint: dark ? "#14ffffff" : "#0c000000"

    // text
    readonly property color text: dark ? "#f3f3f5" : "#18181d"
    readonly property color textDim: dark ? "#a2a2ae" : "#5d5d6a"
    readonly property color textFaint: dark ? "#6c6c78" : "#9a9aa6"

    // brand - warm orange to racing red
    readonly property color accent: "#ff6b1f"
    readonly property color accentHi: "#ff8a45"
    readonly property color accentText: dark ? "#ff7a33" : "#e2540e"
    readonly property color accentSoft: dark ? "#2bff6b1f" : "#1fff6b1f"
    readonly property color red: "#e2231a"
    readonly property color amber: "#eaa23b"
    readonly property color danger: dark ? "#ff5a52" : "#e0362d"
    readonly property color ok: dark ? "#41d392" : "#1f9e63"

    readonly property string font: "Inter"
    readonly property string display: "Inter Display"
    readonly property int radius: 18
    readonly property int radiusSm: 14
}
