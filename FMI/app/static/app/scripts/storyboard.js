// script.js

'use strict';

// JQuery
var g_baseurl;
var g_charts;                       // populated by api_storyboard_def_callback and draw_storyboard
var g_minicharts;
var g_tiles_d;
var g_tiles_select;
var g_options;
var g_storyboard_def_changed = false
var g_storyboards;                  // populated by api_storyboard_def_callback
var g_storyboard;
var g_storyboard_ix;
var g_storyboard_tab_activated;
var g_stats_df;

function benchmark_select_onchange() {
    var benchmark_value = document.getElementById("benchmark_select").value;
    var input = document.getElementsByName("benchmark")[0];
    input.value = benchmark_value;
    //var form_elm = document.getElementById("guide_form");
    //if (form_elm == null) {
    //    var form_elm = document.getElementById("seeker_form");
    //}
    //form_elm.submit();
    var storyboard_ix = document.getElementById("dashboard_select").value;
    var dashboard_name = g_storyboard[storyboard_ix]['name'];
    var dashboard_data = g_storyboard[storyboard_ix]['dashboard_data'];
    // reset the dashboard data to pull since the benchmark has changed
    for (var ix=0; ix<g_storyboard.length; ix++) {
        g_storyboard[storyboard_ix]['dashboard_data'] = 'pull';
    }
    get_dashboard(dashboard_name)
    g_storyboard[storyboard_ix]['dashboard_data'] = 'push';
}

function tile_facet_select_onchange() {
    var facet_field = document.getElementById("tile_facet_select").value;
    var input = document.getElementsByName("tile_facet_field")[0];
    input.value = facet_field;
    //var form_elm = document.getElementById("guide_form");
    //if (form_elm == null) {
    //    var form_elm = document.getElementById("seeker_form");
    //}
    //form_elm.submit();
    var storyboard_ix = document.getElementById("dashboard_select").value;
    var dashboard_name = g_storyboard[storyboard_ix]['name'];
    var dashboard_data = g_storyboard[storyboard_ix]['dashboard_data'];
    // reset the dashboard data to pull since the tile facet changed
    for (var ix = 0; ix < g_storyboard.length; ix++) {
        g_storyboard[storyboard_ix]['dashboard_data'] = 'pull';
    }
    get_dashboard(dashboard_name)
    g_storyboard[storyboard_ix]['dashboard_data'] = 'push';
}

function tile_value_select_onchange() {
    var facet_value = document.getElementById("tile_value_select").value;
    var input = document.getElementsByName("tile_facet_value")[0];
    input.value = facet_value;
    //var params = {
    //    "db_facet_selecion": facet_value
    //};
    // get the form fields and add them as parameters to the GET. The submit will fire off its own GET request
    // document.getElementById("seeker_form").submit();
    // $.get("/search_survey", params, function (data, status) {
    //    var i = 2;
    // });

    for (var grid_name in g_storyboard[g_storyboard_ix].layout) {
        var layout = g_storyboard[g_storyboard_ix].layout[grid_name];
        for (var rownr = 0; rownr < layout.length; rownr++) {
            var row = layout[rownr];
            for (var chartnr = 0; chartnr < row.length; chartnr++) {
                var chart_name = layout[rownr][chartnr];
                if (!g_charts.hasOwnProperty(chart_name)) continue;
                var chart = g_charts[chart_name];
                var X_facet = chart['X_facet']
                var tiles = 'dropdown';
                if ('Z_facet' in chart) {
                    tiles = chart['Z_facet']['tiles'];
                }
                if (tiles != 'dropdown') {
                    continue;
                }
                var div_card_header = document.getElementById(chart_name + "_title");
                div_card_header.innerHTML = "<b>" + chart['chart_title'] + "</b>";
                if (g_tiles_d[chart_name][facet_value] != null) {
                    var chart_data = g_tiles_d[chart_name][facet_value]['chart_data'];
                    if (facet_value != 'All') {
                        div_card_header.innerHTML = div_card_header.innerHTML +
                            " / <font color='red'>" + facet_value + "</font>";
                    }
                } else {
                    var chart_data = g_tiles_d[chart_name]['All']['chart_data'];
                }
                if ("type" in X_facet) {
                    if (X_facet['type'] == 'date') {
                        for (var rix = 1; rix < chart_data.length; rix++) {
                            var s = chart_data[rix][0];
                            if (typeof s === 'string') {
                                var d = new Date(s);
                                chart_data[rix][0] = d
                            }
                        }
                    }
                }
                if (chart_data.length == 0) continue;
                if (chart['chart_type'] == 'RadarChart') {
                    d3_chart(chart_name, chart, facet_value, [1, 2, 3]);
                } else {
                    var dt = google.visualization.arrayToDataTable(chart_data, false);
                    var view = new google.visualization.DataView(dt);
                    g_charts[chart_name].datatable = dt;
                    g_charts[chart_name].view = view;
                    // only redraw for the active storyboard, read the dashboard from the web page instead form g_charts
                    if (typeof g_charts[chart_name].google_db != 'undefined') {
                        g_charts[chart_name].google_db.draw(dt, g_options);
                    }
                }
            }
        }
    }
}


