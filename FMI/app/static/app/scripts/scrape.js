// script.js

'use strict';

// JQuery


function display_message(data) {
    $("#scrape_progress").append("<p>" + data + "</p>");
}

function poll() {
    var poll_interval = 0;

    $.ajax({
        url: "api/scrape_pollresults",
        type: 'GET',
        dataType: 'json',
        cache: false,
        success: function (data) {
            display_message(data);
            poll_interval = 0;
        },
        error: function () {
            poll_interval = 1000;
        },
        complete: function () {
            setTimeout(poll, poll_interval);
        },
    });
}


$('button[name^="scrape"]').click(function () {
    poll();
})

$(document).ready(function () {
//    poll();
});




