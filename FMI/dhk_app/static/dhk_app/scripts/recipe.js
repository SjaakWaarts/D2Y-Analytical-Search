// script.js

'use strict';

// JQuery
//(function ($) {
//    /*-------------------------------------
//    Rating selection
//    -------------------------------------*/
//    $('.rate-wrapper').on('click', '.rate .rate-item', function () {
//        var self = $(this),
//            target = self.parent('.rate');
//        target.addClass('selected');
//        target.find('.rate-item').removeClass('active');
//        self.addClass('active');
//    });
//})(jQuery);


//Set url and csrf variables
//var csrf_token = $("input[name=csrf_token]").val();
var csrftoken = $("input[name=csrfmiddlewaretoken]").val();
var recipe_get_url = $("input[name=recipe_get_url]").val();
var recipe_edit_url = $("input[name=recipe_edit_url]").val();
var recipe_post_url = $("input[name=recipe_post_url]").val();
var api_stream_file_url = $("input[name=api_stream_file_url]").val();

//Vue part
//Vue.http.headers.common['X-CSRF-TOKEN'] = csrftoken;
var app = new Vue({
    el: '#root',
    delimiters: ['[[', ']]'],
    data: {
        average_rating: 0,
        carousel: null,
        cooking_club: {
            'cook': "",
            'email': "",
            'cooking_date': "",
            'address': "",
            'position': null,
            'invitation': "",
            'cost': 0,
            'participants': [],
        },
        bindings: {
            participate_button_disabled: false,
        },
        cc_prev_available: false,
        cc_next_available: false,
        cooking_club_participant: {
            'user': "",
            'email': "",
            'comment': ""
        },
        error_messages: {},
        hits: [],
        id: '',
        leave_review: {
            'name': "",
            'email': "",
            'website': "",
            'stars': 0
        },
        recipe: null,
        shopping_basket: [],
    },
    methods: {
        bind_recipe_edit_url() {
            var url = recipe_edit_url + '?id=' + this.id;
            return encodeURI(url);
        },
        bind_recipe_get_url(format='json') {
            var url = recipe_get_url + '?id=' + this.id + '&format=pdf';
            return encodeURI(url);
        },
        bind_recipe_mail_review_url() {
            var url = "mailto:review@deheerlijkekeuken.nl?subject=" + this.id + "&body=<Plaats hier uw review EN foto's...>%0D%0A%0D%0AVoor een correcte verwerking, verander het Onderwerp niet!%0D%0ABedankt voor u review.";
            return url;
        },
        bind_stream_file_url(url, location) {
            return encodeURI(url + '?location=' + location);
        },
        bind_nav_tab_style(nrtabs) {
            var tab_width = 100 / nrtabs;
            return "width:" + tab_width.toString() + "%; display:flex";
        },
        club_tab_click: function () {
            var today = new Date();
            var dd = String(today.getDate()).padStart(2, '0');
            var mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
            var yyyy = today.getFullYear();
            today = yyyy + '-' + mm + '-' + dd + 'T19:30';
            // this.cooking_club.cooking_date = today;
            if (user.username != "") {
                this.cooking_club.cook = user.username;
                this.cooking_club.email = user.email;
                this.cooking_club.address = user.street + " " + user.housenumber + ", " + user.city;
            }
            this.draw_map();
        },
        club_join_marker_click: function (cooking_club) {
            var textarea_tag = document.getElementById("cc_invitation");
            textarea_tag.value = cooking_club.invitation;
            var cc_cooking_date_tag = document.getElementById("cc_cooking_date");
            var cc_create_button_tag = document.getElementById("cc_create_button");
            var cc_update_button_tag = document.getElementById("cc_update_button");
            var cc_delete_button_tag = document.getElementById("cc_delete_button");
            if (cooking_club.cook === user.username) {
                cc_cooking_date_tag.disabled = true;
                cc_create_button_tag.style.display = "none";
                cc_update_button_tag.style.visibility = "visible";
                cc_delete_button_tag.style.visibility = "visible";
            } else {
                cc_cooking_date_tag.disabled = false;
                cc_create_button_tag.style.display = "block";
                cc_update_button_tag.style.visibility = "hidden";
                cc_delete_button_tag.style.visibility = "hidden";
            }
            this.bindings.participate_button_disabled = false;
            this.cooking_club = cooking_club;
            if (user.username != "") {
                this.cooking_club_participant.user = user.username;
                this.cooking_club_participant.email = user.email;
                for (var px = 0; px < this.cooking_club.participants.length; px++) {
                    if (this.cooking_club.participants[px].user == user.username) {
                        this.bindings.participate_button_disabled = true;
                    }
                }
            } else {
                this.cooking_club_participant.user = "";
                this.cooking_club_participant.email = "";
                this.bindings.participate_button_disabled = false;
            }
            this.cooking_club_participant.comment = "";

            var textarea_tag = document.getElementById("participant_textarea");
            textarea_tag.value = this.cooking_club_participant.comment;
            var button_tag = document.getElementById("participate_button");
            button_tag.innerHTML = "AANMELDEN ETENTJE";
            button_tag.value = "new";
            this.cc_prev_available = false;
            this.cc_next_available = false;
            for (var ix = 0; ix < this.recipe.cooking_clubs.length; ix++) {
                if (cooking_club.cook == this.recipe.cooking_clubs[ix].cook) {
                    if (cooking_club.cooking_date > this.recipe.cooking_clubs[ix].cooking_date) {
                        this.cc_prev_available = true;
                    } else if (cooking_club.cooking_date < this.recipe.cooking_clubs[ix].cooking_date) {
                        this.cc_next_available = true;
                    }
                }
            }
            var recipe_model_div = document.getElementById('recipe-modal');
            $('#recipe-modal').modal('show');
            var cook = cooking_club.cook;
        },
        club_prev_next_click(direction) {
            var cc = null;
            if (direction == 'prev') {
                this.cc_prev_available = false;
            } else {
                this.cc_next_available = false;
            }
            for (var ix = 0; ix < this.recipe.cooking_clubs.length; ix++) {
                if (this.cooking_club.cook === this.recipe.cooking_clubs[ix].cook) {
                    if (this.cooking_club.cooking_date > this.recipe.cooking_clubs[ix].cooking_date && direction === 'prev') {
                        this.cc_next_available = true;
                        if (!cc) {
                            cc = this.recipe.cooking_clubs[ix];
                        } else {
                            this.cc_prev_available = true;
                            if (cc.cooking_date < this.recipe.cooking_clubs[ix].cooking_date) {
                                cc = this.recipe.cooking_clubs[ix];
                            }
                        }
                    } else if (this.cooking_club.cooking_date < this.recipe.cooking_clubs[ix].cooking_date && direction === 'next') {
                        this.cc_prev_available = true;
                        if (!cc) {
                            cc = this.recipe.cooking_clubs[ix];
                        } else {
                            this.cc_next_available = true;
                            if (cc.cooking_date > this.recipe.cooking_clubs[ix].cooking_date) {
                                cc = this.recipe.cooking_clubs[ix];
                            }
                        }
                    }
                }
            }
            if (cc) {
                this.cooking_club = cc;
                this.cooking_date = cc.cooking_date;
            }
        },
        club_participant_update_click: function (index) {
            this.cooking_club_participant.user = this.cooking_club.participants[index].user;
            this.cooking_club_participant.email = this.cooking_club.participants[index].email;
            this.cooking_club_participant.comment = this.cooking_club.participants[index].comment;
            var textarea_tag = document.getElementById("participant_textarea");
            textarea_tag.value = this.cooking_club_participant.comment;
            var button_tag = document.getElementById("participate_button");
            button_tag.innerHTML = "UPDATE AANMELDING";
            button_tag.value = "update-" + index;
            this.bindings.participate_button_disabled = true;
        },
        club_participant_delete_click: function (index) {
            this.cooking_club.participants.splice(index, 1);
            this.cooking_club_participant.user = "";
            this.cooking_club_participant.email = "";
            this.cooking_club_participant.comment = "";
            var textarea_tag = document.getElementById("participant_textarea");
            textarea_tag.value = this.cooking_club_participant.comment;
            var button_tag = document.getElementById("participate_button");
            button_tag.innerHTML = "AANMELDEN ETENTJE";
            button_tag.value = "new";
            this.recipe_post();
        },
        club_participant_me_click: function () {
            this.cooking_club_participant.user = user.username;
            this.cooking_club_participant.email = user.email;
            this.cooking_club_participant.comment = "";
        },
        recipe_get: function () {
            this.$http.get(recipe_get_url, { params: { id: this.id, format: 'json'  } }).then(response => {
                this.recipe = response.body.recipe;
                this.reviews = response.body.reviews;
                this.carousel = this.recipe.images;
                if (this.recipe.reviews.length === 0) {
                    this.average_rating = 0;
                } else {
                    var total_stars = 0;
                    for (var ix = 0; ix < this.recipe.reviews.length; ix++) {
                        total_stars += this.recipe.reviews[ix].stars;
                    }
                    this.average_rating = Math.ceil(total_stars / this.recipe.reviews.length);
                }
            });
        },
        review_post_click: function () {
            var review = {};
            var textarea_tag = document.getElementById("comment_textarea");
            var today = new Date();
            var dd = String(today.getDate()).padStart(2, '0');
            var mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
            var yyyy = today.getFullYear();
            today = yyyy + '-' + mm + '-' + dd;
            review.user = this.leave_review.name;
            review.review_date = today;
            review.review = textarea_tag.value;
            review.stars = this.leave_review.stars;
            this.recipe.reviews.push(review)
            this.recipe_post();
        },
        post_cooking_club_click: function (crud) {
            var textarea_tag = document.getElementById("cc_invitation");
            this.cooking_club.cancelled = (crud === 'delete');
            if (this.cooking_club.cancelled) {
                this.cooking_club.invitation = "GEANNULEERD!!\n"+textarea_tag.value;
            } else {
                this.cooking_club.invitation = textarea_tag.value;
            }
            this.error_messages = {};
            if (this.cooking_club.cooking_date == "") {
                this.error_messages['cooking_date'] = 'Datum EN tijd zijn verplicht!'
                return;
            }
            if (crud === 'create') {
                if (this.recipe.cooking_clubs.some(cc => cc.cooking_date == this.cooking_club.cooking_date)) {
                    alert("Kookclub voor die dag en kok bestaat al");
                    return;
                }
            }
            // asynchroon
            var geocoder = new google.maps.Geocoder();
            var position = null;
            geocoder.geocode({ 'address': this.cooking_club.address, 'region': 'nl' }, function (results, status) {
                if (status === 'OK') {
                    position = results[0].geometry.location;
                    app.cooking_club.position = position;
                    if (crud === 'create') {
                        app.recipe.cooking_clubs.push(app.cooking_club);
                    } else {
                        //var index = parseInt(button_tag.value.split('-')[1]);
                        //this.recipe.cooking_clubs[index] = this.cooking_club;
                    }
                    app.recipe_post();
                } else {
                    alert('Geocoding: "' + cooking_club.address + '", kan adres niet vinden, status: ' + status);
                }
            });
        },
        post_cooking_club_participant_click: function () {
            var participant = {};
            var textarea_tag = document.getElementById("participant_textarea");
            this.cooking_club_participant.comment = textarea_tag.value;
            participant.user = this.cooking_club_participant.user;
            participant.email = this.cooking_club_participant.email;
            participant.comment = this.cooking_club_participant.comment;
            var button_tag = document.getElementById("participate_button");
            if (button_tag.value == "new") {
                var found = false;
                for (var ix = 0; ix < this.cooking_club.participants.length; ix++) {
                    if (participant.user == this.cooking_club.participants[ix].user ||
                        participant.email == this.cooking_club.participants[ix].email) {
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    this.cooking_club.participants.push(participant);
                }
            } else {
                var index = parseInt(button_tag.value.split('-')[1]);
                this.cooking_club.participants[index] = participant;
            }
            this.recipe_post();
        },
        recipe_post: function () {
            var csrftoken_cookie = getCookie('csrftoken');
            var headers = { 'X-CSRFToken': csrftoken_cookie };
            this.$http.post(recipe_post_url, {
                'csrfmiddlewaretoken': csrftoken,
                'recipe': this.recipe,
            },
                { 'headers': headers }).then(response => {
                    this.recipe = response.body.recipe;
                    this.draw_map();
                });
        },
        recipe_ingredient_click: function (event, ingredient) {
            var checkbox_tag = event.target;
            var shopping_item;
            if (checkbox_tag.checked) {
                shopping_item = { 'checkbox_tag': checkbox_tag, 'ingredient': ingredient }
                this.shopping_basket.push(shopping_item);
            } else {
                for (var ix = 0; ix < this.shopping_basket.length; ix++) {
                    shopping_item = this.shopping_basket[ix];
                    if (shopping_item.checkbox_tag == checkbox_tag) {
                        this.shopping_basket.splice(ix, 1);
                        break;
                    }
                }
            }
        },
        review_rating_click: function () {
            var i_tag = event.target;
            var rate_item_tag = i_tag.parentElement;
            var rate_tag = rate_item_tag.parentElement;
            rate_tag.classList.add('selected');
            var active_rate_item_tag = rate_tag.querySelectorAll('.active');
            if (active_rate_item_tag.length > 0) {
                active_rate_item_tag[0].classList.remove('active');
            }
            rate_item_tag.classList.add('active');
            this.leave_review.stars = Number(rate_item_tag.id.slice(-1));
        },
        tab_activate: function(tab) {
            var selector = "#tabs a[href='" + tab + "']";
            $(selector).tab('show');
        },
        draw_map: function () {
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
            //markers = this.workbook.bigtable.
            //    filter(row => row.coord.lat != 0 && row.coord.lng != 0).
            //    map(function (row, i) {
            //        label = row.adres + ',' + row.plaats;
            //        position = new google.maps.LatLng(parseFloat(row.coord.lat), parseFloat(row.coord.lng));
            //        return new google.maps.Marker({
            //            position: position,
            //            label: label
            //        });
            //});
            for (var rownr=0, labelnr=0; rownr < this.recipe.cooking_clubs.length; rownr++) {
                var cooking_club = this.recipe.cooking_clubs[rownr];
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
                        google.maps.event.addListener(marker, 'click', (function (marker, label, cooking_club) {
                            return function () {
                                //infowindow.setContent(label + ' Gastheer: ' + cooking_club.cook + ' datum: ' + cooking_club.cooking_date);
                                //infowindow.open(map, marker);
                                app.club_join_marker_click(cooking_club);
                            }
                        })(marker, label, cooking_club));
                    }
                } else {
                    if (cooking_club.address.length > 2) {
                        //address = row.adres + ',' + row.plaats;
                        address = cooking_club.address;
                        var marker_label = label;
                        // asynchroon
                        //geocoder.geocode({ 'address': address, 'region': 'nl' }, function (results, status) {
                        //    if (status == 'OK') {
                        //        position = results[0].geometry.location;
                        //        var marker = new google.maps.Marker({
                        //            position: position,
                        //            map: map,
                        //            label: label
                        //        });
                        //        markers.push(marker);
                        //        bounds.extend(marker.position);
                        //        google.maps.event.addListener(marker, 'click', (function (marker, label) {
                        //            return function () {
                        //                infowindow.setContent(label);
                        //                infowindow.open(map, marker);
                        //            }
                        //        })(marker, marker_label));
                        //    } else {
                        //        console('Geocoding: ' + address + ', failed, status: ' + status);
                        //    }
                        //})(results, status);
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
        var urlParams = new URLSearchParams(window.location.search);
        this.id = decodeURI(urlParams.has('id') ? urlParams.get('id') : '');
        this.recipe_get();
        if (user.username != "") {
            this.cooking_club.cook = user.username;
            this.cooking_club.email = user.email;
            this.cooking_club.address = user.street + " " + user.housenumber + ", " + user.city;
            this.leave_review.name = user.username;
            this.leave_review.email = user.email;
        }
    },
    updated: function () {
        if (this.recipe.courses.length === 0) {
            this.draw_map();
        }
    }
});


function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}


