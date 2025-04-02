let clonewhole;

async function getSettings() {
    const result = await browser.storage.local.get(['raspip', 'modeslow']);
    return {
        raspip: result.raspip || 'raspberrypi.local',
        modeslow: result.modeslow || 'False'
    };
}

async function handlers() {
    const settings = await getSettings();

    $("#castbtn").click(async () => {
        const tabs = await browser.tabs.query({active: true, currentWindow: true});
        const url_encoded = encodeURIComponent(tabs[0].url);
        await mkrequest(`/stream?url=${url_encoded}&slow=${settings.modeslow}`, 1);
        window.close();
    });

    $("#addqueue").click(async () => {
        const tabs = await browser.tabs.query({active: true, currentWindow: true});
        const url_encoded = encodeURIComponent(tabs[0].url);
        await mkrequest(`/queue?url=${url_encoded}&slow=${settings.modeslow}`, 1);
        window.close();
    });

    // Media controls
    $("#pause").click(() => mkrequest("/video?control=pause", 0));
    $("#stop").click(() => {
        mkrequest("/video?control=stop", 0);
        window.close();
    });
    $("#backward").click(() => mkrequest("/video?control=left", 0));
    $("#forward").click(() => mkrequest("/video?control=right", 0));
    $("#vol_down").click(() => mkrequest("/sound?vol=less", 0));
    $("#vol_up").click(() => mkrequest("/sound?vol=more", 0));
}

function remote(toggle) {
    if (toggle === "show") {
        $("#remote").show();
        $("#whole").css("height", "215px");
    } else {
        $("#remote").hide();
        $("#whole").css("height", "100px");
    }
    handlers();
}

function show(message) {
    $("#whole").html(message);
}

async function test() {
    try {
        const settings = await getSettings();
        const newURL = `http://${settings.raspip}:2020/running`;
        show("Loading...");
        
        const response = await fetch(newURL);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const text = await response.text();
        $("#whole").replaceWith(clonewhole.clone());
        remote(text === "1" ? "show" : "hide");
    } catch(err) {
        show("Error! Make sure the ip/port are correct and the server is running.");
        console.error('Error:', err);
        return "0";
    }
}

$(document).ready(() => {
    clonewhole = $("#whole").clone();
    test();
});
