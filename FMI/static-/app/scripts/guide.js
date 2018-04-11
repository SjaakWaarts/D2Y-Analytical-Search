// script.js

'use strict';

// JQuery

var g_guide;
var g_options;
var g_sites;
var g_site_views;

//function route_step(route_name, step_name) {
//    var input = document.getElementsByName("step_name")[0];
//    input.value = step_name;
//    var step = g_guide['steps'][step_name];

//    if (step['type'] == 'selection') {
//        if (step['selection'][0] == 'graph') {
//            var dashboard = step['selection'][1];
//            var charts = step['selection'][2];
//            g_charts = charts;
//            tab_active('#storyboard_tab');
//            draw_dashboard(dashboard, charts, "All", "dashboard_div");
//        }
//    }
//    if (step['type'] == 'selection') {
//        if (step['selection'][0] == 'gallery') {
//            var gallery = step['selection'][1];
//            var field = step['facet'];
//            var selsize = step['selsize'];
//            tab_active('#results_tab');
//            draw_gallery(field, selsize, gallery);
//        }
//    }
//    if (step['type'] == 'decision') {
//        if (step['selection'][0] == 'gallery') {
//            var gallery = step['selection'][1];
//            var field = step_name
//            var selsize = step['selsize'];
//            tab_active('#results_tab');
//            draw_gallery(field, selsize, gallery);
//        }
//    }
//    if (step['type'] == 'destination') {
//        var url = window.location.href;
//        //strip of the last part of the URL so it can be replaced by the destination url
//        var to = url.lastIndexOf('/');
//        to = to == -1 ? url.length : to + 1;
//        url = url.substring(0, to);
//        var url = getBaseUrl() + "&acountry.keyword=0&agender.keyword=0&aage.keyword=0";
//        window.location.href = url;
//    }
//}

//function route_definition(route_name) {
//    var table = document.getElementById("route_definition_table");
//    var steps = g_guide['steps'];
//    var route_steps = g_guide['routes'][route_name]['1'];

//    for (var step_ix = 0; step_ix < route_steps.length; step_ix++) {
//        var step_name = route_steps[step_ix];
//        var thead = document.createElement("thead");
//        table.appendChild(thead)
//        var td = document.createElement("td");
//        td.colSpan = "2";
//        thead.appendChild(td);
//        var bold = document.createElement("b");
//        bold.innerHTML = step_name;
//        td.appendChild(bold);
//        var tbody = document.createElement("tbody");
//        table.appendChild(tbody)
//        var step = steps[step_name];
//        for (var item in step) {
//            var tr = document.createElement("tr");
//            tbody.appendChild(tr);
//            var td = document.createElement("td");
//            tr.appendChild(td);
//            var txt = document.createTextNode(item);
//            td.appendChild(txt);
//            var td = document.createElement("td");
//            tr.appendChild(td);
//            if (step[item] instanceof Array) {
//                var txt = step[item][0];
//            } else {
//                var txt = step[item];
//            }
//            var txt = document.createTextNode(txt);
//            td.appendChild(txt);
//        }
//        if (step['type'] == 'decision') {
//            var dec_table = document.getElementById("decision_table");
//            var tr = document.createElement("tr");
//            dec_table.appendChild(tr);
//            var td = document.createElement("td");
//            tr.appendChild(td);
//            var label = document.createElement("label");
//            td.appendChild(label);
//            label.setAttribute("for", step_name);
//            label.innerHTML = step_name;
//            var select = document.createElement("select");
//            td.appendChild(select);
//            select.setAttribute("name", step_name);
//            select.setAttribute("id", step_name);
//            select.setAttribute("class", "form-control");
//            select.setAttribute("multiple", true);
//            for (var decision in step['decisionstep']) {
//                var option = document.createElement("option");
//                select.appendChild(option);
//                option.setAttribute("value", decision);
//                option.text = decision;
//            }
//        }
//    }
//}


function tab_active(tab) {
    var selector = "#tabs a[href='" + tab + "']";
    $(selector).tab('show');
    //$(selector).tabs("option", "active", 1);
}


function value2option(map, value) {
    for (var option in map) {
        if (map[option] == value) {
            return option;
        }
    }
    return value;
}

