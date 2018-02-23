// script.js

'use strict';



function draw_conf(chart_name, conf_edit) {
    var chart = g_charts[chart_name];
    var conf_edit_div = document.getElementById("conf_card_div");
    conf_edit_div.innerHTML = "<label>" + chart_name + "</label><br />";
    for (var prop1 in chart) {
        var chart_prop = chart[prop1];
        if (typeof (chart_prop) != 'object') {
            chart_prop = { 'chart': prop1 }
        }
        for (var prop2 in chart_prop) {
            if (prop2 == 'chart') {
                var property = chart_prop['chart'];
                var chart_prop_value = chart[prop1];
            } else {
                var property = prop1 + '.' + prop2;
                var chart_prop_value = chart_prop[prop2];
            }
            if (property in conf_edit) {
                var item_conf = conf_edit[property];
                var form_group_elm = document.createElement("div");
                form_group_elm.setAttribute("class", "form-group");
                conf_edit_div.appendChild(form_group_elm);
                var label_elm = document.createElement("label");
                label_elm.innerHTML = item_conf['descr'];
                form_group_elm.appendChild(label_elm);
                if (item_conf['conf_type'] == "dropdown") {
                    var select_elm = document.createElement("select");
                    select_elm.setAttribute("name", property);
                    form_group_elm.appendChild(select_elm);
                    for (var optix = 0; optix < item_conf['options'].length; optix++) {
                        var option_conf = item_conf['options'][optix];
                        var option_elm = document.createElement("option");
                        option_elm.setAttribute("value", option_conf[1]);
                        option_elm.text = option_conf[0];
                        if (chart_prop[property] == option_conf[1]) {
                            option_elm.setAttribute('selected', true);
                        }
                        select_elm.appendChild(option_elm);
                    }
                } else if (item_conf['conf_type'] == "text") {
                    var input_elm = document.createElement("input");
                    input_elm.setAttribute("name", property);
                    input_elm.value = chart_prop_value;
                    form_group_elm.appendChild(input_elm);
                }
            }
        }
    }
    var input_elm = document.createElement("button");
    input_elm.setAttribute("class", "btn btn-primary");
    input_elm.innerHTML = "Change";
    conf_edit_div.appendChild(input_elm);
    var input_elm = document.createElement("button");
    input_elm.setAttribute("class", "btn btn-primary");
    input_elm.innerHTML = "Add";
    conf_edit_div.appendChild(input_elm);
    g_charts[chart_name] = chart;
}


function api_conf_edit(chart_name) {
    var chart = g_charts[chart_name];
    var headers = {};
    var params = {};
    var site_name = '';
    params['site_select'] = site_name;
    params['chart_name'] = chart_name;
    var url = getBaseUrl() + '/api/conf_edit';

    $.get(url, params, function (data, status) {
        var site_name = data['site_select'];
        var dashboard_name = data['dashboard_name'];
        var chart_name = data['chart_name'];
        //var conf_edit = JSON.parse(data['conf_edit']);
        var conf_edit = data['conf_edit'];
        draw_conf(chart_name, conf_edit);
    });

    //params['csrfmiddlewaretoken'] = csrftoken;
    //params['chart'] = chart;
    //$.post(url, params, function (data, status) {
    //var storyboard = JSON.parse(data['storyboard']);
    //var dashboard_name = data['dashboard_name'];
    //var chart_name = data['chart_name'];
    //var conf_edit = JSON.parse(data['conf_edit']);
    //draw_conf(chart_name, charts, conf_edit);
    //});
}

function add_table_row(tbody, cells) {
    var tr = document.createElement("tr");
    tbody.appendChild(tr)
    for (var ix = 0; ix < cells.length; ix++) {
        var cell = cells[ix];
        var td = document.createElement("td");
        tr.appendChild(td)
        var txt = document.createTextNode(cell);
        td.appendChild(txt)
    }
}

function onclick_configure(chart_name) {
    var chart = g_charts[chart_name];
    var conf_div = document.getElementById('configuration_editor_div');
    var conf_card_div = document.getElementById('conf_card_div');
    var label = conf_card_div.getElementsByTagName("label")[0]
    if (conf_div.classList.contains("collapse")) {
        conf_div.classList.remove("collapse");
        label.innerHTML = chart_name;
        var facet_value = document.getElementById("tile_value_select").value;
        draw_dashboard(g_storyboard[g_storyboard_ix], g_charts, facet_value, g_tiles_select)
    } else {
        if (label.innerHTML == chart_name) {
            conf_div.classList.add("collapse");
            label.innerHTML = ""
            return;
        } else {
            label.innerHTML = chart_name;
        }
    }
    api_conf_edit(chart_name);
    // the display inline style attribute doesnot work, use collapse instead
    //if (conf_div.style.display == "none") {
    //    conf_div.style.dispaly = "initial";
    //} else {
    //    conf_div.style.dispaly = "none";
    //}
}


function onclick_learning(chart_name) {
    alert(chart_name + ": Learning WIP");
}

// The download function takes a CSV string, the filename and mimeType as parameters
// Scroll/look down at the bottom of this snippet to see how download is called
var download = function (content, fileName, mimeType) {
    var a = document.createElement('a');
    mimeType = mimeType || 'application/octet-stream';

    if (navigator.msSaveBlob) { // IE10
        navigator.msSaveBlob(new Blob([content], {
            type: mimeType
        }), fileName);
    } else if (URL && 'download' in a) { //html5 A[download]
        a.href = URL.createObjectURL(new Blob([content], {
            type: mimeType
        }));
        a.setAttribute('download', fileName);
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    } else {
        location.href = 'data:application/octet-stream,' + encodeURIComponent(content); // only this mime type is supported
    }
}

function onclick_download(chart_name) {
    var chart_data = g_tiles_d[chart_name]['All']['chart_data'];
    // Building the CSV from the Data two-dimensional array
    // Each column is separated by ";" and new line "\n" for next row
    var csvContent = '';
    chart_data.forEach(function (infoArray, index) {
        var dataString = infoArray.join(';');
        csvContent += index < chart_data.length ? dataString + '\n' : dataString;
    });

    download(csvContent, chart_name+'.csv', 'text/csv;encoding:utf-8');
}

function onclick_print(chart_name) {
    //var chart_div = document.getElementById(chart_name + '_chdiv');
    var chart_div = document.getElementById('dashboard_images_div');
    var chart_image_name = chart_name + '_image';
    var chart_image_elm = document.getElementsByName(chart_image_name);
    if (chart_image_elm.length > 0) {
        chart_div.innerHTML = '';
        //alert('Card ' + chart_name + " removed.");
    } else {
        var google_db = g_charts[chart_name].google_db;
        var chart_wrapper = g_charts[chart_name].chart_wrapper;
        if (typeof chart_wrapper != 'undefined') {
            var chart = chart_wrapper.getChart();
            chart_div.innerHTML = '<img src="' + chart.getImageURI() + '" name="' + chart_image_name + '" style="border-width=5px">';
            //alert('Card ' + chart_name + " printed.");
        } else {
            alert('Card ' + chart_name + " can not be printed (d3 chart).");
        }
    }
}
