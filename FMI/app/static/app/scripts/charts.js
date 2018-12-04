// script.js

'use strict';

function getBaseUrl() {
    if (typeof insight_api != 'undefined') {
        if (insight_api != '') {
            return insight_api;
        }
    }
    var url = window.location.href;
    //strip of the last part of the URL so it can be replaced by the destination url
    var to = url.lastIndexOf('/');
    to = to == -1 ? url.length : to;
    url = url.substring(0, to);
    return url;
}

function chart_tile_layout_select_onchange(chart_name, containerId) {
    var selectList = document.getElementById(containerId);
    var layout_value = selectList.getElementsByTagName("select")[0].value;
    var facet_value = document.getElementById("tile_value_select").value;
    
    var old_tiles = g_charts[chart_name]['Z_facet']['tiles'];
    var new_tiles = layout_value;
    if (new_tiles.substr(0,4) == 'grid') {
        g_charts[chart_name]['Z_facet']['tiles'] = new_tiles;
        draw_dashboard(g_storyboard[g_storyboard_ix], g_charts, facet_value, g_tiles_select);
    } else if (old_tiles.substr(0, 4) == 'grid') {
        g_charts[chart_name]['Z_facet']['tiles'] = 'dropdown';
        draw_dashboard(g_storyboard[g_storyboard_ix], g_charts, facet_value, g_tiles_select);
    } else {
        g_charts[chart_name]['Z_facet']['tiles'] = new_tiles;
        facet_value = layout_value;
        var chart = g_charts[chart_name];
        var X_facet = chart['X_facet']

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
        if (chart_data.length > 0) {
            if (chart['chart_type'] in  ['RadarChart', 'WordCloudChart']) {
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


//<div class="google-visualization-controls-categoryfilter">
//	<label class="google-visualization-controls-label">Hedonics_</label>
//	<div>
//	<span class="goog-combobox goog-inline-block">
//	<input name="" type="text" autocomplete="off" label="Choose a value..." placeholder="Choose a value..." aria-label="Choose a value..." class="label-input-label">
//	<span class="goog-combobox-button" style="user-select: none;">▼</span>
//	<div class="goog-menu goog-menu-vertical" role="menu" aria-haspopup="true" style="user-select: none; left: 0px; top: 17px; display: none;">
//		<div class="goog-menuitem" role="menuitem" id=":0" style="user-select: none;">
//		<div class="goog-menuitem-content" style="user-select: none;"><b></b>0-Mean</div></div>
//		<div class="goog-menuitem" role="menuitem" id=":1" style="user-select: none;">
//		<div class="goog-menuitem-content" style="user-select: none;"><b></b>1-Excellent</div></div>
//		<div class="goog-menuitem" role="menuitem" id=":2" style="user-select: none;">
//		<div class="goog-menuitem-content" style="user-select: none;"><b></b>2-Top2</div></div>
//		<div class="goog-menuitem" role="menuitem" id=":3" style="user-select: none;">
//		<div class="goog-menuitem-content" style="user-select: none;"><b></b>3-Bottom2</div></div>
//	</div>
//	</span>
//	<ul class="google-visualization-controls-categoryfilter-selected goog-inline-block"></ul>
//	</div>
//</div>

function fill_tiles_chart(chart_name, chart_def, facet_value, containerId) {
    var selectList = document.getElementById(containerId);
    selectList.innerHTML =
        //"<div class='form-group'>" +
        //    "<label for='sel1'>Select Tile-Layout:</label>" +
        //    "<select name='tile_layout_select' class='form-control' id='tile_layout_select'></select>" +
        //"</div>";
        '<div class="google-visualization-controls-categoryfilter">' +
	        '<label class="google-visualization-controls-label">Tile-Layout</label>' +
	        '<div>' +
	            '<span class="goog-combobox goog-inline-block">' +
	            '<select name="" type="text" autocomplete="off" label="Choose facet..." placeholder="Choose facet..." aria-label="Choose facet..." class="label-input-label">' +
	            '<span class="goog-combobox-button" style="user-select: none;">▼</span>' +
	            '</span>' +
	        '</div>' +
	    '</div>';
    var selectList = selectList.getElementsByTagName('select')[0];
    selectList.setAttribute("onChange", "chart_tile_layout_select_onchange('" + chart_name + "','" + containerId + "')");
    var layout_select = new Object();
    layout_select = ['dropdown', 'grid-nx1', 'grid-nx2', 'grid-nx3', 'grid-nx4'];
    var tiles = 'dropdown';
    if ('Z_facet' in chart_def) {
        tiles = chart_def['Z_facet']['tiles'];
    } else {
        chart_def['Z_facet'] = { 'tiles': tiles };
    }
    for (var li = 0; li < layout_select.length; li++) {
        var layout = layout_select[li];
        var option = document.createElement("option");
        option.setAttribute("value", layout);
        if (layout == tiles) {
            option.setAttribute('selected', true);
        }
        option.text = layout;
        selectList.appendChild(option);
    }
}

// JQuery

function d3_chart(chart_name, chart_def, facet_value, colIndexes) {
    var chdivid = '#' + chart_name + '_chdiv'
    var ctdivsid = ['#' + chart_name + '_ct1div', '#' + chart_name + '_ct2div']
    var w = 500,
        h = 500;

    var colorscale = d3.scale.category10();

    //Legend titles
    //var LegendOptions = ['Smartphone', 'Tablet'];

    //Data
    //var d = [
    //          [
    //            { axis: "Email", value: 0.59 },
    //            { axis: "Social Networks", value: 0.56 },
    //            { axis: "Internet Banking", value: 0.42 },
    //            { axis: "News Sportsites", value: 0.34 },
    //            { axis: "Search Engine", value: 0.48 },
    //            { axis: "View Shopping sites", value: 0.14 },
    //            { axis: "Paying Online", value: 0.11 },
    //            { axis: "Buy Online", value: 0.05 },
    //            { axis: "Stream Music", value: 0.07 },
    //            { axis: "Online Gaming", value: 0.12 },
    //            { axis: "Navigation", value: 0.27 },
    //            { axis: "App connected to TV program", value: 0.03 },
    //            { axis: "Offline Gaming", value: 0.12 },
    //            { axis: "Photo Video", value: 0.4 },
    //            { axis: "Reading", value: 0.03 },
    //            { axis: "Listen Music", value: 0.22 },
    //            { axis: "Watch TV", value: 0.03 },
    //            { axis: "TV Movies Streaming", value: 0.03 },
    //            { axis: "Listen Radio", value: 0.07 },
    //            { axis: "Sending Money", value: 0.18 },
    //            { axis: "Other", value: 0.07 },
    //            { axis: "Use less Once week", value: 0.08 }
    //          ], [
    //            { axis: "Email", value: 0.48 },
    //            { axis: "Social Networks", value: 0.41 },
    //            { axis: "Internet Banking", value: 0.27 },
    //            { axis: "News Sportsites", value: 0.28 },
    //            { axis: "Search Engine", value: 0.46 },
    //            { axis: "View Shopping sites", value: 0.29 },
    //            { axis: "Paying Online", value: 0.11 },
    //            { axis: "Buy Online", value: 0.14 },
    //            { axis: "Stream Music", value: 0.05 },
    //            { axis: "Online Gaming", value: 0.19 },
    //            { axis: "Navigation", value: 0.14 },
    //            { axis: "App connected to TV program", value: 0.06 },
    //            { axis: "Offline Gaming", value: 0.24 },
    //            { axis: "Photo Video", value: 0.17 },
    //            { axis: "Reading", value: 0.15 },
    //            { axis: "Listen Music", value: 0.12 },
    //            { axis: "Watch TV", value: 0.1 },
    //            { axis: "TV Movies Streaming", value: 0.14 },
    //            { axis: "Listen Radio", value: 0.06 },
    //            { axis: "Sending Money", value: 0.16 },
    //            { axis: "Other", value: 0.07 },
    //            { axis: "Use less Once week", value: 0.17 }
    //          ]
    //];

    //Options for the Radar chart, other than default
    var chart_title = chart_def['chart_title'];
    if ('options' in chart_def) {
        var options = chart_def['options'];
        if ('width' in options) {
            w = options['width'];
        }
        if ('height' in options) {
            h = options['height'];
        }
    }
    var mycfg = {
        w: w,
        h: h,
        maxValue: 0.6,
        levels: 6,
        //ExtraWidthX: 300
    }

    //Call function to draw the Radar chart
    //Will expect that data is in %'s
    if (g_tiles_d[chart_name][facet_value]['chart_data'].length > 0) {
        var chart_data = g_tiles_d[chart_name][facet_value]['chart_data'];
    } else {
        var chart_data = new Array();
    }

    if (chart_def['chart_type'] == 'RadarChart') {
        RadarChart.draw(chdivid, chart_data, colIndexes, mycfg);
    } else if (chart_def['chart_type'] == 'WordCloudChart') {
        WordCloudChart.draw(chdivid, chart_data, colIndexes, mycfg);
    }


    ////////////////////////////////////////////
    /////////// Initiate legend ////////////////
    ////////////////////////////////////////////

    var data = [];
    var LegendOptions = [];
    for (var colnr = 1; colnr < chart_data[0].length; colnr++) {
        var series = [];
        for (var rownr = 1; rownr < chart_data.length; rownr++) {
            var axis = chart_data[rownr][0];
            var value = chart_data[rownr][colnr];
            series.push({ 'axis': axis, 'value': value });
        }
        if (colIndexes.indexOf(colnr) >= 0) {
            LegendOptions.push(chart_data[0][colnr]);
            data.push(series);
        }
    }

    var svg = d3.select(chdivid)
        .selectAll('svg')

    //Create the title for the legend
    var text = svg.append("text")
        .attr("class", "title")
        .attr("x", 10)
        .attr("y", 20)
        .attr("font-size", "12px")
        .attr("font-weight", "bold")
        .attr("fill", "#404040")
        .text(chart_title);

    //Initiate Legend	
    var legend = svg.append("g")
        .attr("class", "legend")
        //.attr("height", 100)
        //.attr("width", 200)
        .attr('transform', 'translate(175,20)')
    ;
    //Create colour squares
    legend.selectAll('rect')
	  .data(LegendOptions)
	  .enter()
	  .append("rect")
	  .attr("x", w - 65)
	  .attr("y", function (d, i) { return i * 20; })
	  .attr("width", 10)
	  .attr("height", 10)
	  .style("fill", function (d, i) { return colorscale(i); })
    ;
    //Create text next to squares
    legend.selectAll('text')
	  .data(LegendOptions)
	  .enter()
	  .append("text")
	  .attr("x", w - 52)
	  .attr("y", function (d, i) { return i * 20 + 9; })
	  .attr("font-size", "11px")
	  .attr("fill", "#737373")
	  .text(function (d) { return d; })
    ;
}

function filterD3Chart(chart_name, chart_name2) {
    var chart_def2 = g_charts[chart_name2];
    if (g_tiles_d[chart_name2]['All']['chart_data'].length > 0) {
        var chart_data2 = g_tiles_d[chart_name2]['All']['chart_data'];
    } else {
        var chart_data2 = new Array();
    }
    var colIndexes = [];
    for (var i = 0; i < g_charts[chart_name].filters.length; i++) {
        var filter = g_charts[chart_name].filters[i];
        for (var colnr = 1; colnr < chart_data2[0].length; colnr++) {
            if (chart_data2[0][colnr] == filter) {
                colIndexes.push(colnr);
            }
        }
    }
    if (colIndexes.length == 0) {
        colIndexes = [1, 2, 3];
    }
    d3_chart(chart_name2, chart_def2, 'All', colIndexes);
}


function getFilteredColumns(dt, filters) {
    var cols = [];
    for (var fix = 0; fix < filters.length; fix++) {
        var filter_row = filters[fix]['row'];
        var filter_value = filters[fix]['value'];
        for (var cix = 0; cix < dt.getNumberOfColumns() ; cix++) {
            var value = dt.getValue(filter_row, cix);
            var label = dt.getColumnLabel(cix);
            if (label == filter_value) {
                cols.push(cix);
                break;
            }
        }
    }
    return cols;
}

function sortColumns(dt, rownr, frozenColumns, sortAscending) {
    var sortcols = [];
    var cols = [];
    //g_charts[chart_name2].view.setColumns(0, nrcols - 1);
    // first two rows are fixed
    for (var cix = frozenColumns; cix < dt.getNumberOfColumns() ; cix++) {
        var value = dt.getValue(rownr, cix);
        var item = {};
        item['colvalue'] = value;
        item['colindex'] = cix;
        sortcols.push(item);
    }
    sortcols.sort(function (a, b) {
        if (sortAscending) {
            return a['colvalue'] - b['colvalue'];
        } else {
            return b['colvalue'] - a['colvalue'];
        }
    });
    for (var cix = 0; cix < frozenColumns; cix++) {
        cols.push(cix);
    }
    for (var cix = 0; cix < sortcols.length; cix++) {
        cols.push(sortcols[cix]['colindex']);
    }
    return cols;
}

function setFilters(chart_name, categorie) {
    var found = false;
    for (var i = 0; i < g_charts[chart_name].filters.length; i++) {
        var filter = g_charts[chart_name].filters[i];
        if (categorie == filter) {
            g_charts[chart_name].filters.splice(i, 1);
            found = true;
            break;
        }
    }
    if (!found) {
        g_charts[chart_name].filters.push(categorie);
    }
}

function setRowsChart(chart_name, chart_name2) {
    var dt2 = g_charts[chart_name2].datatable;
    var nrrows2 = dt2.getNumberOfRows();
    var nrcols2 = dt2.getNumberOfColumns();
    var setrows = [];
    var transpose = false;
    if ('transpose' in g_charts[chart_name2]) {
        transpose = g_charts[chart_name2]['transpose'];
    }
    if (g_charts[chart_name].filters.length > 0) {
        if (!transpose) {
            for (var i = 0; i < g_charts[chart_name].filters.length; i++) {
                var filter = g_charts[chart_name].filters[i];
                var rowIndexes = dt2.getFilteredRows([{ column: 0, value: filter }]);
                setrows = setrows.concat(rowIndexes);
            }
        } else {
            var filters = [];
            for (var i = 0; i < g_charts[chart_name].filters.length; i++) {
                var filter = g_charts[chart_name].filters[i];
                var rowIndexes = getFilteredColumns(dt2, [{ row: 0, value: filter }]);
                setrows = setrows.concat(rowIndexes);
            }
            // make sure the labels are one of the displayed columns
            setrows = [0].concat(setrows);
        }
    } else {
        if (!transpose) {
            for (var rownr = 0; rownr < nrrows2; rownr++) {
                setrows.push(rownr);
            }
        } else {
            for (var colnr = 0; rownr < nrcols2; colnr++) {
                setrows.push(colnr);
            }
        }
    }
    return setrows;
}

function filterGoogleChart(chart_name, chart_name2) {
    var dt2 = g_charts[chart_name2].datatable;
    var transpose = false;
    if ('transpose' in g_charts[chart_name2]) {
        transpose = g_charts[chart_name2]['transpose'];
    }
    var setrows = setRowsChart(chart_name, chart_name2);
    if (!transpose) {
        g_charts[chart_name2].view.setRows(setrows);
        //g_charts[chart_name2].chart_wrapper.draw();
    } else {
        //g_charts[chart_name2].chart_wrapper.setDataTable(g_charts[chart_name2].datatable);
        g_charts[chart_name2].view.setColumns(setrows);
        //g_charts[chart_name2].chart_wrapper.setView(g_charts[chart_name2].view.toJSON());
        //g_charts[chart_name2].chart_wrapper.draw();
        //for (var cix = 0; cix < g_charts[chart_name2].control_wrappers.length; cix++) {
        //    g_charts[chart_name2].google_db.bind(g_charts[chart_name2].control_wrappers[cix], g_charts[chart_name2].chart_wrapper);
        //}
        //g_charts[chart_name2].google_db.draw(g_charts[chart_name2].data);
    }
    g_charts[chart_name2].google_db.draw(g_charts[chart_name2].view);
}

function filterChart(chart_name, chart_name2) {
    var chdiv2 = chart_name2 + '_chdiv'
    // check whether chart2 is part of existing dashboard
    var chart_div2 = document.getElementById(chdiv2);
    if (chart_div2 != null) {
        if (['RadarChart', 'WordCloudChart'].indexOf(g_charts[chart_name2]['chart_type']) >= 0) {
            filterD3Chart(chart_name, chart_name2)
        } else {
            filterGoogleChart(chart_name, chart_name2)
        }
    }
}


function selectEventChart(chart_name, rowIndex, rowlabel, argument) {
    if (argument == 'country.keyword') {
        var field = argument;
        var select_elm = document.getElementsByName(field)[0];
        select_elm.options[rowIndex].selected = !select_elm.options[rowIndex].selected;
    } else {
        // in case of site menu, this site_view select routine is defined in guide.js
        var view_name = argument;
        country_select(view_name, rowlabel)
    }
}


function google_chart(chart_name, chart_def, facet_value) {
    google.charts.load('current', { 'packages': ['corechart', 'controls'] });
    var tiles = 'dropdown';
    if ('Z_facet' in chart_def) {
        tiles = chart_def['Z_facet']['tiles'];
    }
    if (tiles == 'dropdown') {
        var div_name = chart_name
    } else {
        var div_name = chart_name + "_" + facet_value.split(' ').join('')
    }
    var dbdiv = div_name + '_dbdiv'
    var chdiv = div_name + '_chdiv'
    var ctdivs = [div_name + '_ct1div', div_name + '_ct2div']
    google.charts.setOnLoadCallback(drawVisualization);

    function drawVisualization() {
        if (g_tiles_d[chart_name][facet_value] != null) {
            var chart_data = g_tiles_d[chart_name][facet_value]['chart_data'];
        } else {
            var chart_data = g_tiles_d[chart_name]['All']['chart_data'];
        }
        // in case the X value is a date is still requires converting to a Date
        var X_facet = chart_def['X_facet']
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
        var data = google.visualization.arrayToDataTable(chart_data);
        var view = new google.visualization.DataView(data);
        var chart_type = chart_def['chart_type'];
        var chart_title = chart_def['chart_title'];
        var x_total = true
        //var y_axis = 1 // secondary axis = 1
        if ("total" in X_facet) {
            x_total = X_facet['total']
        }
        var transpose = false
        //var y_axis = 1 // secondary axis = 1
        if ("transpose" in chart_def) {
            transpose = chart_def['transpose']
        }
        if ("Y_facet" in chart_def) {
            var Y_facet = chart_def['Y_facet']
            //if ("axis" in Y_facet) {
            //    y_axis = X_facet['axis']
            //}
        }

        // Series is moved to the Chart Defition
        //var series = {};
        //var axis = 0;
        //for (var colnr=0; colnr<data.getNumberOfColumns(); colnr++) {
        //    series[colnr] = { "targetAxisIndex": axis };
        //    axis = y_axis
        //}

        if (tiles == 'minichart') {
            var t1 = g_tiles_d[chart_name][facet_value].google_db;
        } else {
            var t1 = g_charts[chart_name].google_db;
        }
        if (typeof t1 === 'undefined' || true) {
            var controls = ['StringFilter'];
            if ('controls' in chart_def) {
                var controls = chart_def['controls'];
                if (controls == null) {
                    controls = [];
                }
            }
            var google_db = null;
            if (controls.length > 0) {
                var google_db = new google.visualization.Dashboard(dbdiv);
            }
            var options = {
                //'title': chart_title,
                // 'series': series,
                'allowHtml': true,
                'dataMode': 'regions',
                animation: {
                    duration: 1000,
                    easing: 'out',
                    startup: true,
                }
            };
            if ('options' in chart_def) {
                options = $.extend(options, chart_def['options']);
            }
            if ('formatter' in chart_def) {
                for (var prop in chart_def['formatter']) {
                    if (prop == 'NumberFormat') {
                        var cols = chart_def['formatter'][prop];
                        for (var colix in cols) {
                            var format = cols[colix];
                            var formatter = new google.visualization.NumberFormat(format);
                            colix = Number(colix);
                            formatter.format(data, colix);
                        }
                    }
                    if (prop == 'setColumnProperties') {
                        var cols = chart_def['formatter'][prop];
                        for (var colix in cols) {
                            var properties = cols[colix];
                            colix = Number(colix);
                            data.setColumnProperties(colix, properties)
                            var get_properties = data.getColumnProperties(colix);
                        }
                    }
                    if (prop == 'setProperty') {
                        var cells = chart_def['formatter'][prop];
                        for (var cellix=0; cellix<cells.length; cellix++) {
                            var cell = cells[cellix];
                            data.setProperty(cell[0], cell[1], cell[2], cell[3])
                            var get_properties = data.getProperty(cell[0], cell[1], cell[2]);
                        }
                    }
                }
            }
            var chart_wrapper = new google.visualization.ChartWrapper({
                chartType: chart_type,
                // dataTable: data,
                options : options,
                containerId: chdiv
            });

            chart_wrapper.setChartName(chart_name);
            var control_wrappers = [];

            for (var cix = 0; cix < controls.length; cix++) {
                var control = controls[cix];
                if (control == 'StringFilter') {
                    var control_wrapper = new google.visualization.ControlWrapper({
                        'controlType': 'StringFilter',
                        'containerId': ctdivs[cix],
                        'options': {
                            'filterColumnIndex': 0
                        }
                    });
                } else if (control == 'CategoryFilter') {
                    var label = X_facet['label'];
                    if (transpose) {
                        label = Y_facet['label'];
                    }
                    var control_wrapper = new google.visualization.ControlWrapper({
                        'controlType': 'CategoryFilter',
                        'containerId': ctdivs[cix],
                        'options': {
                            'filterColumnIndex': 0,
                            'ui': {
                                'labelStacking': 'vertical',
                                'label': label,
                                'allowTyping': true,
                                'allowMultiple': true
                            }
                        }
                    });
                } else if (control == 'NumberRangeFilter') {
                    //var label = data.getValue(0, 0);
                    var label = data.getColumnLabel(0);
                    var control_wrapper = new google.visualization.ControlWrapper({
                        'controlType': 'NumberRangeFilter',
                        'containerId': ctdivs[cix],
                        'options': {
                            'filterColumnIndex': 0,
                            //'minValue': 0.0,
                            //'maxValue': 10.0,
                            'ui': {
                                'orientation': 'horizontal',
                                'label': label,
                                //'unitIncrement': 0.1,
                                'blockIncrement' : 5,
                                //'step' : 0.1,
                                //'ticks': 10,
                                'showRangeValues': true,
                            }
                        }
                    });
                } else if (control == 'DateRangeFilter') {
                    //var label = data.getValue(0, 0);
                    var label = data.getColumnLabel(0);
                    var control_wrapper = new google.visualization.ControlWrapper({
                        'controlType': 'DateRangeFilter',
                        'containerId': ctdivs[cix],
                        'options': {
                            'filterColumnIndex': 0,
                            //'minValue': 0.0,
                            //'maxValue': 10.0,
                            'ui': {
                                'orientation': 'horizontal',
                                'label': label,
                                //'unitIncrement': 0.1,
                                //'blockIncrement' : 0.1,
                                //'step': 0.1,
                                'ticks': 10,
                                'showRangeValues': true,
                            }
                        }
                    });
                } else if (control == 'ChartRangeFilter') {
                    //var label = data.getValue(0, 0);
                    var label = data.getColumnLabel(0);
                    var date_end = new Date();
                    var date_begin = new Date(date_end.getFullYear()-1, 0, 1) 

                    var control_wrapper = new google.visualization.ControlWrapper({
                        'controlType': 'ChartRangeFilter',
                        'containerId': ctdivs[cix],
                        'options': {
                            'filterColumnIndex': 0,
                            //'minValue': 0.0,
                            //'maxValue': 10.0,
                            'ui': {
                                'orientation': 'horizontal',
                                'label': label,
                                //'unitIncrement': 0.1,
                                //'blockIncrement' : 0.1,
                                'showRangeValues': true,
                                chartOptions: {
                                    height: 50,
                                    hAxis: {
                                        format: 'yy/MMM'
                                    }
                                }
                            }
                        },
                        'state': {
                            'range': {
                                'start': date_begin,
                                'end': date_end
                            }
                        }
                    });
                    //document.getElementById(ctdivs[cix]).style.height = "50px";
                } else if (control == 'tile_layout_select') {
                    if (tiles == 'dropdown' || facet_value == 'All') {
                        fill_tiles_chart(chart_name, chart_def, facet_value, ctdivs[cix]);
                    }
                }
                control_wrappers.push(control_wrapper);
            }
            if ('listener' in chart_def) {
                var tempListener = google.visualization.events.addOneTimeListener(chart_wrapper, 'ready', function () {
                    var listener = chart_def['listener'];
                    g_charts[chart_name].filters = [];
                    g_charts[chart_name].setrows = [];
                    g_charts[chart_name].sortrows = {};
                    for (var event_name in listener) {
                        if (event_name == 'sort') {
                            google.visualization.events.addListener(chart_wrapper.getChart(), 'sort', function (ev) {
                                var chart_name = chart_wrapper.getChartName();
                                var chart = chart_wrapper.getChart();
                                var dt = chart_wrapper.getDataTable();

                                var columnIndex = ev['column'];
                                //var categorie = dt.getColumnLabel(columnIndex)
                                var categorie = g_charts[chart_name].view.getColumnLabel(columnIndex)
                                //var rowIndexes = g_charts['cand_emotion_col'].view.getFilteredRows([{ column: 0, value: categorie }]);
                                setFilters(chart_name, categorie)
                                var charts2 = g_charts[chart_name]['listener']['sort'];
                                for (var charts2_ix = 0; charts2_ix < charts2.length; charts2_ix++) {
                                    var chart_name2 = charts2[charts2_ix];
                                    filterChart(chart_name, chart_name2);
                                }
                            });
                        }
                        if (event_name == 'select') {
                            google.visualization.events.addListener(chart_wrapper.getChart(), 'select', function (ev) {
                                var chart_name = chart_wrapper.getChartName();
                                var chart = chart_wrapper.getChart();
                                var listen = g_charts[chart_name]['listener']['select'];
                                // getDataTable returns the view, for sorting we use the original datatable
                                var dt = chart_wrapper.getDataTable();
                                var selection = chart.getSelection();
                                for (var i = 0; i < selection.length; i++) {
                                    var item = selection[i];
                                    var columnIndex = item.column;
                                    var rowIndex = item.row;
                                    for (var action in listen) {
                                        var sort_arg = listen[action];
                                        if (action == 'rowsort' && rowIndex != null && columnIndex == null) {
                                            var rowlabel = dt.getValue(rowIndex, 0);
                                            var sortAscending = false;
                                            if (rowlabel in g_charts[chart_name].sortrows) {
                                                sortAscending = !g_charts[chart_name].sortrows[rowlabel];
                                            }
                                            g_charts[chart_name].sortrows[rowlabel] = sortAscending;
                                            var frozenColumns = 1;
                                            if ('options' in g_charts[chart_name]) {
                                                if ('frozenColumns' in g_charts[chart_name]['options']) {
                                                    frozenColumns = g_charts[chart_name]['options']['frozenColumns']
                                                }
                                            }
                                            var setcols = sortColumns(g_charts[chart_name].datatable, rowIndex, frozenColumns, sortAscending);
                                            g_charts[chart_name].view.setColumns(setcols);
                                            // make view effective for not topline???
                                            for (var cix = 0; cix < g_charts[chart_name].control_wrappers.length; cix++) {
                                                g_charts[chart_name].google_db.bind(g_charts[chart_name].control_wrappers[cix], g_charts[chart_name].chart_wrapper);
                                            }
                                            if (g_charts[chart_name].google_db != null) {
                                                g_charts[chart_name].google_db.draw(g_charts[chart_name].view);
                                            } else {
                                                g_charts[chart_name].chart_wrapper.setView(g_charts[chart_name].view.toJSON());
                                                g_charts[chart_name].chart_wrapper.draw();
                                            }
                                        }
                                        if (action == 'colsort' && rowIndex == null && columnIndex != null) {
                                            if (sort_arg == 'categories') {
                                                columnIndex = 0;
                                            }
                                            var columnlabel = dt.getColumnLabel(columnIndex);
                                            var sortAscending = false;
                                            if (columnlabel in g_charts[chart_name].sortrows) {
                                                sortAscending = !g_charts[chart_name].sortrows[columnlabel];
                                            }
                                            g_charts[chart_name].sortrows[columnlabel] = sortAscending;
                                            var setrows = g_charts[chart_name].datatable.getSortedRows({ 'column': columnIndex, 'desc': !sortAscending });
                                            g_charts[chart_name].view.setRows(setrows);
                                            //g_charts[chart_name].chart_wrapper.draw();
                                            if (g_charts[chart_name].google_db != null) {
                                                g_charts[chart_name].google_db.draw(g_charts[chart_name].view);
                                            } else {
                                                g_charts[chart_name].chart_wrapper.setView(g_charts[chart_name].view.toJSON());
                                                g_charts[chart_name].chart_wrapper.draw();
                                            }
                                        }
                                        if (action == 'rowcolfilter' && rowIndex != null && columnIndex != null) {
                                            var rowlabel = dt.getValue(rowIndex, 0);
                                            setFilters(chart_name, rowlabel)
                                            var charts2 = listen[action];
                                            for (var charts2_ix = 0; charts2_ix < charts2.length; charts2_ix++) {
                                                var chart_name2 = charts2[charts2_ix];
                                                filterChart(chart_name, chart_name2);
                                            }
                                        }
                                        if (action == 'join') {
                                            // join data from two base datatables into a new datatable.
                                            var chart_data = [[]];
                                            var chart = g_charts[chart_name];
                                            chart_data[0][0] = chart['X_facet']['label'];
                                            chart_data[0][1] = chart['Y_facet']['label'];
                                            for (var fix = 1; fix <  g_tiles_d[chart_name].length; fix++) {
                                                var facet_value = g_tiles_d[chart_name][fix];
                                                var charts2 = listen[action];
                                                for (var charts2_ix = 0; charts2_ix < charts2.length; charts2_ix++) {
                                                    var chart_name2 = charts2[charts2_ix];
                                                    var chart_data2 = g_tiles_d[chart_name][facet_value]['chart_data'];
                                                    chart_data[fix][charts2_ix + 1] = chart_data2[rowIndex];
                                                    chart_data[fix][charts2_ix + 1] = chart_data2[rowIndex];
                                                }
                                            }
                                        }
                                        if (action == 'select_event') {
                                            var rowlabel = dt.getValue(rowIndex, 0);
                                            var argument = listen[action];
                                            selectEventChart(chart_name, rowIndex, rowlabel, argument);

                                        }
                                    }
                                }
                            });
                        }
                    }
                });
            }
            if (tiles == 'dropdown' || facet_value == 'All') {
                g_charts[chart_name].google_db = google_db;
                g_charts[chart_name].chart_wrapper = chart_wrapper;
                g_charts[chart_name].control_wrappers = control_wrappers;
                g_charts[chart_name].datatable = data;
                g_charts[chart_name].view = view
            }

            if (controls.length > 0) {
                for (var cix = 0; cix < controls.length; cix++) {
                    google_db.bind(control_wrappers[cix], chart_wrapper);
                }
                g_options = {
                    allowHtml   : true,
                    animation   : {
                        duration    : 1000,
                        easing      : 'out',
                        startup     : true,
                    }
                }
                google_db.draw(view, g_options);
            } else {
                chart_wrapper.setDataTable(data);
                chart_wrapper.setView(view.toJSON());
                chart_wrapper.draw();
            }

        }

        // chart_wrapper.draw();
        //g_charts[chart_name].google_db.draw(data, g_options);
        //google_db.draw(data);
    }
}