function fill_tiles(facets_data, tiles_select, tiles_d) {
    g_tiles_select = tiles_select;
    if (typeof g_tiles_d == 'undefined') {
        g_tiles_d = tiles_d;
    } else {
        g_tiles_d = Object.assign(g_tiles_d, tiles_d)
    }

    var selectList = document.getElementById("benchmark_select");
    selectList.innerHTML = "";
    selectList.setAttribute("onChange", "benchmark_select_onchange()");
    var option = document.createElement("option");
    option.setAttribute("value", "All");
    option.text = "All";
    selectList.appendChild(option);
    for (var facet_field in facets_data) {
        var facet_data = facets_data[facet_field];
        if (!facet_data.facet_data) {
            continue;
        }
        var optgroup = document.createElement("optgroup");
        optgroup.setAttribute('value', facet_field);
        optgroup.setAttribute("label", facet_data['label']);
        selectList.appendChild(optgroup);
        var values = facet_data['values']
        for (var vi = 0; vi < values.length; vi++) {
            var facet_value = values[vi];
            var option = document.createElement("option");
            option.setAttribute("value", facet_value);
            if (facet_data['benchmark'] == facet_value) {
                option.setAttribute('selected', true);
            }
            option.text = facet_value;
            optgroup.appendChild(option);
        }
    }

    var selectList = document.getElementById("tile_facet_select");
    selectList.innerHTML = "";
    selectList.setAttribute("onChange", "tile_facet_select_onchange()");
    var option = document.createElement("option");
    option.setAttribute("value", "All");
    option.text = "All";
    selectList.appendChild(option);
    for (var facet_field in facets_data) {
        var facet_data = facets_data[facet_field];
        if (!facet_data.facet_data) {
            continue;
        }
        var option = document.createElement("option");
        option.setAttribute('value', facet_field);
        if (facet_data['selected'] == true) {
            option.setAttribute('selected', true);
        }
        option.text = facet_data['label'];
        selectList.appendChild(option);
    }

    var selectList = document.getElementById("tile_value_select");
    selectList.innerHTML = "";
    selectList.setAttribute("onChange", "tile_value_select_onchange()");
    // "All" provided by tiles_select
    //var option = document.createElement("option");
    //option.setAttribute("value", "All");
    //option.text = "All";
    //selectList.appendChild(option);
    for (var facet_tile in tiles_select) {
        var optgroup = document.createElement("optgroup");
        optgroup.setAttribute("label", facet_tile);
        optgroup.text = facet_tile;
        selectList.appendChild(optgroup);
        for (var fi = 0; fi < tiles_select[facet_tile].length; fi++) {
            var facet_value = tiles_select[facet_tile][fi];
            var option = document.createElement("option");
            option.setAttribute("value", facet_value);
            option.text = facet_value;
            selectList.appendChild(option);
        }
    }
}