function draw_gallery(field, selsize, gallery) {
    var gallery_div = document.getElementById("gallery_div");
    gallery_div.innerHTML = "";

    var table = document.createElement("table");
    gallery_div.appendChild(table)
    for (var img_ix = 0; img_ix < gallery.length; img_ix++) {
        var key_image = gallery[img_ix];
        var tr = document.createElement("tr");
        table.appendChild(tr)
        var td = document.createElement("td");
        tr.appendChild(td)
        var img_elm = document.createElement("img")
        img_elm.setAttribute("width", "250px");
        img_elm.setAttribute("height", "250px");
        img_elm.setAttribute("src", key_image[1]);
        //img_elm.setAttribute("onclick", "gallery_select('"+field+"', '"+key_image[0]+"', '"+selsize+"')");
        td.appendChild(img_elm)
        var td = document.createElement("td");
        tr.appendChild(td)
        var txt = document.createTextNode(key_image[0]);
        td.appendChild(txt)
    }
}

function site_view_clear() {
    var images_div = document.getElementById("gallery_div");
    images_div.innerHTML = "";
    var facet_div = document.getElementById("facet_div");
    facet_div.innerHTML = "";
    var images_div = document.getElementById("images_div");
    images_div.innerHTML = "";
    var carousel_names_div = document.getElementById("carousel_names_div");
    carousel_names_div.innerHTML = "";
    var carousel_ol = document.getElementById("carousel_ol");
    carousel_ol.innerHTML = "";
    var carousel_slides_div = document.getElementById("carousel_slides_div");
    //carousel_slides_div.innerHTML = "";
    var nodes = carousel_slides_div.getElementsByTagName("div");
    for (var i = 0, len = nodes.length; i != len; ++i) {
        carousel_slides_div.removeChild(nodes[0]);
    }
    var dashboard_div = document.getElementById("dashboard_div");
    dashboard_div.innerHTML = "";
}

function show_breadcrumps(site_name) {
    var breadcrumps = {};
    var site = g_sites[site_name];
    for (var menu_name in site['site_menu']['menu_items']) {
        var menu_item = site['site_menu']['menu_items'][menu_name];
        if (menu_item['type'] == 'data-selector') {
            if (Array.isArray(menu_item['view'])) {
                var view_names = menu_item['view'];
            } else {
                var view_names = [menu_item['view']];
            }
            for (var ix = 0; ix < view_names.length; ix++) {
                var view_name = view_names[ix];
                var site_view_filter = g_site_views[view_name];
                if (site_view_filter['type'] == 'selection') {
                    var filters = site_view_filter['filters'];
                    for (var field in filters) {
                        if (filters[field].length > 0) {
                            var facet_field_filters = "";
                            for (var ix = 0; ix < filters[field].length; ix++) {
                                var filter_value = filters[field][ix];
                                if (ix > 0) {
                                    facet_field_filters = facet_field_filters + ', ';
                                }
                                facet_field_filters = facet_field_filters + filter_value;
                            }
                            breadcrumps[field] = facet_field_filters;
                        }
                    }
                }
            }
        }
    }
    var ul_elm = document.getElementById("breadcrumb_div");
    if (ul_elm != null) {
        ul_elm.innerHTML = "";
        for (var field in breadcrumps) {
            var filter_value = breadcrumps[field];
            var li_elm = document.createElement("li");
            li_elm.innerHTML = filter_value;
            ul_elm.appendChild(li_elm);
        }
    }
}

// Called from chart.js in case of a GeoMap chart select_event
function country_select(view_name, option) {
    var site_name = document.getElementById("site_select").value;
    var site_view = g_site_views[view_name];
    var field = 'country.keyword';
    var filters = site_view['filters'];
    var index = filters[field].indexOf(option);
    if (index >= 0) {
        filters[field].splice(index, 1);
    } else {
        filters[field].push(option);
    }
    show_breadcrumps(site_name);
}

function facet_select(site_name, menuy_name, view_name, field, select_elm_id) {
    var site_view = g_site_views[view_name];
    var filters = site_view['filters'];
    filters[field] = [];
    var select_elm = document.getElementById(select_elm_id);
    for (var i = 0; i < select_elm.options.length; i++) {
        var option_elm = select_elm.options[i];
        if (option_elm.selected) {
            filters[field].push(option_elm.value);
        }
    }
    show_breadcrumps(site_name);
    if (site_view['type'] == 'answer_selection') {
        var chart_names = site_view['listener'][field];
        for (var i = 0; i < chart_names.length; i++) {
            var chart = g_charts[chart_names[i]];
            if (chart['X_facet']['field'] == field) {
                chart['X_facet']['answers'] = filters[field];
            } else {
                chart['Y_facet']['answers'] = filters[field];
            }
        }
        g_storyboard_def_changed = true;
    }
}

