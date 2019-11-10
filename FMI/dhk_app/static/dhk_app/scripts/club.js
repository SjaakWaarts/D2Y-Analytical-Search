// script.js

'use strict';

//Set url and csrf variables
//var csrf_token = $("input[name=csrf_token]").val();
var csrftoken = $("input[name=csrfmiddlewaretoken]").val();
var get_recipe_url = $("input[name=get_recipe_url]").val();
var get_cooking_clubs_url = $("input[name=get_cooking_clubs_url]").val();
var post_recipe_url = $("input[name=post_recipe_url]").val();

function yyyymmdd(dateIn) {
    var yyyy = dateIn.getFullYear();
    var mm = dateIn.getMonth() + 1; // getMonth() is zero-based
    var dd = dateIn.getDate();
    var yyyymmdd = String(yyyy + "-" + mm + "-" + dd); // Leading zeros for mm and dd
    return yyyymmdd;
}

//Vue part
//Vue.http.headers.common['X-CSRF-TOKEN'] = csrftoken;
var app = new Vue({
    el: '#root',
    delimiters: ['[[', ']]'],
    data: {
        filter_facets: {
            author: [],
            published_date: "",
            cook: [],
            categories: [],
            cooking_date: {'start' : null, 'end' : null}
        },
        sort_facets: {},
        query_string: null,
        pager: { page_nr: 1, nr_hits: 0, page_size: 25, nr_pages: 0, page_nrs: [], nr_pages_nrs: 5 },
        workbook: null,
        hits: [],
        aggs: [],
        recipe: null,
        average_rating: 0,
        cooking_club: {
            'cook': "",
            'email': "",
            'cooking_date': "",
            'address': "",
            'position': null,
            'invitation': "",
            'cost': 0,
            'participants': []
        },
        cooking_club_participant: {
            'user': "",
            'email': "",
            'comment': ""
        },
        calendar: null,
        calendar_header: {
            left: 'prev,next today',
            center: 'title',
            right: 'month,agendaWeek,agendaDay'
        },
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
        calendar_item_click: function (calendar_item) {
            this.id = calendar_item.id;
            var cooking_club = calendar_item.extendedProps;
            this.get_recipe(cooking_club);
        },
        show_cooking_club: function (cooking_club) {
            this.cooking_club = cooking_club;
            if (user.username != "") {
                this.cooking_club_participant.user = user.username;;
                this.cooking_club_participant.email = user.email;;
            } else {
                this.cooking_club_participant.user = "";
                this.cooking_club_participant.email = "";
            }
            this.cooking_club_participant.comment = "";
            var recipe_model_div = document.getElementById('recipe-modal');
            $('#recipe-modal').modal('show');
        },
        facet_filter: function (facet_name) {
            var facet = this.workbook.facets[facet_name];
            this.get_cooking_clubs();
        },
        get_cooking_clubs: function (sort = null) {
            var csrftoken_cookie = getCookie('csrftoken');
            var headers = { 'X-CSRFToken': csrftoken_cookie };
            if (sort) {
                if (sort in this.sort_facets) {
                    this.sort_facets[sort] = (this.sort_facets[sort] === 'asc' ? 'desc' : 'asc');
                }
                else {
                    this.sort_facets[sort] = 'asc';
                }
            } else {
                this.sort_facets = {};
            }
            if (this.workbook) {
                for (var fix = 0; fix < this.workbook.filters.length; fix++) {
                    var facet_name = this.workbook.filters[fix];
                    var facet = this.workbook.facets[facet_name];
                    this.filter_facets[facet_name] = facet.value;
                }
            }
            this.$http.post(get_cooking_clubs_url, {
                'csrfmiddlewaretoken': csrftoken,
                filter_facets: this.filter_facets,
                sort_facets: this.sort_facets,
                pager: this.pager,
                q: this.query_string
            },
                { 'headers': headers }).then(response => {
                    //this.hits = JSON.parse(response.bodyText);
                    this.workbook = response.body.workbook;
                    this.pager = response.body.pager;
                    if ('hits' in response.body.hits) {
                        this.hits = response.body.hits.hits;
                    }
                    if ('aggs' in response.body) {
                        this.aggs = response.body.aggs;
                    }
                    this.pager.nr_hits = response.body.hits.total;
                    // nr_pages needed to call computed component.page_nrs
                    this.pager.nr_pages = Math.ceil(this.pager.nr_hits / this.pager.page_size);

                    var calendar_items = [];
                    for (var hix = 0; hix < this.hits.length; hix++) {
                        var hit = this.hits[hix];
                        var recipe = hit['_source'];
                        for (var cix = 0; cix < recipe.cooking_clubs.length; cix++) {
                            var cooking_club = recipe.cooking_clubs[cix];
                            calendar_item = {};
                            calendar_item['id'] = hit['_id'];
                            calendar_item['title'] = cooking_club['invitation'];
                            calendar_item['start'] = cooking_club['cooking_date'];
                            calendar_item['end'] = calendar_item['start'];
                            calendar_item['extendedProps'] = cooking_club;
                            calendar_items.push(calendar_item);
                        }
                    }
                    this.calendar.removeAllEvents();
                    for (var ix = 0; ix < calendar_items.length; ix++) {
                        var calendar_item = calendar_items[ix];
                        var event = {
                            id: calendar_item.id,
                            title: calendar_item.title,
                            start: calendar_item.start,
                            end: calendar_item.end,
                            extendedProps: calendar_item.extendedProps
                        }
                        this.calendar.addEvent(event);
                    }
                    if (calendar_items > 0) {
                        var goto_date = this.calendar_items[0].start;
                        this.calendar.gotoDate(goto_date);
                    }
                    this.draw_map(calendar_items)
                });
        },
        recipe_url(url, id) {
            return url + '?id=' + id;
        },
        reset_search: function () {
            for (var fix = 0; fix < this.workbook.filters.length; fix++) {
                var facet_name = this.workbook.filters[fix];
                var facet = this.workbook.facets[facet_name];
                if (facet.type == 'terms') {
                    facet.value = [];
                } else if (facet.type in ['term', 'text']) {
                    facet.value = null;
                } else if (facet.type in ['period']) {
                    facet.value.start = null;
                    facet.value.end = null;
                } else {
                    facet.value = null;
                }
            }
            this.get_cooking_clubs();
        },
        get_recipe: function (cooking_club) {
            this.$http.get(get_recipe_url, { params: { id: this.id } }).then(response => {
                this.recipe = response.body.recipe;
                if (this.recipe.reviews.length == 0) {
                    this.average_rating = 0;
                } else {
                    var total_stars = 0;
                    for (var ix = 0; ix < this.recipe.reviews.length; ix++) {
                        total_stars += this.recipe.reviews[ix].stars;
                    }
                    this.average_rating = Math.ceil(total_stars / this.recipe.reviews.length);
                }
                this.show_cooking_club(cooking_club)
            });
        },
        draw_map: function (calendar_items) {
            var div_name = 'GoogleMap';
            var gmap_div = document.getElementById(div_name);
            gmap_div.innerHTML = "";
            gmap_div.style.height = "400px";
            gmap_div.style.width = "100 %";
            var center = { lat: 52.090736, lng: 5.121420 };
            var zoom = 7;
            var mapType = google.maps.MapTypeId.ROADMAP;
            var label = "";
            var title = "";
            var mapOptions = {
                center: center,
                zoom: zoom
            }
            // Create an array of alphabetical characters used to label the markers.
            var labels = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
            var map = new google.maps.Map(gmap_div, mapOptions);
            var geocoder = new google.maps.Geocoder();
            var bounds = new google.maps.LatLngBounds();
            var infowindow = new google.maps.InfoWindow();
            map.setOptions({ minZoom: 7, maxZoom: 18, mapTypeId: mapType, mapTypeControl: false });
            bounds.extend(center);
            var markers = [];

            for (var rownr = 0, labelnr=0; rownr < calendar_items.length; rownr++) {
                var calendar_item = calendar_items[rownr];
                var cooking_club = calendar_item.extendedProps;
                title = cooking_club.cook + ' / ' + cooking_club.cooking_date.substr(5, 5);
                var position = null;
                if (cooking_club.position.lat != 0 && cooking_club.position.lng != 0) {
                    position = new google.maps.LatLng(parseFloat(cooking_club.position.lat), parseFloat(cooking_club.position.lng));
                    // check if this position has already had a marker
                    var found = false;
                    for (var x = 0; x < markers.length; x++) {
                        if (markers[x].getPosition().equals(position)) {
                            found = true;
                            break;
                        }
                    }
                    if (!found) {
                        label = labels[labelnr % labels.length];
                        labelnr++;
                        var marker = new google.maps.Marker({
                            position: position,
                            map: map,
                            label: label,
                            title: title
                        });
                        markers.push(marker);
                        bounds.extend(marker.position);
                        google.maps.event.addListener(marker, 'click', (function (marker, label, calendar_item) {
                            return function () {
                                //infowindow.setContent(label + ' Gastheer: ' + cooking_club.cook + ' datum: ' + cooking_club.cooking_date);
                                //infowindow.open(map, marker);
                                app.id = calendar_item.id;
                                app.get_recipe(calendar_item.extendedProps);
                            }
                        })(marker, label, calendar_item));
                    }
                } else {
                    if (cooking_club.address.length > 2) {
                        //address = row.adres + ',' + row.plaats;
                        address = cooking_club.address;
                        var marker_label = label;
                    }
                }
            }
            var imagePath = static_assets_url + '/googlemaps/img/m';
            var mcOptions = {
                // gridSize : 20,
                // maxZoom : 5,
                imagePath: imagePath
            }
            var markerCluster = new MarkerClusterer(map, markers, mcOptions);
            // async, fitbounds only works when map is fully loaded.
            //google.maps.event.addListenerOnce(map, 'idle', function () {
            //    map.fitBounds(bounds);
            //});
            google.maps.event.trigger(map, 'resize');
            //map.setCenter(marker.getPosition());
        },
    },
    computed: {
    },
    mounted: function () {
        var today = new Date();
        var startdt = new Date();
        startdt = startdt.setMonth(today.getMonth() - 3);

        var calendarEl = document.getElementById('calendar');
        this.calendar = new FullCalendar.Calendar(calendarEl, {
            locale: 'nl',
            plugins: ['dayGrid'],
            header: this.calendar_header,
            defaultDate: yyyymmdd(today),
            eventClick: function (info) {
                var calendar_item = info.event;
                app.calendar_item_click(calendar_item);
                info.el.style.borderColor = 'red';
            }
        });
        this.get_cooking_clubs();
        this.calendar.render();
    },
});