function card_header(elm, chart_name) {
    var a_elm = document.createElement("a");
    a_elm.setAttribute("href", "#");
    a_elm.setAttribute("onclick", "onclick_configure('" + chart_name + "')");
    a_elm.setAttribute("class", "pull-right");
    a_elm.setAttribute("data-toggle", "tooltip");
    a_elm.setAttribute("title", "Configure");
    a_elm.innerHTML = '&nbsp <span class="glyphicon glyphicon-cog"></span> &nbsp'
    elm.appendChild(a_elm);

    var a_elm = document.createElement("a");
    a_elm.setAttribute("href", "#");
    a_elm.setAttribute("onclick", "onclick_learning('" + chart_name + "')");
    a_elm.setAttribute("class", "pull-right");
    a_elm.setAttribute("data-toggle", "tooltip");
    a_elm.setAttribute("title", "Learning");
    a_elm.innerHTML = '&nbsp <span class="glyphicon glyphicon-education"></span> &nbsp'
    elm.appendChild(a_elm);

    var a_elm = document.createElement("a");
    a_elm.setAttribute("href", "#");
    a_elm.setAttribute("onclick", "onclick_print('" + chart_name + "')");
    a_elm.setAttribute("class", "pull-right");
    a_elm.setAttribute("data-toggle", "tooltip");
    a_elm.setAttribute("title", "Print");
    a_elm.innerHTML = '&nbsp <span class="glyphicon glyphicon-print"></span> &nbsp'
    elm.appendChild(a_elm);

    var a_elm = document.createElement("a");
    a_elm.setAttribute("href", "#");
    a_elm.setAttribute("onclick", "onclick_download('" + chart_name + "')");
    a_elm.setAttribute("class", "pull-right");
    a_elm.setAttribute("data-toggle", "tooltip");
    a_elm.setAttribute("title", "Download");
    a_elm.innerHTML = '&nbsp <span class="glyphicon glyphicon-save"></span> &nbsp'
    elm.appendChild(a_elm);
}

function draw_dashboard_layout(chart_name, chart, facet_value) {
    var tiles = 'dropdown';
    if ('Z_facet' in chart) {
        tiles = chart['Z_facet']['tiles'];
    }
    if (tiles == 'dropdown') {
        var div_name = chart_name
    } else {
        var div_name = chart_name + "_" + facet_value.split(' ').join('');
    }

    var div_card = document.createElement("div");
    var div_card = document.createElement("div");
    div_card.setAttribute("class", "iff-card-6");
    var div_card_header = document.createElement("div");
    div_card_header.setAttribute("class", "iff-card-header");
    div_card_header.setAttribute("id", div_name + "_title");
    div_card.appendChild(div_card_header);
    div_card_header.innerHTML = "<b>" + chart['chart_title'] + "</b>";
    if (facet_value != 'All' && tiles != 'minichart') {
        div_card_header.innerHTML = div_card_header.innerHTML +
            " / <font color='red'>" + facet_value + "</font>";
    }
    card_header(div_card_header, chart_name);
    var div_card_body = document.createElement("div");
    div_card_body.setAttribute("class", "iff-card-body");
    div_card.appendChild(div_card_body);

    var div_db = document.createElement("div");
    div_db.setAttribute("id", div_name + "_dbdiv");
    //div_db.setAttribute("style", "width: 100%; height: 100%");
    div_db.setAttribute("style", "width: 100%;");
    div_card_body.appendChild(div_db);
    var div_cont_db = document.createElement("div");
    div_cont_db.setAttribute("class", "container-fluid");
    div_db.appendChild(div_cont_db);
    if ('help' in chart) {
        //var help_txt = document.createTextNode(chart['help']);
        var div_row_db = document.createElement("div");
        div_row_db.setAttribute("class", "row");
        div_cont_db.appendChild(div_row_db);
        var div_col_db = document.createElement("div");
        div_col_db.setAttribute("class", "col-md-12");
        div_row_db.appendChild(div_col_db);
        var help_txt = document.createElement("b");
        help_txt.innerHTML = chart['help'];
        div_col_db.appendChild(help_txt);
    }
    var nrcontrols = 1
    if ('controls' in chart) {
        nrcontrols = chart['controls'].length;
    }
    var div_row_db = document.createElement("div");
    div_row_db.setAttribute("class", "row");
    div_cont_db.appendChild(div_row_db);
    var c_width = 12 / nrcontrols;
    for (var controlnr = 0; controlnr < nrcontrols; controlnr++) {
        var div_col_db = document.createElement("div");
        div_col_db.setAttribute("class", "col-md-" + c_width);
        div_row_db.appendChild(div_col_db);
        var div_ct = document.createElement("div");
        var control_div_name = div_name + "_ct" + (controlnr + 1) + "div";
        div_ct.setAttribute("id", control_div_name);
        div_col_db.appendChild(div_ct);
    }
    var div_row_db = document.createElement("div");
    div_row_db.setAttribute("class", "row");
    div_cont_db.appendChild(div_row_db);
    var div_col_db = document.createElement("div");
    div_col_db.setAttribute("class", "col-md-12");
    div_row_db.appendChild(div_col_db);
    var div_ch = document.createElement("div");
    div_ch.setAttribute("id", div_name + "_chdiv");
    div_col_db.appendChild(div_ch);

    return div_card;
}