function gallery_select(site_name, menu_name, view_name, field, node, option, selsize) {
    var site_view = g_site_views[view_name];
    var filters = site_view['filters'];
    var index = filters[field].indexOf(option);
    if (index >= 0) {
        filters[field].splice(index, 1);
    } else {
        filters[field].push(option);
    }
    if (site_view['selection'] == 'casc_images') {
        var fields = Object.keys(site_view['filters']);
        var index = fields.indexOf(field);
        index++;
        if (index < fields.length) {
            var casc_field = fields[index];
            var optionsmap = site_view['optionsmap'][casc_field];
            if (option in optionsmap) {
                site_view_casc_images(site_name, menu_name, view_name, casc_field, option)
            }
        }
    }
    show_breadcrumps(site_name);
}

function site_view_images(site_name, menu_name, view_name, div_elm) {
    var site_view = g_site_views[view_name];
    site_view_clear();
    var nrimages = site_view['images'].length;
    var layout = 'grid-nx' + nrimages.toString();
    if ('layout' in site_view) {
        layout = site_view['layout'];
    }
    var re = /(grid)(-?)([A-Za-z1-9]?)(x?)([1-9]?)/
    var ar = re.exec(layout);
    var nrcol = (ar[5] == '') ? 1 : parseInt(ar[5]);
    var l_width = 12 / nrcol;
    var colnr = 0;
    var images_div = document.getElementById(div_elm);
    for (var img_ix = 0; img_ix < site_view['images'].length; img_ix++) {
        var image_src = encodeURI('/static/app/media/' + site_name + '/' + site_view['images'][img_ix]);
        var option = site_view['descr'];
        if ('optionsmap' in site_view) {
            option = value2option(site_view['optionsmap'], site_view['images'][img_ix])
        }
        if (colnr == 0) {
            var div_row = document.createElement("div");
            div_row.setAttribute("class", "row");
            images_div.appendChild(div_row);
        }
        var div_col = document.createElement("div");
        div_col.setAttribute("class", "col-md-" + l_width);
        div_row.appendChild(div_col);
        var img_elm = document.createElement("img");
        div_col.innerHTML = option + "<br />";
        div_col.appendChild(img_elm);
        img_elm.setAttribute("src", image_src);
        img_elm.setAttribute("alt", option);
        if ('style' in site_view) {
            var style = site_view['style'];
            for (var property in style) {
                img_elm.style[property] = style[property];
            }
        }
        if ('listener' in site_view) {
            var field = site_view['listener']['select']['select_event'];
            var selsize = site_view['selsize'];
            var option = value2option(site_view['optionsmap'], site_view['images'][img_ix])
            div_col.setAttribute("onclick", "gallery_select('" + site_name + "','" + menu_name + "','" + view_name + "','" +
                                                            field + "', '" + option + "', '" + selsize + "')");
        }
        colnr = colnr + 1;
        if (colnr == nrcol) {
            colnr = 0
        }
    }
}


function site_view_carousel(site_name, view_name, car_name, car_ix) {
    var carousel_ol = document.getElementById("carousel_ol");
    carousel_ol.innerHTML = "";
    var carousel_slides_div = document.getElementById("carousel_slides_div");
    carousel_slides_div.innerHTML = "";
    var site_view = g_site_views[view_name];
    var carousels = site_view['carousels'];
    var carousel = carousels[car_ix];
    var images = carousel[1];
    for (var img_ix = 0; img_ix < images.length; img_ix++) {
        var li_elm = document.createElement("li");
        li_elm.setAttribute('data-target', '#carousel_div');
        li_elm.setAttribute('data-slide-to', img_ix.toString());
        var div_elm = document.createElement("div");
        div_elm.setAttribute('class', 'carousel-inner');
        var image_src = encodeURI('/static/app/media/' + site_name + '/' + images[img_ix]);
        div_elm.innerHTML = "<img src='" + image_src + "' alt='" + images[img_ix] + "'/>"
        if ('listener' in site_view) {
            var field = site_view['listener']['select']['select_event'];
            var selsize = site_view['selsize'];
            div_elm.setAttribute("onclick", "gallery_select('" + site_name + "', '" + menu_name + "', '" + view_name + "','" +
                                                            field + "', '" + image_src + "', '" + selsize + "')");
        }
        if (img_ix == 0) {
            li_elm.setAttribute('class', 'active');
            div_elm.setAttribute('class', 'item active');
        } else {
            div_elm.setAttribute('class', 'item');
        }
        carousel_ol.appendChild(li_elm);
        carousel_slides_div.appendChild(div_elm);
    }
    $('#carousel_names_div .carousel-selected').removeClass('carousel-selected');
    $('#carousel_names_div #' + car_ix.toString()).addClass('carousel-selected');
}

