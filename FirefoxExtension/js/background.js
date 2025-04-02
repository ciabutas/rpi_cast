// Use modern storage API instead of localStorage
async function getSettings() {
    const result = await browser.storage.local.get(['raspip', 'cmFunction', 'modeslow']);
    return {
        raspip: result.raspip || 'raspberrypi.local',
        cmFunction: result.cmFunction || 'stream',
        modeslow: result.modeslow || 'False'
    };
}

function stopNote() {
    browser.notifications.clear('notif');
}

function notif(title, msg) {
    const opt = {
        type: "basic",
        title: title,
        message: msg,
        iconUrl: "48.png"
    };

    browser.notifications.create('notif', opt);
    setTimeout(stopNote, 4000);
}

async function mkrequest(url, response) {
    try {
        const settings = await getSettings();
        const newURL = `http://${settings.raspip}:2020${url}`;
        
        if (response === 1) {
            notif("RaspberryCast", "Processing video. Please wait ~ 10 seconds.");
        }

        const res = await fetch(newURL);
        
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }

        if (response === 1) {
            const text = await res.text();
            switch(text) {
                case "1":
                    notif("RaspberryCast", "Video should now start playing.");
                    break;
                case "2":
                    notif("RaspberryCast", "Video has been added to queue.");
                    break;
                default:
                    notif("Error", "Please make sure the link is compatible");
            }
        }
    } catch(err) {
        console.error('Request failed:', err);
        notif("Error", "Make sure the ip/port are correct and the server is running.");
    }
}

// Context menu setup
browser.contextMenus.create({
    id: "Castnow",
    title: "Send to Rpi",
    contexts: ["link"]
});

browser.contextMenus.onClicked.addListener(async (info) => {
    const settings = await getSettings();
    const url_encoded_url = encodeURIComponent(info.linkUrl);
    
    if (settings.cmFunction === "stream") {
        mkrequest(`/stream?url=${url_encoded_url}&slow=${settings.modeslow}`, 1);
    } else {
        mkrequest(`/queue?url=${url_encoded_url}&slow=${settings.modeslow}`, 0);
    }
});

// Handle installation
browser.runtime.onInstalled.addListener(() => {
    browser.tabs.create({url: "../options.html"});
});

// Context menu setup
browser.contextMenus.create({
    id: "Castnow",
    title: "Send to Rpi",
    contexts: ["link"]
});

browser.contextMenus.onClicked.addListener(function(info) {
	var url_encoded_url = encodeURIComponent(info.linkUrl);
	if (localStorage.cmFunction == "stream") {
		mkrequest("/stream?url="+url_encoded_url+"&slow="+localStorage.modeslow, 1);
	} else {
		mkrequest("/queue?url="+url_encoded_url+"&slow="+localStorage.modeslow, 0);
	}
	
});

browser.runtime.onInstalled.addListener(function() {
	browser.tabs.create({url: "../options.html"});
});

browser.contextMenus.create({
	id: "Castnow",
	title: "Send to Rpi",
	contexts: ["link"]
});

