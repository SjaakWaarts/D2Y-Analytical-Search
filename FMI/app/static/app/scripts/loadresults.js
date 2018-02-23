// script.js

'use strict';

// JQuery

var g_qa;

$('[name^="select_all"]').click(function () {
    $('[name ^= "selected[]"]').prop('checked', true);
})

$('[name^="select_none"]').click(function () {
    $('[name ^= "selected[]"]').prop('checked', false);
})

$(document).ready(function () {

    var $table = $("#map_column_table").tablesorter({
        widgets: ["zebra", "filter", "resizable"],
        widgetOptions: {
            // class name applied to filter row and each input
            filter_cssFilter: 'tablesorter-filter',
            // search from beginning
            filter_startsWith: true,
            // Set this option to false to make the searches case sensitive
            filter_ignoreCase: true,
            filter_reset: '.reset',
            resizable_addLastColumn: true
        },
    });

    var $table = $("#map_header_table").tablesorter({
        widgets: ["zebra", "filter", "resizable"],
        widgetOptions: {
            // class name applied to filter row and each input
            filter_cssFilter: 'tablesorter-filter',
            // search from beginning
            filter_startsWith: true,
            // Set this option to false to make the searches case sensitive
            filter_ignoreCase: true,
            filter_reset: '.reset',
            resizable_addLastColumn: true
        },
    });

    var $table = $("#map_question_table").tablesorter({
        widgets: ["zebra", "filter", "resizable"],
        widgetOptions: {
            // class name applied to filter row and each input
            filter_cssFilter: 'tablesorter-filter',
            // search from beginning
            filter_startsWith: true,
            // Set this option to false to make the searches case sensitive
            filter_ignoreCase: true,
            filter_reset: '.reset',
            resizable_addLastColumn: true
        },
    });
});


function ans_onchange(col) {
    var qst = document.getElementById(col + "_qst").value;
    var ans = document.getElementById(col + "_ans").value;
}

function qst_onchange(col) {
    var qst = document.getElementById(col + "_qst").value;
    var ans = ""

    var select = document.getElementById(col + "_ans");
    select.innerHTML = "";
    select.setAttribute("onChange", "ans_onchange('"+col+"')");
    // remove any existing options
    var option = document.createElement("option");
    option.setAttribute("value", "");
    option.text = "Select Answer";
    if (ans == "") {
        option.setAttribute('selected', true);
    }
    select.appendChild(option);
    for (var ix=0; ix<g_qa[qst].length; ix++) {
        var answer = g_qa[qst][ix];
        var option = document.createElement("option");
        option.setAttribute("value", answer);
        option.text = answer;
        if (ans == answer) {
            option.setAttribute('selected', true);
        }
        select.appendChild(option);
    }
}

function survey_qa(qa) {
    g_qa = qa
}




