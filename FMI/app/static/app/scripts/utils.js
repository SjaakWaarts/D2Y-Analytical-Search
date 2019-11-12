// script.js

'use strict';

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

function print_date(iso_date) {
    //weekday   : narrow M, short Mon, long Monday
    //year      : 2-digit 01, numeric 2001
    //month     : 2-digit 01, numeric 1, narrow J, short Jan, long January
    //day       : 2-digit 01, numeric 1
    //hour      : 2-digit 12 AM, numeric 12 AM
    //minute    : 2-digit 0, numeric 0
    //second    : 2-digit 0, numeric 0
    //timeZoneName: short 1 / 1 / 2001 GMT + 00: 00, long 1 / 1 / 2001 GMT + 00: 00

    var options = {
        year: "2-digit",
        month: "short",
        day: "2-digit"
    };
    if (typeof iso_date === "string") {
        var date = new Date(iso_date);
    } else {
        var date = iso_date;
    }
    var s = date.toLocaleDateString("nl-NL", options);
    return s;
}


