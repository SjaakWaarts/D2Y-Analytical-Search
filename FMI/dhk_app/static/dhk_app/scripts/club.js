// script.js

'use strict';

//Set url and csrf variables
//var csrf_token = $("input[name=csrf_token]").val();
var csrftoken = $("input[name=csrfmiddlewaretoken]").val();
var get_recipe_url = $("input[name=get_recipe_url]").val();
var post_recipe_url = $("input[name=post_recipe_url]").val();
var calendar_items_url = $("input[name=calendar_items_url]").val();

//Vue part
//Vue.http.headers.common['X-CSRF-TOKEN'] = csrftoken;
var app = new Vue({
    el: '#root',
    delimiters: ['[[', ']]'],
    data: {
        id: '',
        filter_facets: {
            rel_id_path: [],
            dekking_date: { start: null, end: null },
            typevergadering: []
        },
        sort_facets: {},
        query_facets: {
            query_spreker: null,
            query_agenda: null,
            query_string: null,
        },
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
        hits: [],
        aggs: {},
    },
    methods: {
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
        fill_calendar_events: function () {
            this.$http.get(calendar_items_url, {
            }).then(response => {
                var calendar_items = response.body;

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
            }, function (error) {
                console.log(error.statusText);
            });
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
        var startdt = today;
        startdt = startdt.setMonth(today.getMonth() - 3);

        var calendarEl = document.getElementById('calendar');
        this.calendar = new FullCalendar.Calendar(calendarEl, {
            locale: 'nl',
            plugins: ['dayGrid'],
            header: this.calendar_header,
            defaultDate: "2019-09-01",
            eventClick: function (info) {
                var calendar_item = info.event;
                app.calendar_item_click(calendar_item);
                info.el.style.borderColor = 'red';
            }
        });
        this.fill_calendar_events();
        this.calendar.render();
    },
});