function draw_dashboard(dashboard, charts, facet_value, tiles_select) {
    //var dashboard_div = document.getElementById("dashboard_div");
    var dashboard_div = document.getElementById("dashboard_div");
    dashboard_div.innerHTML = "";
    for (var chart_name in charts) {
        var db_chart = charts[chart_name];
        delete db_chart.google_db;
    }

    for (var grid_name in dashboard.layout) {
        var layout = dashboard.layout[grid_name];
        for (var rownr = 0; rownr < layout.length; rownr++) {
            var row = layout[rownr];
            var div_row = document.createElement("div");
            div_row.setAttribute("class", "row iff-margin-t15");
            dashboard_div.appendChild(div_row);
            var l_width = 12 / row.length;
            for (var chartnr = 0; chartnr < row.length; chartnr++) {
                var chart_name = layout[rownr][chartnr];
                var chart = charts[chart_name];
                var div_col = document.createElement("div");
                div_col.setAttribute("class", "col-md-" + l_width);
                div_row.appendChild(div_col);
                var tiles = 'dropdown';
                if ('Z_facet' in chart) {
                    tiles = chart['Z_facet']['tiles'];
                }
                if (tiles == 'dropdown') {
                    var div_card = draw_dashboard_layout(chart_name, chart, facet_value)
                    div_col.appendChild(div_card);
                } else {
                    var re = /(grid)(-?)([A-Za-z1-9]?)(x?)([1-9]?)/
                    var ar = re.exec(tiles);
                    var nrrow = (ar[3] == '') ? 1 : parseInt(ar[3]);
                    var nrcol = (ar[5] == '') ? 1 : parseInt(ar[5]);
                    var nrtiles = 0;
                    for (var facet_tile in tiles_select) {
                        nrtiles = nrtiles + tiles_select[facet_tile].length;
                    }
                    nrrow = (nrtiles % nrcol == 0) ? nrtiles / nrcol : parseInt(nrtiles / nrcol) + 1
                    var l_width = 12 / nrcol;
                    var colnr = 0;
                    for (var facet_tile in tiles_select) {
                        for (var fi = 0; fi < tiles_select[facet_tile].length; fi++) {
                            var facet_value = tiles_select[facet_tile][fi];
                            facet_value = facet_value.split(' ').join('');
                            if (colnr == 0) {
                                var div_row_facet = document.createElement("div");
                                div_row_facet.setAttribute("class", "row");
                                div_col.appendChild(div_row_facet);
                            }
                            var div_col_facet = document.createElement("div");
                            div_col_facet.setAttribute("class", "col-md-" + l_width);
                            div_row_facet.appendChild(div_col_facet);
                            var div_card = draw_dashboard_layout(chart_name, chart, facet_value)
                            div_col_facet.appendChild(div_card);
                            colnr = colnr + 1;
                            if (colnr == nrcol) {
                                colnr = 0
                            }
                        }
                    }
                }
            }
        }
    }

    for (var grid_name in dashboard.layout) {
        var layout = dashboard.layout[grid_name];
        for (var rownr = 0; rownr < layout.length; rownr++) {
            var row = layout[rownr];
            for (var chartnr = 0; chartnr < row.length; chartnr++) {
                var chart_name = layout[rownr][chartnr];
                if (!charts.hasOwnProperty(chart_name)) continue;
                var chart = charts[chart_name];
                var div_card_header = document.getElementById(chart_name + "_title");
                if (g_tiles_d[chart_name][facet_value] != null) {
                    var chart_data = g_tiles_d[chart_name][facet_value]['chart_data'];
                } else {
                    var chart_data = g_tiles_d[chart_name]['All']['chart_data'];
                }
                if (chart_data.length == 0) continue;
                var tiles = 'dropdown';
                if ('Z_facet' in chart) {
                    tiles = chart['Z_facet']['tiles'];
                }
                if (tiles == 'dropdown') {
                    if (['RadarChart', 'WordCloudChart'].indexOf(chart['chart_type']) >= 0) {
                        d3_chart(chart_name, chart, facet_value, [1, 2, 3]);
                    } else {
                        google_chart(chart_name, chart, facet_value);
                    }
                } else {
                    for (var facet_tile in tiles_select) {
                        for (var fi = 0; fi < tiles_select[facet_tile].length; fi++) {
                            var facet_value = tiles_select[facet_tile][fi];
                            if (['RadarChart', 'WordCloudChart'].indexOf(chart['chart_type'])>=0) {
                                d3_chart(chart_name, chart, facet_value, [1, 2, 3]);
                            } else {
                                google_chart(chart_name, chart, facet_value);
                            }
                        }
                    }
                }
            }
        }
    }
}


