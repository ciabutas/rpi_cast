async function saveSettings() {
    const settings = {
        raspip: document.getElementById("raspip").value,
        cmFunction: document.querySelector('input[name="cmFunction"]:checked').value,
        modeslow: document.querySelector('input[name="mode_slow"]:checked').value
    };

    await browser.storage.local.set(settings);
    showMessage("Settings saved successfully!");
}

function showMessage(msg) {
    const messageDiv = document.getElementById("message");
    messageDiv.textContent = msg;
    messageDiv.style.display = "block";
    setTimeout(() => {
        messageDiv.style.display = "none";
    }, 3000);
}

async function loadSettings() {
    const defaults = {
        raspip: 'raspberrypi.local',
        cmFunction: 'stream',
        modeslow: 'False'
    };

    const settings = await browser.storage.local.get(defaults);

    document.getElementById("raspip").value = settings.raspip;
    document.getElementById(settings.cmFunction === "stream" ? "cmFstream" : "cmFqueue").checked = true;
    document.getElementById(settings.modeslow === "False" ? "high_qual" : "bad_qual").checked = true;
}

document.addEventListener("DOMContentLoaded", () => {
    loadSettings();
    document.getElementById("saveButton").addEventListener("click", saveSettings);
});
