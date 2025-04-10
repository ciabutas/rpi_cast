function message(msg, importance) {
	$( "#message" ).html("");
	$( "#message" ).show("slow");
	if (importance == 1) {
		$( "#message" ).html("<p class='bg-success'>"+msg+"</p>");
	} else if (importance == 2) {
		$( "#message" ).html("<p class='bg-danger'>"+msg+"</p>");
	} else {
		$( "#message" ).html("<p class='bg-info'>"+msg+"</p>");
	}
	setTimeout(function() {
		$( "#message" ).hide("slow");
	}, 3000);	
}

function advanced() {
	$( "#advanced" ).toggle("fast");

	if($("#link-text").html() === "More options ▾") {
		$("#link-text").html("More options ▴");
	} else {
		$("#link-text").html("More options ▾");
	}
}


function showHistory() {
	//Only update history when div is being toggled ON
	if (!$( "#history-div" ).is(":visible"))
		updateHistoryDiv();

	$( "#history-div" ).toggle("fast");
}

function addToHistory(url) {
    if (storageAvailable('localStorage')) {
        try {
            let historyArray = JSON.parse(localStorage.getItem('history')) || [];
            url = url.replace(/\"/g, "");
            
            if (!historyArray.includes(url)) {
                historyArray.push(url);
            }
            
            localStorage.setItem('history', JSON.stringify(historyArray));
        } catch (e) {
            console.error('Failed to update history:', e);
        }
    }
}

function mkrequest(url, response) {
    const timeout = 30000; // 30 seconds
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        
        fetch(document.location.origin + url, { signal: controller.signal })
            .then(response => response.json())
            .then(data => {
                clearTimeout(timeoutId);
                handleResponse(data, response);
            })
            .catch(error => {
                clearTimeout(timeoutId);
                message("Request failed: " + error.message, 2);
            });
    } catch (e) {
        message("Request failed: " + e.message, 2);
    }
}

$(function() {

	$( "#castbtn" ).click(function() {
		if ( $( "#media_url" ).val() !== "" ) {
			var url = $( "#media_url" ).val();
			var url_encoded_url = encodeURIComponent(url);
			addToHistory(url);
			mkrequest("/stream?url=" + url_encoded_url, 1);
		} else {
			message("You must enter a link !", 2)
		}	
	});

	$( "#addqueue" ).click(function() {
		if ( $( "#media_url" ).val() !== "" ) {
			var url = $( "#media_url" ).val();
			var url_encoded_url = encodeURIComponent(url);
			mkrequest("/queue?url=" + url_encoded_url, 2)
		} else {
			message("You must enter a link !", 2)
		}		
	});

	$("#clear_search").click(function(){
		$("#media_url").val('');
		$("#clear_search").hide();
	});

	$("#media_url").keyup(function(){
		if($(this).val()) {
			$("#clear_search").show();
		} else {
			$("#clear_search").hide();
		}

	});

	$( "#shutbtn" ).click(function() {
		if ( $( "#time_shut" ).val() !== "" ) {
			var time = $( "#time_shut" ).val();
			console.log($( "#time_shut" ).val());
			mkrequest("/shutdown?time=" + time, 3)
		} else {
			message("You must enter a duration !", 2)
		}
	});	

	$( "#cancelshut" ).click(function() {
		mkrequest("/shutdown?time=cancel", 4)
	});

	$( "#nextqueue" ).click(function() {
		mkrequest("/video?control=next", 1)
	});

	$( "#pause" ).click(function() {
		mkrequest("/video?control=pause", 0);
	});	

	$( "#stop" ).click(function() {
		mkrequest("/video?control=stop", 0);
	});
	
	$( "#backward" ).click(function() {
		mkrequest("/video?control=left", 0);
	});
	
	$( "#forward" ).click(function() {
		mkrequest("/video?control=right", 0);
	});

	$( "#long-backward" ).click(function() {
		mkrequest("/video?control=longleft", 0);
	});
	
	$( "#long-forward" ).click(function() {
		mkrequest("/video?control=longright", 0);
	});
	
	$( "#vol_down" ).click(function() {
		mkrequest("/sound?vol=less", 0);
	});
	
	$( "#vol_up" ).click(function() {
		mkrequest("/sound?vol=more", 0);
	});
	
	
});
