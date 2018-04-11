// script.js

'use strict';

// JQuery


function platform_search_onchange(select) {
    //var options = select.options;
    //for (var i = 0; i < options.length; i++) {
    //    if (options[i].selected) {
    //        var url = options[i].value;
    //        break;
    //    }
    //}
    var url = window.location.href;
    //check on Local or Apache web server
    if (url[url.length - 1] != '/') { url = url + '/' }
    url = url + select.value;
    var input = document.getElementById("platform_search_q");
    var keywords_q = input.value;
    window.location.href = url + "?q=" + keywords_q;
}

function platformsearch(keywords_q) {
    var params = {
        "q": keywords_q,
    };
     //get the form fields and add them as parameters to the GET. The submit will fire off its own GET request
    //document.getElementById("seeker_form").submit();
    // url calculation is needed for WSGI
    var url = window.location.href;
    if (url[url.length-1] != '/') { url = url + '/'}
    url = url + "api/platformsearch";
    $.get(url, params, function (data, status) {
        var select = document.getElementById("platform_search_select");
        // remove any existing options
        select.options.length = 0;
        for (var dataset in data) {
            var option = document.createElement("option");
            option.value = data[dataset]['url'];
            option.text = dataset + " (" + data[dataset]['count']+ ")";
            select.appendChild(option);
        }
    });
}


$("#platform_search_q").keyup(function (e) {
    if (e.keyCode == 13) {
        var input = document.getElementById("platform_search_q");
        var keywords_q = input.value;
        platformsearch(keywords_q);
    }
});