function dashboard_definition(storyboard_ix) {
    g_storyboard_ix = storyboard_ix;
    var table = document.getElementById("db_layout_table");
    if (table != null) {
        // $("#db_layout_div").append($('<table>')).append($('<tr>')).append($('<td Grid>'));
        //var nrrow = table.rows.length;
        //for (var rownr = 0; rownr<nrrow; rownr++) {
        //   table.deleteRow(0);
        //}
        var tb = table.querySelectorAll('tbody');
        for (var i = 0; i < tb.length; i++) {
            tb[i].parentNode.removeChild(tb[i]);
        }
        var th = table.querySelectorAll('thead');
        for (var i = 0; i < th.length; i++) {
            th[i].parentNode.removeChild(th[i]);
        }
        for (var grid_name in g_storyboard[storyboard_ix].layout) {
            var thead = document.createElement("thead");
            table.appendChild(thead)
            var td = document.createElement("td");
            td.colSpan = "2";
            thead.appendChild(td)
            var txt = document.createTextNode(grid_name);
            td.appendChild(txt)
            var tbody = document.createElement("tbody");
            table.appendChild(tbody)
            var layout = g_storyboard[storyboard_ix].layout[grid_name];
            for (var rownr = 0; rownr < layout.length; rownr++) {
                var row = layout[rownr];
                var tr = document.createElement("tr");
                tbody.appendChild(tr)
                for (var chartnr = 0; chartnr < row.length; chartnr++) {
                    var chart_name = layout[rownr][chartnr];
                    //$("#db_layout_div").append($('<tr>')).append($('<td Grid>'));
                    var td = document.createElement("td");
                    tr.appendChild(td)
                    var txt = document.createTextNode(chart_name);
                    td.appendChild(txt)
                }
            }
        }
    }
}

function dashboard_onchange() {
    var storyboard_ix = document.getElementById("dashboard_select").value;
    var input = document.getElementsByName("dashboard_name")[0];
    var dashboard_name = g_storyboard[storyboard_ix]['name'];
    var dashboard_data = g_storyboard[storyboard_ix]['dashboard_data'];
    input.value = dashboard_name;
    var facet_value = document.getElementById("tile_value_select").value;

   // check whether the data is already retrieved, it not raise the request
    if (dashboard_data == 'push') {
        dashboard_definition(storyboard_ix)
        draw_dashboard(g_storyboard[storyboard_ix], g_charts, facet_value, g_tiles_select)
    }
    if (dashboard_data == 'pull') {
        get_dashboard(dashboard_name)
        g_storyboard[storyboard_ix]['dashboard_data'] = 'push';
    }
}


