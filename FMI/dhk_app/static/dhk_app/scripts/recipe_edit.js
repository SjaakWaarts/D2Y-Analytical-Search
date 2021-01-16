// script.js

'use strict';

//Set url and csrf variables
//var csrf_token = $("input[name=csrf_token]").val();
var csrftoken = $("input[name=csrfmiddlewaretoken]").val();
var recipe_get_url = $("input[name=recipe_get_url]").val();
var recipe_edit_url = $("input[name=recipe_edit_url]").val();
var recipe_post_url = $("input[name=recipe_post_url]").val();
var recipe_images_search_url = $("input[name=recipe_images_search_url]").val();
var recipe_carousel_post_url = $("input[name=recipe_carousel_post_url]").val();
var api_stream_file_url = $("input[name=api_stream_file_url]").val();

//Vue part
//Vue.http.headers.common['X-CSRF-TOKEN'] = csrftoken;
var app = new Vue({
    el: '#root',
    delimiters: ['[[', ']]'],
    data: {
        carousel: [],
        featured_ix: null,
        error_messages: {},
        hits: [],
        id: '',
        recipe: null,
        shopping_basket: [],
    },
    methods: {
        bind_recipe_edit_url() {
            var url = recipe_edit_url + '?id=' + this.id;
            return encodeURI(url);
        },
        bind_recipe_get_url() {
            var url = recipe_get_url + '?id=' + this.id + '&format=pdf';
            return encodeURI(url);
        },
        bind_stream_file_url(url, location) {
            return encodeURI(url + '?location=' + location);
        },
        recipe_get: function () {
            this.$http.get(recipe_get_url, { params: { id: this.id, format: 'json'  } }).then(response => {
                this.recipe = response.body.recipe;
                this.reviews = response.body.reviews;
                for (var ix = 0; ix < this.recipe.images.length; ix++) {
                    var slide = {
                        'source': 'word',
                        'location': this.recipe.images[ix].location,
                        'featured': (this.recipe.images[ix].type === 'featured') ? true : false,
                        'checked': true,
                        'type': this.recipe.images[ix].type
                    }
                    this.carousel.push(slide)
                    if (slide.featured) { this.featured_ix = ix }
                }
                for (var ix = 0; ix < this.reviews.length; ix++) {
                    var slide = {
                        'source': 'review',
                        'location': this.reviews[ix].location,
                        'featured': false,
                        'checked': true,
                        'type': 'image'
                    }
                    this.carousel.push(slide)
                }
            });
        },
        recipe_image_radio_click(slide_ix) {
            if (this.featured_ix != null) { this.carousel[this.featured_ix].featured = false; }
            this.featured_ix = slide_ix;
            this.carousel[this.featured_ix].featured = true;
        },
        recipe_image_rotate_click(slide_ix) {
        },
        recipe_images_search_click: function () {
            var review = {};
            var textarea_tag = document.getElementById("search_text");
            var q = textarea_tag.value;
            textarea_tag.value = "Zoeken loopt...";
            this.$http.get(recipe_images_search_url, { params: { id: this.id, q: q } }).then(response => {
                var image_urls = response.body.image_urls;
                textarea_tag.value = q;
                this.carousel = this.carousel.filter(function (slide) {
                    return slide.source != 'search' && slide.checked == true;
                });
                for (var ix = 0; ix < image_urls.length; ix++) {
                    var slide = {
                        'source': 'search',
                        'location': image_urls[ix],
                        'featured': false,
                        'checked': false,
                        'type' : 'image'
                    }
                    this.carousel.push(slide)
                }
            });
        },
        recipe_carousel_post: function () {
            var csrftoken_cookie = getCookie('csrftoken');
            var headers = { 'X-CSRFToken': csrftoken_cookie };
            this.$http.post(recipe_carousel_post_url, {
                'csrfmiddlewaretoken': csrftoken,
                'recipe': this.recipe,
                'carousel' : this.carousel,
            },
                { 'headers': headers }).then(response => {
                    this.recipe = response.body.recipe;
                });
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
                });
        },
    },
    computed: {
    },
    mounted: function () {
        var urlParams = new URLSearchParams(window.location.search);
        this.id = decodeURI(urlParams.has('id') ? urlParams.get('id') : '');
        this.recipe_get();
        if (user.username != "") {
        }
    },
});


function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}


