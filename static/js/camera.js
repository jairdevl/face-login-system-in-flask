const player = document.getElementById('player');
const canvas = document.getElementById('canvas');
const context = canvas.getContext('2d');
const captureButton = document.getElementById('capture');
const scan = document.getElementById('scan');
const img = document.getElementById('pic');
const name = document.getElementById('name');

const vgaconstraints = {
    video: { width: { exact: 640 }, height: { exact: 480 } },
};

function capture() {
    context.drawImage(player, 0, 0, canvas.width, canvas.height);
    player.style.display = "none";
    captureButton.style.display = "none";
    scan.style.display = "block";
    name.style.display = "block";

    cap = canvas.toDataURL('image/png').split(",")[1];
    img.value = cap;
}

function stop() {
    player.srcObject.getVideoTracks().forEach(track => track.stop());
}

navigator.mediaDevices.getUserMedia(vgaconstraints)
    .then((stream) => {
        player.srcObject = stream;
    });