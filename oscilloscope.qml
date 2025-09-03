import QtQuick 2.15
import QtQuick.Window
import QtQuick.Layouts

Rectangle {
    id: window
    visible: true
    anchors.fill: parent

    property var spectrum: []
    property double fftTime: 0
    property double prepTime: 0
    property double frameTime: 0
    color: "black"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

        Text {
            text: "FFT time: " + window.fftTime.toFixed(2) + " µs"
            color: "white"
        }
        Text {
            text: "Prep time: " + window.prepTime.toFixed(2) + " µs"
            color: "white"
        }
        Text {
            text: "Frame time: " + window.frameTime.toFixed(2) + " ms"
            color: "white"
        }

        Canvas {
            id: canvas
            Layout.fillWidth: true
            Layout.fillHeight: true

            onPaint: {
                var start = Date.now();
                var ctx = getContext("2d");
                ctx.reset();
                ctx.fillStyle = "#111";
                ctx.fillRect(0, 0, width, height);
                ctx.strokeStyle = "#0f0";
                ctx.beginPath();
                if (window.spectrum.length > 0) {
                    var logMax = Math.log10(Math.max.apply(Math, window.spectrum));
                    if (logMax <= 0) {
                        logMax = 1;
                    }
                    var step = width / window.spectrum.length;

                    var y0 = height - (Math.log10(window.spectrum[0]) / logMax) * height;
                    ctx.moveTo(0, y0);

                    for (var i = 1; i < window.spectrum.length; i++) {
                        var logVal = Math.log10(Math.max(1, window.spectrum[i]));
                        var y = height - (logVal / logMax) * height;
                        ctx.lineTo(i * step, y);
                    }
                }
                ctx.stroke();
                window.frameTime = Date.now() - start;
            }

            Component.onCompleted: canvas.requestPaint()
        }
    }

    Connections {
        target: worker
        function onDataReady(mags, fft, prep) {
            window.spectrum = mags;
            window.fftTime = fft;
            window.prepTime = prep;
            canvas.requestPaint();  
        }
    }
}
