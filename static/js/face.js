const player = document.getElementById("player");
const canvas = document.getElementById("canvas");
const context = canvas.getContext("2d");
const captureButton = document.getElementById("capture");
const scan = document.getElementById("scan");
const imag = document.getElementById("pic")

const vgaconstraints = {
    video : { with: { exact: 640}, height: { exact: 480 } },
};

function capture() {
    context.drawImage(player, 0, 0, canvas.with, canvas.height);
    player.styl.display = "none";
    captureButton.style.display = "none";
    scan.style.display = "block";

    cap = canvas.toDataURL("/image/png").split(",")[1];
    img.value = cap;
}

function stop() {
    player.srcObject.getVideoTracks().forEach(track => track.stop());
}

navigator.mediaDevices.getUserMedia(vgaconstraints)
    .then((stream) => {
        player.srcObject = stream;
    });