function site_view_carousels_select(site_name, view_name, car_name, car_ix) {
    site_view_carousel(site_name, view_name, car_name, car_ix);
}

function site_view_carousels(site_name, menu_name, view_name) {
    var site_view = g_site_views[view_name];
    site_view_clear();
    var carousel_names_div = document.getElementById("carousel_names_div");
    var carousel_ol = document.getElementById("carousel_ol");
    var carousel_slides_div = document.getElementById("carousel_slides_div");

    var carousels = site_view['carousels'];
    // the names of all carousels are shown at the left
    for (var car_ix = 0; car_ix < carousels.length; car_ix++) {
        var carousel = carousels[car_ix];
        var car_name = carousel[0];
        var div_elm = document.createElement("div");
        div_elm.setAttribute('id', car_ix.toString());
        div_elm.setAttribute("onclick", "site_view_carousels_select('" + site_name + "', '" +
            view_name + "', '" + car_name + "', " + car_ix.toString() + ")");
        div_elm.innerHTML = car_name;
        carousel_names_div.appendChild(div_elm);
    }
    // the images of the first carousel is shown at the right
    site_view_carousel(site_name, view_name, carousels[0][0], 0);
}

function site_view_casc_images(site_name, menu_name, view_name, field, node) {
    var site_view = g_site_views[view_name];
    site_view_clear();
    var layout = 'grid-nx5';
    if ('layout' in site_view) {
        layout = site_view['layout'];
    }
    var re = /(grid)(-?)([A-Za-z1-9]?)(x?)([1-9]?)/
    var ar = re.exec(layout);
    var nrcol = (ar[5] == '') ? 1 : parseInt(ar[5]);
    var l_width = 12 / nrcol;
    var colnr = 0;
    var images_div = document.getElementById("gallery_div");
    var optionsmap = site_view['optionsmap'][field][node];
    for (var option in optionsmap) {
        var image = optionsmap[option];
        var image_src = encodeURI('/static/app/media/' + site_name + '/' + image);
        if (colnr == 0) {
            var div_row = document.createElement("div");
            div_row.setAttribute("class", "row");
            images_div.appendChild(div_row);
        }
        var div_col = document.createElement("div");
        div_col.setAttribute("class", "col-md-" + l_width);
        div_row.appendChild(div_col);
        var img_elm = document.createElement("img");
        div_col.innerHTML = option + "<br />";
        div_col.appendChild(img_elm);
        img_elm.setAttribute("src", image_src);
        img_elm.setAttribute("alt", option);
        if ('style' in site_view) {
            var style = site_view['style'];
            for (var property in style) {
                img_elm.style[property] = style[property];
            }
        }
        var selsize = site_view['selsize'];
        div_col.setAttribute("onclick", "gallery_select('" + site_name + "', '" + menu_name + "', '" + view_name + "','" +
                                                        field + "','" + node + "', '" + option + "', '" + selsize + "')");
        colnr = colnr + 1;
        if (colnr == nrcol) {
            colnr = 0
        }
    }
}

function site_view_facet(site_name, menu_name, view_name, div_elm) {
    var site_view = g_site_views[view_name];
    var field = Object.keys(site_view['filters'])[0];
    var facet_div = document.getElementById(div_elm);
    var form_group_elm = document.createElement("div");
    form_group_elm.setAttribute("class", "form-group");
    facet_div.appendChild(form_group_elm);
    var label_elm = document.createElement("label");
    label_elm.innerHTML = site_view['descr'];
    form_group_elm.appendChild(label_elm);
    var select_elm = document.createElement("select");
    select_elm.setAttribute("name", view_name);
    var size = 3;
    if ('optionsmap' in site_view) {
        size = Object.keys(site_view['optionsmap']).length;
        if (size < 3) { size = 3 } else if (size > 15) size = 15;
    }
    select_elm.setAttribute("size", size);
    select_elm.setAttribute("class", "form-control facet-select");
    select_elm.setAttribute("multiple", "multiple");
    var select_elm_id = div_elm + "_" + field + "_select";
    select_elm.setAttribute("id", select_elm_id);
    select_elm.setAttribute("onclick", "facet_select('" + site_name + "', '" + menu_name + "', '" + view_name + "', '" +
                                                    field + "', '" + select_elm_id + "')");
    form_group_elm.appendChild(select_elm);
    for (var option in site_view['optionsmap']) {
        var option_elm = document.createElement("option");
        option_elm.setAttribute("value", option);
        option_elm.text = option;
        //option_elm.setAttribute("onclick", "facet_select('" + site_name + "', '" + menu_name + "', '" + view_name + "', '" +
        //                                                field + "', '" + option + "')");
        var index = site_view['filters'][field].indexOf(option);
        if (index >= 0) {
            option_elm.setAttribute('selected', true);
        }
        select_elm.appendChild(option_elm);
    }
}

