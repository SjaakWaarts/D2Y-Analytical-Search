// script.js

'use strict';


function draw_minicharts(minicharts) {
    if (typeof g_minicharts == 'undefined') {
        g_minicharts = minicharts;
    } else {
        g_minicharts = Object.assign(g_minicharts, minicharts);
    }

    for (var chart_name in minicharts) {
        if (!minicharts.hasOwnProperty(chart_name)) return;
        var chart = minicharts[chart_name];
        var X_facet = chart['X_facet']
        var field = X_facet['field'];
        for (var id in g_tiles_d[chart_name]) {
            var dashboard_div = document.getElementById("cell_" + field + "_" + id);
            dashboard_div.innerHTML = "";
            g_tiles_d[chart_name][id]['google_db'] = null;
            var div_card = document.createElement("div");
            var div_name = chart_name + "_" + id.split(' ').join('');
            div_card.setAttribute("id", div_name + "_chdiv");
            dashboard_div.appendChild(div_card);
            // var div_card_header = document.getElementById(chart_name + "_title");
            if (g_tiles_d[chart_name][id] == null) continue;
            var chart_data = g_tiles_d[chart_name][id]['chart_data'];
            if (chart_data.length == 0) continue;
            if (['RadarChart', 'WordCloudChart'].indexOf(chart['chart_type']) >= 0) {
                d3_chart(chart_name, chart, id, [1, 2, 3]);
            } else {
                google_chart(chart_name, chart, id);
            }
        }
    } 
}