function chart_selection_onchange() {
    var chart_name = document.getElementById("chart_selecion_select").value;
    var table = document.getElementById("chart_definition_table");
    table.innerHTML = "";
    var thead = document.createElement("thead");
    table.appendChild(thead)
    var td = document.createElement("td");
    td.colSpan = "2";
    thead.appendChild(td)
    var txt = document.createTextNode(chart_name);
    td.appendChild(txt)
    var tbody = document.createElement("tbody");
    table.appendChild(tbody)
    var chart = g_charts[chart_name];
    add_table_row(tbody, ['Title', chart.chart_title]);
    add_table_row(tbody, ['Type', chart.chart_type]);
    add_table_row(tbody, ['X', chart.X_facet.field]);
    if ('Y_facet' in chart) {
        add_table_row(tbody, ['Y', chart.Y_facet.field]);
    }
}

function draw_storyboard(storyboard, dashboard_name, charts, tiles_select) {
    if (typeof g_charts == 'undefined') {
        g_charts = charts;
    } else {
        g_charts = Object.assign(g_charts, charts);
    }
    if (typeof g_storyboard == 'undefined') {
        g_storyboard = storyboard;
    } else {
        g_storyboard = Object.assign(g_storyboard, storyboard);
    }

    var select = document.getElementById("dashboard_select");
    if (select != null) {
        select.setAttribute("onChange", "dashboard_onchange()");
        // remove any existing options
        select.options.length = 0;
        var active_nr;
        for (var ix = 0; ix < storyboard.length; ix++) {
            var option = document.createElement("option");
            option.setAttribute("value", ix);
            option.text = storyboard[ix].name;
            if (storyboard[ix].active == true || storyboard[ix].name == dashboard_name) {
                option.setAttribute('selected', true);
                active_nr = ix;
            }
            select.appendChild(option);
        }
    }
    var chart_selection_div = document.getElementById("chart_selection_div");
    if (chart_selection_div != null) {
        var select = document.createElement("select");
        select.setAttribute("id", "chart_selecion_select");
        select.setAttribute("onChange", "chart_selection_onchange()");
        chart_selection_div.appendChild(select);
        // remove any existing options
        select.options.length = 0;
        for (var chart_name in charts) {
            var option = document.createElement("option");
            option.setAttribute("value", chart_name);
            option.text = chart_name;
            select.appendChild(option);
        }
    }
    //chart_definitions(charts);
    dashboard_definition(active_nr);
    draw_dashboard(g_storyboard[active_nr], g_charts, "All", tiles_select)
}

function set_hidden_param(param_name, param_value) {
    var input = document.getElementsByName(param_name)[0];
    input.value = param_value;
}