// called by server
//function site_menu_show(site_name, menu_name) {
//    var menu_items = g_sites[site_name].site_menu.menu_items;
//    var menu_item = menu_items[menu_name];
//    var input = document.getElementsByName("menu_name")[0];
//    input.value = menu_name;
//    switch (menu_item.type) {
//        case 'data-selector':
//            data_selector(site_name, menu_name);
//            break;
//        case 'view-selector':
//            view_selector(site_name, menu_name);
//            break;
//        case 'site-view':
//            break;
//        default:
//            console.log('site_menu_show, unknown menu_item.type ' + menu_item.type);
//    }
//}

function fill_params_view_dashboard(site_name, menu_name, view_name, filters) {
    var site_view = g_site_views[view_name];
    var params = {};
    params['workbook_name'] = site_view["workbook_name"];
    params['storyboard_name'] = site_view["storyboard_name"];
    params['dashboard_name'] = site_view["dashboard_name"];
    params['site_name'] = site_name;
    params['menu_name'] = menu_name;
    params['view_name'] = view_name;
    // set hidden parameters to communicate with storyboard.js
    set_hidden_param("workbook_name", params['workbook_name']);
    set_hidden_param("storyboard_name", params['storyboard_name']);
    set_hidden_param("dashboard_name", params['dashboard_name']);
    set_hidden_param("menu_name", params['menu_name']);
    set_hidden_param("view_name", params['view_name']);
    var input = document.getElementsByName("benchmark")[0];
    var benchmark = input.value;
    params['benchmark'] = benchmark;
    var input = document.getElementsByName("tile_facet_field")[0];
    var tile_facet_field = input.value;
    params['tile_facet_field'] = tile_facet_field;
    var input = document.getElementsByName("tile_facet_value")[0];
    var tile_facet_value = input.value;
    params['tile_facet_value'] = tile_facet_value;

    if (typeof filters != 'undefined') { // when called from Angular, filters are also in g_site_views
        for (var filter_field in filters) {
            params[filter_field] = filters[filter_field];
        }
    } else {
        var site = g_sites[site_name];
        for (var menu_name in site['site_menu']['menu_items']) {
            var menu_item = site['site_menu']['menu_items'][menu_name];
            if (menu_item['type'] == 'data-selector') {
                if (Array.isArray(menu_item['view'])) {
                    var view_names = menu_item['view'];
                } else {
                    var view_names = [menu_item['view']];
                }
                for (var ix = 0; ix < view_names.length; ix++) {
                    var view_name = view_names[ix];
                    var site_view_filter = g_site_views[view_name];
                    if (site_view_filter['type'] == 'selection') {
                        var filters = site_view_filter['filters'];
                        for (var field in filters) {
                            if (filters[field].length > 0) {
                                var facet_field_filters = "";
                                for (var ix = 0; ix < filters[field].length; ix++) {
                                    var filter_value = filters[field][ix];
                                    if (ix > 0) {
                                        facet_field_filters = facet_field_filters + ',';
                                    }
                                    facet_field_filters = facet_field_filters + filter_value;
                                }
                                params[field] = facet_field_filters;
                            }
                        }
                    }
                }
            }
        }
        show_breadcrumps(site_name);
    }

    return params;
}


function site_view_charts(site_name, menu_name, view_name, l_site_views, l_sites, filters, baseurl) {
    g_site_views = l_site_views;
    g_sites = l_sites;
    g_baseurl = baseurl.substring(0, baseurl.length - 1);
    var site_view = g_site_views[view_name];
    disable_selects_storyboard(true);
    var params = fill_params_view_dashboard(site_name, menu_name, view_name, filters);
    var seeker_url = site_view['url'];
    //var url = 'http://10.20.33.102/FMI';
    //var url = 'http://localhost:56138';
    var url = g_baseurl + seeker_url;
    $.ajax({
        url: url,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
        method: 'GET',
        data: params,
        success: get_dashboard_callback
    });
}

//function csrfSafeMethod(method) {
//    // these HTTP methods do not require CSRF protection
//    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
//}

