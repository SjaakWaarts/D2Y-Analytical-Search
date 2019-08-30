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
var get_recipe_url = $("input[name=get_recipe_url]").val();
var post_recipe_url = $("input[name=post_recipe_url]").val();
var api_stream_file_url = $("input[name=api_stream_file_url]").val();

//Vue part
//Vue.http.headers.common['X-CSRF-TOKEN'] = csrftoken;
var app = new Vue({
    el: '#root',
    delimiters: ['[[', ']]'],
    data: {
        iframe_src: null,
        id : '',
        recipe: null,
        average_rating : 0,
        hits: [],
        shopping_basket: [],
        leave_review: {
            'comment': "",
            'name': "",
            'email': "",
            'website': "",
            'stars' : 0
        },
    },
    methods: {
        bind_stream_file_url(url, location) {
            return encodeURI(url + '?location=' + location);
        },
        bind_nav_tab_style(nrtabs) {
            var tab_width = 100 / nrtabs
            return "width:" + tab_width.toString()+"%; display:flex";
        },
        get_recipe: function () {
            this.$http.get(get_recipe_url, { params: { id: this.id }}).then(response => {
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
            });
        },
        leave_review_click: function () {
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
            this.post_recipe();
        },
        post_recipe: function () {
            var csrftoken_cookie = getCookie('csrftoken');
            var headers = { 'X-CSRFToken': csrftoken_cookie }
            this.$http.post(post_recipe_url, {
                'csrfmiddlewaretoken': csrftoken,
                'recipe': this.recipe,
            },
                { 'headers': headers }).then(response => {
                this.recipe = response.body.recipe;
            });
        },
        rate_click: function(event) {
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
        kookclub_tab_click: function () {
            var div_name = 'GoogleMap';
            this.draw_map(div_name);
        },
        kookclub_join_marker_click: function (cooking_club) {
            var cook = cooking_club.cook;
        },
        draw_map: function (elm_id) {
            var gmap_div = document.getElementById(elm_id);
            gmap_div.innerHTML = "";
            gmap_div.style.height = "400px";
            gmap_div.style.width = "100 %";
            var center = { lat: 52.090736, lng: 5.121420 };
            var zoom = 7;
            var mapType = google.maps.MapTypeId.ROADMAP;
            var label = "";
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
            map.setOptions({ minZoom: 7, maxZoom: 18, mapTypeId: mapType });
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
            for (var rownr = 0; rownr < this.recipe.cooking_clubs; rownr++) {
                var cooking_club = this.recipe.cooking_clubs[rownr];
                label = labels[rownr % labels.length];
                var position = null;
                if (cooking_club.location.lat != 0 && cooking_club.location.lng != 0) {
                    position = new google.maps.LatLng(parseFloat(cooking_club.location.lat), parseFloat(cooking_club.location.lng));
                    var marker = new google.maps.Marker({
                        position: position,
                        map: map,
                        label: label
                    });
                    markers.push(marker);
                    bounds.extend(marker.position);
                    google.maps.event.addListener(marker, 'click', (function (marker, label, cooking_club) {
                        return function () {
                            infowindow.setContent(label + 'kok ' + cooking_club.cook);
                            infowindow.open(map, marker);
                            app.kookclub_join_marker_click(cooking_club);
                        }
                    })(marker, label, cooking_club));
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
        this.get_recipe();
    },
});

function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}