function getParameterByName(name, url) {
    if (!url) {
        url = window.location.href;
    }
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

function get_workbook_dashboard_names() {
    var input = document.getElementsByName("workbook_name")[0];
    var workbook_name = getParameterByName("workbook_name");
    input.value = workbook_name;
    var input = document.getElementsByName("storyboard_name")[0];
    var storyboard_name = getParameterByName("storyboard_name");
    input.value = storyboard_name;
    var input = document.getElementsByName("dashboard_name")[0];
    var dashboard_name = getParameterByName("dashboard_name");
    input.value = dashboard_name;
}

function disable_selects_storyboard(disabled) {
    var select_elm = document.getElementById("dashboard_select");
    select_elm.disabled = disabled;
    var select_elm = document.getElementById("benchmark_select");
    select_elm.disabled = disabled;
    var select_elm = document.getElementById("tile_facet_select");
    select_elm.disabled = disabled;
    var select_elm = document.getElementById("tile_value_select");
    select_elm.disabled = disabled;
}

function fill_params_dashboard(dashboard_name) {
    var params = {};
    var input = document.getElementsByName("workbook_name")[0];
    var workbook_name = input.value;
    params['workbook_name'] = workbook_name;
    var input = document.getElementsByName("storyboard_name")[0];
    var storyboard_name = input.value;
    params['storyboard_name'] = storyboard_name;
    params['dashboard_name'] = dashboard_name;
    var input = document.getElementsByName("benchmark")[0];
    var benchmark = input.value;
    params['benchmark'] = benchmark;
    var input = document.getElementsByName("tile_facet_field")[0];
    var tile_facet_field = input.value;
    params['tile_facet_field'] = tile_facet_field;
    var input = document.getElementsByName("tile_facet_value")[0];
    var tile_facet_value = input.value;
    params['tile_facet_value'] = tile_facet_value;

    if (typeof g_facets_data != 'undefined') { // when called first time from guide.html
        for (var facet_field in g_facets_data) {
            var facet_field_filters = getParameterByName(facet_field);
            if (facet_field_filters != '' && facet_field_filters != null) {
                params[facet_field] = facet_field_filters;
            }
        }
    }

    return params;
}

function get_dashboard_callback(data, status) {
    var view_name = data['view_name'];
    var dashboard_name = data['dashboard_name'];
    var storyboard = JSON.parse(data['storyboard']);
    var charts = JSON.parse(data['dashboard']);
    var facets_data = JSON.parse(data['facets_data']);
    var tiles_select = JSON.parse(data['tiles_select']);
    var tiles_d = JSON.parse(data['tiles_d']);
    //var stats_df = JSON.parse(data['stats_df']);
    //g_storyboard[storyboard_ix]['dashboard_data'] = 'push';
    disable_selects_storyboard(false);
    fill_tiles(facets_data, tiles_select, tiles_d);
    draw_storyboard(storyboard, dashboard_name, charts, tiles_select);
}

function get_dashboard(dashboard_name) {
    disable_selects_storyboard(true);
    var params = fill_params_dashboard(dashboard_name);
    //var view_name = getParameterByName("view_name");
    var input = document.getElementsByName("view_name")[0];
    if (typeof input != 'undefined') {
        var view_name = input.value;
    }
    var seeker_url = '/search_survey?';
    if (view_name != null && view_name != "") {
        var site_view = g_site_views[view_name];
        seeker_url = site_view['url'];
    }
    if (typeof g_baseurl == 'undefined') {
        var loc = window.location;
        var url = window.location.href;
        //strip of the last part of the URL so it can be replaced by the destination url
        var to = url.lastIndexOf('/');
        var from = url.indexOf('/');
        to = to == -1 ? url.length : to;
        var pathArray = window.location.pathname.split('/');
        var n = pathArray.length - 1;
        if (pathArray[n].length == 0) { n = n - 1 } // sometimes there is a last / in the url
        var url_name = pathArray[n].substring(0, 6);
        if (url_name == 'search') {
            url = loc.protocol + "//" + loc.host + pathArray.join('/') + "?"
        } else {
            url = url.substring(0, to) + seeker_url;
        }
    } else {
        var url = g_baseurl + seeker_url;
    }

    //$.get(url, params, get_dashboard_callback);
    $.ajax({
        url: url,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
        method: 'GET',
        data: params,
        success: get_dashboard_callback
    });

    //params['csrfmiddlewaretoken'] = csrftoken;
    //$.post(url, params, function (data, status) {
    //    var view_name = data['view_name'];
    //    var dashboard_name = data['dashboard_name'];
    //    var site_view = g_site_views[view_name];
    //    //var storyboard = site_view['storyboard'];
    //    var storyboard = JSON.parse(data['storyboard']);
    //    var charts = JSON.parse(data['dashboard']);
    //    var facets_data = JSON.parse(data['facets_data']);
    //    var tiles_select = JSON.parse(data['tiles_select']);
    //    var tiles_d = JSON.parse(data['tiles_d']);
    //    //var stats_df = JSON.parse(data['stats_df']);
    //    fill_tiles(facets_data, tiles_select, tiles_d);
    //    draw_storyboard(storyboard, dashboard_name, charts, tiles_select);
    //});
}