//$.ajaxSetup({
//    beforeSend: function (xhr, settings) {
//        var csrf_required = csrfSafeMethod(settings.type);
//        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
//            xhr.setRequestHeader("X-CSRFToken", csrftoken);
//        }
//    }
//});

function get_view_dashboard(site_name, menu_name, view_name) {
    var site_view = g_site_views[view_name];
    disable_selects_storyboard(true);
    var params = fill_params_view_dashboard(site_name, menu_name, view_name);
    var seeker_url = site_view['url'];
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
    $.get(url, params, get_dashboard_callback);
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


// called by server
function site_view_show(site_name, menu_name, view_name) {
    var menu_items = g_sites[site_name].site_menu.menu_items;
    var menu_item = menu_items[menu_name];
    var views = menu_item['views'];
    var site_view = g_site_views[view_name];
    var input = document.getElementsByName("view_name")[0];
    input.value = view_name;
    switch (site_view.type) {
        case 'images':
            tab_active('#results_tab');
            site_view_images(site_name, menu_name, view_name, "images_div")
            break;
        case 'carousels':
            tab_active('#results_tab');
            site_view_carousels(site_name, menu_name, view_name)
            break;
        case 'charts':
            tab_active('#storyboard_tab');

            get_view_dashboard(site_name, menu_name, view_name);
            break;
        default:
            console.log('site_view_show, unknown menu_item.type ' + menu_item.type);
    }
}

function site_view_select(site_name, menu_name, view_name) {
    site_view_show(site_name, menu_name, view_name);
    //document.getElementById("guide_form").submit();
}


function view_selector(site_name, menu_name) {
    var site_menu_views_div = document.getElementById("site_menu_views_div");
    site_menu_views_div.innerHTML = "";
    var view_style_div = document.getElementById("view_style_div");

    var menu_items = g_sites[site_name].site_menu.menu_items;
    var menu_item = menu_items[menu_name];
    var views = menu_item['views'];
    tab_active('#site_menu_views_tab');
    if ('style' in menu_item) {
        var style = menu_item['style'];
        for (var property in style) {
            view_style_div.style[property] = style[property];
        }
    }

    for (var view_ix = 0; view_ix < views.length; view_ix++) {
        var view_name = views[view_ix];
        var site_view = g_site_views[view_name];
        //var a_elm = document.createElement("a");
        //var href = window.location.href
        //href = href.substring(0, href.search('guide'))
        //href = href + 'guide?site_select=' + site_name + "&menu_name=" + menu_name + "&view_name=" + view_name
        //a_elm.setAttribute("href", encodeURI(href));
        //a_elm.setAttribute("onclick", "site_view_select('" + site_name + "', '" + menu_name + "', '" + view_name + "')");
        //col_elm.appendChild(a_elm);
        var div_elm = document.createElement("div");
        div_elm.setAttribute("onclick", "site_view_select('" + site_name + "', '" + menu_name + "', '" + view_name + "')");
        div_elm.setAttribute("flex", "1 1 auto");
        var image_src = '/static/app/media/' + site_name + '/' + view_name + '.jpg';
        div_elm.innerHTML = "<div class='info-card'>" +
                            "<div class='info-card-front'><img class='card-image' src='" + image_src +"'></div>" +
                            "<div class='info-card-back'><h3>" + site_view['descr'] + "</h3></div>" +
                            site_view['descr'] +
                        "</div>"
        site_menu_views_div.appendChild(div_elm)
    }
}


function data_selector(site_name, menu_name, view_name) {
    var menu_items = g_sites[site_name].site_menu.menu_items;
    var site_view = g_site_views[view_name];
    tab_active('#filters_tab');
    switch (site_view.selection) {
        case 'graph':
            //document.getElementById("guide_form").submit();
            tab_active('#storyboard_tab');
            get_view_dashboard(site_name, menu_name, view_name)
            break;
        case 'images':
            tab_active('#filters_tab');
            site_view_images(site_name, menu_name, view_name, "gallery_div")
            break;
        case 'casc_images':
            tab_active('#filters_tab');
            var fields = Object.keys(site_view['filters']);
            var field = fields[0]
            site_view_casc_images(site_name, menu_name, view_name, field, "root")
            break;
        case 'carousels':
            tab_active('#results_tab');
            site_view_carousels(site_name, menu_name, view_name)
            break;
        case 'facet':
            tab_active('#filters_tab');
            site_view_facet(site_name, menu_name, view_name, "facet_div")
            break;
        default:
            console.log('data_selector, unknown site_view.selection ' + site_view.selection);
    }
}

// called by user
function site_menu_select(site_name, menu_name) {
    //console.log(menu_name);
    var menu_items = g_sites[site_name].site_menu.menu_items;
    var menu_item = menu_items[menu_name];
    var input = document.getElementsByName("menu_name")[0];
    input.value = menu_name;
    var input = document.getElementsByName("view_name")[0];
    input.value = '';
    switch (menu_item.type) {
        case 'data-selector':
            site_view_clear();
            if (Array.isArray(menu_item['view'])) {
                var view_names = menu_item['view'];
            } else {
                var view_names = [menu_item['view']];
            }
            for (var ix = 0; ix < view_names.length; ix++) {
                var view_name = view_names[ix];
                data_selector(site_name, menu_name, view_name);
            }
            //site_view_select(site_name, menu_name, '')
            break;
        case 'view-selector':
            if ('workbook_name' in g_sites[site_name] && g_storyboard_def_changed) {
                var workbook_name = g_sites[site_name]['workbook_name'];
                api_post_storyboard_def(workbook_name)
                g_storyboard_def_changed = false;
            }
            view_selector(site_name, menu_name);
            break;
        case 'site-view':
            break;
        default:
            console.log('site_menu_select, unknown menu_item.type ' + menu_item.type);
    }
}

function site_show(site_name) {
    var site_menu_elm = document.getElementById("site_menu");
    var menu = g_sites[site_name].site_menu.menu;
    var menu_items = g_sites[site_name].site_menu.menu_items;

    for (var menu_ix = 0; menu_ix < menu.length; menu_ix++) {
        var menu_name = menu[menu_ix];
        var menu_item = menu_items[menu_name];
        var glyph = ""
        switch (menu_item.type) {
            case 'data-selector':
                glyph = '<span class="glyphicon glyphicon-filter"></span>'
                break;
            case 'view-selector':
            case 'site-view':
            default:
                glyph = '<span class="glyphicon glyphicon-sunglasses"></span>'
        }
        var a_elm = document.createElement("a");
        a_elm.innerHTML = glyph + menu_name;
        a_elm.setAttribute("onclick", "site_menu_select('" + site_name + "', '" + menu_name + "')");
        site_menu_elm.appendChild(a_elm)
    }
}

function site_onchange() {
    var site_name = document.getElementById("site_select").value;
    var site_menu_elm = document.getElementById("site_menu");
    site_menu_elm.innerHTML = "";
    var input = document.getElementsByName("menu_name")[0];
    input.value = '';
    var input = document.getElementsByName("view_name")[0];
    input.value = '';
    //document.getElementById("guide_form").submit();
    site_view_clear();
    if (site_name != "") {
        api_site_menu(site_name);
    }
}


// guided_menu is called by guide.html on load
// 1. It loads the site_select dropdown box
// 2. In case a site_name is already selected, that site is set to active and is shown
// 3. When also a menu_name is specified, that site menu is also shown
// 4. In case also a view_name is specified for a view_selected menu item, that view is shown
function guided_menu(site_name, menu_name, view_name, sites, site_views) {
    g_sites = sites;
    g_site_views = site_views;

    var select = document.getElementById("site_select");
    select.innerHTML = "";
    select.setAttribute("onChange", "site_onchange()");
    // remove any existing options
    var option = document.createElement("option");
    option.setAttribute("value", "");
    option.text = "Select a site";
    if (site_name == "") {
        option.setAttribute('selected', true);
    }
    select.appendChild(option);
    for (var site_key in sites) {
        var option = document.createElement("option");
        option.setAttribute("value", site_key);
        option.text = sites[site_key].descr;
        if (site_name == site_key) {
            option.setAttribute('selected', true);
        }
        select.appendChild(option);
    }

    if (site_name != "") {
        site_show(site_name);
        //if (menu_name != "") {
        //    site_menu_show(site_name, menu_name);
        //    if (view_name != "") {
        //        site_view_show(site_name, menu_name, view_name);
        //    }
        //}
    }
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



function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function api_error(xhr, error) {
    console.debug(xhr);
    console.debug(error);
}

function api_site_menu_callback(data, status) {
    // var csrftoken = '{{ csrf_token }}';
    var route_name = data['route_name'];
    var step_name = data['step_name'];
    var site_name = data['site_name'];
    var menu_name = data['menu_name'];
    var view_name = data['view_name'];
    var benchmark = data['benchmark'];
    var sites = data['sites'];
    var site_views = data['site_views'];
    set_hidden_param("benchmark", benchmark);
    get_workbook_dashboard_names();
    guided_menu(site_name, menu_name, view_name, sites, site_views);
    if ('workbook_name' in g_sites[site_name]) {
        var workbook_name = g_sites[site_name]['workbook_name'];
        api_get_storyboard_def(workbook_name)
    }
}

function api_site_menu(site_name) {
    var headers = {};
    var params = {};
    params['site_select'] = site_name;
    var url = getBaseUrl() + '/api/site_menu';
    //$.get(url, params, api_site_menu_callback);
    //$.ajax({
    //    url: url,
    //    headers: headers,
    //    method: 'GET',
    //    dataType: 'json',
    //    data: params,
    //    success: api_site_menu_callback,
    //    error: api_error
    //});

    var cookie_csrftoken = getCookie('csrftoken');
    var dom_csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
    //headers['csrftoken'] = csrftoken;
    params['csrfmiddlewaretoken'] = cookie_csrftoken;
    //params['site_views'] = JSON.stringify(g_site_views);
    //$.post(url, headers = headers, params = params, api_site_menu_callback);
    $.ajax({
        url: url,
        headers: headers,
        method: 'POST',
        dataType: 'json',
        data: params,
        success: api_site_menu_callback,
        error: api_error
    });
}


function api_storyboard_def_callback(data, status) {
    var workbook_name = data['workbook_name'];
    g_storyboards = data['storyboards'];
    g_charts = data['charts'];
}


function api_post_storyboard_def(workbook_name) {
    var headers = {
        'X-Requested-With': 'XMLHttpRequest',
    };

    var cookie_csrftoken = getCookie('csrftoken');
    var dom_csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
    //headers['csrftoken'] = csrftoken;
    // empty google chart variables to enable json stringify.
    for (var chart_name in g_charts) {
        var chart = g_charts[chart_name];
        delete chart.google_db;
        delete chart.chart_wrapper;
        delete chart.control_wrappers;
        delete chart.datatable;
        delete chart.view;
    }
    var params = {};
    params['csrfmiddlewaretoken'] = cookie_csrftoken;
    params['workbook_name'] = workbook_name;
    params['storyboards'] = JSON.stringify(g_storyboards);
    params['charts'] = JSON.stringify(g_charts);
    var url = getBaseUrl() + '/api/storyboard_def';
    // first to the get on this website to obtain the token.
    //$.get(url, params, api_site_menu_callback);
    $.ajax({
        url: url,
        headers: headers,
        method: 'POST',
        dataType: 'json',
        data: params,
        success: api_storyboard_def_callback,
        error: api_error
    });
}

function api_get_storyboard_def(workbook_name) {
    var headers = {
        'X-Requested-With': 'XMLHttpRequest',
    };
    var params = {};
    params['workbook_name'] = workbook_name;
    var url = getBaseUrl() + '/api/storyboard_def';
    // first to the get on this website to obtain the token.
    //$.get(url, params, api_site_menu_callback);
    $.ajax({
        url: url,
        headers: headers,
        method: 'GET',
        dataType: 'json',
        data: params,
        success: api_storyboard_def_callback,
        error: api_error
    });
}

function api_get_post_storyboard_def_get_callback(html, status) {
    var dom_array = $.parseHTML(html);
    var form_elm = $(dom_array).filter('form').get(0)
    var input_elm = form_elm.getElementsByTagName('input')[0];
    var csrfoken = input_elm.value;
    var table_elm = $(dom_array).filter('table').get(0)
    var td_elms = table_elm.getElementsByTagName('td');
    var workbook_name = td_elms[1].textContent;
    var headers = {};
    var params = {};
    var url = getBaseUrl() + '/api/storyboard_def';
    params['csrfmiddlewaretoken'] = csrftoken;
    params['workbook_name'] = workbook_name;
    params['storyboards'] = JSON.stringify(g_storyboards);
    params['charts'] = JSON.stringify(g_charts);
    //$.post(url, headers = headers, params = params, api_site_menu_callback);
    $.ajax({
        url: url,
        headers: headers,
        method: 'POST',
        dataType: 'json',
        data: params,
        success: api_storyboard_def_callback,
        error: api_error
    });
}

function api_get_post_storyboard_def(workbook_name) {
    var headers = {};
    var params = {};
    params['api_request'] = 'api_csrftoken'
    params['workbook_name'] = workbook_name;
    var url = getBaseUrl() + '/api/storyboard_def';
    // first to the get on this website to obtain the token.
    //$.get(url, params, api_site_menu_callback);
    $.ajax({
        url: url,
        headers: headers,
        method: 'GET',
        dataType: 'html',
        data: params,
        success: api_get_post_storyboard_def_get_callback,
        error: api_error
    });
}

