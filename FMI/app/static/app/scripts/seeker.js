// script.js

'use strict';

// JQuery


function tab_active() {
    var input = document.getElementsByName("tab")[0];
    var query = window.location.search;
    var tab = getParameterByName("tab");
    input.value = tab;
    var selector = "#tabs a[href='" + tab + "']";
    //$('#tabs a[href="#summary_tab"]').tab('show');
    $(selector).tab('show');
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



function add_table_row_cells(table, cells) {
    var tr = document.createElement("tr");
    table.appendChild(tr)
    for (var cell in cells) {
        var td = document.createElement("td");
        tr.appendChild(td)
        var txt = document.createTextNode(cells[cell]);
        td.appendChild(txt)
    }
}

function correlation_selecion_onchange() {
    var question = document.getElementById("correlation_selecion_select").value;
}

function question_selecion_onchange() {
    var question = document.getElementById("question_selecion_select").value;
    var table = document.getElementById("stats_table");
    var tbody = table.getElementsByTagName("tbody")[0]
    tbody.innerHTML = "";
    if (question == "Select") {
        return;
    }
    for (var stat in g_stats_df) {
        if (question == g_stats_df[stat].question) {
            var mean = g_stats_df[stat].mean.toFixed(2);
            var std = g_stats_df[stat].std.toFixed(2);
            add_table_row_cells(tbody, [g_stats_df[stat].answer, g_stats_df[stat].value, g_stats_df[stat].count,
                mean, std, g_stats_df[stat].min, g_stats_df[stat].max]);
        }
    }
    $(table).trigger("update");
    $(table).trigger("appendCache");
}

function facts_norms(stats_df) {
    g_stats_df = stats_df;

    var question_selection_div = document.getElementById("question_selecion_div");
    if (question_selection_div == null) {
        return;
    }
    var select = document.createElement("select");
    select.setAttribute("id", "question_selecion_select");
    select.setAttribute("onChange", "question_selecion_onchange()");
    question_selection_div.appendChild(select);
    // remove any existing options
    select.options.length = 0;
    var questions = ["Select"];
    for (var stat in stats_df) {
        var question = stats_df[stat].question;
        var found = false;
        for (var qix = 0; qix < questions.length; qix++) {
            if (question == questions[qix]) {
                found = true;
                break;
            }
        }
        if (!found) {
            questions.push(question);
        }
    }
    for (question in questions) {
        var option = document.createElement("option");
        option.setAttribute("value", questions[question]);
        option.text = questions[question];
        select.appendChild(option);
    }
    var correlation_selection_div = document.getElementById("correlation_selecion_div");
    var select = document.createElement("select");
    select.setAttribute("id", "correlation_selecion_select");
    select.setAttribute("onChange", "correlation_selecion_onchange()");
    correlation_selection_div.appendChild(select);
    for (question in questions) {
        var option = document.createElement("option");
        option.setAttribute("value", questions[question]);
        option.text = questions[question];
        select.appendChild(option);
    }

    var stats_facets_b = document.getElementById("stats_facets_b");
    var facets = "";
    for (var facet_tile in g_tiles_select) {
        if (facets == "") {
            facets = facet_tile;
        } else {
            facets = facets.concat(", ", facet_tile);
        }
    }
    var txt = document.createTextNode(facets);
    stats_facets_b.appendChild(txt);
}

// submit the form when a botton is pressed for Keyword load or search
function keyword_button_submit(button) {
    var input = document.getElementsByName("keyword_button")[0];
    input.value = button;
    input.form.submit()
}


$(document).ready(function () {
    $('[data-toggle="tooltip"]').tooltip(); 
});

Vue.component('treeselect', VueTreeselect.Treeselect)

var app = new Vue({
    el: '#root',
    delimiters: ['[[', ']]'],
    data: {
        filter_facets: {},
        sort_facets: {},
        query_string: null,
        pager: { page_nr: 1, nr_hits: 0, page_size: 25, nr_pages: 0, page_nrs: [], nr_pages_nrs: 5 },
        workbook: {
            facets: {}},
        hits: [],
        aggs: [],
        storyboard_redraw: true,
        m_treeselect_value: null,
        treeselect_options: [{
            id: 'a',
            label: 'a',
            children: [{
                id: 'aa',
                label: 'aa',
            }, {
                id: 'ab',
                label: 'ab',
            }],
        }, {
            id: 'b',
            label: 'b',
        }, {
            id: 'c',
            label: 'c',
        }],
    },
    methods: {
        accordion_collapse: function (hide) {
            var accordion_item_elms = document.getElementsByClassName("accordion-item");
            for (var ix = 0; ix < accordion_item_elms.length; ix++) {
                var accordion_item_elm = accordion_item_elms[ix];
                var field = accordion_item_elm.getAttribute("name");
                var accordion_arrow_elm = accordion_item_elm.getElementsByClassName("accordion_arrow")[0];
                var accordion_item_content_elm = accordion_item_elm.getElementsByClassName("accordion-item-content")[0];
                if (hide && accordion_arrow_elm.classList.contains('accordion_arrow--open')) {
                    accordion_arrow_elm.classList.remove('accordion_arrow--open');
                    accordion_item_content_elm.style.display = "none";
                }
                if (!hide && !accordion_arrow_elm.classList.contains('accordion_arrow--open')) {
                    accordion_arrow_elm.classList.add('accordion_arrow--open');
                    accordion_item_content_elm.style.display = "block";
                }
            }
        },
        accordion_arrow_toggle: function (event) {
            var accordion_header_elm = event.currentTarget;
            var accordion_item_elm = accordion_header_elm.closest(".accordion-item");
            var field = accordion_item_elm.getAttribute("name");
            var accordion_arrow_elm = accordion_item_elm.getElementsByClassName("accordion_arrow")[0];
            var accordion_item_content_elm = accordion_item_elm.getElementsByClassName("accordion-item-content")[0];
            if (accordion_arrow_elm.classList.contains('accordion_arrow--open')) {
                accordion_arrow_elm.classList.remove('accordion_arrow--open');
                accordion_item_content_elm.style.display = "none";
            } else {
                accordion_arrow_elm.classList.add('accordion_arrow--open');
                accordion_item_content_elm.style.display = "block";
            }
        },
        facet_terms_input_change(value, instanceId) {
            // [Vue tip]: Prop "instanceid" is passed to component <Anonymous>, but the declared prop name is "instanceId".
            // Note that HTML attributes are case-insensitive and camelCased props need to use their kebab-case equivalents when using in-DOM templates.
            // You should probably use "instance-id" instead of "instanceId".
            var id = instanceId.substring(0, instanceId.length - 5);
            id = id + '_select';
            var select_elm = document.getElementById(id);
            Array.from(select_elm.options).forEach(function (option_elm) {
                if (value.includes(option_elm.value)) {
                    option_elm.selected = true;
                } else {
                    option_elm.selected = false;
                }
            })
        },
        search_filter() {
            // load the hidden input "tab" with the current active tabpage
            var input = document.getElementsByName("tab")[0];
            var ul = document.getElementById("tabs");
            var items = ul.getElementsByClassName("nav-link");
            for (var i = 0; i < items.length; ++i) {
                var a_elm = items[i];
                if (a_elm.classList.contains("active")) {
                    var href = a_elm.href;
                    var n = href.lastIndexOf("#");
                    var tab = href.substr(n, href.length - 1);
                    input.value = tab;
                }
            }
        },
        search_reset() {
            var url = "?q=";
            // load the hidden input "tab" with the current active tabpage
            var input = document.getElementsByName("tab")[0];
            var ul = document.getElementById("tabs");
            var items = ul.getElementsByClassName("nav-link");
            for (var i = 0; i < items.length; ++i) {
                var a_elm = items[i];
                if (a_elm.classList.contains("active")) {
                    var href = a_elm.href;
                    var n = href.lastIndexOf("#");
                    var tab = href.substr(n, href.length - 1);
                    input.value = tab;
                    var url = url + "&tab=" + encodeURIComponent(tab);
                }
            }
            var workbook_name = getParameterByName("workbook_name");
            if (workbook_name != null) {
                url = url + "&workbook_name=" + encodeURIComponent(workbook_name);
            }
            var input = document.getElementsByName("dashboard_name")[0];
            var dashboard_name = input.value;
            if (dashboard_name != null) {
                url = url + "&dashboard_name=" + encodeURIComponent(dashboard_name);
            }
            document.getElementById("_reset").href = url;
        },
        storyboard_tab_click(event) {
            if (this.storyboard_redraw) {
                if (typeof g_storyboard != 'undefined') {
                    draw_dashboard(g_storyboard[g_storyboard_ix], g_charts, "All", g_tiles_select)
                }
                this.storyboard_redraw = false;
            }
        },
    },
    computed: {
        isopen : function () {
            // opn = this.workbook.facets[field].isopen;
            var opn = true;
            return opn;
        }
    },
    beforeMount: function () {
        for (var facet_name in g_facets_data) {
            var facet_data = g_facets_data[facet_name];
            this.workbook.facets[facet_data.field] = facet_data;
            this.workbook.facets[facet_data.field].options = [];
            for (var ix = 0; ix < facet_data.values.length; ix++) {
                var option = facet_data.values[ix];
                var node = { id: option, label: option };
                this.workbook.facets[facet_data.field].options.push(node);
            }
        }
    },
    mounted: function () {
    },

});

tab_active();
get_workbook_dashboard_names();




